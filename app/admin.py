import hashlib
from datetime import datetime
from flask_admin import AdminIndexView, expose, Admin, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_login import current_user, logout_user
from flask import request, redirect, url_for, flash, render_template
from app import app, db, admin, login_manager, dao, utils
from app.models import User, Student, Exam, Question, Answer, Role, ExamResult, Subject, Chapter, ExamQuestions, Comment


class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        logout_user()
        flash('Bạn cần đăng nhập với quyền quản trị để truy cập trang này.', 'error')
        return redirect(url_for('login', next=request.url))

    list_template = 'admin/model/list.html'
    create_template = 'admin/model/create.html'
    edit_template = 'admin/model/edit.html'
    details_template = 'admin/model/details.html'


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
    column_list = ['id', 'name', 'username', 'email', 'role', 'gender', 'createdAt']
    column_searchable_list = ['name', 'username', 'email']
    column_filters = ['role', 'gender', 'createdAt']
    column_sortable_list = ['id', 'name', 'username', 'email', 'createdAt']
    column_labels = {
        'id': 'ID',
        'name': 'Họ tên',
        'username': 'Tên đăng nhập',
        'email': 'Email',
        'role': 'Vai trò',
        'gender': 'Giới tính',
        'createdAt': 'Ngày tạo'
    }

    can_create = True
    can_edit = True
    can_delete = True

    form_excluded_columns = ['password', 'student', 'admin', 'comments', 'exams', 'questions', 'answers']

    def on_model_change(self, form, model, is_created):
        if hasattr(form, 'password') and form.password.data:
            model.password = str(hashlib.md5(form.password.data.encode('utf-8')).hexdigest())


class ExamAdmin(AuthenticatedView):
    column_list = ['id', 'exam_name', 'subject', 'duration', 'createBy', 'createAt', 'user']
    column_searchable_list = ['exam_name', 'createBy']
    column_filters = ['subject', 'createAt', 'duration']
    column_sortable_list = ['id', 'exam_name', 'duration', 'createAt']
    column_labels = {
        'id': 'ID',
        'exam_name': 'Tên đề thi',
        'subject': 'Môn học',
        'duration': 'Thời gian (phút)',
        'createBy': 'Người tạo',
        'createAt': 'Ngày tạo',
        'user': 'Tác giả'
    }

    form_excluded_columns = ['exam_results', 'exam_questions', 'comments', 'createAt']

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            model.user_id = current_user.id
            model.createBy = current_user.name
            model.createAt = datetime.now()
            self.session.add(model)
            self._on_model_change(form, model, True)
            self.session.commit()
            return model
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash('Lỗi khi tạo đề thi: %s' % str(ex), 'error')
            self.session.rollback()
            return False


class QuestionAdmin(AuthenticatedView):
    column_list = ['id', 'question_title', 'chapter', 'createBy', 'createAt']
    column_searchable_list = ['question_title', 'createBy']
    column_filters = ['chapter', 'createAt']
    column_sortable_list = ['id', 'question_title', 'createAt']
    column_labels = {
        'id': 'ID',
        'question_title': 'Câu hỏi',
        'chapter': 'Chương',
        'createBy': 'Người tạo',
        'createAt': 'Ngày tạo'
    }

    form_excluded_columns = ['answers', 'exam_questions', 'createAt']

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            model.user_id = current_user.id
            model.createBy = current_user.name
            model.createAt = datetime.now()
            self.session.add(model)
            self._on_model_change(form, model, True)
            self.session.commit()
            return model
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash('Lỗi khi tạo câu hỏi: %s' % str(ex), 'error')
            self.session.rollback()
            return False


class AnswerAdmin(AuthenticatedView):
    column_list = ['id', 'question', 'answer_text', 'is_correct', 'createBy']
    column_searchable_list = ['answer_text', 'createBy']
    column_filters = ['question', 'is_correct']
    column_sortable_list = ['id', 'answer_text', 'is_correct']
    column_labels = {
        'id': 'ID',
        'question': 'Câu hỏi',
        'answer_text': 'Đáp án',
        'is_correct': 'Đúng/Sai',
        'createBy': 'Người tạo'
    }

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            model.user_id = current_user.id
            model.createBy = current_user.name
            self.session.add(model)
            self._on_model_change(form, model, True)
            self.session.commit()
            return model
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash('Lỗi khi tạo đáp án: %s' % str(ex), 'error')
            self.session.rollback()
            return False


class SubjectAdmin(AuthenticatedView):
    column_list = ['id', 'subject_name', 'description', 'admin']
    column_searchable_list = ['subject_name', 'description']
    column_filters = ['id']
    column_labels = {
        'id': 'ID',
        'subject_name': 'Tên môn học',
        'description': 'Mô tả',
        'admin': 'Quản trị viên'
    }

    form_excluded_columns = ['chapters', 'exams']


class ChapterAdmin(AuthenticatedView):
    column_list = ['id', 'chapter_name', 'subject']
    column_searchable_list = ['chapter_name']
    column_filters = ['subject']
    column_labels = {
        'id': 'ID',
        'chapter_name': 'Tên chương',
        'subject': 'Môn học'
    }

    form_excluded_columns = ['questions']


class ExamResultAdmin(AuthenticatedView):
    column_list = ['id', 'student', 'exam', 'score', 'taken_exam']
    column_searchable_list = ['student.user.name']
    column_filters = ['exam', 'score', 'taken_exam']
    column_sortable_list = ['id', 'score', 'taken_exam']
    column_labels = {
        'id': 'ID',
        'student': 'Học sinh',
        'exam': 'Đề thi',
        'score': 'Điểm',
        'taken_exam': 'Thời gian thi'
    }

    can_create = False
    can_edit = False


class CommentAdmin(AuthenticatedView):
    column_list = ['id', 'user', 'exam', 'content', 'created_at']
    column_searchable_list = ['content', 'user.name']
    column_filters = ['exam', 'created_at']
    column_sortable_list = ['id', 'created_at']
    column_labels = {
        'id': 'ID',
        'user': 'Người dùng',
        'exam': 'Đề thi',
        'content': 'Nội dung',
        'created_at': 'Ngày tạo'
    }


class ReportsView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        exam_stats = db.session.query(
            Exam.exam_name,
            db.func.count(ExamResult.id).label('attempts'),
            db.func.avg(ExamResult.score).label('avg_score'),
            db.func.max(ExamResult.score).label('max_score'),
            db.func.min(ExamResult.score).label('min_score')
        ).outerjoin(ExamResult, Exam.id == ExamResult.exam_id).group_by(Exam.id).all()

        user_stats = db.session.query(
            User.name,
            db.func.count(ExamResult.id).label('attempts'),
            db.func.avg(ExamResult.score).label('avg_score')
        ).join(Student, User.id == Student.user_id).join(ExamResult, Student.id == ExamResult.student_id).group_by(User.id).all()

        return self.render('admin/reports.html', exam_stats=exam_stats, user_stats=user_stats)


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
            'total_attempts': ExamResult.query.count(),
            'total_questions': Question.query.count(),
            'total_subjects': Subject.query.count(),
            'total_comments': Comment.query.count()
        }

        recent_exams = Exam.query.order_by(Exam.createAt.desc()).limit(5).all()

        recent_activities = [
            {
                'type': 'primary',
                'icon': 'plus',
                'time_ago': '5 phút trước',
                'description': 'Thêm đề thi mới'
            },
            {
                'type': 'success',
                'icon': 'person-plus',
                'time_ago': '1 giờ trước',
                'description': 'Người dùng mới đăng ký'
            },
            {
                'type': 'warning',
                'icon': 'pencil',
                'time_ago': '2 giờ trước',
                'description': 'Cập nhật câu hỏi'
            }
        ]

        return self.render('admin/dashboard.html', stats=stats, recent_exams=recent_exams, recent_activities=recent_activities)


admin.index_view = CustomAdminIndexView(name='Trang chủ', template='admin/dashboard.html', url='/admin')


admin.add_view(UserAdmin(User, db.session, name='Người dùng', category='Quản lý'))
admin.add_view(ExamAdmin(Exam, db.session, name='Đề thi', category='Quản lý'))
admin.add_view(QuestionAdmin(Question, db.session, name='Câu hỏi', category='Quản lý'))
admin.add_view(AnswerAdmin(Answer, db.session, name='Đáp án', category='Quản lý'))
admin.add_view(SubjectAdmin(Subject, db.session, name='Môn học', category='Danh mục'))
admin.add_view(ChapterAdmin(Chapter, db.session, name='Chương', category='Danh mục'))
admin.add_view(ExamResultAdmin(ExamResult, db.session, name='Kết quả thi', category='Báo cáo'))
admin.add_view(CommentAdmin(Comment, db.session, name='Bình luận', category='Quản lý'))
admin.add_view(DashboardAdminView(name='Trang chủ', endpoint='dashboard', url='/admin/dashboard'))


admin.add_view(ReportsView(name='Thống kê', endpoint='reports', category='Báo cáo'))


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
    return dict(
        current_user=current_user,
        admin=admin
    )