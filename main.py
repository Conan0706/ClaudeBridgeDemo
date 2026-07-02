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

    logger.info("body keys: %s", list(body.keys()))

    claudeMessages = body.get("messages", [])

    logger.info("claudeMessages type: %s", type(claudeMessages).__name__)

    if isinstance(claudeMessages, list):
        logger.info("claudeMessages length: %s", len(claudeMessages))
        logger.info(
            "roles: %s",
            [
                msg.get("role") if isinstance(msg, dict) else type(msg).__name__
                for msg in claudeMessages
            ],
        )
    else:
        logger.info("claudeMessages value: %r", claudeMessages)

    userText = getLatestUserText(claudeMessages)
    logger.info("入力テキスト：%r", userText)

    internalResponse = getInternalResponse(userText)

    if internalResponse is not None:
        logger.info("内部リクエストとして処理します：%r", internalResponse)

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
            "model": "qwen2.5-coder:0.5b",
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

def extractTextFromContent(content) -> str:
    if isinstance(content, str):
        return content.strip()

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


def getLatestUserText(messages: list) -> str:
    for msg in reversed(messages):
        if msg.get("role") != "user":
            logger.info("最後のuserメッセージ：%s", json.dumps(msg, ensure_ascii=False, indent=2))
            break

        content = msg.get("content", "")
        text = extractTextFromContent(content)

        if text:
            return text

    return ""

def getInternalResponse(userText: str) -> str | None:
    if not userText:
        return ""

    if "[SUGGESTION MODE:" in userText:
        return ""

    if "Write the title in the predominant language" in userText:
        return "Claude Bridge検証"

    return None