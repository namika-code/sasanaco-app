# ==========================
# サーバー切換え
# ==========================
LOCAL_SERVER = 0
XREA_SERVER = 1

# ==========================
# DB文字数制限
# ==========================
DB_USER_NAME_MAX = 150
DB_USER_PASS_MAX = 255
DB_USER_DEPARTMENT_MAX = 150
DB_USER_LAST_NAME_MAX = 50
DB_USER_FIRST_NAME_MAX = 50

DB_PRODUCT_NAME_MAX = 150
DB_PRODUCT_CODE_MAX = 150
DB_PRODUCT_CATEGORY_MAX = 150

DB_STOCK_TYPE_MAX = 150
DB_STOCK_NOTE_MAX = 500

DB_TASK_TITLE = 150
DB_TASK_CONTENT = 3000
DB_TASK_COMMENT = 3000 # 1タスクに対して複数コメント統合登録

DB_ALERT_MESSAGE = 1000
DB_GROUP_NAME = 50

# ==========================
# フォーム入力制限
# ==========================
USER_NAME_MAX = 20
USER_PASS_MIN = 4
USER_PASS_MAX = 10
USER_DEPARTMENT_MAX = 20

STOCK_QUANTITY_MAX = 10000
STOCK_QUANTITY_MIN = 0
INOUT_QUANTITY_MIN = 1
STOCK_TYPE_MAX = 50

PRODUCT_NAME_MAX = 50
PRODUCT_CODE_MAX = 50
PRODUCT_CATEGORY_MAX = 50

NOTE_MAX = 255
DATE_MAX = "9999-12-31"


# リスト
USER_DEPARTMENTS = [
    '総務',
    '経理',
    '営業',
    '開発',
]

PRODUCT_CATEGORIES = [
    '日用品',
    '事務用品',
    '備品',
    'その他',
]

PRODUCT_INOUT = [
    '入庫',
    '出庫',
]