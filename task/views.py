from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, Task,  Alert, AlertUser, Group, GroupMember
from forms import TaskForm
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from datetime import date, timedelta, datetime, time

# taskのBlueprint
task_bp = Blueprint('task', __name__, url_prefix='/task')

# =======================
# ルーティング
# =======================

################################################################################################
################################################################################################
# 一覧
@task_bp.route('/')
@login_required
def index():

    # 全部取得の場合
    # 未着手課題を取得
    # unstarted_tasks  = Task.query.filter_by(task_status='unstarted').all()
    # # 未完了課題を取得
    # uncompleted_tasks  = Task.query.filter_by(task_status='progress').all()
    # # 完了課題を取得
    # completed_tasks  = Task.query.filter_by(task_status='complete').all()

    # 全員、関係する分のみ取得           
    unstarted_tasks = (
        db.session.query(Task)
        .outerjoin(Group)
        .outerjoin(GroupMember)
        .filter(
            or_(GroupMember.user_id == current_user.user_id,
                Task.user_id == current_user.user_id),
            Task.task_status == "unstarted"
        )
        .order_by(Task.due_date.asc(), Task.start_date.asc())
        .all()
    )

    uncompleted_tasks = (
        db.session.query(Task)
        .outerjoin(Group)
        .outerjoin(GroupMember)
        .filter(
            or_(GroupMember.user_id == current_user.user_id,
                Task.user_id == current_user.user_id),
            Task.task_status == "progress"
        )
        .order_by(Task.due_date.asc(), Task.start_date.asc())
        .all()
    )

    completed_tasks = (
        db.session.query(Task)
        .outerjoin(Group)
        .outerjoin(GroupMember)
        .filter(
            or_(GroupMember.user_id == current_user.user_id,
                Task.user_id == current_user.user_id),
            Task.task_status == "complete"
        )
        .order_by(Task.due_date.desc(), Task.start_date.desc())
        .all()
    )


    return render_template(
        'task/index.html',
        unstarted_tasks=unstarted_tasks,
        uncompleted_tasks=uncompleted_tasks, 
        completed_tasks=completed_tasks,
        date=date,
        timedelta=timedelta
    )
################################################################################################
################################################################################################

# =========================
# タスク作成
# =========================
@task_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = TaskForm()   # Formインスタンス追加
    
    # DBからgroupを取得し、タプルリストを作成
    form.group_id.choices = [(-1, 'プライベート')] + [(g.group_id, g.groupname) for g in Group.query.all()]
    
    if form.validate_on_submit():
        # データ入力取得
        title = form.title.data
        content = form.task_content.data
        group_id = form.group_id.data
        if group_id == -1:
            group_id = None
        task_status = form.task_status.data
        
        # 🔴【DateTime対応】フォームの日付データに時間を結合する
        # 開始日は「その日の 00:00:00」にする
        start_datetime = datetime.combine(form.start_date.data, time.min)
        # 締切日も「その日の 00:00:00」にする
        due_datetime = datetime.combine(form.due_date.data, time.min)
        
        if title:
            # 登録処理
            task = Task(
                title=title,
                task_content=content,
                user_id=current_user.user_id,
                group_id=group_id,
                task_status=task_status,
                start_date=start_datetime,  # 変換後のDateTime型を渡す
                due_date=due_datetime,      # 変換後のDateTime型を渡す
            )
            db.session.add(task)  # ここで自動的に creation_date に現在日時を挿入

            # 通知用
            # いったんコミット --> 通知登録時にtaskテーブルを使う
            db.session.commit()
            
            timestamp = task.creation_date.strftime('%Y-%m-%d %H:%M')
            username = current_user.full_name
            
            # 通知テーブルを作成する関数呼び出し
            make_alert(task, timestamp, username, type='registered')
            # 通知をコミット
            db.session.commit()

            flash('タスクを新規登録しました。')
            # 画面遷移
            return redirect(url_for('task.index'))
            
    return render_template('task/create_task.html', form=form, task=None, current_date=date.today())

# ユーザー一覧読込(select2用)
@task_bp.route('/api/users')
@login_required
def users_api():
    users = User.query.all()
    return [
        {
            'id': u.user_id,
            'text': u.full_name,
            'username': u.username,
            'department': u.department
        }
        for u in users
    ]

# グループの新規作成
@task_bp.route('/api/group', methods=['POST'])
@login_required
def create_group_api():

    data = request.get_json()

    groupname = (data.get('groupname') or "").strip()

    # 空チェック
    if not groupname:
        return {"error": "グループ名は必須です"}, 400

    # 重複チェック
    exists = Group.query.filter_by(groupname=groupname).first()

    if exists:
        return {"error": "同名のグループが既に存在します"}, 409

    group = Group(groupname=groupname)

    db.session.add(group)
    db.session.flush()

    members = data.get('members') or []

    # 型統一 + 重複排除
    members = list(set(int(m) for m in members if m))

    # 自分は必ず入れる
    members.append(current_user.user_id)

    # 再度重複除去
    members = list(set(members))

    for uid in members:
        db.session.add(GroupMember(
            group_id=group.group_id,
            user_id=uid
        ))

    try:
        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return {
            "error": "同名のグループが既に存在します"
        }, 409

    return {
        "group_id": group.group_id,
        "groupname": group.groupname,
        "members": members
    }

# 既存グループの読込
@task_bp.route('/api/group/<int:group_id>', methods=['GET'])
@login_required
def get_group_api(group_id):

    group = Group.query.get_or_404(group_id)

    members = (
        db.session.query(User)
        .join(GroupMember, GroupMember.user_id == User.user_id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )

    return {
        "group_id": group.group_id,
        "groupname": group.groupname,
        "members": [
            {
                "id": u.user_id,
                "name": u.full_name,
                "department": u.department,
                "gender": u.gender
            }
            for u in members
        ]
    }

# 既存グループのメンバー更新
@task_bp.route('/api/group/<int:group_id>/members', methods=['PUT'])
@login_required
def sync_group_members(group_id):

    data = request.get_json()
    
    raw_members = data.get("members", [])
    new_members = set(
        int(m) for m in raw_members if str(m).isdigit()
    )

    current_members = {
        m.user_id for m in GroupMember.query.filter_by(group_id=group_id)
    }

    # 追加
    to_add = new_members - current_members
    # 削除
    to_delete = current_members - new_members

    if to_delete:
        GroupMember.query.filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id.in_(to_delete)
        ).delete(synchronize_session=False)

    for uid in to_add:
        db.session.add(GroupMember(
            group_id=group_id,
            user_id=uid
        ))

    db.session.commit()

    return {"success": True}

# 更新(Form使用)
@task_bp.route('/update/<int:task_id>', methods=['GET', 'POST'])
@login_required
def update(task_id):
    # DBから一致メモ取得。見つからんなら404エラー表示
    target_data = Task.query.filter_by(
        task_id=task_id, 
        user_id=current_user.user_id
        ).first_or_404()
    form = TaskForm(obj=target_data, task_id=target_data.task_id)
    
    # DBからgroupを取得し、タプルリストを作成
    form.group_id.choices = [(-1, 'プライベート')] + [(g.group_id, g.groupname) for g in Group.query.all()]
    
    if form.validate_on_submit():
        # 変更処理
        target_data.title = form.title.data
        target_data.task_content = form.task_content.data

        target_data.start_date = datetime.combine(form.start_date.data, time.min)
        target_data.due_date = datetime.combine(form.due_date.data, time.min)
        
        group_id = form.group_id.data
        target_data.group_id = None if group_id == -1 else group_id
        target_data.task_status = form.task_status.data

        # 通知用
        # 日時とユーザーを取得
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        username = current_user.full_name
        # 通知テーブルを作成する関数呼び出し
        make_alert(target_data, timestamp, username, type='updated')

        db.session.commit() # ここで自動的に update_date に現在日時を挿入
        
        flash('タスク内容を更新しました。')
        # 画面遷移
        return redirect(url_for('task.index'))
    
    return render_template(
        'task/update_task.html',
        form=form,
        edit_id=target_data.task_id,
        creation_date=target_data.creation_date,
        update_date=target_data.update_date
    )
    
# 削除ボタン
@task_bp.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete(task_id):
    # 対象データ取得。見つからんなら404エラー表示
    # 管理者は全部削除可
    if current_user.user_id == 1:
        task = Task.query.filter_by(task_id=task_id).first_or_404()
    # 管理者以外は入力したタスクのみ削除可
    else:           
        task = Task.query.filter_by(
            task_id=task_id, 
            user_id=current_user.user_id
            ).first_or_404()

    # 削除処理
    db.session.delete(task)
    db.session.commit()
    flash('タスクを削除しました。')
    # 画面遷移
    return redirect(url_for('task.index'))

# 完了ボタン
@task_bp.route('/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    # 対象データ取得。見つからんなら404エラー表示
    task = Task.query.get_or_404(task_id)
    # ステータスに「complete」を設定
    task.task_status = 'complete'
    db.session.commit()
    # 画面遷移
    return redirect(url_for('task.index'))

# 未完了ボタン
@task_bp.route('/<int:task_id>/uncomplete', methods=['POST'])
@login_required
def uncomplete_task(task_id):
    # 対象データ取得。見つからんなら404エラー表示
    task = Task.query.get_or_404(task_id)
    # ステータスに「progress」を設定
    task.task_status = 'progress'
    db.session.commit()
    # 画面遷移
    return redirect(url_for('task.index'))

# 未着手ボタン
@task_bp.route('/<int:task_id>/unstart', methods=['POST'])
@login_required
def unstart_task(task_id):
    # 対象データ取得。見つからんなら404エラー表示
    task = Task.query.get_or_404(task_id)
    # ステータスに「unstarted」を設定
    task.task_status = 'unstarted'
    db.session.commit()
    # 画面遷移
    return redirect(url_for('task.index'))

# コメント追加
@task_bp.route('/comment/<int:task_id>/add', methods=['POST'])
@login_required
def add_comment(task_id):
    # 対象データ取得。見つからんなら404エラー表示
    task = Task.query.get_or_404(task_id)

    # 日時とユーザーを取得
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    username = current_user.full_name
    # 入力されたコメントを取得
    comment = (request.form.get('task_comment') or '').strip()
    # 追加するコメントに日時、入力者追加
    new_comment = f"({timestamp}){username}: {comment}"

    # これまでのコメントを取得
    old_comment = (task.task_comment or '').strip()

    # 登録するコメントを組立て
    if old_comment == '':       # 空＝１つ目
        registered_comment = new_comment
    else:                       # ２つ目以降
        registered_comment = old_comment + '\n' + new_comment

    # コメントテーブル作っていないから、コメントは１つだけ。2500文字までとする。10件くらい
    if len(registered_comment) > 2500:    
        flash('これ以上コメントを追加できません。')
    else:
        task.task_comment = registered_comment

        # テーブルの更新日を変更する
        # task.update_date = date.today()  
        task.update_date = datetime.now()
        # models.pyを date -> datetimeに変更のため更新

        # 通知テーブルを作成する関数呼び出し
        make_alert(task, timestamp, username, type='comment_added')
        
        db.session.commit()
        flash('コメントを追加しました。')
    # 画面遷移
    return redirect(url_for('task.index'))

# コメント削除
@task_bp.route('/comment/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_comment(task_id):
    # 対象データ取得。見つからんなら404エラー表示
    task = Task.query.get_or_404(task_id)
    # タスク自体は消さないから空で上書き
    task.task_comment = ""
    db.session.commit()
    flash('コメントを削除しました。')
    # 画面遷移
    return redirect(url_for('task.index'))

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
        # 💡 開始は3日前の 00:00:00 から
        since_datetime = datetime.combine(task.due_date.date() - timedelta(days=3), datetime.min.time())
        # 💡 終了は締切日当日の 23:59:59 までしっかり残す！
        until_datetime = datetime.combine(task.due_date.date(), datetime.max.time())
        
        alert2 = Alert(
            task_id=task.task_id,
            alert_type='deadline',
            alert_since=since_datetime,
            alert_until=until_datetime,
            message="期限まで３日をきっています。"
        )
        db.session.add(alert2)
        
        # タスク作成者(自分)だけに
        db.session.add(AlertUser(alert=alert2, user_id=task.user_id))

    # 更新だったら時、期限3日前通知の日付を上書き
    if type == 'updated' and task.due_date:
        # 通知一覧テーブルから対象のデータを取得
        since_datetime = datetime.combine(task.due_date.date() - timedelta(days=3), datetime.min.time())
        until_datetime = datetime.combine(task.due_date.date(), datetime.max.time())
        
        alert2 = Alert.query.filter_by(
            task_id=task.task_id,
            alert_type='deadline'
        ).first()

        # たぶん、ないことはないけど。
        if alert2:
            # 既存の三日前通知を更新。変更していなくても、変更していても上書き。
            alert2.alert_since = since_datetime
            alert2.alert_until = until_datetime
        else:
            # もし存在しなければ新規作成。たぶん、ないことはないけど。
            alert2 = Alert(
                task_id=task.task_id,
                alert_type='deadline',
                alert_since=since_datetime,
                alert_until=until_datetime,
                message="期限まで３日をきっています。"
            )
            db.session.add(alert2)
            
            # タスク作成者だけに通知
            db.session.add(AlertUser(alert=alert2, user_id=task.user_id))