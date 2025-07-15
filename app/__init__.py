from urllib.parse import quote
import cloudinary
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "DHWOIAH_WAHD*(WAD*Y(W*A"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:%s@localhost/exams?charset=utf8mb4" % quote('123456')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

cloudinary.config(
    cloud_name = "denmq54ke",
    api_key = "628893662521679",
    api_secret = "vZN_2d4jJOvSwlCFRp7pU_zgH58",
    secure=True
)