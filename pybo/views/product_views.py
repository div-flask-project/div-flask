import ast
from flask import render_template, Blueprint, request, session, g, jsonify
from pybo import db
from pybo.models import TourProduct, Review, ProductLike
from sqlalchemy import text

bp = Blueprint('product', __name__, url_prefix='/product')

REGION_ALIAS = {
    'all': 'all',
    'sudo': 'sudo',
    'seoul': 'sudo',
    'gang': 'gang',
    'gangwon': 'gang',
    'chung': 'chung',
    'chungcheong': 'chung',
    'geong': 'geong',
    'gyeongsang': 'geong',
    'jeon': 'jeon',
    'jeolla': 'jeon',
    'jeju': 'jeju'
}

@bp.route('/main_product')
def main_product():
    kw = request.args.get('kw', default='', type=str).strip()
    raw_region = request.args.get('region', 'all').lower()
    selected_region = REGION_ALIAS.get(raw_region, 'all')

    query = TourProduct.query
    if kw:
        query = query.filter(TourProduct.name.ilike(f"%{kw}%"))

    products_data = query.all()

    return render_template(
        'product/main_product.html',
        products=products_data,
        selected_region=selected_region,
        kw=kw
    )


@bp.route('/sub_product/<int:product_id>')
def sub_product(product_id):
    selected_product = TourProduct.query.get_or_404(product_id)
    product_review = Review.query.filter_by(product_id=product_id).all()
    product_images = selected_product.get_image_list()

    # itinerary
    raw_itinerary = selected_product.itinerary_json
    product_itinerary = []

    if isinstance(raw_itinerary, str) and raw_itinerary.strip():
        try:
            product_itinerary = ast.literal_eval(raw_itinerary)
        except Exception:
            product_itinerary = []
    elif isinstance(raw_itinerary, list):
        product_itinerary = raw_itinerary

    # details
    raw_details = selected_product.detail_content
    product_details = {}

    if isinstance(raw_details, str) and raw_details.strip():
        try:
            product_details = ast.literal_eval(raw_details)
        except Exception:
            product_details = {}
    elif isinstance(raw_details, dict):
        product_details = raw_details

    session_db = TourProduct.query.session
    is_liked = False
    if g.user:
        # 안전한 db.session 방식으로 변경
        check_query = text("SELECT user_id FROM direct_product_like WHERE user_id = :u_id AND product_id = :p_id")
        already_liked = db.session.execute(check_query, {'u_id': g.user.id, 'p_id': product_id}).fetchone()

        if already_liked:
            is_liked = True  # 추천한 기록이 있다면 True로 변경


    return render_template('product/sub_product.html',
                           product=selected_product, reviews=product_review,
                           product_images=product_images,
                           product_itinerary=product_itinerary,
                           product_details=product_details,
                           is_liked=is_liked)


@bp.route('/sub_product/like', methods=['POST'])
def toggle_product_like():
    if not g.user:
        return jsonify({'error': 'unauthorized', 'message': '로그인이 필요합니다.'}), 401

    data = request.get_json() or {}
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'error': 'bad_request'}), 400

    selected_product = TourProduct.query.get_or_404(product_id)

    create_table_query = """
                         CREATE TABLE IF NOT EXISTS direct_product_like
                         (
                             user_id INTEGER NOTNULL,
                             product_id INTEGER NOT NULL,
                             PRIMARY KEY (user_id,product_id)
                         );
                         """
    try:
        db.session.execute(text(create_table_query))
        db.session.commit()
    except Exception:
        db.session.rollback()

    check_query = text("SELECT user_id FROM direct_product_like WHERE user_id = :u_id AND product_id = :p_id")
    already_liked = db.session.execute(check_query, {'u_id': g.user.id, 'p_id': product_id}).fetchone()

    if already_liked:
        selected_product.recommendation_count = max(0, (selected_product.recommendation_count or 0) - 1)

        delete_query = text("DELETE FROM direct_product_like WHERE user_id = :u_id AND product_id = :p_id")
        db.session.execute(delete_query, {'u_id': g.user.id, 'p_id': product_id})
        status = "canceled"
    else:
        selected_product.recommendation_count = (selected_product.recommendation_count or 0) + 1

        insert_query = text("INSERT INTO direct_product_like (user_id, product_id) VALUES (:u_id, :p_id)")
        db.session.execute(insert_query, {'u_id': g.user.id, 'p_id': product_id})
        status = "liked"

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'database_error', 'details': str(e)}), 500

    return jsonify({
        'success': True,
        'status': status,
        'recommendation_count': selected_product.recommendation_count
    }), 200


