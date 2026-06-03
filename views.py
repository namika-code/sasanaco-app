from flask import render_template
from app import app
from werkzeug.exceptions import NotFound, InternalServerError
from flask import redirect, url_for

# =======================
# 404エラーハンドリング
# =======================
@app.errorhandler(NotFound)
def show_404_page(error):
    msg = error.description
    print('エラー内容:', msg)
    return render_template('errors/404.html', msg=msg), 404

# =======================
# 500エラーハンドリング
# =======================
@app.errorhandler(InternalServerError)
def show_500_page(error):
    # 500エラーの場合、error.descriptionには詳細が出ないことが多い
    print('サーバーエラーが発生しました')
    return render_template('errors/500.html'), 500

# =======================
# 最初に表示される画面
# =======================
@app.route("/")
def index():
    return redirect(url_for("auth.login"))