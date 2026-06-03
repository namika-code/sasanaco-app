from flask import render_template, Blueprint
from wikipediaapi import Wikipedia
from forms import WikiForm
from flask_login import login_required


# Blueprint
wiki_bp = Blueprint('wiki', __name__, url_prefix='/wiki')
wiki_ja = Wikipedia(user_agent='User-Agent: Chrome/120.0.0.0', language='ja')

# =======================
# ルーティング
# =======================
# wiki検索
@wiki_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = WikiForm()   # Formインスタンス生成
    if form.validate_on_submit():
        # データ入力取得
        keyword = form.keyword.data
        if keyword:
            page = wiki_ja.page(keyword)

            # 検索結果
            if page.exists():
                return render_template('wiki/wiki_search_result.html',
                                   keyword=keyword, 
                                   summary=page.summary[:200],
                                   url=page.fullurl
                )
            else:
                return render_template('wiki/wiki_search_result.html',
                               error='指定されたキーワードの結果は見つかりませんでした。')
    return render_template('wiki/wiki_search.html', form=form)