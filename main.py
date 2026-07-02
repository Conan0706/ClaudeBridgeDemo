# ファイル/ディレクトリ操作用のパッケージ
from pathlib import Path
# OSに関する操作、今回は環境変数セット用
import os
# 時刻取得用のパッケージ
import time

# fastAPI取得
from fastapi import FastAPI, Request
# api通信のJSONレスポンス返答用
from fastapi.responses import JSONResponse
# Ollama操作用
from langchain_ollama import ChatOllama
# システムメッセージ(役割やルール)、メッセージ(プロンプト)指示用
from langchain_core.messages import HumanMessage, SystemMessage

app = FastAPI()

# resolve() : 相対パスを絶対パスに変換
# Pathオブジェクトに変換しておく
BASE_DIR = Path(__file__).parent.resolve()
# / : 結合用
SAMPLE_MD_PATH = BASE_DIR / "sample.md"
# ollamaへのリンク
OLLAMA_LINK = "http://host.docker.internal:11434"

llm = ChatOllama(
    model = "qwen2.5-coder:0.5b",
    base_url = OLLAMA_LINK,
    temperature = 0.2, # ランダム性：高いほど自由度が高い、低いほど固い
)

@app.get("/")
def root():
    return {"status": "LangChain Claude Bridge is running."}


@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()

    claudeMessages = body.get("messeges",[])
    systemPrompt = body.get("system", "")

    userText = getLatestUserText(claudeMessages)
    sampleMd = readSampleMd()

    prompt = f"""
        あなたはClaude Code CLIから呼び出されるローカルLLMです。

        ユーザーの依頼：{userText}

        以下はBridge側で読み込んだsample.mdの内容です。
        --- sample.md ---
        {sampleMd}
        --- end ---

        sample.mdの内容を参照して、ユーザーの依頼に答えてください。
    """
    langChainMessages = []

    if systemPrompt:
        langChainMessages.append(SystemMessage(content = systemPrompt))
    
    langChainMessages.append(HumanMessage(content = prompt))

    # invoke：ローカルLLMにテキストを渡して生成を行う
    result = llm.invoke(langChainMessages)

    return JSONResponse(
        {
            "id": f"msg_{int(time.time())}",
            "type": "message",
            "role": "assistant",
            "model": body.get("model", "qwen2.5-coder:0.5b"),
            "content": [
                {
                    "type": "text",
                    "text": result.content,
                }
            ],
            "stop_response": "end_turn",
            "stop_sequence": None, # 停止文字列の指定
            "usage": {
                "input_token": 0,
                "output_token": 0,
            }
        }
    )

# sample.md読み込み用関数
# 戻り値をstrで返す型ヒント指定
def readSampleMd() -> str:
    if not SAMPLE_MD_PATH.exists():
        return "ERROR:sample.mdが見つかりません。"
    
    return SAMPLE_MD_PATH.read_text(encoding = "utf-8")

def getLatestUserText(messages):

    # 送られたメッセージのうち、最後のuesrメッセージのみ取り出す
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        
        # TODO 後ほどレスポンスを分岐しなくていいように調整できないか検討
        content = msg.get("content", "")

        # 文字列ならそのまま返す
        if isinstance(content, str):
            return content
        
        # Listでメッセージが返る場合テキストに整形
        if isinstance(content, list):
            texts = []
            for item in content:
                if item.get("type") == "text":
                    texts.append(item.get("text", ""))
            return "\n".join(texts)
    return ""