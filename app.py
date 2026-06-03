from flask import Flask, session, redirect, url_for
from flask_migrate import Migrate
from models import db, User
from flask_login import LoginManager, current_user, logout_user
from flask_wtf.csrf import CSRFProtect
from auth.views import auth_bp
from task.views import task_bp
from wiki.views import wiki_bp
from top.views import top_bp
from stock.views import stock_bp
from rest.views import rest_bp
from mypage.views import mypage_bp
from alert.views import alert_bp
from config import LocalConfig, XreaConfig
from constants import LOCAL_SERVER, XREA_SERVER
import time
# =====================================
# サーバータイプ選択
# =====================================
server_type = LOCAL_SERVER
# server_type = XREA_SERVER

# ============================
# Flask
# ============================
app = Flask(__name__)

# =====================================
# Config
# =====================================
if server_type == LOCAL_SERVER:
    app.config.from_object(LocalConfig)
elif server_type == XREA_SERVER:
    app.config.from_object(XreaConfig)
# app.config.from_object(config.Config) 

# =====================================
# Extensions
# =====================================
csrf = CSRFProtect(app)     # CSRF有効化
db.init_app(app)            # dbとFlaskとの紐づけ
# with app.app_context():
#     db.create_all()  # 空っぽのDBに、最新のテーブルを自動で作成する
migrate = Migrate(app, db)  # マイグレーションとの紐づけ(Flaskとdb)

login_manager = LoginManager()  # インスタンス作成
login_manager.init_app(app)     # LoginManagerとFlaskとの紐づけ
login_manager.login_message = '認証していません:ログインしてください'
# 未認証のユーザーがアクセスした際リダイレクトされる関数名を設定
login_manager.login_view ='auth.login'  # blueprint対応

# =====================================
# Blueprint
# =====================================
app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)
app.register_blueprint(top_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(wiki_bp)
app.register_blueprint(rest_bp)
app.register_blueprint(mypage_bp)
app.register_blueprint(alert_bp)

# =====================================
# セッションタイムアウト監視（12時間）
# =====================================
@app.before_request
def check_session_timeout():
    # 1. ログインしていないユーザーはチェックをスルー
    if not current_user.is_authenticated:
        return

    # 2. XREAサーバーの時だけこのタイムアウト処理を動かす
    if app.config.get('SESSION_PERMANENT') == True:
        return

    now_ts = time.time()  # 現在の時刻を「秒数（数字）」で取得
    last_active_ts = session.get('last_active_ts')

    # 3. 最後の操作から「12時間（43200秒）」以上経っていたら強制ログアウト
    if last_active_ts and (now_ts - float(last_active_ts)) > 43200:
        logout_user()
        session.clear()
        return redirect(url_for('auth.login'))

    # 4. 操作があったら、最終アクティブ時刻を「現在の秒数」で更新
    session['last_active_ts'] = now_ts
    
# =====================================
# LoginManager
# =====================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ※こいつここに置かないといけない！！
# ルーティング情報はappのインスタンス作ってからimportする必要ある
from views import *

# ============================
# WSGI用/ CGI 用(今回XREAがWSGIサポートしてない説あるのでCGIで動かしてる)
# ============================
application = app

# ============================
# ローカル実行用
# ============================
if __name__ == '__main__':
    if isinstance(app, Flask):
        # 同じWiFi内で実行できる(上記コメントアウトして、下記有効)
        # サーバーになるPCのWindowsファイアウォールをオフにして、IPアドレス:5000って検索すればOK
        app.run(host='0.0.0.0', port=5000, debug=True) # 本番時は、debug=Falseで！！