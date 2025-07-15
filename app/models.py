import datetime
from enum import Enum as RoleEnum
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, Enum
from app import app, db

class Role(RoleEnum):
    ADMIN = 1,
    TEACHER = 2,
    STUDENT = 3

class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

class User(Base, UserMixin):
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    avatar = Column(String(100), default="https://res.cloudinary.com/denmq54ke/image/upload/v1752161601/login_register_d1oj9t.png")
    role = Column(Enum(Role), default=Role.STUDENT)
    gender = Column(String(6), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updateAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subject(Base):
    subject_name = Column(String(100), nullable=False)
    description = Column(String(200), nullable=True)

# class

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        # db.create_all()