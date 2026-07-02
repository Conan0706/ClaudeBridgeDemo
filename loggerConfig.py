import logging
from logging.handlers import RotatingFileHandler

from config import LOG_DIR, LOG_FILE

"""
# ログファイルの出力セットアップ
# main.pyで初回に呼ばれる
"""
def setUpLogger() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger("claude_bridge")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    fileHundler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024 * 1024 * 5,
        backupCount=3,
        encoding="utf-8",
    )

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fileHundler.setFormatter(formatter)

    logger.addHandler(fileHundler)

    return logger
