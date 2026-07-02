# ファイル/ディレクトリ操作用のパッケージ
from pathlib import Path

# resolve() : 相対パスを絶対パスに変換
# Pathオブジェクトに変換しておく
BASE_DIR = Path(__file__).parent.resolve()
# / : 結合用
SAMPLE_MD_PATH = BASE_DIR / "sample.md"

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "bridge.log"

OLLAMA_LINK = "http://host.docker.internal:11434"
OLLAMA_MODEL = "qwen2.5-coder:3b"
OLLAMA_TEMPERATURE = 0.2 # ランダム性：高いほど自由度が高い、低いほど固い
