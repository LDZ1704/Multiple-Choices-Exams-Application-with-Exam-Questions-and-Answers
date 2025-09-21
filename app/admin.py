import hashlib
from datetime import datetime, timedelta
from flask_admin import AdminIndexView, expose, Admin, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_login import current_user, logout_user
from flask import request, redirect, url_for, flash, render_template, Response, jsonify
from sqlalchemy import func, and_, desc
from wtforms import fields, validators
import csv
from io import StringIO
from app import app, db, admin
from app.models import User, Student, Exam, Question, Answer, Role, ExamResult, Subject, Chapter, ExamQuestions, \
    Comment, Admin, Notification, ExamSession, StudyRecommendation, LearningPath, SuspiciousActivity, Rating
from flask_admin.form import BaseForm


class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        logout_user()
        flash('Bạn cần đăng nhập với quyền quản trị để truy cập trang này.', 'error')
        return redirect(url_for('login', next=request.url))

    can_view_details = True
    details_template = 'admin/model/details.html'
    edit_template = 'admin/model/edit.html'
    create_template = 'admin/model/edit.html'
    list_template = 'admin/model/list.html'
    page_size = 20
    can_export = True


class AuthenticatedBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        logout_user()
        flash('Bạn cần đăng nhập với quyền quản trị để truy cập trang này.', 'error')
        return redirect(url_for('login', next=request.url))


class CustomAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return redirect(url_for('dashboard.index'))

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        logout_user()
        flash('Bạn cần đăng nhập với quyền quản trị để truy cập trang này.', 'error')
        return redirect(url_for('login', next=request.url))


class UserAdmin(AuthenticatedView):
    column_list = ['id', 'name', 'username', 'password', 'email', 'role', 'gender', 'createdAt', 'updateAt']
    column_searchable_list = ['name', 'username', 'email', 'role', 'gender']
    column_filters = ['name', 'role', 'gender']
    column_labels = {
        'id': 'ID',
        'name': 'Họ tên',
        'username': 'Tên đăng nhập',
        'password': 'Mật khẩu',
        'email': 'Email',
        'role': 'Vai trò',
        'gender': 'Giới tính',
        'createdAt': 'Ngày tạo',
        'updateAt': 'Ngày cập nhật'
    }

    form_excluded_columns = ['student', 'admin', 'comments', 'exams', 'questions', 'answers', 'createdAt', 'updateAt']

    form_columns = ['name', 'username', 'email', 'password', 'role', 'gender']

    def scaffold_form(self):
        form_class = super().scaffold_form()
        form_class.name = fields.StringField('Họ tên', validators=[validators.DataRequired('Tên là bắt buộc')])
        form_class.username = fields.StringField('Tên đăng nhập', validators=[validators.DataRequired('Tên đăng nhập là bắt buộc')])
        form_class.email = fields.StringField('Email', validators=[validators.DataRequired('Email là bắt buộc'), validators.Email('Email không hợp lệ')])
        form_class.password = fields.PasswordField('Mật khẩu', validators=[validators.DataRequired('Mật khẩu là bắt buộc')])
        form_class.gender = fields.StringField('Giới tính', validators=[validators.DataRequired('Giới tính là bắt buộc')])

        delattr(form_class, 'role')
        form_class.role = fields.SelectField('Vai trò',
                                             choices=[(Role.ADMIN.value, 'Admin'), (Role.STUDENT.value, 'Student')],
                                             validators=[validators.DataRequired('Vai trò là bắt buộc')],
                                             coerce=int)
        return form_class

    def on_model_change(self, form, model, is_created):
        if hasattr(form, 'role') and form.role.data:
            if form.role.data == 1:
                model.role = Role.ADMIN
            elif form.role.data == 2:
                model.role = Role.STUDENT

        if hasattr(form, 'password') and form.password.data:
            if not is_created:
                current_password = db.session.get(User, model.id).password if model.id else None
                new_password_hash = str(hashlib.md5(form.password.data.encode('utf-8')).hexdigest())

                if current_password != new_password_hash:
                    model.password = new_password_hash
            else:
                model.password = str(hashlib.md5(form.password.data.encode('utf-8')).hexdigest())

        if is_created:
            model.createdAt = datetime.now()

            if model.role == Role.STUDENT:
                student = Student(user=model)
                db.session.add(student)
            elif model.role == Role.ADMIN:
                admin_record = Admin(user=model)
                db.session.add(admin_record)
        else:
            model.updateAt = datetime.now()

    def on_model_delete(self, model):
        try:
            Comment.query.filter_by(user_id=model.id).delete()
            Notification.query.filter_by(user_id=model.id).delete()

            if model.role == Role.STUDENT:
                student = Student.query.filter_by(user_id=model.id).first()
                if student:
                    exam_results = ExamResult.query.filter_by(student_id=student.id).all()
                    for result in exam_results:
                        result.student_name = model.name
                        result.student_id = None
                    ExamSession.query.filter_by(student_id=student.id).delete()
                    StudyRecommendation.query.filter_by(student_id=student.id).delete()
                    LearningPath.query.filter_by(student_id=student.id).delete()
                    SuspiciousActivity.query.filter_by(student_id=student.id).delete()
                    db.session.delete(student)

            elif model.role == Role.ADMIN:
                admin_record = Admin.query.filter_by(user_id=model.id).first()
                exams = Exam.query.filter_by(user_id=model.id).all()
                for exam in exams:
                    exam_results = ExamResult.query.filter_by(exam_id=exam.id).all()
                    for result in exam_results:
                        result.exam_name = exam.exam_name
                        result.exam_id = None
                    Rating.query.filter_by(exam_id=exam.id).delete()
                    ExamQuestions.query.filter_by(exam_id=exam.id).delete()
                    Comment.query.filter_by(exam_id=exam.id).delete()
                    ExamSession.query.filter_by(exam_id=exam.id).delete()
                    SuspiciousActivity.query.filter_by(exam_id=exam.id).delete()
                    Notification.query.filter_by(exam_id=exam.id).delete()
                Exam.query.filter_by(user_id=model.id).delete()
                if admin_record:
                    db.session.delete(admin_record)

            db.session.delete(model)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f'Không thể xóa người dùng: {str(e)}')


class ExamAdmin(AuthenticatedView):
    column_list = ['id', 'exam_name', 'subject.subject_name', 'duration', 'start_time', 'end_time' , 'createBy', 'createAt']
    column_searchable_list = ['exam_name', 'createBy']
    column_filters = ['subject.subject_name', 'duration', 'createBy']
    column_labels = {
        'id': 'ID',
        'exam_name': 'Tên đề thi',
        'subject.subject_name': 'Môn học',
        'duration': 'Thời gian (phút)',
        'start_time': 'Thời gian bắt đầu',
        'end_time': 'Thời gian kết thúc',
        'createBy': 'Người tạo',
        'createAt': 'Ngày tạo'
    }

    form_excluded_columns = ['exam_results', 'exam_questions', 'comments', 'createAt', 'createBy', 'user']

    form_args = {
        'exam_name': {'validators': [validators.DataRequired("Tên đề thi là bắt buộc")]},
        'subject': {
            'query_factory': lambda: Subject.query.all(),
            'get_label': lambda s: s.subject_name,
            'validators': [validators.DataRequired("Môn học là bắt buộc")]
        },
        'duration': {'validators': [validators.DataRequired("Thời gian thi là bắt buộc"),
                                    validators.NumberRange(min=1, max=300, message="Thời gian từ 1-300 phút")]},
        'start_time': {'validators': [validators.DataRequired("Thời gian bắt đầu là bắt buộc")]},
        'end_time': {'validators': [validators.DataRequired("Thời gian kết thúc là bắt buộc")]},
        'user': {
            'query_factory': lambda: User.query.all(),
            'get_label': lambda u: u.username
        }
    }

    column_formatters = {
        'subject.subject_name': lambda v, c, m, p: m.subject.subject_name if m.subject else '-'
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.user_id = current_user.id
            model.createBy = current_user.name
            model.createAt = datetime.now()

    def on_model_delete(self, model):
        try:
            exam_results = ExamResult.query.filter_by(exam_id=model.id).all()
            for result in exam_results:
                if not result.exam_name:
                    result.exam_name = model.exam_name
                result.exam_id = None
            Rating.query.filter_by(exam_id=model.id).delete()
            ExamSession.query.filter_by(exam_id=model.id).delete()
            SuspiciousActivity.query.filter_by(exam_id=model.id).delete()
            Notification.query.filter_by(exam_id=model.id).delete()
            Comment.query.filter_by(exam_id=model.id).delete()
            ExamQuestions.query.filter_by(exam_id=model.id).delete()

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f'Không thể xóa đề thi: {str(e)}')


class QuestionAdmin(AuthenticatedView):
    column_list = ['id', 'question_title', 'chapter', 'createBy', 'createAt']
    column_searchable_list = ['question_title', 'createBy']
    column_filters = ['chapter', 'createBy']
    column_labels = {
        'id': 'ID',
        'question_title': 'Câu hỏi',
        'chapter': 'Chương',
        'createBy': 'Người tạo',
        'createAt': 'Ngày tạo'
    }

    form_excluded_columns = ['answers', 'exam_questions', 'createAt', 'createBy', 'user']

    form_args = {
        'question_title': {
            'validators': [validators.DataRequired("Câu hỏi là bắt buộc")]
        },
        'chapter': {
            'query_factory': lambda: Chapter.query.all(),
            'get_label': lambda c: c.chapter_name,
            'validators': [validators.DataRequired("Chương là bắt buộc")]
        }
    }

    form_columns = ['question_title', 'chapter']

    def scaffold_form(self):
        form_class = super().scaffold_form()
        form_class.question_title = fields.TextAreaField(
            'Câu hỏi',
            validators=[validators.DataRequired('Câu hỏi là bắt buộc')],
            render_kw={'rows': 4}
        )
        return form_class

    column_formatters = {
        'chapter': lambda v, c, m, p: m.chapter.chapter_name if m.chapter else '-'
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.user_id = current_user.id
            model.createBy = current_user.name
            model.createAt = datetime.now()


class AnswerAdmin(AuthenticatedView):
    column_list = ['id', 'question.question_title', 'answer_text', 'is_correct', 'explanation', 'createBy']
    column_searchable_list = ['answer_text', 'createBy']
    column_filters = ['question.question_title', 'is_correct', 'createBy']
    column_labels = {
        'id': 'ID',
        'question.question_title': 'Câu hỏi',
        'answer_text': 'Đáp án',
        'is_correct': 'Đúng/Sai',
        'explanation': 'Giải thích',
        'createBy': 'Người tạo'
    }

    column_formatters = {
        'question.question_title': lambda v, c, m, p: m.question.question_title if m.question else '-'
    }

    form_excluded_columns = ['createBy', 'user']

    form_args = {
        'question': {
            'query_factory': lambda: Question.query.all(),
            'get_label': lambda q: q.question_title[:50],
            'validators': [validators.DataRequired("Câu hỏi là bắt buộc")]
        },
        'answer_text': {'validators': [validators.DataRequired("Đáp án là bắt buộc")]},
        'user': {
            'query_factory': lambda: User.query.all(),
            'get_label': lambda u: u.username
        }
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.user_id = current_user.id
            model.createBy = current_user.name


class SubjectAdmin(AuthenticatedView):
    column_list = ['id', 'subject_name', 'description']
    column_searchable_list = ['subject_name']
    column_filters = ['subject_name']
    column_labels = {
        'id': 'ID',
        'subject_name': 'Tên môn học',
        'description': 'Mô tả'
    }

    column_formatters = {
        'admin': lambda v, c, m, p: m.admin.user.name if m.admin and m.admin.user else '-'
    }

    form_excluded_columns = ['chapters', 'exams', 'admin']

    form_args = {
        'subject_name': {'validators': [validators.DataRequired("Tên môn học là bắt buộc")]},
        'description': {'validators': [validators.Optional()]}
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            admin_record = Admin.query.filter_by(user_id=current_user.id).first()
            if admin_record:
                model.admin_id = admin_record.id


class ChapterAdmin(AuthenticatedView):
    column_list = ['id', 'chapter_name', 'subject.subject_name']
    column_searchable_list = ['chapter_name']
    column_filters = ['chapter_name']
    column_labels = {
        'id': 'ID',
        'chapter_name': 'Tên chương',
        'subject.subject_name': 'Môn học'
    }

    form_excluded_columns = ['questions']

    form_args = {
        'chapter_name': {'validators': [validators.DataRequired("Tên chương là bắt buộc")]},
        'subject': {
            'query_factory': lambda: Subject.query.all(),
            'get_label': lambda s: s.subject_name,
            'validators': [validators.DataRequired("Môn học là bắt buộc")]
        }
    }

    column_formatters = {
        'subject.subject_name': lambda v, c, m, p: m.subject.subject_name if m.subject else '-'
    }


class ExamResultAdmin(AuthenticatedView):
    column_list = ['id', 'student.user.name', 'exam.exam_name', 'score', 'taken_exam', 'time_taken', 'is_first_attempt',
                   'difficulty_level', 'time_efficiency']
    column_searchable_list = ['student.user.name', 'exam.exam_name']
    column_filters = ['exam.exam_name', 'student.user.name', 'score', 'is_first_attempt', 'difficulty_level']
    column_labels = {
        'id': 'ID',
        'student.user.name': 'Học sinh',
        'exam.exam_name': 'Đề thi',
        'score': 'Điểm',
        'taken_exam': 'Thời gian thi',
        'time_taken': 'Thời gian làm (giây)',
        'is_first_attempt': 'Lần đầu thi',
        'difficulty_level': 'Mức độ khó',
        'time_efficiency': 'Hiệu suất thời gian',
        'user_answers': 'Câu trả lời của người dùng'
    }

    column_formatters = {
        'student': lambda v, c, m, p: m.student.user.name if m.student and m.student.user else '-',
        'student.user.name': lambda v, c, m, p: m.student.user.name if m.student and m.student.user else '-',
        'exam.exam_name': lambda v, c, m, p: m.exam.exam_name if m.exam else '-',
        'time_efficiency': lambda v, c, m, p: f"{m.time_efficiency:.2f}" if m.time_efficiency else '-'
    }

    can_create = False
    can_edit = True
    form_columns = ['score', 'difficulty_level', 'time_efficiency']

    def scaffold_form(self):
        form_class = super().scaffold_form()
        form_class.difficulty_level = fields.SelectField('Mức độ khó', choices=[('easy', 'Dễ'), ('medium', 'Trung bình'), ('hard', 'Khó')], validators=[validators.Optional()])
        return form_class

    def on_form_prefill(self, form, id):
        if hasattr(form, 'score'):
            form.score.validators = [validators.NumberRange(min=0, max=100)]


class CommentAdmin(AuthenticatedView):
    column_list = ['id', 'user.name', 'exam.exam_name', 'content', 'created_at', 'updated_at']
    column_searchable_list = ['content']
    column_filters = ['exam.exam_name', 'user.name']
    column_labels = {
        'id': 'ID',
        'user.name': 'Người dùng',
        'exam.exam_name': 'Đề thi',
        'content': 'Nội dung',
        'created_at': 'Ngày tạo',
        'updated_at': 'Ngày cập nhật'
    }

    form_excluded_columns = ['created_at', 'updated_at']

    form_args = {
        'content': {'validators': [validators.DataRequired("Nội dung bình luận là bắt buộc")]},
        'exam': {
            'query_factory': lambda: Exam.query.all(),
            'get_label': lambda e: e.exam_name,
            'validators': [validators.DataRequired("Đề thi là bắt buộc")]
        },
        'user': {
            'query_factory': lambda: User.query.all(),
            'get_label': lambda u: u.username,
            'validators': [validators.DataRequired("Người dùng là bắt buộc")]
        }
    }

    column_formatters = {
        'user.name': lambda v, c, m, p: m.user.name if m.user else '-',
        'exam.exam_name': lambda v, c, m, p: m.exam.exam_name if m.exam else '-'
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_at = datetime.now()
        model.updated_at = datetime.now()


class RatingAdmin(AuthenticatedView):
    column_list = ['id', 'user.name', 'exam.exam_name', 'rating', 'created_at', 'updated_at']
    column_searchable_list = ['user.name', 'exam.exam_name']
    column_filters = ['rating', 'created_at']
    column_labels = {
        'id': 'ID',
        'user.name': 'Người dùng',
        'exam.exam_name': 'Đề thi',
        'rating': 'Đánh giá (1-5 sao)',
        'created_at': 'Ngày tạo',
        'updated_at': 'Ngày cập nhật'
    }

    form_excluded_columns = ['created_at', 'updated_at']
    form_args = {
        'user': {
            'query_factory': lambda: User.query.all(),
            'get_label': lambda u: u.name,
            'validators': [validators.DataRequired("Người dùng là bắt buộc")]
        },
        'exam': {
            'query_factory': lambda: Exam.query.all(),
            'get_label': lambda e: e.exam_name,
            'validators': [validators.DataRequired("Đề thi là bắt buộc")]
        },
        'rating': {'validators': [validators.DataRequired("Đánh giá là bắt buộc"), validators.NumberRange(min=1, max=5, message="Đánh giá từ 1-5 sao")]}
    }

    column_formatters = {
        'user.name': lambda v, c, m, p: m.user.name if m.user else '-',
        'exam.exam_name': lambda v, c, m, p: m.exam.exam_name if m.exam else '-'
    }


class ExamSessionAdmin(AuthenticatedView):
    column_list = ['id', 'student.user.name', 'exam.exam_name', 'start_time', 'is_paused', 'is_completed', 'current_question_index', 'isolations_count']
    column_searchable_list = ['student.user.name', 'exam.exam_name']
    column_filters = ['is_paused', 'is_completed', 'is_terminated', 'start_time']
    column_labels = {
        'id': 'ID',
        'student.user.name': 'Học sinh',
        'exam.exam_name': 'Đề thi',
        'start_time': 'Thời gian bắt đầu',
        'is_paused': 'Đang tạm dừng',
        'is_completed': 'Đã hoàn thành',
        'current_question_index': 'Câu hỏi hiện tại',
        'isolations_count': 'Số lần vi phạm',
        'window_focus_lost_count': 'Mất tập trung cửa sổ'
    }

    form_excluded_columns = ['start_time', 'pause_time', 'resume_time', 'total_paused_duration', 'user_answers', 'question_order', 'answer_orders']
    can_create = False
    can_edit = True

    column_formatters = {
        'student': lambda v, c, m, p: m.student.user.name if m.student and m.student.user else '-',
        'student.user.name': lambda v, c, m, p: m.student.user.name if m.student and m.student.user else '-',
        'exam.exam_name': lambda v, c, m, p: m.exam.exam_name if m.exam else '-'
    }


class SuspiciousActivityAdmin(AuthenticatedView):
    column_list = ['id', 'student.user.name', 'exam.exam_name', 'activity_type', 'timestamp']
    column_searchable_list = ['student.user.name', 'exam.exam_name', 'activity_type']
    column_filters = ['activity_type', 'timestamp']
    column_labels = {
        'id': 'ID',
        'student.user.name': 'Học sinh',
        'exam.exam_name': 'Đề thi',
        'activity_type': 'Loại hoạt động',
        'timestamp': 'Thời gian',
        'details': 'Chi tiết'
    }

    can_create = False
    can_edit = False
    can_delete = True


class NotificationAdmin(AuthenticatedView):
    column_list = ['id', 'user.name', 'title', 'notification_type', 'is_read', 'created_at']
    column_searchable_list = ['user.name', 'title', 'message']
    column_filters = ['notification_type', 'is_read', 'created_at']
    column_labels = {
        'id': 'ID',
        'user.name': 'Người dùng',
        'title': 'Tiêu đề',
        'message': 'Nội dung',
        'notification_type': 'Loại thông báo',
        'exam.exam_name': 'Đề thi',
        'is_read': 'Đã đọc',
        'created_at': 'Ngày tạo'
    }

    form_excluded_columns = ['created_at']
    form_args = {
        'user': {
            'query_factory': lambda: User.query.all(),
            'get_label': lambda u: u.name,
            'validators': [validators.DataRequired("Người dùng là bắt buộc")]
        },
        'title': {'validators': [validators.DataRequired("Tiêu đề là bắt buộc")]},
        'message': {'validators': [validators.DataRequired("Nội dung là bắt buộc")]},
        'exam': {
            'query_factory': lambda: Exam.query.all(),
            'get_label': lambda e: e.exam_name,
            'validators': [validators.Optional()]
        }
    }

    column_formatters = {
        'user.name': lambda v, c, m, p: m.user.name if m.user else '-',
    }

    def scaffold_form(self):
        form_class = super().scaffold_form()
        form_class.notification_type = fields.SelectField('Loại thông báo',
            choices=[
                ('info', 'Thông tin'), ('warning', 'Cảnh báo'), ('success', 'Thành công'),
                ('reminder', 'Nhắc nhở'), ('result', 'Kết quả'), ('suggestion', 'Đề xuất'),
                ('new_exam', 'Đề thi mới')
            ],
            validators=[validators.DataRequired('Loại thông báo là bắt buộc')])
        return form_class


class LogoutView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        logout_user()
        flash('Đã đăng xuất thành công.', 'success')
        return redirect('/admin')


class DashboardAdminView(AuthenticatedBaseView):
    @expose('/')
    def index(self, **kwargs):
        stats = {
            'total_exams': Exam.query.count(),
            'total_users': User.query.count(),
            'total_students': Student.query.count(),
            'total_attempts': ExamResult.query.count(),
            'total_questions': Question.query.count(),
            'total_subjects': Subject.query.count(),
            'total_comments': Comment.query.count()
        }
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        stats['today_attempts'] = ExamResult.query.filter(db.func.date(ExamResult.taken_exam) == today).count()
        stats['week_attempts'] = ExamResult.query.filter(db.func.date(ExamResult.taken_exam) >= week_ago).count()
        recent_exams = Exam.query.order_by(Exam.createAt.desc()).limit(5).all()
        recent_time = datetime.now() - timedelta(minutes=30)
        stats['active_sessions'] = ExamResult.query.filter(ExamResult.taken_exam >= recent_time).count()
        recent_results = db.session.query(ExamResult).join(Exam).join(Student).join(User).order_by(desc(ExamResult.taken_exam)).limit(10).all()
        return self.render('admin/dashboard.html', stats=stats, recent_exams=recent_exams, recent_results=recent_results, datetime=datetime, current_user=current_user)


class AnalyticsReportsView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        try:
            total_students = User.query.filter_by(role=Role.STUDENT).count()
            total_exams = Exam.query.count()
            total_attempts = ExamResult.query.count()
            total_questions = Question.query.count()
            total_subjects = Subject.query.count()
            total_comments = Comment.query.count()

            avg_score_result = db.session.query(func.avg(ExamResult.score)).scalar()
            avg_score = round(avg_score_result, 1) if avg_score_result else 0

            today = datetime.now().date()
            week_ago = today - timedelta(days=7)

            new_students_today = User.query.filter(and_(User.role == Role.STUDENT, func.date(User.createdAt) == today)).count()
            attempts_today = ExamResult.query.filter(func.date(ExamResult.taken_exam) == today).count()
            week_attempts = ExamResult.query.filter(func.date(ExamResult.taken_exam) >= week_ago).count()
            active_exams = db.session.query(Exam.id).join(ExamResult).distinct().count()

            exam_stats = db.session.query(
                Exam.exam_name,
                Subject.subject_name,
                func.coalesce(func.count(ExamResult.id), 0).label('attempts'),
                func.coalesce(func.avg(ExamResult.score), 0).label('avg_score'),
                func.coalesce(func.max(ExamResult.score), 0).label('max_score'),
                func.coalesce(func.min(ExamResult.score), 0).label('min_score')
            ).select_from(Exam).join(Subject, Exam.subject_id == Subject.id) \
                .outerjoin(ExamResult, Exam.id == ExamResult.exam_id) \
                .group_by(Exam.id, Exam.exam_name, Subject.subject_name) \
                .order_by(func.coalesce(func.count(ExamResult.id), 0).desc()) \
                .all()

            top_students = db.session.query(
                User.name,
                func.coalesce(func.avg(ExamResult.score), 0).label('avg_score'),
                func.count(ExamResult.id).label('total_exams')
            ).select_from(User) \
                .join(Student, User.id == Student.user_id) \
                .outerjoin(ExamResult, Student.id == ExamResult.student_id) \
                .group_by(User.id, User.name) \
                .having(func.count(ExamResult.id) > 0) \
                .order_by(func.coalesce(func.avg(ExamResult.score), 0).desc()) \
                .limit(10).all()

            user_stats = db.session.query(
                User.name,
                func.coalesce(func.avg(ExamResult.score), 0).label('avg_score')
            ).select_from(User) \
                .join(Student, User.id == Student.user_id) \
                .outerjoin(ExamResult, Student.id == ExamResult.student_id) \
                .group_by(User.id, User.name).all()

            top_exams = self.get_top_exams_with_stats()

            total_stats = {
                'total_exams': total_exams,
                'total_students': total_students,
                'total_attempts': total_attempts,
                'total_questions': total_questions,
                'total_subjects': total_subjects,
                'total_comments': total_comments
            }

            avg_study_time = 45
            improvement_rate = 68

            if avg_score >= 70:
                score_trend = "Tăng trưởng"
            elif avg_score >= 50:
                score_trend = "Ổn định"
            else:
                score_trend = "Cần cải thiện"

            return self.render('admin/analytics_reports.html',
                               total_students=total_students,
                               total_exams=total_exams,
                               total_attempts=total_attempts,
                               avg_score=avg_score,
                               new_students_today=new_students_today,
                               attempts_today=attempts_today,
                               week_attempts=week_attempts,
                               active_exams=active_exams,
                               top_exams=top_exams,
                               avg_study_time=avg_study_time,
                               improvement_rate=improvement_rate,
                               score_trend=score_trend,
                               total_stats=total_stats,
                               exam_stats=exam_stats,
                               top_students=top_students,
                               user_stats=user_stats,
                               current_user=current_user)
        except Exception as e:
            flash(f'Lỗi khi tải dữ liệu analytics: {str(e)}', 'error')
            return self.render('admin/analytics_reports.html',
                               total_students=0,
                               total_exams=0,
                               total_attempts=0,
                               avg_score=0,
                               new_students_today=0,
                               attempts_today=0,
                               week_attempts=0,
                               active_exams=0,
                               top_exams=[],
                               avg_study_time=0,
                               improvement_rate=0,
                               score_trend="Không có dữ liệu",
                               total_stats={},
                               exam_stats=[],
                               top_students=[],
                               user_stats=[],
                               current_user=current_user)

    def get_top_exams_with_stats(self):
        try:
            exams = db.session.query(Exam).join(Subject).all()
            exam_stats = []
            for exam in exams:
                results = ExamResult.query.filter_by(exam_id=exam.id).all()
                if results:
                    total_attempts = len(results)
                    avg_score = sum(r.score for r in results) / total_attempts
                    completion_rate = 100
                    if avg_score >= 80:
                        difficulty = 'easy'
                    elif avg_score >= 60:
                        difficulty = 'medium'
                    else:
                        difficulty = 'hard'

                    exam.stats = {
                        'total_attempts': total_attempts,
                        'avg_score': round(avg_score, 1),
                        'completion_rate': completion_rate,
                        'difficulty': difficulty
                    }
                    exam_stats.append(exam)
            return sorted(exam_stats, key=lambda x: x.stats['total_attempts'], reverse=True)[:10]
        except Exception as e:
            return []

    @expose('/export/')
    def export_data(self, **kwargs):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Exam Name', 'Subject', 'Attempts', 'Avg Score', 'Max Score', 'Min Score'])
        exam_stats = db.session.query(
            Exam.exam_name,
            Subject.subject_name,
            db.func.count(ExamResult.id).label('attempts'),
            db.func.avg(ExamResult.score).label('avg_score'),
            db.func.max(ExamResult.score).label('max_score'),
            db.func.min(ExamResult.score).label('min_score')
        ).outerjoin(ExamResult).join(Subject).group_by(Exam.id).all()
        for stat in exam_stats:
            writer.writerow([
                stat.exam_name,
                stat.subject_name,
                stat.attempts,
                f"{stat.avg_score:.2f}" if stat.avg_score else "0",
                stat.max_score or "0",
                stat.min_score or "0"
            ])
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=analytics_reports.csv'}
        )

    @expose('/analytics-data')
    def analytics_data(self, **kwargs):
        range_param = request.args.get('range', '7d')
        days_map = {'7d': 7, '30d': 30, '90d': 90}
        days = days_map.get(range_param, 7)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        activity_data = self.get_activity_data(start_date, end_date)
        score_distribution = self.get_score_distribution()
        subject_stats = self.get_subject_statistics()

        return jsonify({
            'activity': {
                'dates': activity_data['dates'],
                'exam_attempts': activity_data['attempts'],
                'new_users': activity_data['new_users']
            },
            'score_distribution': score_distribution,
            'subjects': {
                'names': subject_stats['names'],
                'attempts': subject_stats['attempts'],
                'avg_scores': subject_stats['avg_scores']
            }
        })

    @expose('/exam-analytics/<int:exam_id>')
    def exam_analytics(self, exam_id, **kwargs):
        exam = Exam.query.get_or_404(exam_id)
        results = ExamResult.query.filter_by(exam_id=exam_id).all()
        if not results:
            return jsonify({'error': 'Không có dữ liệu'})

        total_attempts = len(results)
        avg_score = sum(r.score for r in results) / total_attempts
        avg_time = exam.duration * 0.8
        completion_rate = 95
        score_ranges = {
            'labels': ['0-20', '21-40', '41-60', '61-80', '81-100'],
            'counts': [
                len([r for r in results if 0 <= r.score <= 20]),
                len([r for r in results if 21 <= r.score <= 40]),
                len([r for r in results if 41 <= r.score <= 60]),
                len([r for r in results if 61 <= r.score <= 80]),
                len([r for r in results if 81 <= r.score <= 100])
            ]
        }

        difficult_questions = [
            {
                'question': 'Câu hỏi mẫu về kiến thức nâng cao',
                'correct_rate': 25,
                'difficulty': 'Hard'
            },
            {
                'question': 'Bài tập tính toán phức tạp',
                'correct_rate': 35,
                'difficulty': 'Hard'
            }
        ]
        return jsonify({
            'total_attempts': total_attempts,
            'avg_score': round(avg_score, 1),
            'avg_time': round(avg_time, 1),
            'completion_rate': completion_rate,
            'score_ranges': score_ranges,
            'difficult_questions': difficult_questions
        })

    @expose('/export-analytics')
    def export_analytics(self, **kwargs):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Exam Name', 'Subject', 'Total Attempts', 'Avg Score', 'Status'])
        exams = Exam.query.join(Subject).all()
        for exam in exams:
            results = ExamResult.query.filter_by(exam_id=exam.id).all()
            if results:
                avg_score = sum(r.score for r in results) / len(results)
                status = 'Active' if len(results) > 0 else 'Inactive'
                writer.writerow([
                    exam.exam_name,
                    exam.subject.subject_name,
                    len(results),
                    round(avg_score, 2),
                    status
                ])
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=analytics_report.csv'}
        )

    def get_top_exams_with_stats(self):
        exams = db.session.query(Exam).join(Subject).all()
        exam_stats = []
        for exam in exams:
            results = ExamResult.query.filter_by(exam_id=exam.id).all()
            if results:
                total_attempts = len(results)
                avg_score = sum(r.score for r in results) / total_attempts
                completion_rate = 100
                if avg_score >= 80:
                    difficulty = 'easy'
                elif avg_score >= 50:
                    difficulty = 'medium'
                else:
                    difficulty = 'hard'

                exam.stats = {
                    'total_attempts': total_attempts,
                    'avg_score': round(avg_score, 1),
                    'completion_rate': completion_rate,
                    'difficulty': difficulty
                }
                exam_stats.append(exam)
        return sorted(exam_stats, key=lambda x: x.stats['total_attempts'], reverse=True)[:10]

    def get_activity_data(self, start_date, end_date):
        dates = []
        attempts = []
        new_users = []
        current = start_date.date()
        end = end_date.date()
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            dates.append(date_str)
            day_attempts = ExamResult.query.filter(func.date(ExamResult.taken_exam) == current).count()
            attempts.append(day_attempts)
            day_users = User.query.filter(and_(User.role == Role.STUDENT, func.date(User.createdAt) == current)).count()
            new_users.append(day_users)
            current += timedelta(days=1)
        return {
            'dates': dates,
            'attempts': attempts,
            'new_users': new_users
        }

    def get_score_distribution(self):
        results = ExamResult.query.all()
        if not results:
            return [0, 0, 0, 0]

        weak = len([r for r in results if r.score < 40])
        average = len([r for r in results if 40 <= r.score < 65])
        good = len([r for r in results if 65 <= r.score < 80])
        excellent = len([r for r in results if r.score >= 80])

        return [weak, average, good, excellent]

    def get_subject_statistics(self):
        subjects = Subject.query.all()
        names = []
        attempts = []
        avg_scores = []

        for subject in subjects:
            exam_ids = [e.id for e in Exam.query.filter_by(subject_id=subject.id).all()]
            if exam_ids:
                results = ExamResult.query.filter(ExamResult.exam_id.in_(exam_ids)).all()
                if results:
                    names.append(subject.subject_name)
                    attempts.append(len(results))
                    avg_score = sum(r.score for r in results) / len(results)
                    avg_scores.append(round(avg_score, 1))

        return {
            'names': names,
            'attempts': attempts,
            'avg_scores': avg_scores
        }


admin.index_view = CustomAdminIndexView(name='Trang chủ', url='/admin')

admin.add_view(UserAdmin(User, db.session, name='Người dùng', category='Quản lý'))
admin.add_view(ExamAdmin(Exam, db.session, name='Đề thi', category='Quản lý'))
admin.add_view(QuestionAdmin(Question, db.session, name='Câu hỏi', category='Quản lý'))
admin.add_view(AnswerAdmin(Answer, db.session, name='Đáp án', category='Quản lý'))
admin.add_view(CommentAdmin(Comment, db.session, name='Bình luận', category='Quản lý'))
admin.add_view(SubjectAdmin(Subject, db.session, name='Môn học', category='Danh mục'))
admin.add_view(ChapterAdmin(Chapter, db.session, name='Chương', category='Danh mục'))
admin.add_view(ExamResultAdmin(ExamResult, db.session, name='Kết quả thi', category='Báo cáo'))
admin.add_view(RatingAdmin(Rating, db.session, name='Đánh giá', category='Quản lý'))
admin.add_view(ExamSessionAdmin(ExamSession, db.session, name='Phiên thi', category='Quản lý'))
admin.add_view(SuspiciousActivityAdmin(SuspiciousActivity, db.session, name='Hoạt động nghi ngờ', category='Bảo mật'))
admin.add_view(NotificationAdmin(Notification, db.session, name='Thông báo', category='Quản lý'))
admin.add_view(AnalyticsReportsView(name='Phân tích & Báo cáo', endpoint='analytics_reports', category='Báo cáo'))
admin.add_view(DashboardAdminView(name='Trang chủ', endpoint='dashboard'))

admin.add_link(MenuLink(name='Trang chính', url='/', category='Liên kết'))
admin.add_link(MenuLink(name='Đăng xuất', url='/logout', category='Liên kết'))


@app.route('/admin')
@app.route('/admin/')
def redirect_to_dashboard():
    if not (current_user.is_authenticated and current_user.role == Role.ADMIN):
        logout_user()
        flash('Bạn cần đăng nhập với quyền quản trị để truy cập trang này.', 'error')
        return redirect(url_for('login'))
    return redirect(url_for('dashboard.index'))


@app.template_filter('chr_from_ascii_offset')
def chr_from_ascii_offset(value, offset):
    return chr(value + offset)


@app.context_processor
def inject_admin_vars():
    return dict(current_user=current_user, admin=admin)