from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Product, Stock
from flask_login import login_required, current_user
from forms import CreateStockForm, StockForm

import plotly.graph_objs as go
import plotly.io as pio
from flask import send_file
import pandas as pd
from io import BytesIO
from datetime import date, datetime
from sqlalchemy import func, case
from collections import defaultdict
import constants as const

# stockのBlueprint
stock_bp = Blueprint('stock', __name__, url_prefix='/stock')

# =======================
# 一覧
# =======================
@stock_bp.route('/')
@login_required
def index():
    # 在庫集計（SQL）calc_current_stock関数とは別にした方がいいらしい
    stock_sum = db.session.query(
        Stock.product_id,
        func.sum(
            case(
                (Stock.stock_type == '入庫', Stock.stock_quantity),
                else_=-Stock.stock_quantity
            )
        ).label('current_stock')
    ).group_by(Stock.product_id).subquery()

    results = db.session.query(
        Product,
        func.coalesce(stock_sum.c.current_stock, 0)
    ).outerjoin(
        stock_sum, Product.product_id == stock_sum.c.product_id
    ).all()

    # カテゴリごとにまとめる
    grouped = defaultdict(list)

    for product, stock in results:
        category = product.product_category or '未分類'

        grouped[category].append({
            'product': product,
            'stock': stock
        })

    # カテゴリ一覧
    categories = const.PRODUCT_CATEGORIES.copy()

    return render_template(
        'stock/index.html',
        grouped=grouped,
        categories=categories
    )

# =======================
# 新規作成
# =======================
@stock_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CreateStockForm()

    # GET時：初期値をセット
    if request.method == 'GET':
        form.stock_type.data = const.PRODUCT_INOUT[0]

    # POST時：バリデーション
    if form.validate_on_submit():

        # 商品登録
        product = Product(
            product_code=form.product_code.data,
            product=form.product.data,
            product_category=form.product_category.data,
            min_stock=form.min_stock.data or 0
        )

        db.session.add(product)
        db.session.flush()  # product_id取得


        # 初期在庫登録
        stock = Stock(
            product_id=product.product_id,
            user_id=current_user.user_id,
            inout_date=form.inout_date.data,
            stock_type=form.stock_type.data,
            stock_quantity=form.stock_quantity.data,
            note=form.note.data
        )

        db.session.add(stock)
        db.session.commit()

        flash(f'{product.product_category}/{product.product}：新規登録完了')
        return redirect(url_for('stock.index'))

    return render_template(
        'stock/create_form.html',
        form=form,
        PRODUCT_INOUT=const.PRODUCT_INOUT,
        PRODUCT_CATEGORIES=const.PRODUCT_CATEGORIES,

        PRODUCT_NAME_MAX=const.PRODUCT_NAME_MAX,
        PRODUCT_CODE_MAX=const.PRODUCT_CODE_MAX,
        NOTE_MAX=const.NOTE_MAX,
        STOCK_QUANTITY_MAX=const.STOCK_QUANTITY_MAX,
        STOCK_QUANTITY_MIN=const.STOCK_QUANTITY_MIN,
        DATE_MAX=const.DATE_MAX,
    )


# =======================
# 詳細
# =======================
@stock_bp.route('/<int:product_id>')
@login_required
def detail(product_id):
    product = Product.query.get_or_404(product_id)
    stock_rows = get_stock_rows(product_id)

    return render_template(
        'stock/detail.html',
        product=product,
        stock_rows=stock_rows
    )


# =======================
# Excel出力
# =======================
@stock_bp.route('/<int:product_id>/export_excel')
@login_required
def export_excel(product_id):

    stock_rows = get_stock_rows(product_id)

    df = pd.DataFrame(stock_rows)
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='stock')

    output.seek(0)

    filename = request.args.get('filename')

    if not filename:
        product = Product.query.get_or_404(product_id)
        filename = f"{product.product}_{datetime.now().strftime('%Y%m%d')}"
    
    if not filename.endswith('.xlsx'):
        filename += '.xlsx'

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



# =======================
# 入出庫
# =======================
@stock_bp.route('/<int:product_id>/inout', methods=['GET', 'POST'])
@login_required
def inout(product_id):

    product = Product.query.get_or_404(product_id)
    form = StockForm()

    if form.validate_on_submit():

        qty = form.stock_quantity.data

        # 数量未入力チェック
        if qty is None:
            flash('数量を入力してください')
            return redirect(url_for('stock.inout', product_id=product_id))

        # 数量範囲チェック
        if not (const.INOUT_QUANTITY_MIN <= qty <= const.STOCK_QUANTITY_MAX):
            flash(
                f'数量は{const.INOUT_QUANTITY_MIN}〜{const.STOCK_QUANTITY_MAX}の範囲で入力してください'
            )
            return redirect(url_for('stock.inout', product_id=product_id))

        # 時系列在庫チェック
        result = validate_stock_transition(
            product_id,
            form.inout_date.data,
            form.stock_type.data,
            qty
        )

        # マイナス
        if result == 'minus':
            flash('この日付で登録すると在庫がマイナスになります')
            return redirect(url_for('stock.inout', product_id=product_id))

        # 上限超え
        if result == 'over':
            flash(f'在庫上限（{ const.STOCK_QUANTITY_MAX }）を超えるため登録できません')
            return redirect(url_for('stock.inout', product_id=product_id))

        # 在庫登録
        stock = Stock(
            product_id=product_id,
            user_id=current_user.user_id,
            inout_date=form.inout_date.data,
            stock_type=form.stock_type.data,
            stock_quantity=qty,
            note=form.note.data
        )

        db.session.add(stock)
        db.session.commit()

        # 現在在庫取得
        current_stock = calc_current_stock(product_id)

        flash(f'{product.product} 在庫更新（現在在庫：{current_stock}）')

        return redirect(url_for('stock.inout', product_id=product_id))

    # GET表示
    stock_rows = get_stock_rows(product_id)
    current_stock = calc_current_stock(product_id)

    return render_template(
        'stock/inout.html',
        product=product,
        product_id=product_id,
        form=form,
        stock_rows=stock_rows,
        current_stock=current_stock,
        latest_stock_id=stock_rows[-1]['no'] if stock_rows else None,

        STOCK_QUANTITY_MAX=const.STOCK_QUANTITY_MAX,
        STOCK_QUANTITY_MIN=const.STOCK_QUANTITY_MIN,
        NOTE_MAX=const.NOTE_MAX,
        DATE_MAX=const.DATE_MAX,
    )

# =======================
# グラフ
# =======================
@stock_bp.route('/<int:product_id>/graph')
def graph(product_id):
    product = Product.query.get_or_404(product_id)

    chart_type = request.args.get('chart_type', 'bar')  # line / bar / 3d

    stocks = Stock.query.filter_by(product_id=product_id)\
        .order_by(Stock.inout_date, Stock.stock_id).all()

    # 日付ごとにグループ化
    daily = defaultdict(list)

    for s in stocks:
        day = s.inout_date.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        daily[day].append(s)

    # 日単位で在庫計算
    dates = []
    values = []
    current = 0

    for day in sorted(daily.keys()):
        for s in daily[day]:
            if s.stock_type == '入庫':
                current += s.stock_quantity
            else:
                current -= s.stock_quantity

        dates.append(day)
        values.append(current)

    # =========================
    # グラフ生成
    # =========================
    fig = go.Figure()

    # 折れ線
    if chart_type == 'line':

        fig.add_trace(
            go.Scatter(
                x=[d.strftime('%Y-%m-%d') for d in dates],
                y=values,
                mode='lines+markers',
                name='在庫数'
            )
        )

        # 日付重複防止
        fig.update_xaxes(type='category')

    # 棒グラフ
    elif chart_type == 'bar':

        fig.add_trace(
            go.Bar(
                # 文字列化してカテゴリ軸にする
                x=[d.strftime('%Y-%m-%d') for d in dates],
                y=values,
                name='在庫数'
            )
        )

        fig.update_xaxes(type='category')

    # 3D(今回あんま意味ないけど作りたくて)
    elif chart_type == '3d':

        x_vals = []
        y_vals = []
        z_vals = []
        hover_text = []

        current = 0

        for i, s in enumerate(stocks, start=1):

            # 表示用日付
            day = s.inout_date.strftime('%Y-%m-%d')

            # 入出庫
            if s.stock_type == '入庫':
                move = s.stock_quantity
                current += s.stock_quantity
            else:
                move = -s.stock_quantity
                current -= s.stock_quantity


            ##### X = 登録順
            x_vals.append(i)

            # 入出庫量
            y_vals.append(move)

            # 累計在庫
            z_vals.append(current)

            # ホバー情報
            hover_text.append(
                f'日付: {day}<br>'
                f'入出庫: {move}<br>'
                f'累計在庫: {current}'
            )

        fig = go.Figure(data=[

            go.Scatter3d(

                x=x_vals,
                y=y_vals,
                z=z_vals,

                text=hover_text,
                hoverinfo='text',

                mode='lines+markers',

                marker=dict(

                    size=6,

                    # 在庫量で色変化
                    color=z_vals,

                    colorscale='Viridis',

                    opacity=0.9
                ),

                line=dict(
                    width=4
                )
            )
        ])

        fig.update_layout(

            title=f'{product.product} 3D在庫推移',

            scene=dict(

                xaxis=dict(
                    title='登録順'
                ),

                yaxis=dict(
                    title='入出庫量'
                ),

                zaxis=dict(
                    title='累計在庫'
                )
            ),

            margin=dict(
                l=0,
                r=0,
                b=0,
                t=50
            )
        )

    # 共通レイアウト
    fig.update_layout(
        title=f'{product.product} 在庫グラフ',
        xaxis_title='日付',
        yaxis_title='在庫数'
    )

    graph_html = pio.to_html(fig, full_html=False)

    return render_template(
        'stock/graph.html',
        graph=graph_html,
        chart_type=chart_type,
        product_id=product_id,
        product=product
    )

# =========================
# 共通関数：在庫履歴＋在庫計算
# =========================
def get_stock_rows(product_id):

    stocks = Stock.query.filter_by(product_id=product_id).order_by(Stock.inout_date, Stock.stock_id).all()

    current_stock = 0
    rows = []

    for i, s in enumerate(stocks, start=1):

        if s.stock_type == '入庫':
            current_stock += s.stock_quantity
        else:
            current_stock -= s.stock_quantity

        rows.append({
            'no': i,
            'date': s.inout_date,
            'type': s.stock_type,
            'qty': s.stock_quantity,
            'stock': current_stock,
            'user': s.user.username,
            'note': s.note
        })

    return rows


# =========================
# 共通関数：現在在庫計算
# =========================
def calc_current_stock(product_id):
    stocks = Stock.query.filter_by(product_id=product_id)\
        .order_by(Stock.inout_date, Stock.stock_id).all()

    total = 0
    for s in stocks:
        if s.stock_type == '入庫':
            total += s.stock_quantity
        else:
            total -= s.stock_quantity

    return total


# =======================
# 商品削除
# =======================
@stock_bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
def delete(product_id):

    # 管理者チェック
    if current_user.user_id != 1:
        flash('削除権限がありません')
        return redirect(url_for('stock.detail', product_id=product_id))

    product = Product.query.get_or_404(product_id)

    # 関連在庫も削除
    Stock.query.filter_by(product_id=product_id).delete()

    # 商品削除
    db.session.delete(product)
    db.session.commit()

    flash(f'{product.product} を削除しました')

    return redirect(url_for('stock.index'))

# =======================
# 在庫数整合性チェック
# =======================
def validate_stock_transition(product_id, new_date, new_type, new_qty):

    # 既存在庫取得
    stocks = Stock.query.filter_by(product_id=product_id)\
        .order_by(Stock.inout_date, Stock.stock_id).all()

    rows = []

    # 既存データ（DBからは datetime 型で取得）
    for s in stocks:
        rows.append({
            'date': s.inout_date,
            'order': s.stock_id,
            'type': s.stock_type,
            'qty': s.stock_quantity
        })

    actual_date = new_date
    # 画面から送られてきた new_date が「date型」だったら「datetime型」に変換
    if isinstance(new_date, date) and not isinstance(new_date, datetime):
        actual_date = datetime.combine(new_date, datetime.min.time())

    # 新規データ（型を統一した actual_date を使用）
    rows.append({
        'date': actual_date,
        'order': 999999999,
        'type': new_type,
        'qty': new_qty
    })

    # 日付順＋登録順
    rows.sort(key=lambda x: (x['date'], x['order']))

    # 在庫シミュレーション
    current = 0

    for r in rows:

        if r['type'] == '入庫':
            current += r['qty']
        else:
            current -= r['qty']

        # マイナス
        if current < 0:
            return 'minus'

        # 上限到達も禁止
        if current > const.STOCK_QUANTITY_MAX:
            return 'over'

    return 'ok'
