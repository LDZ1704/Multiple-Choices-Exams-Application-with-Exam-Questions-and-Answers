from flask_admin import AdminIndexView, expose, Admin, BaseView
from app import app, db, admin, login_manager
from app.models import User, Student, Exam, Question, Answer, Role
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user


class AuthenticatedView(ModelView):
    def is_accessible(self):
        if not current_user.is_authenticated or current_user.role != Role.ADMIN:
            logout_user()
            return False
        return True

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Student, db.session))
admin.add_view(ModelView(Exam, db.session))
admin.add_view(ModelView(Question, db.session))
admin.add_view(ModelView(Answer, db.session))