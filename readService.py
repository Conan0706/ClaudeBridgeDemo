from config import SAMPLE_MD_PATH

"""
# sample.mdを読み込み用関数
"""
def readSampleMD() -> str:
    if not SAMPLE_MD_PATH.exists():
        return "ERROR: sample.mdが見つかりません。"

    return SAMPLE_MD_PATH.read_text(encoding="utf-8")

"""
# Ollamaに送るプロンプトを整形
"""
def buildOllamaPrompt(user_text: str, markdown: str) -> str:
    return f"""
        以下のMarkdownを読んで、質問に答えてください。
        本文を丸ごとコピーせず、質問に必要な内容だけ答えてください。

        質問:
        {user_text}

        Markdown:
        {markdown}

        回答:
    """
