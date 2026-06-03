from flask import Blueprint, render_template, redirect, url_for, flash
from models import db, User
from forms import LoginForm, SignUpForm
from flask_login import login_user, logout_user, login_required, current_user
from constants import (
    USER_NAME_MAX, 
    USER_PASS_MIN,
    USER_PASS_MAX,
)

# authのBlueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# =======================
# ログイン
# =======================
@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    # ログイン済みなら認証を飛ばしてトップページへ
    if current_user.is_authenticated:
        return redirect(url_for('top.index'))
    
    form = LoginForm()  # インスタンス生成
    if form.validate_on_submit():
        # データ入力取得
        username = form.username.data
        password = form.password.data
        # 対象User取得
        user = User.query.filter_by(username=username).first()

        # 認証判定
        if user and user.check_password(password):
            # 成功
            login_user(user)    # 引数のuser使用してユーザーログイン状態へ
            return redirect(url_for('top.index'))
        else:
            # 失敗
            flash('ログインできませんでした')

    return render_template(
        'auth/login_form.html', 
        form=form,
        USER_NAME_MAX=USER_NAME_MAX, 
        USER_PASS_MIN=USER_PASS_MIN,
        USER_PASS_MAX=USER_PASS_MAX,
    )

# =======================
# ログアウト
# =======================
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()   # 現在ログインしてるユーザーをログアウト
    flash('ログアウトしました')
    return redirect(url_for('auth.login'))


# サインアップ(Form使用)
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = SignUpForm() # インスタンス生成
    if form.validate_on_submit():
        # データ入力取得
        username = form.username.data
        password = form.password.data
        department = form.department.data
        last_name = form.last_name.data
        first_name = form.first_name.data
        gender = form.gender.data or None

        # モデル生成
        user = User(
            username=username,
            department=department,
            last_name=last_name,
            first_name=first_name,
            gender=gender
        )
        # パスワードハッシュ化
        user.set_password(password)

        # 登録処理
        db.session.add(user)
        db.session.commit()
        flash('ユーザー登録しました')
        return redirect(url_for('auth.login'))
    
    return render_template(
        'auth/register_form.html', 
        form=form,
        USER_NAME_MAX=USER_NAME_MAX, 
        USER_PASS_MIN=USER_PASS_MIN,
        USER_PASS_MAX=USER_PASS_MAX,
    )

