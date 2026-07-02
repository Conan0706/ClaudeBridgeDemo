# ファイル/ディレクトリ操作用のパッケージ
from pathlib import Path
# OSに関する操作、今回は環境変数セット用
import os
# 時刻取得用のパッケージ
import time

import json
import logging
from logging.handlers import RotatingFileHandler

# fastAPI取得
from fastapi import FastAPI, Request
# api通信のJSONレスポンス返答用
from fastapi.responses import JSONResponse
# Ollama操作用
from langchain_ollama import ChatOllama
# システムメッセージ(役割やルール)、メッセージ(プロンプト)指示用
from langchain_core.messages import HumanMessage

app = FastAPI()

# resolve() : 相対パスを絶対パスに変換
# Pathオブジェクトに変換しておく
BASE_DIR = Path(__file__).parent.resolve()

# TODO ログに関する情報を出力が安定したら削除する
# ログ出力用
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "bridge.log"

logger = logging.getLogger("claude_bridge")
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=1024 * 1024 * 5,
    backupCount=3,
    encoding="utf-8",
)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
)

file_handler.setFormatter(formatter)

logger.handlers.clear()
logger.addHandler(file_handler)

# / : 結合用
SAMPLE_MD_PATH = BASE_DIR / "sample.md"
# ollamaへのリンク
OLLAMA_LINK = "http://host.docker.internal:11434"

llm = ChatOllama(
    model = "qwen2.5-coder:3b",
    base_url = OLLAMA_LINK,
    temperature = 0.2, # ランダム性：高いほど自由度が高い、低いほど固い
)

@app.get("/")
def root():
    return {"status": "LangChain Claude Bridge is running."}


@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()

    claudeMessages = body.get("messages", [])

    userText = getLatestUserText(claudeMessages)

    # 内部処理用かユーザーからの入力のものかを判定
    internalResponse = getInternalResponse(userText)

    # 内部処理に関するものはOllamaに投げずそのままClaude Codeへ返す
    if internalResponse is not None:
        return JSONResponse(
            {
                "id": f"msg_{int(time.time())}",
                "type": "message",
                "role": "assistant",
                "model": "qwen2.5-coder:3b",
                "content": [
                    {
                        "type": "text",
                        "text": internalResponse,
                    }
                ],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                },
            }
        )

    # Markdownを呼んで回答を返す
    sampleMd = readSampleMd()

    prompt = f"""
        以下のMarkdownを読んで、質問に答えてください。
        本文を丸ごとコピーせず、質問に必要な内容だけ答えてください。

        質問:
        {userText}

        Markdown:
        {sampleMd}

        回答:
    """

    langChainMessages = [
        HumanMessage(content=prompt)
    ]

    result = llm.invoke(langChainMessages)

    answer = result.content.strip()

    return JSONResponse(
        {
            "id": f"msg_{int(time.time())}",
            "type": "message",
            "role": "assistant",
            "model": "qwen2.5-coder:3b",
            "content": [
                {
                    "type": "text",
                    "text": answer,
                }
            ],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
            },
        }
    )

# sample.md読み込み用関数
# 戻り値をstrで返す型ヒント指定
def readSampleMd() -> str:
    if not SAMPLE_MD_PATH.exists():
        return "ERROR:sample.mdが見つかりません。"
    
    return SAMPLE_MD_PATH.read_text(encoding = "utf-8")

# Claudeからの値を文章に整形する
def extractTextFromContent(content) -> str:
    # 文字列なら空文字を削除して返す
    if isinstance(content, str):
        return content.strip()

    # Listなら配列にtextを取得して返す
    if isinstance(content, list):
        texts = []

        for item in content:
            if isinstance(item, str):
                texts.append(item.strip())

            elif isinstance(item, dict):
                text = item.get("text", "")

                if text:
                    text = text.strip()

                    # Claude Codeが追加するsystem-reminderは除外
                    if not text.startswith("<system-reminder>"):
                        texts.append(text)

        return "\n".join([text for text in texts if text]).strip()

    return ""

# 会話のロールがuserのものだけを抽出して返す
# 文章の抽出処理はextractTextFromContent()に投げる
def getLatestUserText(messages: list) -> str:
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue

        content = msg.get("content", "")
        logger.info(content)
        text = extractTextFromContent(content)

        if text:
            return text

    return ""

# Claude CodeからBridgeに送られる内部リクエストをOllamaに投げるか仕分ける
# Ollamaに投げる情報が肥大化しすぎないように
def getInternalResponse(userText: str) -> str | None:
    # userTextがからの場合は内部処理として空文字を返す
    if not userText:
        return ""

    # SUGGESTION MODEは次にユーザーが入力しそうな候補をあげるものなので不要
    if "[SUGGESTION MODE:" in userText:
        return ""

    # 会話タイトルは固定で[Claude Bridge検証]
    if "Write the title in the predominant language" in userText:
        return "Claude Bridge検証"

    return None