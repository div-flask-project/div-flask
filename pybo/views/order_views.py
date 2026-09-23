import json
from flask import Blueprint, render_template, request, redirect, url_for, session, g, flash
from flask_login import current_user
from pybo import db
from pybo.models import TourProduct, User, Order, OrderItem, Payment

bp = Blueprint('order', __name__, url_prefix='/order')


def check_is_member():
    """로그인 사용자 여부 판별 (Flask-Login, Flask session, g.user 종합 확인)"""
    try:
        if current_user and current_user.is_authenticated:
            return True, current_user
    except Exception:
        pass

    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            return True, user

    if hasattr(g, 'user') and g.user:
        return True, g.user

    return False, None


@bp.route("/reserve", methods=['GET'])
def reserve():
    """여행 상품 예약 및 여행객 정보 입력 화면"""
    product_id = request.args.get('product_id', type=int)
    headcount = request.args.get('headcount', 1, type=int)
    if headcount < 1:
        headcount = 1

    # 상품 정보 조회
    if not product_id:
        product = TourProduct.query.first()
        if not product:
            return "등록된 여행 상품이 없습니다.", 404
        product_id = product.id
    else:
        product = TourProduct.query.get_or_404(product_id)

    # 회원 / 비회원 여부 판별
    is_member, logged_user = check_is_member()

    # 가격 및 할인 계산
    unit_original_price = product.original_price
    unit_discount = product.get_discount_amount(is_member=is_member)
    unit_final_price = product.get_discounted_price(is_member=is_member)

    total_original = unit_original_price * headcount
    total_discount = unit_discount * headcount
    total_final = unit_final_price * headcount

    items_to_checkout = [{
        'product': product,
        'quantity': headcount,
        'original_price': unit_original_price,
        'final_price': unit_final_price,
        'subtotal_original': total_original,
        'subtotal_final': total_final
    }]

    return render_template(
        'order/reserve.html',
        product=product,
        items=items_to_checkout,
        headcount=headcount,
        is_member=is_member,
        logged_user=logged_user,
        unit_original_price=unit_original_price,
        unit_discount=unit_discount,
        unit_final_price=unit_final_price,
        total_original=total_original,
        total_discount=total_discount,
        total_final=total_final,
        direct_product_id=product.id
    )


@bp.route("/payment", methods=['POST'])
def payment():
    """예약 정보 및 여행객 목록 수신 후 결제 화면으로 이동"""
    product_id = request.form.get('product_id', type=int)
    headcount = request.form.get('headcount', 1, type=int)
    if headcount < 1:
        headcount = 1

    product = TourProduct.query.get_or_404(product_id)
    is_member, logged_user = check_is_member()

    # 필수 약관 동의 서버 사이드 검증
    agree_special_val = request.form.get('agree_special') in ['1', 'on', 'true', 'True']
    agree_privacy_val = request.form.get('agree_privacy') in ['1', 'on', 'true', 'True']
    agree_sensitive_val = request.form.get('agree_sensitive') in ['1', 'on', 'true', 'True']
    agree_location_val = request.form.get('agree_location') in ['1', 'on', 'true', 'True']
    
    if not (agree_special_val and agree_privacy_val and agree_sensitive_val):
        flash('필수 약관(국내여행 특별약관, 개인정보 제3자 제공, 민감정보 수집)에 모두 동의해주셔야 합니다.', 'danger')
        return redirect(url_for('order.reserve', product_id=product.id, headcount=headcount))

    # 예약자 정보 수집
    guest_name = request.form.get('guest_name', '').strip()
    guest_phone = request.form.get('guest_phone', '').strip()
    guest_email = request.form.get('guest_email', '').strip()

    if is_member and logged_user:
        reserver_name = logged_user.name
        reserver_phone = logged_user.phone
        reserver_email = logged_user.email
    else:
        reserver_name = guest_name or '비회원 고객'
        reserver_phone = guest_phone
        reserver_email = guest_email

    # 여행객별 상세 정보 목록 수집 (이름, 남/여, 전화번호, 생년월일)
    names = request.form.getlist('traveler_name[]')
    genders = request.form.getlist('traveler_gender[]')
    phones = request.form.getlist('traveler_phone[]')
    births = request.form.getlist('traveler_birth[]')

    travelers = []
    for i in range(headcount):
        t_name = names[i].strip() if i < len(names) else ''
        t_gender = genders[i].strip() if i < len(genders) else '남'
        t_phone = phones[i].strip() if i < len(phones) else ''
        t_birth = births[i].strip() if i < len(births) else ''

        # 대표 여행자(1번) 정보가 비어있으면 예약자 정보로 대체
        if i == 0 and not t_name:
            t_name = reserver_name
        if i == 0 and not t_phone:
            t_phone = reserver_phone

        travelers.append({
            'index': i + 1,
            'name': t_name or f"여행객 {i + 1}",
            'gender': t_gender,
            'phone': t_phone or '-',
            'birth': t_birth or '-'
        })

    # 결제 금액 계산
    unit_original_price = product.original_price
    unit_discount = product.get_discount_amount(is_member=is_member)
    unit_final_price = product.get_discounted_price(is_member=is_member)

    total_original = unit_original_price * headcount
    total_discount = unit_discount * headcount
    total_final = unit_final_price * headcount

    return render_template(
        'order/payment.html',
        product=product,
        headcount=headcount,
        is_member=is_member,
        logged_user=logged_user,
        reserver_name=reserver_name,
        reserver_phone=reserver_phone,
        reserver_email=reserver_email,
        travelers=travelers,
        travelers_json=json.dumps(travelers, ensure_ascii=False),
        agree_special=agree_special_val,
        agree_privacy=agree_privacy_val,
        agree_sensitive=agree_sensitive_val,
        agree_location=agree_location_val,
        unit_original_price=unit_original_price,
        unit_discount=unit_discount,
        unit_final_price=unit_final_price,
        total_original=total_original,
        total_discount=total_discount,
        total_final=total_final
    )


@bp.route("/pay/complete", methods=['POST'])
def pay_complete():
    """결제 완료 처리 및 주문 저장"""
    product_id = request.form.get('product_id', type=int)
    headcount = request.form.get('headcount', 1, type=int)
    payment_method = request.form.get('payment_method', 'CARD')

    product = TourProduct.query.get_or_404(product_id)
    is_member, logged_user = check_is_member()

    reserver_name = request.form.get('reserver_name', '')
    reserver_phone = request.form.get('reserver_phone', '')
    reserver_email = request.form.get('reserver_email', '')
    travelers_json = request.form.get('travelers_json', '[]')

    # 약관 동의 값 수신
    agree_special = request.form.get('agree_special') in ['1', 'on', 'true', 'True']
    agree_privacy = request.form.get('agree_privacy') in ['1', 'on', 'true', 'True']
    agree_sensitive = request.form.get('agree_sensitive') in ['1', 'on', 'true', 'True']
    agree_location = request.form.get('agree_location') in ['1', 'on', 'true', 'True']

    unit_final_price = product.get_discounted_price(is_member=is_member)
    unit_discount = product.get_discount_amount(is_member=is_member)
    total_original = product.original_price * headcount
    total_discount = unit_discount * headcount
    total_final = unit_final_price * headcount

    order_no = Order.generate_order_no()
    order = Order(
        order_no=order_no,
        user_id=logged_user.id if (is_member and logged_user) else None,
        guest_name=reserver_name if not is_member else None,
        guest_phone=reserver_phone if not is_member else None,
        guest_email=reserver_email if not is_member else None,
        original_amount=total_original,
        discount_amount=total_discount,
        status='COMPLETED',
        agree_special=agree_special,
        agree_privacy=agree_privacy,
        agree_sensitive=agree_sensitive,
        agree_location=agree_location
    )
    db.session.add(order)
    db.session.flush()

    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=headcount,
        unit_price=unit_final_price,
        discount_applied=unit_discount
    )
    db.session.add(order_item)

    payment = Payment(
        order_id=order.id,
        payment_method=payment_method,
        paid_amount=total_final,
        transaction_id=f"TX-{order_no}",
        status='SUCCESS'
    )
    db.session.add(payment)
    db.session.commit()

    try:
        travelers = json.loads(travelers_json)
    except Exception:
        travelers = []

    return render_template(
        'order/complete.html',
        order=order,
        product=product,
        headcount=headcount,
        travelers=travelers,
        payment_method=payment_method,
        total_final=total_final
    )
