import os
from dotenv import load_dotenv

load_dotenv()

# =======================
# 設定
# =======================
class Config(object):
    DEBUG=True
    SECRET_KEY = os.getenv("SECRET_KEY")   # CSRFやセッションで使用
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 警告対策

class LocalConfig(Config):
    DEBUG=True
    SQLALCHEMY_DATABASE_URI = os.getenv("LOCAL_DB_URI")
    SESSION_PERMANENT = True        # セッションを保持（ブラウザを閉じてもログイン維持）

class XreaConfig(Config):
    DEBUG=False # 本番環境のため
    SQLALCHEMY_DATABASE_URI = os.getenv("XREA_DB_URI")
    SESSION_PERMANENT = False       # セッションを破棄（ブラウザを閉じたらログアウト）