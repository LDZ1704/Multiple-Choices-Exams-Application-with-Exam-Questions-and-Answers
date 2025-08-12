import hashlib
from datetime import datetime, timedelta
from flask_admin import AdminIndexView, expose, Admin, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_login import current_user, logout_user
from flask import request, redirect, url_for, flash, render_template, Response
from wtforms import fields, validators
import csv
from io import StringIO
from app import app, db, admin
from app.models import User, Student, Exam, Question, Answer, Role, ExamResult, Subject, Chapter, ExamQuestions, Comment, Admin


class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        logout_user()
        flash('Bạn cần đăng nhập với quyền quản trị để truy cập trang này.', 'error')
        return redirect(url_for('login', next=request.url))

    can_view_details = True
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

    def on_model_change(self, form, model, is_created):
        if is_created:
            if hasattr(model, 'password') and model.password:
                model.password = str(hashlib.md5(model.password.encode('utf-8')).hexdigest())
            model.createdAt = datetime.now()

            if model.role == Role.STUDENT:
                student = Student(user=model)
                db.session.add(student)
            elif model.role == Role.ADMIN:
                admin_record = Admin(user=model)
                db.session.add(admin_record)
        else:
            model.updateAt = datetime.now()


class ExamAdmin(AuthenticatedView):
    column_list = ['id', 'exam_name', 'subject.subject_name', 'duration', 'start_time', 'end_time' , 'createBy', 'createAt']
    column_searchable_list = ['exam_name', 'createBy']
    column_filters = ['subject', 'duration']
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

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.user_id = current_user.id
            model.createBy = current_user.name
            model.createAt = datetime.now()

    def on_model_delete(self, model):
        if ExamResult.query.filter_by(exam_id=model.id).first():
            raise Exception('Không thể xóa đề thi đã có người thi')


class QuestionAdmin(AuthenticatedView):
    column_list = ['id', 'question_title', 'chapter.chapter_name', 'createBy', 'createAt']
    column_searchable_list = ['question_title', 'createBy']
    column_filters = ['chapter']
    column_labels = {
        'id': 'ID',
        'question_title': 'Câu hỏi',
        'chapter.chapter_name': 'Chương',
        'createBy': 'Người tạo',
        'createAt': 'Ngày tạo'
    }

    form_excluded_columns = ['answers', 'exam_questions', 'createAt', 'createBy', 'user']

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.user_id = current_user.id
            model.createBy = current_user.name
            model.createAt = datetime.now()


class AnswerAdmin(AuthenticatedView):
    column_list = ['id', 'question.question_title', 'answer_text', 'is_correct', 'explanation', 'createBy']
    column_searchable_list = ['answer_text', 'createBy']
    column_filters = ['question', 'is_correct']
    column_labels = {
        'id': 'ID',
        'question.question_title': 'Câu hỏi',
        'answer_text': 'Đáp án',
        'is_correct': 'Đúng/Sai',
        'explanation': 'Giải thích',
        'createBy': 'Người tạo'
    }

    form_excluded_columns = ['createBy', 'user']

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

    form_excluded_columns = ['chapters', 'exams', 'admin']

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


class ExamResultAdmin(AuthenticatedView):
    column_list = ['id', 'student.user.name', 'exam.exam_name', 'score', 'taken_exam', 'user_answers']
    column_searchable_list = ['student.user.name', 'exam.exam_name']
    column_filters = ['exam.exam_name', 'score']
    column_labels = {
        'id': 'ID',
        'student.user.name': 'Học sinh',
        'exam.exam_name': 'Đề thi',
        'score': 'Điểm',
        'taken_exam': 'Thời gian thi',
        'user_answers': 'Câu trả lời của người dùng'
    }

    can_create = False
    can_edit = True
    form_columns = ['score']

    def on_form_prefill(self, form, id):
        if hasattr(form, 'score'):
            form.score.validators = [validators.NumberRange(min=0, max=100)]


class CommentAdmin(AuthenticatedView):
    column_list = ['id', 'user.name', 'exam.exam_name', 'content', 'created_at', 'updated_at']
    column_searchable_list = ['content']
    column_filters = ['exam', 'user']
    column_labels = {
        'id': 'ID',
        'user.name': 'Người dùng',
        'exam.exam_name': 'Đề thi',
        'content': 'Nội dung',
        'created_at': 'Ngày tạo',
        'update_at': 'Ngày cập nhật'
    }

    form_excluded_columns = ['created_at', 'updated_at']

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_at = datetime.now()
        model.updated_at = datetime.now()


class ReportsView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        stats = {
            'total_users': User.query.count(),
            'total_students': Student.query.count(),
            'total_exams': Exam.query.count(),
            'total_attempts': ExamResult.query.count(),
            'total_questions': Question.query.count(),
            'total_subjects': Subject.query.count(),
            'total_comments': Comment.query.count()
        }

        exam_stats = db.session.query(
            Exam.exam_name,
            Subject.subject_name,
            db.func.count(ExamResult.id).label('attempts'),
            db.func.avg(ExamResult.score).label('avg_score'),
            db.func.max(ExamResult.score).label('max_score'),
            db.func.min(ExamResult.score).label('min_score')
        ).join(Subject).outerjoin(ExamResult).group_by(Exam.id, Exam.exam_name, Subject.subject_name).order_by(db.func.count(ExamResult.id).desc()).limit(20).all()

        top_students = db.session.query(
            User.name,
            db.func.coalesce(db.func.avg(ExamResult.score), 0).label('avg_score'),
            db.func.count(ExamResult.id).label('total_exams')
        ).select_from(User).join(Student, User.id == Student.user_id) \
            .outerjoin(ExamResult, Student.id == ExamResult.student_id) \
            .group_by(User.id, User.name) \
            .order_by(db.func.coalesce(db.func.avg(ExamResult.score), 0).desc()).limit(10).all()

        user_stats = db.session.query(
            User.name,
            db.func.coalesce(db.func.avg(ExamResult.score), 0).label('avg_score')
        ).select_from(User).join(Student, User.id == Student.user_id) \
            .outerjoin(ExamResult, Student.id == ExamResult.student_id) \
            .group_by(User.id, User.name).all()

        return self.render('admin/reports.html', total_stats=stats, exam_stats=exam_stats, top_students=top_students, user_stats=user_stats)

    @expose('/export/')
    def export_data(self):
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
            headers={'Content-Disposition': 'attachment; filename=exam_reports.csv'}
        )


class LogoutView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        logout_user()
        flash('Đã đăng xuất thành công.', 'success')
        return redirect('/admin')


class DashboardAdminView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
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

        return self.render('admin/dashboard.html', stats=stats, recent_exams=recent_exams, datetime=datetime)


admin.index_view = CustomAdminIndexView(name='Trang chủ', url='/admin')

admin.add_view(UserAdmin(User, db.session, name='Người dùng', category='Quản lý'))
admin.add_view(ExamAdmin(Exam, db.session, name='Đề thi', category='Quản lý'))
admin.add_view(QuestionAdmin(Question, db.session, name='Câu hỏi', category='Quản lý'))
admin.add_view(AnswerAdmin(Answer, db.session, name='Đáp án', category='Quản lý'))
admin.add_view(CommentAdmin(Comment, db.session, name='Bình luận', category='Quản lý'))
admin.add_view(SubjectAdmin(Subject, db.session, name='Môn học', category='Danh mục'))
admin.add_view(ChapterAdmin(Chapter, db.session, name='Chương', category='Danh mục'))
admin.add_view(ExamResultAdmin(ExamResult, db.session, name='Kết quả thi', category='Báo cáo'))
admin.add_view(ReportsView(name='Thống kê', endpoint='reports', category='Báo cáo'))
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