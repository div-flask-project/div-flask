from datetime import datetime, timedelta
from sqlalchemy import inspect, text
from pybo import db
from pybo.models import TimeDeal, TourProduct


def seed_time_deals():
    try:
        inspector = inspect(db.engine)
        if not inspector.has_table('time_deal') or not inspector.has_table('tour_products'):
            print("❌ 테이블이 존재하지 않습니다.")
            return

        TimeDeal.query.delete()
        db.session.commit()
    except Exception as e:
        print(f"❌ 초기화 오류: {e}")
        return

    db_products = TourProduct.query.order_by(TourProduct.recommendation_count.desc()).limit(3).all()

    if not db_products or len(db_products) < 3:
        db_products = TourProduct.query.order_by(TourProduct.id.desc()).limit(3).all()

    if not db_products or len(db_products) == 0:
        print("❌ 진짜 상품 DB(tour_products)에 등록된 여행 상품이 단 하나도 없습니다. 상품을 먼저 등록해주세요.")
        return

    p_main = db_products[0]
    main_deal_id = p_main.id
    main_image = p_main.image_url if p_main.image_url else '/static/img/tours/default-tour.jpg'
    main_title = p_main.name
    main_desc = p_main.description
    main_price = p_main.original_price if p_main.original_price else 349000

    p_sub1 = db_products[1] if len(db_products) > 1 else db_products[0]
    sub1_id = p_sub1.id
    sub1_image = p_sub1.image_url if p_sub1.image_url else '/static/img/tours/default-tour.jpg'
    sub1_title = p_sub1.name
    sub1_desc = p_sub1.description
    sub1_price = p_sub1.original_price if p_sub1.original_price else 289000

    p_sub2 = db_products[2] if len(db_products) > 2 else db_products[0]
    sub2_id = p_sub2.id
    sub2_image = p_sub2.image_url if p_sub2.image_url else '/static/img/tours/default-tour.jpg'
    sub2_title = p_sub2.name
    sub2_desc = p_sub2.description
    sub2_price = p_sub2.original_price if p_sub2.original_price else 199000

    main_end = datetime.now() + timedelta(days=4, hours=8, minutes=51)
    sub1_end = datetime.now() + timedelta(days=3)
    sub2_end = datetime.now() + timedelta(days=3)

    try:
        db.session.execute(text("""
            INSERT OR REPLACE INTO time_deal (id, product_type, airline, title, hashtags, description, price, end_date, image_file, badge1, badge2) 
            VALUES (:id, 'main', '[대한항공]', :title, '#감성독채 #우도 보트투어 #한라산 트레킹 #돌문화공원', :desc, :price, :end_date, :img, '에어카텔 풀패키지', '특급호텔 1박 업그레이드')
        """), {
            "id": main_deal_id, "title": main_title, "desc": main_desc, "price": main_price,
            "end_date": main_end.strftime('%Y-%m-%d %H:%M:%S'), "img": main_image
        })

        db.session.execute(text("""
            INSERT OR REPLACE INTO time_deal (id, product_type, airline, title, hashtags, description, price, end_date, image_file, badge1, badge2) 
            VALUES (:id, 'sub', '[크루즈선박]', :title, '#독도입도 #울릉도육로관광 #명이나물정식', :desc, :price, :end_date, :img, '독도관광 포함', '전일정 식사제공')
        """), {
            "id": sub1_id, "title": sub1_title, "desc": sub1_desc, "price": sub1_price,
            "end_date": sub1_end.strftime('%Y-%m-%d %H:%M:%S'), "img": sub1_image
        })

        db.session.execute(text("""
            INSERT OR REPLACE INTO time_deal (id, product_type, airline, title, hashtags, description, price, end_date, image_file, badge1, badge2) 
            VALUES (:id, 'sub', '[KTX고속열차]', :title, '#해운대캡슐열차 #경주황리단길 #야경투어', :desc, :price, :end_date, :img, 'KTX 왕복포함', '5성급 온천호텔')
        """), {
            "id": sub2_id, "title": sub2_title, "desc": sub2_desc, "price": sub2_price,
            "end_date": sub2_end.strftime('%Y-%m-%d %H:%M:%S'), "img": sub2_image
        })

        db.session.commit()
        print(f"[성공] 진짜 상품 데이터베이스와 타임딜(ID: {main_deal_id}, {sub1_id}, {sub2_id}) 자동 동기화 시딩 완료!")
    except Exception as e:
        db.session.rollback()
        print(f"[오류] 자동화 시딩 실패 오류 내용: {e}")
