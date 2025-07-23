from urllib.parse import quote
import cloudinary
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin

app = Flask(__name__)

app.secret_key = "DHWOIAH_WAHD*(WAD*Y(W*A"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:%s@localhost/exams?charset=utf8mb4" % quote('123456')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['PAGE_SIZE'] = 6

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'lamn9049@gmail.com'
app.config['MAIL_PASSWORD'] = 'bvuv pifb xaot waeb'
app.config['MAIL_DEFAULT_SENDER'] = 'lamn9049@gmail.com'

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager(app)

login_manager.login_view = 'login'
login_manager.login_message = 'Bạn cần đăng nhập để truy cập vào trang này'

admin = Admin(app=app, name='LmaoQuizManagement', template_mode='bootstrap4')

cloudinary.config(
    cloud_name="denmq54ke",
    api_key="628893662521679",
    api_secret="vZN_2d4jJOvSwlCFRp7pU_zgH58",
    secure=True
)
