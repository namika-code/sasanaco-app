from flask import Blueprint, render_template, redirect, url_for
from models import db,  Product, Task,  Alert, AlertUser
from flask_login import login_required, current_user
from stock.views import calc_current_stock
from datetime import datetime

# topのBlueprint
top_bp = Blueprint('top', __name__, url_prefix='/top')

# =======================
# TOP画面
# =======================
@top_bp.route('/')
@login_required
def index():

    # タスク通知
    today = datetime.now()
    # 対象の通知を取得
    alerts = (
        db.session.query(Alert)
        .join(Alert.alert_users)
        .outerjoin(Alert.task)  # Task に JOIN
        .filter(
            AlertUser.user_id == current_user.user_id,
            AlertUser.is_read.is_(False),
            Alert.alert_since <= today,
            Alert.alert_until >= today,
            ~(
                (Alert.alert_type == 'deadline') &
                (Task.task_status == 'complete')
            )
        )
        .all()
    )

    low_stock_products = []

    # 総務だけ在庫チェック
    if current_user.department == '総務':
        products = Product.query.all()

        for p in products:
            current_stock = calc_current_stock(p.product_id)

            if current_stock <= (p.min_stock or 0):
                low_stock_products.append({
                    'product_id': p.product_id,
                    'product_name': p.product,
                    'current_stock': current_stock,
                    'min_stock': p.min_stock
                })

    return render_template('top/index.html', alerts=alerts, low_stock_products=low_stock_products, current_time=datetime.now())

# タスク通知既読処理
@top_bp.route('/alert/<int:alert_id>/read', methods=['POST'])
@login_required
def read_alert(alert_id):
    alert_user = AlertUser.query.filter_by(
        alert_id=alert_id,
        user_id=current_user.user_id
    ).first()

    if alert_user:
        alert_user.is_read = True   # 既読に変更
        db.session.commit()

    return redirect(url_for('top.index'))   # リダイレクトすると既読は消える
