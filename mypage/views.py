from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from models import db, User, Product, Stock, Task,  Alert, AlertUser, Group, GroupMember
from forms import ProfileForm
from flask_login import login_required, current_user
from wtforms.validators import ValidationError
from datetime import date, timedelta, datetime

from constants import ( # 修正するときあればここも他と一緒にしてほしい…
    USER_DEPARTMENTS, 
    PRODUCT_CATEGORIES, 
    PRODUCT_INOUT,
    PRODUCT_NAME_MAX,
    PRODUCT_CODE_MAX,
    NOTE_MAX,
    STOCK_QUANTITY_MAX,
    STOCK_QUANTITY_MIN,
    USER_NAME_MAX, 
    USER_PASS_MIN, 
    USER_PASS_MAX,
)

# mypageのBlueprint
mypage_bp = Blueprint('mypage', __name__, url_prefix='/mypage')

# =======================
# ルーティング
# =======================
# 管理者トップページ
@mypage_bp.route('/')
@login_required
def index():
    # 画面遷移
    form = ProfileForm(obj=current_user)
    return render_template('mypage/index.html', form=form)


# ==============================================
# ここから管理者メニュー
# ==============================================
# ユーザの一括登録
@mypage_bp.route('/admin_register_form', methods=['GET', 'POST'])
@login_required
def admin_register_form():
    if request.method == 'POST':
        errors = []
        rows = []  # 入力値を保持してテンプレートに返す

        # 全行を読み込んでエラーがないか確認する
        for i in range(10):
            row = {
                "username": request.form.get(f"username_{i}", "").strip(),
                "password": request.form.get(f"password_{i}", "").strip(),
                "department": request.form.get(f"department_{i}", "").strip(),
                "last_name": request.form.get(f"last_name_{i}", "").strip(),
                "first_name": request.form.get(f"first_name_{i}", "").strip(),
                "gender": request.form.get(f"gender_{i}", "").strip(),
            }
            rows.append(row)

        # バリデーション
        for i, row in enumerate(rows):
            username = row["username"]
            password = row["password"]
            department = row["department"]
            

            # 全部空なら無視
            if not username:    # 一旦これで通してるけど修正必要っぽい。下記で正しいはずだけど、JSかHTMLでずれてる可能性あり
                continue
            # if not username and not password and not department:
            #     continue

            # ユーザー名
            if not username:
                errors.append(f"{i+1} 行目: ユーザー名が未入力です。")
            elif len(username) > USER_NAME_MAX:
                errors.append(f"{i+1} 行目: ユーザー名は{USER_NAME_MAX}文字以内です。")
            else:
                # 重複確認
                existing = User.query.filter_by(username=username).first()
                if existing:
                    errors.append(f"{i+1} 行目: ユーザー名「{username}」は既に登録されています。")

            # パスワード
            if not password:
                errors.append(f"{i+1} 行目: パスワードが未入力です。")
            elif not (USER_PASS_MIN <= len(password) <= USER_PASS_MAX):
                errors.append(f"{i+1} 行目: パスワードは{USER_PASS_MIN}〜{USER_PASS_MAX}文字です。")
            elif not (
                any(c.isalpha() for c in password) and
                any(c.isdigit() for c in password) and
                any(c in '!@#$%^&*()' for c in password)
            ):
                errors.append(f"{i+1} 行目: パスワードには英字・数字・記号(!@#$%^&*())を含めてください。")

            # 部署
            if not department:
                errors.append(f"{i+1} 行目: 部署が未選択です。")
            elif department not in USER_DEPARTMENTS:
                errors.append(f"{i+1} 行目: 不正な部署が選択されました。")

        # エラーがあれば登録しない、入力残して入力一覧表示
        if errors:
            for e in errors:
                flash(e)
            return render_template(
                'mypage/admin_register_form.html', 
                departments=USER_DEPARTMENTS, 
                rows=rows,
                USER_NAME_MAX=USER_NAME_MAX,
                USER_PASS_MIN=USER_PASS_MIN,
                USER_PASS_MAX=USER_PASS_MAX,
            )

        # エラー無ければ登録
        count = 0
        for row in rows:
            username = row["username"]
            password = row["password"]
            department = row["department"]

            if not username:  # 空行とばす
                continue

            user = User(
                username=username,
                department=department,
                last_name=row["last_name"] or None,
                first_name=row["first_name"] or None,
                gender=row["gender"] or None
            )

            user.set_password(password)
            db.session.add(user)
            count += 1

        db.session.commit()
        if count == 0:
            flash("登録するユーザーがありません。")
            return redirect(url_for('mypage.admin_register_form'))

        flash(f"{count} 件のユーザーを登録しました。")
        return redirect(url_for('mypage.admin_register_form'))

    # GETの場合
    return render_template(
        'mypage/admin_register_form.html',
        departments=USER_DEPARTMENTS,
        rows=[{
            "username": "",
            "password": "",
            "department": USER_DEPARTMENTS[0],
            "last_name": "",
            "first_name": "",
            "gender": ""
        } for _ in range(10)],
        USER_NAME_MAX=USER_NAME_MAX,
        USER_PASS_MIN=USER_PASS_MIN,
        USER_PASS_MAX=USER_PASS_MAX,
    )

# ユーザ一覧を表示
@mypage_bp.route('/users/list')
@login_required
def user_list():
    users = User.query.all()
    return render_template('mypage/user_list.html', users=users)

# 選択したユーザを削除
@mypage_bp.route('/users/delete_selected', methods=['POST'])
@login_required
def delete_selected_users():
    ids = request.form.getlist('user_ids')
    
    # 実際に削除対象となった件数をカウントする用
    deleted_count = 0

    if ids:
        for user_id in ids:
            # user_id=1（管理者）は絶対に削除処理を通さない
            if int(user_id) == 1:
                continue
            
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                deleted_count += 1
        
        if deleted_count > 0:
            db.session.commit()
            flash(f"{deleted_count} 件のユーザを削除しました。")
        else:
            flash("有効なユーザが選択されていません。")

    return redirect(url_for('mypage.user_list'))

# タスクの一括登録
@mypage_bp.route('/admin_task_register', methods=['GET', 'POST'])
@login_required
def admin_task_register():
    groups = Group.query.all()  # プルダウン用

    # メンバー名リストの辞書を作る
    group_members = {
        str(g.group_id): [
            m.user.full_name if m.user else "(不明なユーザー)"
            for m in g.group_members
        ]
        for g in groups
    }

    if request.method == 'POST':
        errors = []
        rows = []

        # 全行を読み込んでエラーがないか確認する
        for i in range(10):
            row = {
                "title": request.form.get(f"title_{i}", "").strip(),
                "content": request.form.get(f"content_{i}", "").strip(),
                "start": request.form.get(f"start_{i}", "").strip(),
                "due": request.form.get(f"due_{i}", "").strip(),
                "group": request.form.get(f"group_{i}", "").strip(),
            }
            rows.append(row)

        # バリデーション
        for i, row in enumerate(rows):
            title = row["title"]
            content = row["content"]
            start = row["start"]
            due = row["due"]
            group = row["group"]

            # 全部空なら無視
            if not title and not content and not start and not due and not group:
                continue

            # タイトル
            if not title:
                errors.append(f"{i+1} 行目: タスク名が未入力です。")
            elif len(title) > 40:
                errors.append(f"{i+1} 行目: タスク名は40文字以内です。")

            # タスク内容
            if content and len(content) > 2400:
                errors.append(f"{i+1} 行目: タスク内容は2400文字以内です。")

            # 開始日
            if not start:
                errors.append(f"{i+1} 行目: 開始日が未入力です。")

            # 締切日
            if not due:
                errors.append(f"{i+1} 行目: 締切日が未入力です。")

            # 開始日と締切日の前後チェック
            if start and due:
                try:
                    start_date = date.fromisoformat(start)
                    due_date = date.fromisoformat(due)
                    if due_date < start_date:
                        errors.append(f"{i+1} 行目: 締切日は開始日より後の日付を入力してください。")
                except ValueError:
                    errors.append(f"{i+1} 行目: 日付の形式が不正です。")

            # グループ(空欄はプライベート)
            if group:
                g = Group.query.get(group)
                if not g:
                    errors.append(f"{i+1} 行目: 不正なグループが選択されました。")

        # エラーがあれば登録しない、入力残して入力一覧表示
        if errors:
            for e in errors:
                flash(e)
            return render_template('mypage/admin_task_register.html', rows=rows, groups=groups, group_members=group_members)

        # エラー無ければ登録
        count = 0
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        username = current_user.username

        for row in rows:
            if not row["title"]:  # 空行とばす
                continue

            task = Task(
                user_id=current_user.user_id,
                title=row["title"],
                task_content=row["content"],
                start_date=row["start"],
                due_date=row["due"],
                creation_date=date.today(),
                group_id=row["group"] or None
            )
            db.session.add(task)
            db.session.commit()  # task_id を確定させる
            # 通知登録
            make_alert(task, timestamp, username, type='registered')
            db.session.commit()

            count += 1

        if count == 0:
            flash("登録するタスクがありません。")
        else:        
            flash(f"{count} 件のタスクを登録しました。")
        return redirect(url_for('mypage.admin_task_register'))

    # GETの場合
    return render_template(
        'mypage/admin_task_register.html',
        rows=[{"title": "", "content": "", "start": "", "due": "", "group": ""} for _ in range(10)],
        groups=groups, group_members=group_members
    )

# タスク一覧を表示
@mypage_bp.route('/tasks/list')
@login_required
def task_list():
    tasks = Task.query.all()
    return render_template('mypage/task_list.html', tasks=tasks)

# 選択したタスクを削除
@mypage_bp.route('/tasks/delete_selected', methods=['POST'])
@login_required
def delete_selected_tasks():
    ids = request.form.getlist('task_ids')

    if ids:
        for task_id in ids:
            task = Task.query.get(task_id)
            if task:
                db.session.delete(task)
        db.session.commit()
        flash(f"{len(ids)} 件のタスクを削除しました。")

    return redirect(url_for('mypage.task_list'))

# グループ一覧を表示
@mypage_bp.route('/groups/list')
@login_required
def group_list():
    groups = Group.query.all()
    return render_template('mypage/group_list.html', groups=groups)

# 選択したグループを削除
@mypage_bp.route('/groups/delete_selected', methods=['POST'])
@login_required
def delete_selected_groups():
    ids = request.form.getlist('group_ids')

    if ids:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        username = current_user.username

        for group_id in ids:
            group = Group.query.get(group_id)
            if group:
                # 削除する前にグループ削除通知を作成
                make_alert2(group, timestamp, username)
                db.session.commit()

                # グループに紐づくタスクを取得
                tasks = Task.query.filter_by(group_id=group.group_id).all()
                # タスクに紐づく通知を削除
                for task in tasks:
                    alerts = Alert.query.filter_by(task_id=task.task_id).all()
                    for alert in alerts:
                        db.session.delete(alert)
                db.session.commit()

                # グループ＋メンバー削除
                db.session.delete(group)
        db.session.commit()
        flash(f"{len(ids)} 件のグループを削除しました。")

    return redirect(url_for('mypage.group_list'))

# グループ作成
@mypage_bp.route('/admin_group_create', methods=['GET', 'POST'])
def admin_group_create():
    users = User.query.order_by(User.username).all()

    if request.method == 'POST':
        print(request.form)
        groupname = request.form.get("groupname", "").strip()
        selected_members = request.form.getlist("members[]")

        errors = []

        # バリデーション
        if not groupname:
            errors.append("グループ名が未入力です。")
        elif len(groupname) > 20:
            errors.append("グループ名は20文字以内です。")
        else:
            # 重複確認
            existing = Group.query.filter_by(groupname=groupname).first()
            if existing:
                errors.append(f"グループ名「{groupname}」は既に存在しています。")

        # 未選択はエラー
        if not selected_members:
            errors.append("メンバーが選択されていません。")

        # エラーがあれば再表示
        if errors:
            for e in errors:
                flash(e)
            return render_template(
                "mypage/admin_group_create.html",
                users=users, groupname=groupname, selected_members=[int(m) for m in selected_members]
            )

        # エラー無ければ登録
        group = Group(groupname=groupname)
        db.session.add(group)
        db.session.flush()  # group_idを取得

        for uid in selected_members:
            gm = GroupMember(group_id=group.group_id, user_id=int(uid))
            db.session.add(gm)

        db.session.commit()
        flash("グループを作成しました。")

        return redirect(url_for('mypage.admin_group_create'))

    # GET の場合
    return render_template("mypage/admin_group_create.html", users=users, groupname="", selected_members=[])

# グループ編集
@mypage_bp.route('/admin_group_edit/<int:group_id>', methods=['GET', 'POST'])
def admin_group_edit(group_id):
    group = Group.query.get_or_404(group_id)
    users = User.query.order_by(User.username).all()

    if request.method == 'POST':
        groupname = request.form.get("groupname", "").strip()
        selected_members = request.form.getlist("members[]")

        errors = []

        # バリデーション
        if not groupname:
            errors.append("グループ名が未入力です。")
        elif len(groupname) > 20:
            errors.append("グループ名は20文字以内です。")
        else:
            # 重複確認
            existing = Group.query.filter(
                Group.groupname == groupname,
                Group.group_id != group.group_id
            ).first()
            if existing:
                errors.append(f"グループ名「{groupname}」は既に存在しています。")

        if not selected_members:
            errors.append("メンバーが選択されていません。")

        if errors:
            for e in errors:
                flash(e)
            return render_template(
                "mypage/admin_group_edit.html",
                group=group, users=users, groupname=groupname, selected_members=[int(m) for m in selected_members]
            )

        # 上書きする
        group.groupname = groupname
        GroupMember.query.filter_by(group_id=group.group_id).delete()  # 既存メンバーを全消し
        for uid in selected_members:
            group_member = GroupMember(group_id=group.group_id, user_id=int(uid))
            db.session.add(group_member)

        db.session.commit()
        flash("グループを更新しました。")

        return redirect(url_for('mypage.group_list'))

    # GET の場合
    selected_members = [gm.user_id for gm in group.group_members]

    return render_template(
        "mypage/admin_group_edit.html",
        group=group, users=users, groupname=group.groupname, selected_members=selected_members
    )

# 編集画面へ移動
@mypage_bp.route('/admin_group_edit_redirect')
def admin_group_edit_redirect():
    group_ids = request.args.getlist("group_ids")
    group_id = int(group_ids[0])
    return redirect(url_for('mypage.admin_group_edit', group_id=group_id))

# 通知をテーブルに登録
def make_alert(task, timestamp, username, type):
    if type == 'registered':
        message = f"({timestamp}){username}さんがタスクを登録しました。"
    elif type == 'updated':
        message = f"({timestamp}){username}さんがタスクを更新しました。"
    elif type == 'comment_added':
        message = f"({timestamp}){username}さんがコメントを追加しました。"
    else:
        pass
    
    # 更新通知を登録
    alert = Alert(
        task_id=task.task_id,
        alert_type=type,
        alert_since=datetime.now(),
        alert_until=datetime.now() + timedelta(days=7),
        message=message
    )
    db.session.add(alert)

    # 通知相手を登録
    # グループ登録されている時、メンバー全員に(コメントした人以外)
    if task.group_id:
        members = GroupMember.query.filter_by(group_id=task.group_id).all()
        for member in members:
            if member.user_id != current_user.user_id:
                db.session.add(AlertUser(alert=alert, user_id=member.user_id))
    # プライベートの時、タスク作成者だけに(コメントした人(=管理者)以外)
    else:
        if task.user_id != current_user.user_id:
            db.session.add(AlertUser(alert=alert, user_id=task.user_id))

    # 新規登録だったら、期限3日前更新通知登録
    if type == 'registered' and task.due_date:
        alert2 = Alert(
            task_id=task.task_id,
            alert_type='deadline',
            alert_since=task.due_date - timedelta(days=3),
            alert_until=task.due_date,
            message="期限まで３日をきっています。"
        )
        db.session.add(alert2)

        # タスク作成者(自分)だけに
        db.session.add(AlertUser(alert=alert2,user_id=task.user_id))

    # 更新だったら時、期限3日前通知の日付を上書き
    if type == 'updated' and task.due_date:
        # 通知一覧テーブルから対象のデータを取得
        alert2 = Alert.query.filter_by(
            task_id=task.task_id,
            alert_type='deadline'
        ).first()

        # たぶん、ないことはないけど。
        if alert2:
            # 既存の三日前通知を更新。変更していなくても、変更していても上書き。
            alert2.alert_since = task.due_date - timedelta(days=3)
            alert2.alert_until = task.due_date
        else:
            # もし存在しなければ新規作成。たぶん、ないことはないけど。
            alert2 = Alert(
                task_id=task.task_id,
                alert_type='deadline',
                alert_since=task.due_date - timedelta(days=3),
                alert_until=task.due_date,
                message="期限まで３日をきっています。"
            )
            db.session.add(alert2)

            # タスク作成者だけに通知
            db.session.add(AlertUser(alert=alert2, user_id=task.user_id))

# 通知をテーブルに登録　グループ削除通知
def make_alert2(group, timestamp, username):
    message = f"({timestamp}){username}さんがグループ「{group.groupname}」を削除しました。"

    alert = Alert(
        task_id=None,  # グループ削除task_id不要
        alert_type='group_deleted',
        alert_since=datetime.now(),
        alert_until=datetime.now() + timedelta(days=7),
        message=message
    )
    db.session.add(alert)

    # 通知相手：グループに所属していた全メンバー
    members = GroupMember.query.filter_by(group_id=group.group_id).all()
    for member in members:
        db.session.add(AlertUser(alert=alert, user_id=member.user_id))


# 商品の一括登録
@mypage_bp.route('/admin_stock_register', methods=['GET', 'POST'])
@login_required
def admin_stock_register():

    if request.method == 'POST':

        errors = []
        rows = []

        # 入力取得
        for i in range(10):

            row = {
                "product_code": request.form.get(f"product_code_{i}", "").strip().upper(),
                "product": request.form.get(f"product_{i}", "").strip(),
                "product_category": request.form.get(f"product_category_{i}", "").strip(),
                "min_stock": request.form.get(f"min_stock_{i}", "").strip(),
                "inout_date": request.form.get(f"inout_date_{i}", "").strip(),
                "stock_quantity": request.form.get(f"stock_quantity_{i}", "").strip(),
                "note": request.form.get(f"note_{i}", "").strip(),
            }

            rows.append(row)

        # バリデーション
        for i, row in enumerate(rows):

            product_code = row["product_code"]
            product = row["product"]
            category = row["product_category"]
            min_stock = row["min_stock"]
            inout_date = row["inout_date"]
            stock_quantity = row["stock_quantity"]
            note = row["note"]

            # 完全空行スキップ
            if (
                product_code == "" and product == "" and category == "" and
                min_stock == "" and inout_date == "" and stock_quantity == "" and note == ""
            ):
                continue

            # 商品コード
            if product_code == "":
                errors.append(f"{i+1} 行目: 商品コードが未入力です。")
            elif len(product_code) > PRODUCT_CODE_MAX:
                errors.append(f"{i+1} 行目: 商品コードは{PRODUCT_CODE_MAX}文字以内です。")
            else:
                existing = Product.query.filter_by(product_code=product_code).first()
                if existing:
                    errors.append(
                        f"{i+1} 行目: 商品コード「{product_code}」は既に登録されています。"
                    )

            # 商品名
            if product == "":
                errors.append(f"{i+1} 行目: 商品名が未入力です。")
            elif len(product) > PRODUCT_NAME_MAX:
                errors.append(f"{i+1} 行目: 商品名は{PRODUCT_NAME_MAX}文字以内です。")

            # カテゴリ
            if category == "":
                errors.append(f"{i+1} 行目: カテゴリが未選択です。")
            elif category not in PRODUCT_CATEGORIES:
                errors.append(f"{i+1} 行目: 不正なカテゴリです。")

            # 在庫下限
            if min_stock == "":
                errors.append(f"{i+1} 行目: 在庫下限が未入力です。")
            else:
                try:
                    min_stock_int = int(min_stock)

                    if not (STOCK_QUANTITY_MIN <= min_stock_int <= STOCK_QUANTITY_MAX):
                        errors.append(
                            f"{i+1} 行目: 在庫下限は{STOCK_QUANTITY_MIN}〜{STOCK_QUANTITY_MAX}の範囲で入力してください。"
                        )

                except ValueError:
                    errors.append(f"{i+1} 行目: 在庫下限は数値で入力してください。")

            # 日付
            if inout_date == "":
                errors.append(f"{i+1} 行目: 日付が未入力です。")

            # 数量
            if stock_quantity == "":
                errors.append(f"{i+1} 行目: 数量が未入力です。")
            else:
                try:
                    qty = int(stock_quantity)

                    if not (STOCK_QUANTITY_MIN <= qty <= STOCK_QUANTITY_MAX):
                        errors.append(
                            f"{i+1} 行目: 数量は{STOCK_QUANTITY_MIN}〜{STOCK_QUANTITY_MAX}で入力してください。"
                        )

                except ValueError:
                    errors.append(f"{i+1} 行目: 数量は数値で入力してください。")

            # 備考
            if len(note) > NOTE_MAX:
                errors.append(f"{i+1} 行目: 備考は{NOTE_MAX}文字以内です。")

        # エラー時
        if errors:
            for e in errors:
                flash(e)

            return render_template(
                'mypage/admin_stock_register.html',
                rows=rows,
                PRODUCT_CATEGORIES=PRODUCT_CATEGORIES,
                PRODUCT_INOUT=PRODUCT_INOUT,

                PRODUCT_NAME_MAX=PRODUCT_NAME_MAX,
                PRODUCT_CODE_MAX=PRODUCT_CODE_MAX,

                STOCK_QUANTITY_MIN=STOCK_QUANTITY_MIN,
                STOCK_QUANTITY_MAX=STOCK_QUANTITY_MAX,
                NOTE_MAX=NOTE_MAX,
            )

        # 登録
        count = 0

        for row in rows:

            if row["product_code"] == "":
                continue

            product = Product(
                product_code=row["product_code"],
                product=row["product"],
                product_category=row["product_category"],
                min_stock=int(row["min_stock"])
            )

            db.session.add(product)
            db.session.flush()

            stock = Stock(
                product_id=product.product_id,
                user_id=current_user.user_id,
                inout_date=date.fromisoformat(row["inout_date"]),
                stock_type=PRODUCT_INOUT[0],  # 入庫固定
                stock_quantity=int(row["stock_quantity"]),
                note=row["note"]
            )

            db.session.add(stock)
            count += 1

        db.session.commit()

        if count == 0:
            flash("登録する商品がありません。")
        else:
            flash(f"{count} 件の商品を登録しました。")

        return redirect(url_for('mypage.admin_stock_register'))

    # GET
    return render_template(
        'mypage/admin_stock_register.html',
        rows=[{
            "product_code": "",
            "product": "",
            "product_category": "",
            "min_stock": "",
            "inout_date": "",
            "stock_quantity": "",
            "note": ""
        } for _ in range(10)],
        PRODUCT_CATEGORIES=PRODUCT_CATEGORIES,
        PRODUCT_INOUT=PRODUCT_INOUT,

        PRODUCT_NAME_MAX=PRODUCT_NAME_MAX,
        PRODUCT_CODE_MAX=PRODUCT_CODE_MAX,

        STOCK_QUANTITY_MIN=STOCK_QUANTITY_MIN,
        STOCK_QUANTITY_MAX=STOCK_QUANTITY_MAX,
        NOTE_MAX=NOTE_MAX,
    )


# 在庫管理表一覧を表示
@mypage_bp.route('/stocks/list')
@login_required
def stock_list():

    # Product一覧
    products = Product.query.order_by(Product.product_id).all()

    return render_template(
        'mypage/stock_list.html',
        products=products
    )

# 管理者：在庫表一括削除（商品単位）
@mypage_bp.route('/stock/delete_selected', methods=['POST'])
@login_required
def delete_selected_stocks():

    # 管理者チェック
    if current_user.user_id != 1:
        abort(403)

    # 商品IDを取得（stock_idsじゃなくproduct_idsにする）
    product_ids = request.form.getlist('product_ids')

    if not product_ids:
        flash('選択されていません')
        return redirect(url_for('mypage.stock_list'))

    # 商品単位で削除
    for product_id in product_ids:

        product = Product.query.get(product_id)
        
        if product:

            # ① 在庫履歴を全部削除
            Stock.query.filter_by(product_id=product_id).delete()

            # ② 商品（在庫表）を削除
            db.session.delete(product)

    db.session.commit()

    flash('選択した在庫管理表を削除しました')
    return redirect(url_for('mypage.stock_list'))

# ---------------------------------------------------------
# プロフィール更新
@mypage_bp.route('/profile/update', methods=['POST'])
@login_required
def profile_update():
    form = ProfileForm()

    if form.validate_on_submit():
        current_user.last_name = form.last_name.data
        current_user.first_name = form.first_name.data
        current_user.gender = form.gender.data or None

        db.session.commit()
        flash("プロフィールを更新しました。")

    return redirect(url_for('mypage.index'))