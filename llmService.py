# Ollama操作用
from langchain_ollama import ChatOllama
# システムメッセージ(役割やルール)、メッセージ(プロンプト)指示用
from langchain_core.messages import HumanMessage

from config import OLLAMA_LINK, OLLAMA_MODEL, OLLAMA_TEMPERATURE

llm = ChatOllama(
    model = OLLAMA_MODEL,
    base_url = OLLAMA_LINK,
    temperature = OLLAMA_TEMPERATURE
)

"""
# Ollama送信用関数
"""
def invokeOllama(prompt: str) -> str:
    result = llm.invoke([HumanMessage(content=prompt)])
    return result.content.strip()