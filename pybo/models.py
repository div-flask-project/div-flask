from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
import enum
import uuid
import json
from pybo import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False, index=True) # ID
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(80), nullable=False)                                # 이름
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)   # email
    phone = db.Column(db.String(30), unique=True, nullable=False)                 # 전화번호
    #role = db.Column(db.String(20), default='MEMBER')                             # MEMBER, ADMIN
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    reviews = db.relationship('Review', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    #cart = db.relationship('Cart', backref='user', uselist=False, cascade='all, delete-orphan')
    likes = db.relationship('ProductLike', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

class RegionEnum(str, enum.Enum):
    SEOUL_GYEONGGI = "서울/경기"
    JEONLA = "전라"
    CHUNGCHEONG = "충청"
    GANGWON = "강원"
    GYEONGSANG = "경상"
    JEJU = "제주"

    @classmethod
    def get_display_names(cls):
        return [r.value for r in cls]

class TourProduct(db.Model):
    __tablename__ = 'tour_products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    region = db.Column(db.String(50), nullable=False, index=True) # 6개 지역
    #theme_id = db.Column(db.Integer, db.ForeignKey('themes.id'), nullable=False)
    original_price = db.Column(db.Integer, nullable=False)
    member_discount_rate = db.Column(db.Float, default=0.15) # 회원 15% 기본 할인
    recommendation_count = db.Column(db.Integer, default=0, index=True) # 누적 추천수
    image_url = db.Column(db.String(255), default='/static/img/default-tour.jpg')
    image_urls = db.Column(db.Text, nullable=True) # JSON 문자열 형태의 3~4개 이상 이미지 URL 목록
    schedule_summary = db.Column(db.String(100), nullable=True) # 여행 일정 요약
    cities = db.Column(db.String(100), nullable=True) # 여행 주요 도시
    departure_info = db.Column(db.String(150), nullable=True) # 출발 안내
    arrival_info = db.Column(db.String(150), nullable=True) # 도착 안내
    itinerary_json = db.Column(db.Text, nullable=True) # 상세 여행일정 JSON
    detail_content = db.Column(db.Text, nullable=True) # 상세 소개/하이라이트/포함/불포함 JSON
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    reviews = db.relationship('Review', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('ProductLike', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    #cart_items = db.relationship('CartItem', backref='product', lazy='dynamic')
    def get_discounted_price(self, is_member=False):
        """회원인 경우 할인율이 적용된 가격을 반환, 비회원은 정가 반환"""
        if is_member:
            return int(self.original_price * (1 - self.member_discount_rate))
        return self.original_price

    def get_discount_amount(self, is_member=False):
        """회원 할인 금액 반환"""
        if is_member:
            return self.original_price - self.get_discounted_price(True)
        return 0

    def get_average_rating(self):
        """상품 평점 평균 계산"""
        review_list = self.reviews.all()
        if not review_list:
            return 0.0
        return round(sum(r.rating for r in review_list) / len(review_list), 1)

    def is_liked_by(self, user):
        """특정 사용자가 이미 추천했는지 여부"""
        if not user or not getattr(user, 'id', None):
            return False
        return self.likes.filter_by(user_id=user.id).first() is not None

    def get_image_list(self):
        """다중 이미지 URL 목록을 반환하고, 없으면 대표 이미지 또는 기본 이미지를 반환한다."""
        import json
        import ast

        raw = self.image_urls

        if raw:
            # 1) JSON 시도
            try:
                urls = json.loads(raw)
                if isinstance(urls, list) and urls:
                    return [u for u in urls if isinstance(u, str) and u.strip()]
            except Exception:
                pass

            # 2) Python literal 시도
            try:
                urls = ast.literal_eval(raw)
                if isinstance(urls, list) and urls:
                    return [u for u in urls if isinstance(u, str) and u.strip()]
            except Exception:
                pass

            # 3) 줄바꿈 분리
            urls = [u.strip() for u in raw.splitlines() if u.strip()]
            if urls:
                return urls

        if self.image_url:
            return [self.image_url]

        return ["/static/img/default-tour.jpg"]
    def set_image_list(self, urls):
        """이미지 URL 목록을 JSON으로 직렬화하여 저장하고 대표 이미지 동기화"""
        import json
        if isinstance(urls, list):
            self.image_urls = json.dumps(urls, ensure_ascii=False)
            if urls:
                self.image_url = urls[0]
        elif isinstance(urls, str):
            self.image_urls = urls
            self.image_url = urls

    def get_nearby_products(self, limit=6):
        """동일 권역(근처)의 다른 관광 상품 목록 조회 (부족할 경우 전체 추천순으로 보충)"""
        nearby = TourProduct.query.filter(
            TourProduct.region == self.region,
            TourProduct.id != self.id
        ).order_by(TourProduct.recommendation_count.desc(), TourProduct.id.asc()).limit(limit).all()

        if len(nearby) < limit:
            existing_ids = [self.id] + [p.id for p in nearby]
            extra = TourProduct.query.filter(
                ~TourProduct.id.in_(existing_ids)
            ).order_by(TourProduct.recommendation_count.desc(), TourProduct.id.asc()).limit(limit - len(nearby)).all()
            nearby.extend(extra)

        return nearby

    def get_schedule_summary(self):
        if self.schedule_summary:
            return self.schedule_summary
        return "당일 힐링 코스 (08:30 ~ 19:30)"

    def get_cities(self):
        if self.cities:
            return self.cities
        clean_name = self.name.split('(')[0].replace('&', ' ').replace('/', ' ')
        tokens = [t.strip() for t in clean_name.split() if len(t.strip()) >= 2]
        spot_names = tokens[:2] if tokens else [self.region]
        return f"{self.region} ({' - '.join(spot_names)})"

    def get_departure_info(self):
        if self.departure_info:
            return self.departure_info
        return f"08:30 {self.region} 거점 주요 전철역 / KTX역 앞 집결 후 전용 투어 버스 탑승"

    def get_arrival_info(self):
        if self.arrival_info:
            return self.arrival_info
        return f"19:30 {self.region} 거점 역 및 시내 중심가 순차 하차 및 투어 종료"

    def get_itinerary(self):
        """일자별/시간대별 상세 여행 일정 반환 (DB에 없으면 기본 일정 생성)"""
        import json
        if self.itinerary_json:
            try:
                data = json.loads(self.itinerary_json)
                if isinstance(data, list) and len(data) > 0:
                    return data
            except Exception:
                pass

        # 기본 일정 fallback
        title_core = self.name.split('(')[0].strip()
        return [
            {
                "day": 1,
                "title": f"낭만과 여유를 즐기는 {self.region} 테마 힐링 여행",
                "meals": {
                    "breakfast": "개별 조식 또는 차량 내 간단 생수/다과",
                    "lunch": f"{self.region} 현지 로컬 맛집 향토 특선 중식",
                    "dinner": "자유식 (복귀 후 또는 개별 식사)"
                },
                "timeline": [
                    {
                        "time": "08:30 ~ 09:30",
                        "icon": "🚌",
                        "title": f"지정 집결지 미팅 및 {self.region} 출발",
                        "location": f"{self.region} 주요 역 앞 집결처",
                        "desc": "가이드 미팅 후 전용 투어 버스 탑승, 안전 수칙 안내 및 오늘의 여행 일정 브리핑."
                    },
                    {
                        "time": "10:00 ~ 12:00",
                        "icon": "🌿",
                        "title": f"{title_core} 오전 핵심 관광",
                        "location": f"{self.region} 대표 명소",
                        "desc": f"{self.description[:120]}... 쾌적한 힐링 산책과 포토존 자유 시간."
                    },
                    {
                        "time": "12:30 ~ 13:40",
                        "icon": "🍽️",
                        "title": f"{self.region} 현지 제철 향토 미식 중식",
                        "location": f"{self.region} 로컬 지정 식당",
                        "desc": f"현지에서 엄선한 정갈하고 맛있는 제철 식재료 향토 요리를 즐기는 여유로운 점심 시간."
                    },
                    {
                        "time": "14:10 ~ 16:30",
                        "icon": "📸",
                        "title": f"{self.region} 오후 문화 체험 및 감성 명소",
                        "location": f"{self.region} 주요 관광 코스",
                        "desc": f"아름다운 풍경을 배경으로 인생 사진을 남기고, 현지 특유의 정취를 만끽하는 힐링 코스."
                    },
                    {
                        "time": "17:00 ~ 18:00",
                        "icon": "☕",
                        "title": "로컬 감성 거리 & 카페 자유 시간",
                        "location": f"{self.region} 중심 감성 거리",
                        "desc": "지역 유명 베이커리/특산물 쇼핑 및 분위기 좋은 카페에서 여유로운 티타임."
                    },
                    {
                        "time": "18:00 ~ 19:30",
                        "icon": "🚌",
                        "title": "투어 종료 및 복귀/해산",
                        "location": f"{self.region} 거점 역 및 시내 중심지",
                        "desc": "전용 차량 탑승 후 안전하게 출발지로 복귀, 순차 하차 및 개별 해산."
                    }
                ]
            }
        ]

    def get_detail_info(self):
        """상품 소개, 핵심 포인트(하이라이트), 포함/불포함, 집결/준비사항 상세 정보 반환"""
        import json
        if self.detail_content:
            try:
                data = json.loads(self.detail_content)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass

        # 기본 상세 정보 fallback
        title_core = self.name.split('(')[0].strip()
        return {
            "intro": f"{self.description} 바쁜 일상에서 벗어나 오롯이 자연과 문화를 느끼며 진정한 재충전을 경험해보세요.",
            "highlights": [
                {
                    "title": f"전문 가이드와 함께하는 {self.region} 핵심 명소 투어",
                    "desc": "기계적인 설명 대신 현지인의 재미있는 역사와 문화 스토리텔링을 통해 여행지의 깊이를 더합니다."
                },
                {
                    "title": f"{title_core} 인생 포토존과 힐링 산책",
                    "desc": "사계절 변화하는 아름다운 풍경 속에서 가족, 연인, 친구와 함께 잊지 못할 추억을 만듭니다."
                },
                {
                    "title": "스트레스 없는 편안한 전용 차량 이동",
                    "desc": "대중교통 환승 부담 없이 쾌적한 전용 차량으로 목적지까지 안전하고 여유롭게 이동합니다."
                }
            ],
            "included": [
                "전 일정 왕복 전용 투어 버스 차량비 (유류비/통행료/기사 수고비 포함)",
                "전문 문화관광 가이드 인솔 및 해설비",
                f"{title_core} 주요 관광지 입장료",
                "차량 내 시원한 생수 제공"
            ],
            "excluded": [
                "개인 식사비 및 음료비",
                "개인 기호 식품 및 기념품 구매 비용",
                "선택 체험 프로그램 이용료",
                "개인 여행자보험 (개별 가입 권장)"
            ],
            "meeting_info": [
                {"point": f"{self.region} 거점 집결지", "time": "08:30", "place": f"{self.region} 주요 역 1번 출구 앞"},
                {"point": "추가 픽업지", "time": "09:00", "place": f"{self.region} 시내 중심 지하철역 앞"}
            ],
            "dropoff_info": [
                {"point": "1차 하차", "time": "18:30", "place": f"{self.region} 주요 역 앞"},
                {"point": "2차 하차", "time": "19:30", "place": f"{self.region} 시내 중심지"}
            ],
            "preparation": [
                "편안한 보행을 위해 편한 운동화나 워킹화 착용을 권장합니다.",
                "계절과 기온 변화에 대비한 가벼운 겉옷이나 얇은 외투.",
                "스마트폰 카메라 충전을 위한 보조배터리.",
                "야외 활동을 위한 모자, 선글라스, 양산 등 햇빛 차단 용품."
            ],
            "cancellation_policy": [
                "출발 3일 전 취소 시: 100% 전액 환불",
                "출발 2일 전 취소 시: 80% 환불 (위약금 20%)",
                "출발 1일 전 취소 시: 70% 환불 (위약금 30%)",
                "출발 당일 취소 또는 미탑승 시: 50% 환불 (위약금 50%)"
            ]
        }

    def __repr__(self):
        return f"<TourProduct {self.name} ({self.region})>"
    
class ProductLike(db.Model):
    __tablename__ = 'direct_product_like'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='uix_user_product_like'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('tour_products.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('tour_products.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5, nullable=False) # 1~5
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Review {self.title} (Rating: {self.rating})>"

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True) # 비회원 구매 시 None
    guest_name = db.Column(db.String(80), nullable=True)   # 비회원 구매자 이름
    guest_email = db.Column(db.String(120), nullable=True) # 비회원 이메일
    guest_phone = db.Column(db.String(30), nullable=True)  # 비회원 전화번호
    original_amount = db.Column(db.Integer, nullable=False)
    discount_amount = db.Column(db.Integer, default=0)
    #final_amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='COMPLETED') # PENDING, COMPLETED, CANCELLED
    
    # 약관 및 개인정보 동의 항목
    agree_special = db.Column(db.Boolean, default=True, nullable=False)     # 국내여행 특별약관 [필수]
    agree_privacy = db.Column(db.Boolean, default=True, nullable=False)     # 개인정보 제3자 제공동의 [필수]
    agree_sensitive = db.Column(db.Boolean, default=True, nullable=False)   # 민감정보 수집 및 이용 동의 [필수]
    agree_location = db.Column(db.Boolean, default=False, nullable=False)   # 위치 정보 이용 동의 [선택]
    
    # 여행 출발 지정일 (오늘 이후 2주일 이내)
    travel_date = db.Column(db.String(20), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    accommodations = db.relationship('OrderAccommodation', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='order', uselist=False, cascade='all, delete-orphan')

    @classmethod
    def generate_order_no(cls):
        now_str = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        rand_str = uuid.uuid4().hex[:6].upper()
        return f"ORD-{now_str}-{rand_str}"

    @property
    def final_amount(self):
        return (self.original_amount or 0) - (self.discount_amount or 0)

    @property
    def is_past_travel_date(self):
        """이용일이 지났는지 여부 판별 (오늘 이전 날짜인 경우 True)"""
        if not self.travel_date:
            return False
        try:
            t_date = datetime.strptime(self.travel_date.strip(), '%Y-%m-%d').date()
            return t_date < datetime.now().date()
        except Exception:
            return False

    @property
    def primary_product(self):
        """주문의 대표 관광 상품 반환"""
        try:
            item = self.items.first()
            return item.product if item else None
        except Exception:
            return None

    @property
    def nearby_products(self):
        """주문된 관광 상품과 연관된 근처 관광지 목록 반환"""
        prod = self.primary_product
        if prod:
            return prod.get_nearby_products(limit=6)
        return TourProduct.query.order_by(TourProduct.recommendation_count.desc(), TourProduct.id.asc()).limit(6).all()

    @property
    def accommodation_booking(self):
        """주문에 포함된 연계 숙박 예약 정보 (단일 건 또는 None)"""
        try:
            return self.accommodations.first()
        except Exception:
            return None

    def get_user_review(self, user=None, product_id=None):
        """해당 주문의 상품에 대해 사용자가 이미 작성한 Review가 있는지 조회하여 반환"""
        target_pid = product_id
        if not target_pid:
            item = self.items.first()
            if item:
                target_pid = item.product_id

        if not target_pid:
            return None

        if not (user and hasattr(user, 'id')):
            return None

        target_uid = user.id
        return Review.query.filter_by(user_id=target_uid, product_id=target_pid).order_by(Review.created_at.desc()).first()
    
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('tour_products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False) # 주문 시점 적용가
    discount_applied = db.Column(db.Integer, default=0) # 개당 할인액

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), unique=True, nullable=False)
    payment_method = db.Column(db.String(30), default='CARD') # CARD, BANK_TRANSFER, EASY_PAY
    paid_amount = db.Column(db.Integer, nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='SUCCESS') # SUCCESS, FAILED, CANCELLED
    paid_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Accommodation(db.Model):
    __tablename__ = 'accommodations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)      # 숙소명
    category = db.Column(db.String(30), nullable=False, index=True)   # 호텔 / 민박
    region = db.Column(db.String(50), nullable=False, index=True)     # 권역 (RegionEnum 값)
    location = db.Column(db.String(255), nullable=False)              # 장소 및 상세 주소
    price_per_night = db.Column(db.Integer, nullable=False)           # 1박 요금
    image_url = db.Column(db.String(255), nullable=False)             # 이미지 경로 (/static/img/accomodation/...)
    description = db.Column(db.Text, nullable=True)                   # 숙소 특징 / 한줄 소개
    rating = db.Column(db.Float, default=4.8)                         # 평점
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Accommodation [{self.category}] {self.name} ({self.region})>"


class OrderAccommodation(db.Model):
    __tablename__ = 'order_accommodations'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    accommodation_id = db.Column(db.Integer, db.ForeignKey('accommodations.id'), nullable=False)
    nights = db.Column(db.Integer, default=1, nullable=False)         # 숙박 일수 (기본 1박)
    price_per_night = db.Column(db.Integer, nullable=False)           # 결제 시점 1박 요금
    total_price = db.Column(db.Integer, nullable=False)               # 총 숙박 요금 (nights * price_per_night)
    check_in_date = db.Column(db.String(20), nullable=True)           # 체크인 날짜
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    accommodation = db.relationship('Accommodation', backref='order_bookings')

    def __repr__(self):
        return f"<OrderAccommodation order_id={self.order_id} acc_id={self.accommodation_id}>"

#타임딜 참고

class TimeDeal(db.Model):
    __tablename__ = 'time_deal'

    id = db.Column(db.Integer, primary_key=True)
    product_type = db.Column(db.String(10), nullable=False, default='sub')  # 'main'(큰 카드) 또는 'sub'(우측 작은 카드)
    airline = db.Column(db.String(50), nullable=False)  # 예: [아시아나항공], [이스타항공]
    title = db.Column(db.String(200), nullable=False)  # 예: 호주 시드니 | 멜버른 6/7일
    hashtags = db.Column(db.String(200))  # 예: #오페라하우스 내부 #시드니타워
    description = db.Column(db.Text)  # 예: 도시의 낭만과 대자연의 호흡...
    price = db.Column(db.Integer, nullable=False)  # 가격 (숫자로 저장)
    end_date = db.Column(db.DateTime, nullable=False)  # 마감 시간 (디데이 계산용)
    image_file = db.Column(db.String(100), nullable=False)  # 이미지 파일명 (예: sydney.jpg)
    badge1 = db.Column(db.String(50))  # 태그/배지 1 (예: 블루마운틴 시닉4콤보)
    badge2 = db.Column(db.String(50))  # 태그/배지 2 (예: 시드니타워)

# 고객센터
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    create_date = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    email = db.Column(db.String(100), nullable=False)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), default="일반")
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)