from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
import enum
import uuid
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

class RegionEnum(str, enum.Enum):
    SEOUL_GYEONGGI = "서울/경기"
    JEONLA = "전라"
    CHUNGCHEONG = "충청"
    GANGWON = "강원"
    GYEONGBUK = "경북"
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
        if not user or not user.is_authenticated:
            return False
        return self.likes.filter_by(user_id=user.id).first() is not None

    def get_image_list(self):
        """관광 상품의 다중 이미지 URL 목록 반환 (없을 경우 기본 image_url 또는 기본 이미지 반환)"""
        if self.image_urls:
            try:
                import json
                urls = json.loads(self.image_urls)
                if isinstance(urls, list) and len(urls) > 0:
                    return urls
            except Exception:
                urls = [u.strip() for u in self.image_urls.splitlines() if u.strip()]
                if urls:
                    return urls
        if self.image_url:
            return [self.image_url]
        return ['/static/img/default-tour.jpg']

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

    def __repr__(self):
        return f"<TourProduct {self.name} ({self.region})>"
    
class ProductLike(db.Model):
    __tablename__ = 'product_likes'
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
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    #accommodations = db.relationship('OrderAccommodation', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='order', uselist=False, cascade='all, delete-orphan')

    @classmethod
    def generate_order_no(cls):
        now_str = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        rand_str = uuid.uuid4().hex[:6].upper()
        return f"ORD-{now_str}-{rand_str}"

    @property
    def final_amount(self):
        return (self.original_amount or 0) - (self.discount_amount or 0)
    
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
