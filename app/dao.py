import hashlib
from app.models import User, Student, Admin
from app import db
import cloudinary
import random
from datetime import datetime, timedelta
import string


def auth_user(username, password, role=None):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())

    u = User.query.filter(User.username.__eq__(username),
                          User.password.__eq__(password))
    if role:
        u = u.filter(User.role.__eq__(role))

    return u.first()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def existence_check(table, attribute, value):
    return table.query.filter(getattr(table, attribute).__eq__(value)).first()


def add_user(name, username, password, email, gender):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = User(name=name, username=username, password=password, email=email, gender=gender)
    db.session.add(user)
    db.session.commit()


def add_student(user):
    student = Student(user_id=user.id)
    db.session.add(student)
    db.session.commit()


def add_admin(user):
    admin = Admin(user_id=user.id)
    db.session.add(admin)
    db.session.commit()


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def update_password(user_id, new_password):
    user = User.query.get(user_id)
    if user:
        user.password = str(hashlib.md5(new_password.encode('utf-8')).hexdigest())
        user.updateAt = datetime.now()
        db.session.commit()
        return True
    return False
