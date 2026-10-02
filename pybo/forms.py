# pybo/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp, NumberRange, Optional
from pybo.models import User
from datetime import datetime, timedelta, date
import re


# =========================================================================
# 1. 회원가입 검증 폼 (UserCreateForm)
# =========================================================================
class UserCreateForm(FlaskForm):
    user_id = StringField('아이디', validators=[
        DataRequired('아이디는 필수 입력 항목입니다.'),
        Length(min=4, max=25, message='아이디는 4자 이상 25자 이하로 입력해 주세요.'),
        Regexp('^[a-zA-Z0-9]+$', message='아이디는 영문 대소문자와 숫자만 사용할 수 있습니다.')
    ])

    name = StringField('이름', validators=[
        DataRequired('이름은 필수 입력 항목입니다.')
    ])

    email = EmailField('이메일', validators=[
        DataRequired('이메일은 필수 입력 항목입니다.'),
        Email('올바른 이메일 형식이 아닙니다.')
    ])

    phone = StringField('전화번호', validators=[
        DataRequired('전화번호는 필수 입력 항목입니다.')
    ])

    password = PasswordField('비밀번호', validators=[
        DataRequired('비밀번호는 필수 입력 항목입니다.'),
        Length(min=6, message='비밀번호는 최소 6자 이상이어야 합니다.')
    ])

    password_confirm = PasswordField('비밀번호 확인', validators=[
        DataRequired('비밀번호 확인은 필수 입력 항목입니다.'),
        EqualTo('password', message='비밀번호가 일치하지 않습니다.')
    ])

    def validate_user_id(self, field):
        if User.query.filter_by(user_id=field.data).first():
            raise ValidationError('이미 사용 중인 아이디입니다.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('이미 등록된 이메일 주소입니다.')

    def validate_phone(self, field):
        if User.query.filter_by(phone=field.data).first():
            raise ValidationError('이미 등록된 전화번호입니다.')


# =========================================================================
# 2. 로그인 검증 폼 (UserLoginForm)
# =========================================================================
class UserLoginForm(FlaskForm):
    user_id = StringField('아이디', validators=[
        DataRequired('아이디를 입력해 주세요.')
    ])
    password = PasswordField('비밀번호', validators=[
        DataRequired('비밀번호를 입력해 주세요.')
    ])


class OptionalIntegerField(IntegerField):
    """빈 문자열이나 공백, 0 등이 입력되어도 오류(Not a valid integer value) 없이 None으로 안전하게 처리하는 IntegerField"""
    def process_formdata(self, valuelist):
        if not valuelist:
            self.data = None
            return
        val = str(valuelist[0]).strip()
        if not val or val in ['0', 'None', 'null', 'undefined']:
            self.data = None
            return
        try:
            self.data = int(val)
        except (ValueError, TypeError):
            self.data = None


# =========================================================================
# 3. 여행 상품 예약 검증 폼 (OrderReserveForm)
# =========================================================================
class OrderReserveForm(FlaskForm):
    product_id = IntegerField('상품 ID', validators=[
        DataRequired('예약하실 여행 상품 정보가 올바르지 않습니다.')
    ])

    headcount = IntegerField('예약 인원수', default=1, validators=[
        DataRequired('예약 인원수를 입력해 주세요.'),
        NumberRange(min=1, max=20, message='예약 인원은 1명 이상 20명 이하이어야 합니다.')
    ])

    # 비회원(Guest) 예약자 정보 (비회원 예약 시 필수)
    guest_name = StringField('예약자 성함', validators=[
        Length(max=80, message='예약자 성함은 80자 이내로 입력해 주세요.')
    ])

    guest_phone = StringField('휴대폰 번호', validators=[
        Length(max=30, message='휴대폰 번호는 30자 이내로 입력해 주세요.')
    ])

    guest_email = EmailField('이메일 주소', validators=[
        Length(max=120, message='이메일 주소는 120자 이내로 입력해 주세요.')
    ])

    # 여행 날짜 (오늘 이후 2주일 이내 선택)
    travel_date = StringField('여행 날짜', validators=[
        DataRequired('여행 날짜를 선택해 주세요.')
    ])

    # 필수 약관 동의 (국내여행 특별약관, 개인정보 제3자 제공, 민감정보 수집)
    agree_special = BooleanField('국내여행 특별약관 동의', validators=[
        DataRequired('국내여행 특별약관[필수]에 동의하셔야 예약을 진행하실 수 있습니다.')
    ])

    agree_privacy = BooleanField('개인정보 제3자 제공동의', validators=[
        DataRequired('개인정보 제3자 제공동의[필수]에 동의하셔야 예약을 진행하실 수 있습니다.')
    ])

    agree_sensitive = BooleanField('민감정보 수집 및 이용 동의', validators=[
        DataRequired('민감정보 수집 및 이용 동의[필수]에 동의하셔야 예약을 진행하실 수 있습니다.')
    ])

    # 선택 약관 동의 (위치 정보 이용 동의)
    agree_location = BooleanField('위치 정보 이용 동의')

    # 연관 숙박 상품 ID (회원 선택 시 옵션, 미선택 시 안전하게 None 처리)
    accommodation_id = OptionalIntegerField('연계 숙박 상품 ID', validators=[Optional()])

    def __init__(self, *args, is_member=False, **kwargs):
        super(OrderReserveForm, self).__init__(*args, **kwargs)
        self.is_member = is_member

    def validate_travel_date(self, field):
        """여행 날짜 검증: 오늘 이후부터 2주일(14일) 이내만 허용"""
        val = (field.data or '').strip()
        if not val:
            raise ValidationError('여행 날짜는 필수 입력 항목입니다.')
        try:
            selected_date = datetime.strptime(val, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError('올바른 날짜 형식(YYYY-MM-DD)을 입력해 주세요.')

        today = datetime.now().date()
        min_date = today + timedelta(days=1)
        max_date = today + timedelta(days=14)

        if selected_date < min_date:
            raise ValidationError('여행 날짜는 오늘 이후(내일)부터 선택 가능합니다.')
        if selected_date > max_date:
            raise ValidationError(f'여행 날짜는 오늘 기준 2주일 이내({max_date.strftime("%Y-%m-%d")}까지)만 선택 가능합니다.')

    def validate_guest_name(self, field):
        """비회원 예약 시 예약자 성함 필수 검증"""
        if not self.is_member and not (field.data and field.data.strip()):
            raise ValidationError('비회원 예약 시 예약자 성함은 필수 입력 항목입니다.')

    def validate_guest_phone(self, field):
        """비회원 예약 시 휴대폰 번호 필수 검증"""
        if not self.is_member and not (field.data and field.data.strip()):
            raise ValidationError('비회원 예약 시 휴대폰 번호는 필수 입력 항목입니다.')

    def validate_guest_email(self, field):
        """비회원 예약 시 이메일 주소 및 형식 필수 검증"""
        if not self.is_member:
            val = (field.data or '').strip()
            if not val:
                raise ValidationError('비회원 예약 시 이메일 주소는 필수 입력 항목입니다.')
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', val):
                raise ValidationError('올바른 이메일 형식을 입력해 주세요.')


# 호환성 별칭
ReserveForm = OrderReserveForm

