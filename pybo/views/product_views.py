import json

from flask import render_template, Blueprint, request

from pybo.forms import OrderReserveForm
from pybo.models import TourProduct

from pybo import db
from pybo.models import User, TourProduct, Review


bp = Blueprint('product', __name__, url_prefix='/product')

@bp.route('/main_product')
def main_product():
    products_data = TourProduct.query.all()
    selected_region = request.args.get('region', 'all').strip().lower()

    def get_region_key(region_str):
        if not region_str:
            return 'other'
        if any(k in region_str for k in ['서울', '경기', '인천', '수도']):
            return 'sudo'
        if '강원' in region_str:
            return 'gang'
        if any(k in region_str for k in ['충청', '충북', '충남', '대전', '세종']):
            return 'chung'
        if any(k in region_str for k in ['경북', '경남', '경상', '부산', '대구', '울산']):
            return 'geong'
        if any(k in region_str for k in ['전라', '전북', '전남', '광주']):
            return 'jeon'
        if '제주' in region_str:
            return 'jeju'
        return 'other'

    products_by_region = {
        'all': products_data,
        'sudo': [],
        'gang': [],
        'chung': [],
        'geong': [],
        'jeon': [],
        'jeju': [],
    }

    for p in products_data:
        key = get_region_key(p.region)
        if key in products_by_region:
            products_by_region[key].append(p)

    if selected_region not in products_by_region:
        selected_region = 'all'

    return render_template(
        'product/main_product.html',
        products=products_data,
        products_by_region=products_by_region,
        selected_region=selected_region
    )


@bp.route('/sub_product/<int:product_id>')
def sub_product(product_id):
    selected_product = TourProduct.query.get_or_404(product_id)

    if isinstance(selected_product.image_urls, str):
        try:
            valid_json_string = selected_product.image_urls.replace("'", '"')
            selected_product.image_urls = json.loads(valid_json_string)
        except Exception:
            selected_product.image_urls = selected_product.image_urls.strip("[]").replace("'", "").split(", ")

    return render_template('product/sub_product.html', product=selected_product)




@bp.route('/sub_product', methods=['GET'])
def reserve():
    headcount = request.args.get('headcount', 1, type=int)
    if headcount < 1:
        headcount = 1

    form = OrderReserveForm(headcount=headcount)

    return render_template('product/sub_product.html', headcount=headcount, form=form)

