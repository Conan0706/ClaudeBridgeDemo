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

"""
# 会話のロールがuserのものだけを抽出して返す関数
# 文章の抽出処理はextractTextFromContent()に投げる
"""
def getLatestUserText(messages: list) -> str:
    if not isinstance(messages, list):
        return ""
    
    for msg in reversed(messages):
        if not isinstance(msg, dict):
            continue

        if msg.get("role") != "user":
            continue

        content = msg.get("content", "")
        text = extractTextFromContent(content)

        if text:
            return text

    return ""

"""
# Claude CodeからBridgeに送られる内部リクエストをOllamaに投げるかの仕分け関数
# Ollamaに投げる情報が肥大化しすぎないように
"""
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