from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from sqlalchemy import func

from pybo import db
from pybo.models import TourProduct, Review, User, Order, OrderItem
from pybo.forms import ReviewForm

bp = Blueprint('review', __name__, url_prefix='/review')

def check_user_booked_product(user, product_id):
    """로그인된 회원이 해당 여행 상품을 예약(취소되지 않은 주문)했는지 확인"""
    if not user or not hasattr(user, 'id'):
        return False
    return db.session.query(Order).join(OrderItem, Order.id == OrderItem.order_id).filter(
        Order.user_id == user.id,
        OrderItem.product_id == product_id,
        Order.status != 'CANCELLED'
    ).first() is not None

@bp.route('/list')
def list():
    if g.user is None:
        flash('로그인이 필요한 서비스입니다.')
        return redirect(url_for('auth.login', next=request.full_path))
    
    page = request.args.get('page', default=1, type=int)
    region = request.args.get('region', default='', type=str).strip()
    kw = request.args.get('kw', default='', type=str).strip()

    # 상단 이달의 베스트 후기용 (리뷰 수가 많은 인기 상품 상위 3개)
    popular_products = db.session.query(TourProduct, func.count(Review.id).label('review_count')) \
        .outerjoin(TourProduct.reviews) \
        .group_by(TourProduct.id) \
        .order_by(func.count(Review.id).desc()) \
        .all()

    # 전체 후기 목록 쿼리 (상품 및 작성자 조인)
    review_query = Review.query.join(TourProduct).outerjoin(User)

    if region and region not in ('전체', '전체선택', '전체보기'):
        review_query = review_query.filter(TourProduct.region == region)

    if kw:
        search_kw = f"%{kw}%"
        review_query = review_query.filter(
            Review.title.ilike(search_kw) |
            Review.content.ilike(search_kw) |
            TourProduct.name.ilike(search_kw) |
            TourProduct.region.ilike(search_kw) |
            User.name.ilike(search_kw) |
            User.user_id.ilike(search_kw)
        )

    review_list = review_query.order_by(Review.created_at.desc()).paginate(page=page, per_page=10)

    # DB에 존재하는 고유 권역 목록
    distinct_regions = [r[0] for r in db.session.query(TourProduct.region).distinct().order_by(TourProduct.region).all()]

    return render_template(
        'review/review_list.html',
        popular_products=popular_products,
        review_list=review_list,
        region_list=distinct_regions,
        selected_region=region,
        kw=kw
    )

@bp.route('/detail/<int:product_id>')
def detail(product_id):
    selected_product = TourProduct.query.get_or_404(product_id)
    all_product_reviews = db.session.query(Review).filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    review_count = len(all_product_reviews)
    latest_review_date = all_product_reviews[0].created_at.strftime('%Y-%m-%d') if all_product_reviews else None
    avg_rating = round(sum(r.rating for r in all_product_reviews) / review_count, 1) if review_count > 0 else 0.0

    review_id = request.args.get('review_id', type=int)
    selected_review = None

    if review_id:
        target_review = Review.query.filter_by(id=review_id, product_id=product_id).first()
        if target_review:
            reviews = [target_review]
            selected_review = target_review
        else:
            reviews = all_product_reviews
    else:
        reviews = all_product_reviews

    can_review = False
    user_review = None
    is_my_review = False
    my_review = None

    if hasattr(g, 'user') and g.user:
        can_review = check_user_booked_product(g.user, product_id)
        user_review = Review.query.filter_by(user_id=g.user.id, product_id=product_id).first()
        my_review = user_review
        if selected_review:
            is_my_review = (selected_review.user_id == g.user.id)
        else:
            is_my_review = (user_review is not None)

    return render_template(
        "review/review_detail.html",
        product=selected_product,
        reviews=reviews,
        selected_review=selected_review,
        review_count=review_count,
        latest_review_date=latest_review_date,
        avg_rating=avg_rating,
        can_review=can_review,
        user_review=user_review,
        is_my_review=is_my_review,
        my_review=my_review
    )

@bp.route('/view/<int:review_id>')
def view(review_id):
    review = Review.query.get_or_404(review_id)
    return redirect(url_for('review.detail', product_id=review.product_id, review_id=review.id))

@bp.route('/delete/<int:review_id>', methods=['GET', 'POST'])
def delete(review_id):
    """자신의 Review 삭제 기능: 본인 확인 후 삭제"""
    review = Review.query.get_or_404(review_id)
    product_id = review.product_id

    # 로그인 확인 및 본인 작성 여부 검증
    if not (hasattr(g, 'user') and g.user and review.user_id == g.user.id):
        flash('본인이 작성한 후기만 삭제할 수 있습니다.', 'danger')
        return redirect(url_for('review.detail', product_id=product_id))

    try:
        db.session.delete(review)
        db.session.commit()
        flash('작성하신 여행 후기가 성공적으로 삭제되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'후기 삭제 중 오류가 발생했습니다: {str(e)}', 'danger')

    next_url = request.args.get('next') or request.form.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('review.detail', product_id=product_id))

@bp.route('/create/<int:product_id>', methods=['GET', 'POST'])
@bp.route('/create', methods=['GET', 'POST'])
def create(product_id=None):
    # 비로그인 사용자 후기 작성 차단: 로그인 페이지로 리다이렉트
    if not (hasattr(g, 'user') and g.user):
        flash('후기를 작성하려면 먼저 로그인해 주세요.', 'warning')
        return redirect(url_for('auth.login', next=request.full_path))

    if product_id is None:
        product_id = request.args.get('product_id', type=int) or request.form.get('product_id', type=int)

    if not product_id:
        flash('후기를 작성하실 여행 상품을 선택해 주세요.', 'warning')
        return redirect(url_for('review.list'))

    selected_product = TourProduct.query.get_or_404(product_id)

    order_no = (request.args.get('order_no', '') or request.form.get('order_no', '')).strip()
    order = None
    if order_no:
        order = Order.query.filter_by(order_no=order_no).first()

    # 예약자 검증: 로그인된 회원의 경우 자신이 예약한 상품에만 작성 가능
    if not check_user_booked_product(g.user, product_id):
        flash('해당 여행 상품을 예약하신 회원만 후기를 작성하실 수 있습니다.', 'danger')
        return redirect(url_for('review.detail', product_id=product_id))

    all_product_reviews = db.session.query(Review).filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    review_count = len(all_product_reviews)
    latest_review_date = all_product_reviews[0].created_at.strftime('%Y-%m-%d') if all_product_reviews else None
    avg_rating = round(sum(r.rating for r in all_product_reviews) / review_count, 1) if review_count > 0 else 0.0

    form = ReviewForm()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        try:
            rating = int(request.form.get('rating', 5))
            if rating < 1 or rating > 5:
                rating = 5
        except (ValueError, TypeError):
            rating = 5

        if not title:
            flash('후기 제목을 입력해 주세요.', 'danger')
        elif not content:
            flash('후기 내용을 입력해 주세요.', 'danger')
        else:
            # 작성자: 로그인된 회원
            author_user = g.user

            now = datetime.now(timezone.utc)
            new_review = Review(
                user_id=author_user.id,
                product_id=selected_product.id,
                title=title,
                content=content,
                rating=rating,
                created_at=now,
                updated_at=now
            )
            db.session.add(new_review)
            db.session.commit()

            flash('소중한 여행 후기가 성공적으로 등록되었습니다!', 'success')
            return redirect(url_for('review.detail', product_id=selected_product.id, review_id=new_review.id))

    return render_template(
        'review/review_create.html',
        product=selected_product,
        order=order,
        order_no=order_no,
        form=form,
        reviews=all_product_reviews,
        review_count=review_count,
        latest_review_date=latest_review_date,
        avg_rating=avg_rating
    )

@bp.route('/edit/<int:review_id>', methods=['GET', 'POST'])
@bp.route('/modify/<int:review_id>', methods=['GET', 'POST'])
def modify(review_id):
    """자신의 Review 수정 기능: 수정 시 작성 시간을 현재 수정된 시간으로 갱신"""
    review = Review.query.get_or_404(review_id)

    # 본인 확인: 로그인 상태이며 작성자 본인인지 확인
    if not (hasattr(g, 'user') and g.user and review.user_id == g.user.id):
        flash('본인이 작성한 후기만 수정할 수 있습니다.', 'danger')
        return redirect(url_for('review.detail', product_id=review.product_id, review_id=review.id))

    selected_product = review.product
    all_product_reviews = db.session.query(Review).filter_by(product_id=review.product_id).order_by(Review.created_at.desc()).all()
    review_count = len(all_product_reviews)
    latest_review_date = all_product_reviews[0].created_at.strftime('%Y-%m-%d') if all_product_reviews else None
    avg_rating = round(sum(r.rating for r in all_product_reviews) / review_count, 1) if review_count > 0 else 0.0

    form = ReviewForm(obj=review)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        try:
            rating = int(request.form.get('rating', review.rating))
            if rating < 1 or rating > 5:
                rating = review.rating
        except (ValueError, TypeError):
            rating = review.rating

        if not title:
            flash('후기 제목을 입력해 주세요.', 'danger')
        elif not content:
            flash('후기 내용을 입력해 주세요.', 'danger')
        else:
            # Review 수정 및 review의 시간은 수정된 시간으로 변경
            now = datetime.now(timezone.utc)
            review.title = title
            review.content = content
            review.rating = rating
            review.created_at = now  # review 시간은 수정된 시간으로 변경
            review.updated_at = now
            db.session.commit()

            flash('여행 후기가 성공적으로 수정되었습니다.', 'success')
            return redirect(url_for('review.detail', product_id=review.product_id, review_id=review.id))

    return render_template(
        'review/review_modify.html',
        review=review,
        product=selected_product,
        form=form,
        reviews=all_product_reviews,
        review_count=review_count,
        latest_review_date=latest_review_date,
        avg_rating=avg_rating
    )
