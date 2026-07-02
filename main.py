from fastapi import FastAPI, Request

from ClaudeMessageParser import getInternalResponse, getLatestUserText
from ClaudeResponse import createClaudeResponse
from llmService import invokeOllama
from loggerConfig import setUpLogger
from readService import buildOllamaPrompt, readSampleMD

app = FastAPI()
logger = setUpLogger()


@app.get("/")
def root():
    return {"status": "LangChain Claude Bridge is running."}


@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()
    claudeMessage = body.get("messages", [])

    # ユーザーからの会話の身を取得する
    userText = getLatestUserText(claudeMessage)
    logger.info("input_text=%r", userText)

    # 内部処理用のものかを判定
    internalResponse = getInternalResponse(userText)

    if internalResponse is not None:
        logger.info("internal_request_response=%r", internalResponse)
        # None以外の値が入ると内部処理用として、そのままCluadeへ返す
        return createClaudeResponse(internalResponse)

    # マークダウン読み込みからOllamaへの送信
    markdown = readSampleMD()
    prompt = buildOllamaPrompt(userText, markdown)

    answer = invokeOllama(prompt)

    # Ollamaからの回答をClaude用に整形して返す
    return createClaudeResponse(answer)
