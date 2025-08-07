import hashlib
from datetime import datetime, timedelta
from flask_admin import AdminIndexView, expose, Admin, BaseView
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.helpers import get_redirect_target
from flask_admin.menu import MenuLink
from flask_admin.model.helpers import get_mdict_item_or_list
from flask_login import current_user, logout_user
from flask import request, redirect, url_for, flash, render_template
from flask_admin import form
from app import app, db, admin, login_manager, dao, utils
from app.models import User, Student, Exam, Question, Answer, Role, ExamResult, Subject, Chapter, ExamQuestions, Comment, Admin
import csv
from io import StringIO
from flask import Response
from wtforms import fields


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

    form_excluded_columns = ['student', 'admin', 'comments', 'exams', 'questions', 'answers', 'createdAt', 'updateAt']

    form_extra_fields = {
        'new_password': fields.PasswordField('Mật khẩu mới')
    }

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)

            if form.password.data:
                model.password = str(hashlib.md5(form.password.data.encode('utf-8')).hexdigest())

            self.session.add(model)
            self.session.flush()

            if model.role == Role.STUDENT:
                student = Student(user_id=model.id)
                self.session.add(student)
            elif model.role == Role.ADMIN:
                admin_record = Admin(user_id=model.id)
                self.session.add(admin_record)

            self.session.commit()
            return model
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi tạo người dùng: {str(ex)}', 'error')
            return False

    def update_model(self, form, model):
        try:
            form.populate_obj(model)

            if hasattr(form, 'new_password') and form.new_password.data:
                model.password = str(hashlib.md5(form.new_password.data.encode('utf-8')).hexdigest())

            if model.role == Role.STUDENT and not model.student:
                student = Student(user_id=model.id)
                self.session.add(student)
            elif model.role == Role.ADMIN and not model.admin:
                admin_record = Admin(user_id=model.id)
                self.session.add(admin_record)

            self.session.commit()
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi cập nhật người dùng: {str(ex)}', 'error')
            return False

    def delete_model(self, model):
        try:
            if model.student:
                ExamResult.query.filter_by(student_id=model.student.id).delete()
                self.session.delete(model.student)

            if model.admin:
                self.session.delete(model.admin)

            self.session.delete(model)
            self.session.commit()
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi xóa người dùng: {str(ex)}', 'error')
            return False


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

    form_excluded_columns = ['exam_results', 'exam_questions', 'comments', 'createAt', 'createBy', 'user']

    def create_model(self, form):
        try:
            if form.duration.data <= 0:
                flash('Thời gian thi phải lớn hơn 0', 'error')
                return False

            model = self.model()
            form.populate_obj(model)
            model.user_id = current_user.id
            model.createBy = current_user.name
            model.createAt = datetime.now()

            self.session.add(model)
            self.session.commit()
            flash(f'Đã tạo thành công đề thi "{model.exam_name}"', 'success')
            return model
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi tạo đề thi: {str(ex)}', 'error')
            return False

    def update_model(self, form, model):
        try:
            if form.duration.data <= 0:
                flash('Thời gian thi phải lớn hơn 0', 'error')
                return False

            form.populate_obj(model)
            self.session.commit()
            flash(f'Đã cập nhật thành công đề thi "{model.exam_name}"', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi cập nhật đề thi: {str(ex)}', 'error')
            return False

    def delete_model(self, model):
        try:
            if model.exam_results:
                flash('Không thể xóa đề thi đã có người thi', 'error')
                return False

            ExamQuestions.query.filter_by(exam_id=model.id).delete()
            Comment.query.filter_by(exam_id=model.id).delete()

            self.session.delete(model)
            self.session.commit()
            flash(f'Đã xóa thành công đề thi "{model.exam_name}"', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi xóa đề thi: {str(ex)}', 'error')
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

    form_excluded_columns = ['answers', 'exam_questions', 'createAt', 'createBy', 'user']

    def create_model(self, form):
        try:
            existing = Question.query.filter_by(question_title=form.question_title.data).first()
            if existing:
                flash('Câu hỏi này đã tồn tại', 'error')
                return False

            model = self.model()
            form.populate_obj(model)
            model.user_id = current_user.id
            model.createBy = current_user.name
            model.createAt = datetime.now()

            self.session.add(model)
            self.session.commit()
            flash(f'Đã tạo thành công câu hỏi', 'success')
            return model
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi tạo câu hỏi: {str(ex)}', 'error')
            return False

    def delete_model(self, model):
        try:
            Answer.query.filter_by(question_id=model.id).delete()
            ExamQuestions.query.filter_by(question_id=model.id).delete()

            self.session.delete(model)
            self.session.commit()
            flash('Đã xóa thành công câu hỏi', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi xóa câu hỏi: {str(ex)}', 'error')
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
        'createBy': 'Người tạo',
        'explanation': 'Giải thích'
    }

    form_excluded_columns = ['createBy', 'user']

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            model.user_id = current_user.id
            model.createBy = current_user.name

            self.session.add(model)
            self.session.commit()
            flash('Đã tạo thành công đáp án', 'success')
            return model
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi tạo đáp án: {str(ex)}', 'error')
            return False

    def update_model(self, form, model):
        try:
            form.populate_obj(model)
            self.session.commit()
            flash('Đã cập nhật thành công đáp án', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi cập nhật đáp án: {str(ex)}', 'error')
            return False


class SubjectAdmin(AuthenticatedView):
    column_list = ['id', 'subject_name', 'description', 'admin']
    column_searchable_list = ['subject_name', 'description']
    column_filters = ['subject_name']
    column_labels = {
        'id': 'ID',
        'subject_name': 'Tên môn học',
        'description': 'Mô tả',
        'admin': 'Quản trị viên'
    }

    form_excluded_columns = ['chapters', 'exams', 'admin']

    def get_query(self):
        return self.session.query(self.model).join(Admin)

    def create_model(self, form):
        try:
            existing = Subject.query.filter_by(subject_name=form.subject_name.data).first()
            if existing:
                flash('Môn học này đã tồn tại', 'error')
                return False

            admin_record = Admin.query.filter_by(user_id=current_user.id).first()
            if not admin_record:
                flash('Bạn cần có quyền admin để tạo môn học', 'error')
                return False

            model = self.model()
            form.populate_obj(model)
            model.admin_id = admin_record.id

            self.session.add(model)
            self.session.commit()
            flash(f'Đã tạo thành công môn học "{model.subject_name}"', 'success')
            return model
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi tạo môn học: {str(ex)}', 'error')
            return False

    def update_model(self, form, model):
        try:
            existing = Subject.query.filter(Subject.subject_name == form.subject_name.data, Subject.id != model.id).first()
            if existing:
                flash('Tên môn học này đã tồn tại', 'error')
                return False

            form.populate_obj(model)
            self.session.commit()
            flash(f'Đã cập nhật thành công môn học "{model.subject_name}"', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi cập nhật môn học: {str(ex)}', 'error')
            return False

    def delete_model(self, model):
        try:
            if model.chapters:
                flash('Không thể xóa môn học đã có chương', 'error')
                return False

            if model.exams:
                flash('Không thể xóa môn học đã có đề thi', 'error')
                return False

            self.session.delete(model)
            self.session.commit()
            flash(f'Đã xóa thành công môn học "{model.subject_name}"', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi xóa môn học: {str(ex)}', 'error')
            return False


class ChapterAdmin(AuthenticatedView):
    column_list = ['id', 'chapter_name', 'subject']
    column_searchable_list = ['chapter_name']
    column_filters = ['subject']
    column_sortable_list = ['id', 'chapter_name']
    column_labels = {
        'id': 'ID',
        'chapter_name': 'Tên chương',
        'subject': 'Môn học'
    }

    form_excluded_columns = ['questions']

    def create_model(self, form):
        try:
            existing = Chapter.query.filter_by(chapter_name=form.chapter_name.data, subject_id=form.subject.data.id if hasattr(form.subject.data, 'id') else form.subject_id.data).first()

            if existing:
                flash('Tên chương này đã tồn tại trong môn học', 'error')
                return False

            model = self.model()
            form.populate_obj(model)

            self.session.add(model)
            self.session.commit()
            flash(f'Đã tạo thành công chương "{model.chapter_name}"', 'success')
            return model
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi tạo chương: {str(ex)}', 'error')
            return False

    def update_model(self, form, model):
        try:
            existing = Chapter.query.filter(Chapter.chapter_name == form.chapter_name.data, Chapter.subject_id == (form.subject.data.id if hasattr(form.subject.data, 'id') else form.subject_id.data), Chapter.id != model.id).first()

            if existing:
                flash('Tên chương này đã tồn tại trong môn học', 'error')
                return False

            form.populate_obj(model)
            self.session.commit()
            flash(f'Đã cập nhật thành công chương "{model.chapter_name}"', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi cập nhật chương: {str(ex)}', 'error')
            return False

    def delete_model(self, model):
        try:
            if model.questions:
                flash('Không thể xóa chương đã có câu hỏi', 'error')
                return False

            self.session.delete(model)
            self.session.commit()
            flash(f'Đã xóa thành công chương "{model.chapter_name}"', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi xóa chương: {str(ex)}', 'error')
            return False


class ExamResultAdmin(AuthenticatedView):
    column_list = ['id', 'student', 'exam', 'score', 'taken_exam']
    column_searchable_list = ['student.user.name', 'exam.exam_name']
    column_filters = ['exam', 'score', 'taken_exam']
    column_sortable_list = ['id', 'score', 'taken_exam']
    column_labels = {
        'id': 'ID',
        'student': 'Học sinh',
        'exam': 'Đề thi',
        'score': 'Điểm',
        'taken_exam': 'Thời gian thi',
        'user_answers': 'Câu trả lời'
    }

    can_create = False
    can_edit = True
    can_delete = True

    column_formatters = {
        'score': lambda v, c, m, p: f"{m.score}/100",
        'student': lambda v, c, m, p: m.student.user.name if m.student and m.student.user else 'N/A'
    }

    form_columns = ['score']

    def update_model(self, form, model):
        try:
            if form.score.data < 0 or form.score.data > 10:
                flash('Điểm phải trong khoảng 0-10', 'error')
                return False

            old_score = model.score
            form.populate_obj(model)
            self.session.commit()
            flash(f'Đã cập nhật điểm từ {old_score} thành {model.score}', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi cập nhật kết quả: {str(ex)}', 'error')
            return False

    def delete_model(self, model):
        try:
            student_name = model.student.user.name if model.student and model.student.user else 'N/A'
            exam_name = model.exam.exam_name if model.exam else 'N/A'

            self.session.delete(model)
            self.session.commit()
            flash(f'Đã xóa kết quả thi của {student_name} - đề {exam_name}', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi xóa kết quả thi: {str(ex)}', 'error')
            return False

    # Custom view để xem chi tiết câu trả lời
    @expose('/details/')
    def details_view(self):
        return_url = get_redirect_target() or self.get_url('.index_view')
        id = get_mdict_item_or_list(request.args, 'id')

        if id is None:
            return redirect(return_url)

        model = self.get_one(id)
        if model is None:
            flash('Không tìm thấy kết quả thi', 'error')
            return redirect(return_url)

        return self.render('admin/exam_result_details.html', model=model, return_url=return_url)


class CommentAdmin(AuthenticatedView):
    column_list = ['id', 'user', 'exam', 'content', 'created_at']
    column_searchable_list = ['content', 'user.name']
    column_filters = ['exam', 'created_at', 'user']
    column_sortable_list = ['id', 'created_at']
    column_labels = {
        'id': 'ID',
        'user': 'Người dùng',
        'exam': 'Đề thi',
        'content': 'Nội dung',
        'created_at': 'Ngày tạo',
        'updated_at': 'Ngày cập nhật'
    }

    column_formatters = {
        'content': lambda v, c, m, p: (m.content[:50] + '...') if len(m.content) > 50 else m.content,
        'user': lambda v, c, m, p: m.user.name if m.user else 'N/A'
    }

    form_excluded_columns = ['created_at', 'updated_at']

    can_create = True
    can_edit = True
    can_delete = True

    def create_model(self, form):
        try:
            if not form.content.data.strip():
                flash('Nội dung bình luận không được để trống', 'error')
                return False

            model = self.model()
            form.populate_obj(model)
            model.created_at = datetime.now()
            model.updated_at = datetime.now()

            self.session.add(model)
            self.session.commit()
            flash('Đã tạo thành công bình luận', 'success')
            return model
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi tạo bình luận: {str(ex)}', 'error')
            return False

    def update_model(self, form, model):
        try:
            if not form.content.data.strip():
                flash('Nội dung bình luận không được để trống', 'error')
                return False

            form.populate_obj(model)
            model.updated_at = datetime.now()
            self.session.commit()
            flash('Đã cập nhật thành công bình luận', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi cập nhật bình luận: {str(ex)}', 'error')
            return False

    def delete_model(self, model):
        try:
            user_name = model.user.name if model.user else 'N/A'
            self.session.delete(model)
            self.session.commit()
            flash(f'Đã xóa bình luận của {user_name}', 'success')
            return True
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi xóa bình luận: {str(ex)}', 'error')
            return False

    # Custom action để duyệt/ẩn bình luận hàng loạt
    @action('approve', 'Duyệt', 'Bạn có chắc muốn duyệt các bình luận đã chọn?')
    def action_approve(self, ids):
        try:
            query = Comment.query.filter(Comment.id.in_(ids))
            count = query.count()
            # Có thể thêm trường is_approved vào model Comment
            # query.update({Comment.is_approved: True})
            self.session.commit()
            flash(f'Đã duyệt {count} bình luận', 'success')
        except Exception as ex:
            self.session.rollback()
            flash(f'Lỗi khi duyệt bình luận: {str(ex)}', 'error')


class ReportsView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        total_stats = {
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
            Exam.id,
            Subject.subject_name,
            db.func.count(ExamResult.id).label('attempts'),
            db.func.avg(ExamResult.score).label('avg_score'),
            db.func.max(ExamResult.score).label('max_score'),
            db.func.min(ExamResult.score).label('min_score')
        ).outerjoin(ExamResult, Exam.id == ExamResult.exam_id).join(Subject, Exam.subject_id == Subject.id).group_by(Exam.id, Exam.exam_name, Subject.subject_name).order_by(db.func.count(ExamResult.id).desc()).all()

        user_stats = db.session.query(
            User.name,
            User.id,
            db.func.count(ExamResult.id).label('attempts'),
            db.func.avg(ExamResult.score).label('avg_score'),
            db.func.max(ExamResult.score).label('max_score')
        ).join(Student, User.id == Student.user_id).join(ExamResult, Student.id == ExamResult.student_id).group_by(User.id).all()

        top_students = db.session.query(
            User.name,
            db.func.avg(ExamResult.score).label('avg_score'),
            db.func.count(ExamResult.id).label('total_exams')
        ).join(Student, User.id == Student.user_id).join(ExamResult, Student.id == ExamResult.student_id).group_by(User.id).order_by(db.func.avg(ExamResult.score).desc()).limit(10).all()

        subject_stats = db.session.query(
            Subject.subject_name,
            db.func.count(Exam.id).label('total_exams'),
            db.func.count(Question.id).label('total_questions'),
            db.func.count(Chapter.id).label('total_chapters')
        ).outerjoin(Exam, Subject.id == Exam.subject_id).outerjoin(Chapter, Subject.id == Chapter.subject_id).outerjoin(Question, Chapter.id == Question.chapter_id).group_by(Subject.id).all()

        monthly_scores = db.session.query(
            db.func.date_format(ExamResult.taken_exam, '%Y-%m').label('month'),
            db.func.avg(ExamResult.score).label('avg_score'),
            db.func.count(ExamResult.id).label('attempts')
        ).group_by(db.func.date_format(ExamResult.taken_exam, '%Y-%m')).order_by(db.func.date_format(ExamResult.taken_exam, '%Y-%m')).all()

        return self.render('admin/reports.html', total_stats=total_stats, exam_stats=exam_stats, user_stats=user_stats, top_students=top_students, subject_stats=subject_stats, monthly_scores=monthly_scores)

    @expose('/export/')
    def export_data(self):
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(['Tên đề thi', 'Môn học', 'Số lượt thi', 'Điểm TB', 'Điểm cao nhất', 'Điểm thấp nhất'])

        exam_stats = db.session.query(
            Exam.exam_name,
            Subject.subject_name,
            db.func.count(ExamResult.id).label('attempts'),
            db.func.avg(ExamResult.score).label('avg_score'),
            db.func.max(ExamResult.score).label('max_score'),
            db.func.min(ExamResult.score).label('min_score')
        ).outerjoin(ExamResult, Exam.id == ExamResult.exam_id).join(Subject, Exam.subject_id == Subject.id).group_by(Exam.id).all()

        for stat in exam_stats:
            writer.writerow([stat.exam_name, stat.subject_name, stat.attempts, f"{stat.avg_score:.2f}" if stat.avg_score else "0", stat.max_score or "0", stat.min_score or "0"])

        output.seek(0)
        return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=exam_reports.csv'})


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

        recent_exams = db.session.query(Exam).order_by(Exam.createAt.desc()).limit(5).all()

        recent_activities = []

        latest_exams = Exam.query.order_by(Exam.createAt.desc()).limit(3).all()
        for exam in latest_exams:
            time_diff = datetime.now() - exam.createAt
            if time_diff.days == 0:
                time_ago = f"{time_diff.seconds // 3600} giờ trước" if time_diff.seconds > 3600 else f"{time_diff.seconds // 60} phút trước"
            else:
                time_ago = f"{time_diff.days} ngày trước"

            recent_activities.append({
                'type': 'primary',
                'icon': 'file-plus',
                'time_ago': time_ago,
                'description': f'Tạo đề thi "{exam.exam_name}"'
            })

        latest_users = User.query.order_by(User.createdAt.desc()).limit(5).all()
        for user in latest_users:
            time_diff = datetime.now() - user.createdAt
            if time_diff.days == 0:
                time_ago = f"{time_diff.seconds // 3600} giờ trước" if time_diff.seconds > 3600 else f"{time_diff.seconds // 60} phút trước"
            else:
                time_ago = f"{time_diff.days} ngày trước"

            recent_activities.append({
                'type': 'success',
                'icon': 'person-plus',
                'time_ago': time_ago,
                'description': f'Người dùng mới: {user.name}'
            })

        recent_activities = sorted(recent_activities, key=lambda x: x['time_ago'], reverse=False)[:5]

        return self.render('admin/dashboard.html', stats=stats, recent_exams=recent_exams, recent_activities=recent_activities, datetime=datetime)


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