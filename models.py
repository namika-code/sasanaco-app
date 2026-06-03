from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import relationship
import constants as const
from datetime import datetime

db = SQLAlchemy()   # Flask-SQLAlchemyの作成

# ============================
# ユーザー
# ============================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    # ユーザーID
    user_id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
    ) 
     # ユーザー名
    username = db.Column(  
        db.String(const.DB_USER_NAME_MAX), 
        unique=True, 
        nullable=False,
    )
    # パスワード
    password = db.Column( 
        db.String(const.DB_USER_PASS_MAX), 
        nullable=False,
    )
    # 部署
    department = db.Column(
        db.String(const.DB_USER_DEPARTMENT_MAX),
        nullable=False,
    )
    # 姓
    last_name = db.Column(
        db.String(const.DB_USER_LAST_NAME_MAX),
        nullable=True,
    )
    # 名
    first_name = db.Column(
        db.String(const.DB_USER_FIRST_NAME_MAX),
        nullable=True,
    )
    # 性別
    gender = db.Column(
        db.Enum(
            'male',
            'female',
            'other',
            name='gender_enum'
        ),
        nullable=True,
    )

    # リレーション
    stocks = relationship('Stock', back_populates='user') # 1対多 (ユーザー 対 在庫)
    tasks = relationship('Task', back_populates='user', cascade='all, delete-orphan')   # 1対多 (ユーザー 対 タスク)
    group_members = relationship('GroupMember', back_populates='user', cascade='all, delete-orphan')    # 1対多 (ユーザー 対 グループメンバー)
    alert_users = relationship('AlertUser', back_populates='user', cascade='all, delete-orphan')        # User対AlertUser 1対多

    # パスワードをハッシュ化して設定
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    # 入力したパスワードとハッシュ化パスワードの比較
    def check_password(self, password):
        return check_password_hash(self.password, password)

    # Flask-Login用
    def get_id(self):
        return str(self.user_id)
    
    # フルネーム表示
    @property
    def full_name(self):
        if self.last_name and self.first_name:
            return f'{self.last_name} {self.first_name}'
        elif self.last_name:
            return self.last_name
        elif self.first_name:
            return self.first_name
        else:
            return self.username

# ============================
# 商品
# ============================
class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    # 商品ID
    product_id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
    )
    # 商品名
    product = db.Column(
        db.String(const.DB_PRODUCT_NAME_MAX),
        nullable=False,
    )
    # 商品コード
    product_code = db.Column(
        db.String(const.DB_PRODUCT_CODE_MAX), 
        unique=True,
        nullable=False,
    )
    # 商品カテゴリ
    product_category = db.Column(
        db.String(const.DB_PRODUCT_CATEGORY_MAX),
        nullable=False,        
    )
    # 在庫下限
    min_stock = db.Column(
        db.Integer, 
        nullable=False, 
        default=0
    )

    # リレーション
    stocks = relationship('Stock', back_populates='product')# 1対多 (商品 対 在庫)

    def get_id(self):
        return str(self.product_id)

# ============================
# 在庫
# ============================
class Stock(db.Model):
    __tablename__ = 'stocks'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    # 在庫ID
    stock_id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
    )
    # 商品ID
    product_id = db.Column(
        db.Integer, 
        db.ForeignKey('products.product_id'), 
        nullable=False,
    )
    # ユーザーID
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.user_id'), 
        nullable=False,
    )

    # 入出庫日
    inout_date = db.Column(
        db.DateTime, 
        default=datetime.now,
        nullable=False,
    )
    # 在庫種別
    stock_type = db.Column(
        db.String(const.DB_STOCK_TYPE_MAX), 
        nullable=False,
    )
    # 在庫数量
    stock_quantity = db.Column(
        db.Integer, 
        nullable=False, 
        default=0,
    )
    # 備考
    note = db.Column(
        db.String(const.DB_STOCK_NOTE_MAX),
        nullable=True
    )

    # リレーション
    user = relationship('User', back_populates='stocks')      # 多対1 (在庫 対 ユーザー)
    product = relationship('Product', back_populates='stocks')# 多対1 (在庫 対 商品)

    def get_id(self):
        return str(self.stock_id)


# ============================
# タスク
# ============================
class Task(db.Model):
    __tablename__ = 'tasks'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    # タスクID
    task_id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
    )
    # ユーザーID
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.user_id', ondelete='CASCADE'), 
        nullable=False,
    )
    # グループID
    group_id = db.Column(
        db.Integer, 
        db.ForeignKey('groups.group_id'), 
        nullable=True,
    )
    
    # タスク名
    title = db.Column(
        db.String(const.DB_TASK_TITLE), 
        nullable=False,
    )
    # タスク内容
    task_content = db.Column(
        db.String(const.DB_TASK_CONTENT), 
        nullable=True,
    )
    # タスク進捗状況
    task_status = db.Column(
        db.Enum('unstarted', 'progress', 'complete'), 
        nullable=False,
        default='unstarted',
    )
    # 作成日
    creation_date = db.Column(
        db.DateTime, 
        nullable=False,
        default=datetime.now,
    )
    # 開始日
    start_date = db.Column(
        db.DateTime, 
        nullable=False,
    )
    # 更新日
    update_date = db.Column(
        db.DateTime, 
        nullable=True,
        onupdate=datetime.now,
    )
    # 締切日
    due_date = db.Column(
        db.DateTime, 
        nullable=False,
    )
    # タスクコメント
    task_comment = db.Column(
        db.String(const.DB_TASK_COMMENT), 
        nullable=True,
    )    # DB的には2万文字くらいまでいける

    # リレーション
    user = relationship('User', back_populates='tasks')   # 多対1 (タスク 対 ユーザー)
    alerts = relationship('Alert', back_populates='task', cascade='all, delete-orphan') # 1対多 (タスク 対 通知)
    group = relationship('Group', back_populates='tasks') # 1対多 (タスク 対 グループ)

    def get_id(self):
        return str(self.task_id)  

# ============================
# 通知
# ============================
class Alert(db.Model):
    __tablename__ = 'alerts'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    # 通知ID
    alert_id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
    )
    # タスクID
    task_id = db.Column(
        db.Integer, 
        db.ForeignKey('tasks.task_id', ondelete='CASCADE'), 
        nullable=True,
    )

    # メッセージ
    message = db.Column(
        db.String(const.DB_ALERT_MESSAGE),
        nullable=False,
    )
    # 通知種別
    alert_type = db.Column(
        db.Enum(
            'registered', 
            'updated', 
            'comment_added', 
            'deadline', 
            'group_deleted',
        ),
        nullable=False,
        default='registered',
    )
    # 通知開始
    alert_since = db.Column(
        db.DateTime,
        nullable=True,
    )
    # 通知期限
    alert_until = db.Column(
        db.DateTime,
        nullable=True,
    )

    # リレーション
    task = relationship('Task', back_populates='alerts')  # 多対1 (通知 対 タスク)
    alert_users = relationship('AlertUser', back_populates='alert', cascade='all, delete-orphan')  # Alert対AlertUser 1対多
    
    def get_id(self):
        return str(self.alert_id)

# ============================
# 通知既読管理
# ============================
class AlertUser(db.Model):
    __tablename__ = 'alert_users'
    __table_args__ = (
        db.UniqueConstraint('alert_id', 'user_id'),
        {'mysql_engine': 'InnoDB'}
    )

    # 通知ユーザーID
    alert_user_id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
    )
    # 通知ID
    alert_id = db.Column(
        db.Integer, 
        db.ForeignKey('alerts.alert_id', ondelete='CASCADE'), 
        nullable=False,
    )
    # ユーザーID
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.user_id', ondelete='CASCADE'), 
        nullable=False,
    )
    # 既読
    is_read = db.Column(
        db.Boolean, 
        nullable=False,
        default=False,
    )

    # リレーション
    alert = db.relationship('Alert', back_populates='alert_users')      # Alert対AlertUser 1対多
    user = db.relationship('User', back_populates='alert_users')        # User対AlertUser 1対多

# ============================
# グループ
# ============================
class Group(db.Model):
    __tablename__ = 'groups'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    # グループID
    group_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    # グループ名
    groupname = db.Column(
        db.String(const.DB_GROUP_NAME),
        unique=True,
        nullable=False
    )

    # リレーション
    tasks = relationship('Task', back_populates='group')   # 1対多 (グループ 対 タスク)
    group_members = relationship(
        'GroupMember',
        back_populates='group',
        cascade='all, delete-orphan'
    )                                                      # 1対多 (グループ 対 グループメンバー)

    def get_id(self):
        return str(self.group_id)

# ============================
# グループメンバー
# ============================
class GroupMember(db.Model):
    __tablename__ = 'group_members'
    __table_args__ = (
        db.UniqueConstraint('group_id', 'user_id'),
        {'mysql_engine': 'InnoDB'}
    )

    # グループメンバーID
    group_member_id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
    )
    # グループID
    group_id = db.Column(
        db.Integer, 
        db.ForeignKey('groups.group_id', ondelete='CASCADE'), 
        nullable=False,
    )
    # ユーザーID
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.user_id', ondelete='CASCADE'), 
        nullable=False,
    )

    # リレーション
    user = relationship('User', back_populates='group_members')   # 多対1 (グループメンバー 対 ユーザー)
    group = relationship('Group', back_populates='group_members') # 1対多 (グループメンバー 対 グループ)

    def get_id(self):
        return str(self.group_member_id)