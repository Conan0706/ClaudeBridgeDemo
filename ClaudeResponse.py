# 時刻取得用のパッケージ
import time
# api通信のJSONレスポンス返答用
from fastapi.responses import JSONResponse

from config import OLLAMA_MODEL

"""
Claudeに返すレスポンスをClaude用に整形する関数
"""
def createClaudeResponse(text: str) -> JSONResponse:
    return JSONResponse (
        {
            "id": f"msg_{int(time.time())}",
            "type": "message",
            "role": "assistant",
            "model": OLLAMA_MODEL,
            "content": [
                {
                    "type": "text",
                    "text": text,
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