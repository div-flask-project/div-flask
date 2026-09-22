import os
BASE_DIR = os.path.dirname(__file__)
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'travel.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Forma module 환경 변수
SECRET_KEY = 'secret key'# config.py