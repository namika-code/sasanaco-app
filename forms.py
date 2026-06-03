from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField, SubmitField, PasswordField, RadioField, DateField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange, InputRequired, Optional
from models import User
import datetime
from models import Product
import constants as const

# ==========================
# タスク用入力クラス
# ==========================
class TaskForm(FlaskForm):
    title = StringField('タスク名：')
    task_content = TextAreaField('タスク内容：')
    start_date = DateField(
        '開始日：',
        format='%Y-%m-%d',
        default=datetime.date.today,
        render_kw={'max': const.DATE_MAX},
    )
    due_date = DateField(
        '締切日：', 
        format='%Y-%m-%d',
        default=datetime.date.today,
        render_kw={'max': const.DATE_MAX},
    )
    group_id = SelectField('グループ：', coerce=int, validators=[])
    task_status = RadioField(
        'ステータス：',
        choices=[
            ('unstarted', '未着手'),
            ('progress', '進行中'),
            ('complete', '完了')
        ],
        default='unstarted'
    )
    submit = SubmitField('送信')
    

    def __init__(self, task_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_id = task_id
    
    def validate_start_date(self, field):
        if field.data:
            if field.data.year > 9999:
                raise ValidationError("年の値が不正です")
        
    def validate_due_date(self, field):
        if self.start_date.data and field.data:
            if field.data < self.start_date.data:
                raise ValidationError('締切日は開始日以降にしてください')
            if field.data.year > 9999:
                raise ValidationError("年の値が不正です")
        
# ==========================
# ログイン用入力クラス
# ==========================
class LoginForm(FlaskForm):
    username = StringField('ユーザー名:',
                            validators=[
                                DataRequired(message='ユーザー名を入力してください'),
                                Length(max=const.USER_NAME_MAX, message=f'ユーザー名は{const.USER_NAME_MAX}文字以内で入力してください')
                            ]
    )
    password = PasswordField('パスワード:',
                            validators=[
                                DataRequired(message='パスワードを入力してください'),
                                Length(const.USER_PASS_MIN, const.USER_PASS_MAX, message=f'{const.USER_PASS_MIN}〜{const.USER_PASS_MAX}文字で入力してください')
                            ]
    )
    submit = SubmitField('ログイン')

# ==========================
# ユーザーの属性情報（名前、性別）
# ==========================
class BaseProfileForm(FlaskForm):
    last_name = StringField(
        '姓',
        validators=[
            Optional(),
            Length(max=30)
        ]
    )
    first_name = StringField(
        '名',
        validators=[
            Optional(),
            Length(max=30)
        ]
    )
    gender = SelectField(
        '性別',
        choices=[
            ('', '未選択'),
            ('male', '男性'),
            ('female', '女性'),
            ('other', 'その他')
        ],
        validators=[Optional()]
    )

# ==========================
# ユーザー登録用入力クラス
# ==========================
class SignUpForm(BaseProfileForm):
    username = StringField(
        'ユーザー名',
        validators=[
            DataRequired(message='ユーザー名を入力してください'),
            Length(max=const.USER_NAME_MAX, message=f'ユーザー名は{const.USER_NAME_MAX}文字以内で入力してください')
        ]
    )
    password = PasswordField(
        'パスワード',
        validators=[
            DataRequired(message='パスワードを作成してください'),
            Length(const.USER_PASS_MIN, const.USER_PASS_MAX, message=f'{const.USER_PASS_MIN}〜{const.USER_PASS_MAX}文字で作成してください')
        ]
    )
    department = SelectField(
        '部署',
        choices=[(d, d) for d in const.USER_DEPARTMENTS],
        validators=[DataRequired(message='部署を選択してください')]
    )
    submit = SubmitField('ユーザー登録')

    # カスタムバリデータ(ユーザー名重複チェック)
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('そのユーザー名は既に使用されています')
    
    # カスタムバリデータ(英数字、記号含まれてるかチェック)
    def validate_password(self, password):
        if not (
            any(c.isalpha() for c in password.data) and \
            any(c.isdigit() for c in password.data) and \
            any(c in '!@#$%^&*()' for c in password.data)
        ):
            raise ValidationError('パスワードには【英数字と記号:!@#$%^&*()】を含める必要があります')

# ==========================
# ユーザー情報編集用入力クラス
# ==========================
class ProfileForm(BaseProfileForm):
    submit = SubmitField('更新')

# ==========================
# Wiki用入力クラス
# ==========================
class WikiForm(FlaskForm):
    # タイトル
    keyword = StringField('検索ワード:', render_kw={ 'placeholder': '入力してください'})
    submit = SubmitField('Wiki検索')
    
# ==========================
# 商品登録用クラス
# ==========================
class CreateStockForm(FlaskForm):
    # カスタムバリデータ(商品コード重複チェック)
    def validate_product_code(self, field):
        code = field.data.upper()

        product = Product.query.filter(
            Product.product_code == code
        ).first()

        if product:
            raise ValidationError('この商品コードは既に登録されています')
        field.data = code

    # product
    product_code = StringField(
        '商品コード',
        validators=[
            DataRequired(message='商品コードは必須です'),
            Length(max=const.PRODUCT_CODE_MAX, message=f'{const.PRODUCT_CODE_MAX}文字以内で入力してください')
        ]
    )

    product = StringField(
        '商品名',
        validators=[
            DataRequired(message='商品名は必須です'),
            Length(max=const.PRODUCT_NAME_MAX, message=f'{const.PRODUCT_NAME_MAX}文字以内で入力してください')
        ]
    )

    product_category = RadioField(
        'カテゴリ',
        choices=[(c, c) for c in const.PRODUCT_CATEGORIES],
        validators=[
            DataRequired(message='カテゴリを選択してください')
        ]
    )

    min_stock = IntegerField(
        '在庫下限（通知）',
        validators=[
            InputRequired(message='在庫下限を入力してください'),
            NumberRange(
                min=const.STOCK_QUANTITY_MIN, 
                max=const.STOCK_QUANTITY_MAX,
                message=f'{const.STOCK_QUANTITY_MIN}〜{const.STOCK_QUANTITY_MAX}の数値を入力してください')
        ],
        default=0
    )

    # stock
    inout_date = DateField(
        '日付',
        format='%Y-%m-%d',
        default=datetime.date.today,
        render_kw={'max': const.DATE_MAX},
        validators=[
            DataRequired(message='日付を入力してください')
        ]
    )
    stock_type = RadioField(
        '種別',
        choices=[(d, d) for d in const.PRODUCT_INOUT],
        default=const.PRODUCT_INOUT[0],
        validators=[DataRequired()]
    )

    stock_quantity = IntegerField(
        '数量',
        validators=[
            InputRequired(),
            NumberRange(min=const.STOCK_QUANTITY_MIN, 
                        max=const.STOCK_QUANTITY_MAX, 
                        message=f'{const.STOCK_QUANTITY_MIN}〜{const.STOCK_QUANTITY_MAX}の範囲で入力してください')
        ],
        default=0
    )

    note = TextAreaField(
        '備考',
        validators=[
            Length(max=const.NOTE_MAX, message=f'{const.NOTE_MAX}文字以内で入力してください')
        ]
    )

    submit = SubmitField('登録')


# ==========================
# 在庫登録用クラス
# ==========================
class StockForm(FlaskForm):
    inout_date = DateField(
        '日付',
        format='%Y-%m-%d',
        default=datetime.date.today,
        render_kw={'max': const.DATE_MAX},
        validators=[DataRequired()]
    )
    stock_type = RadioField(
        '種別',
        choices=[(d, d) for d in const.PRODUCT_INOUT],
        default=const.PRODUCT_INOUT[0],
        validators=[DataRequired()]
    )

    stock_quantity = IntegerField(
        '数量',
        validators=[
            InputRequired(message='数量を入力してください'),
            NumberRange(min=1, # 新規登録は0許容だけどここは1以上 
                        max=const.STOCK_QUANTITY_MAX, 
                        message=f'{const.STOCK_QUANTITY_MIN}〜{const.STOCK_QUANTITY_MAX}の範囲で入力してください')
        ],
        default=None
    )

    note = TextAreaField(
        '備考',
        validators=[
            Length(max=const.NOTE_MAX, message=f'{const.NOTE_MAX}文字以内で入力してください')
        ]
    )

    submit = SubmitField('登録')
