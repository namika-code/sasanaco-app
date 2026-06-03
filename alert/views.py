from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import db, AlertUser

alert_bp = Blueprint('alert', __name__, url_prefix='/alert')

# 通知既読処理
@alert_bp.route('/read/<int:alert_user_id>', methods=['POST'])
@login_required
def read_alert(alert_user_id):

    alert_user = AlertUser.query.filter_by(
        alert_user_id=alert_user_id,
        user_id=current_user.user_id
    ).first_or_404()

    alert_user.is_read = True
    db.session.commit()

    return jsonify({
        "success": True,
        "alert_user_id": alert_user_id,
        "alert_id": alert_user.alert_id
    })