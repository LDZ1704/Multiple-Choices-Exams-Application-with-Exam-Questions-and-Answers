import re
import os
from sqlalchemy import func
from flask import session, jsonify
from flask_login import login_user, login_required
from app import login_manager, utils
from app.models import ExamSession, Notification
from app.models import Admin as AdminModels
import app.dao as dao
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.admin import *
import qrcode
from io import BytesIO
import base64
from app.notification_scheduler import init_notification_scheduler
from app.recommendation_engine import recommendation_engine
from app.smart_chatbot import smart_chatbot
from celery_tasks import generate_daily_recommendations
from celery_tasks import generate_personalized_study_plan
from celery.result import AsyncResult
from notification_service import NotificationService
import io
import csv
from flask import make_response
from websocket_client import ws_client


@app.context_processor
def inject_user():
    return dict(current_user=current_user, admin=admin, dao=dao)


@app.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        unread_count = NotificationService.get_unread_count(current_user.id)
        return dict(unread_notifications_count=unread_count)
    return dict(unread_notifications_count=0)


@app.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    unread_only = request.args.get('unread', False, type=bool)

    notifications_pagination = NotificationService.get_user_notifications(current_user.id, page=page, per_page=10, unread_only=unread_only)

    return render_template('notifications.html',
                           notifications=notifications_pagination.items,
                           pagination=notifications_pagination,
                           unread_only=unread_only)


@app.route('/api/notifications/unread-count')
@login_required
def get_unread_notifications_count():
    count = NotificationService.get_unread_count(current_user.id)
    return jsonify({'count': count})


@app.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    success = NotificationService.mark_as_read(notification_id, current_user.id)
    return jsonify({'success': success})


@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    NotificationService.mark_all_as_read(current_user.id)
    return jsonify({'success': True})


@app.route('/api/notifications/recent')
@login_required
def get_recent_notifications():
    notifications = NotificationService.get_user_notifications(current_user.id, per_page=5).items

    data = []
    for n in notifications:
        data.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%d/%m/%Y %H:%M'),
            'exam_id': n.exam_id
        })

    return jsonify({'notifications': data})


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)

    message = request.args.get('message')
    message_type = request.args.get('type', 'info')

    if message:
        if message == 'saved':
            flash('Đã lưu bài thi thành công!', 'success')
        elif message == 'completed':
            flash('Đã hoàn thành bài thi!', 'success')
        elif message == 'timeout':
            flash('Hết thời gian làm bài!', 'warning')
        return redirect(url_for('index', page=page, search=search_query))

    exams_pagination = dao.get_exams_with_pagination(
        page=page,
        per_page=app.config['PAGE_SIZE'],
        search_query=search_query.strip() if search_query else None
    )

    exams_with_stats = []
    for exam in exams_pagination.items:
        stats = utils.get_exam_stats(exam.id)
        question_count = utils.count_exam_questions(exam.id)

        exams_with_stats.append({
            'exam': exam,
            'stats': stats,
            'question_count': question_count
        })

    return render_template('index.html', exams=exams_with_stats, pagination=exams_pagination, search_query=search_query)


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        next_page = request.args.get('next')
        user_id = current_user.id if current_user.is_authenticated else None

        user = dao.auth_user(username, password)

        if user:
            login_user(user)
            flash('Chào mừng ' + user.name + ' tới LmaoQuiz', 'success')

            if user.role == Role.ADMIN:
                if not dao.existence_check(AdminModels, 'user_id', user.id):
                    dao.add_admin(user)
                return redirect('/admin')
            elif user.role == Role.STUDENT:
                if not dao.existence_check(Student, 'user_id', user.id):
                    dao.add_student(user)
                if next_page == '/login':
                    return redirect('/')
                return redirect(next_page) if next_page else redirect('/')
        else:
            flash('Thông tin tài khoản và mật khẩu không chính xác!', 'danger')

    return render_template('login.html', username=username)


@login_manager.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/logout')
@login_required
def logout():
    user_id = current_user.id if current_user.is_authenticated else None
    logout_user()

    if user_id:
        if ws_client.connected:
            ws_client.send_event({
                'type': 'user_logout',
                'user_id': user_id
            })
    flash('Đã đăng xuất thành công.', 'success')
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    regex_username = '^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9]+$'
    regex_password = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$'
    username = email = name = gender = ''
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email']
        name = request.form['name'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        gender = request.form.get('gender')

        has_error = False

        if dao.existence_check(User, 'username', username):
            flash('Tên tài khoản này đã tồn tại!', 'danger')
            has_error = True
        if ' ' in username:
            flash('Tên tài khoản không được chứa dấu cách!', 'danger')
            has_error = True
        elif not re.fullmatch(regex_username, username):
            flash('Tên tài khoản phải có cả chữ và số!', 'danger')
            has_error = True
        if len(username) < 6:
            flash('Tên tài khoản phải có ít nhất 6 ký tự!', 'danger')
            has_error = True
        if name:
            if len(name) < 2 or len(name) > 50:
                flash('Tên phải có 2-50 ký tự!', 'danger')
                has_error = True
            elif any(char.isdigit() or char in '!@#$%^&*()_+=[]{}|;:"<>,.?/~`' for char in name):
                flash('Tên không được chứa số hoặc ký tự đặc biệt!', 'danger')
                has_error = True
            elif name.isspace():
                flash('Tên không được chỉ chứa khoảng trắng!', 'danger')
                has_error = True
        if not re.fullmatch(regex_password, password):
            flash('Mật khẩu phải có ít nhất 6 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt!', 'danger')
            has_error = True
        if not password.__eq__(confirm_password):
            flash('Bạn phải xác nhận lại mật khẩu giống mật khẩu của bạn.', 'danger')
            has_error = True
        if '@' not in email:
            flash('Email phải theo đúng định dạng (abc@example.com)!', 'danger')
            has_error = True
        elif dao.existence_check(User, 'email', email):
            flash('Email đã tồn tại trong hệ thống!', 'danger')
            has_error = True

        if has_error:
            return render_template('register.html', username=username, email=email, name=name, gender=gender)
        else:
            data = request.form.copy()
            del data['confirm-password']
            dao.add_user(**data)
            flash('Chào mừng ' + name + ' tới LmaoQuiz', 'success')
            return redirect('/login')

    return render_template('register.html', username=username, email=email, name=name, gender=gender)


@app.route('/examdetail')
def exam_detail():
    exam_id = request.args.get('id', type=int)
    comment_page = request.args.get('comment_page', 1, type=int)
    ranking_page = request.args.get('ranking_page', 1, type=int)
    session_obj = None

    if not exam_id:
        flash('Không tìm thấy đề thi!', 'error')
        return redirect(url_for('index'))

    exam = dao.get_exam_by_id(exam_id)
    if not exam:
        flash('Đề thi này đã bị xóa hoặc không tồn tại!', 'error')
        return redirect(url_for('index'))

    if current_user.is_authenticated:
        student = dao.get_student_by_user_id(current_user.id)
        if student:
            session_obj = dao.get_exam_session(student.id, exam_id)

    stats = utils.get_exam_stats(exam_id)
    question_count = utils.count_exam_questions(exam_id)

    comments_pagination = utils.get_exam_comments_with_pagination(exam_id, page=comment_page, per_page=app.config['COMMENT_SIZE'])

    ranking_pagination = dao.get_exam_ranking_with_pagination(
        exam_id=exam_id,
        page=ranking_page,
        per_page=20
    )

    ranking_stats = None
    if dao.count_exam_participants(exam_id) > 0:
        ranking_stats = {
            'total_participants': dao.count_exam_participants(exam_id),
            'avg_score': dao.get_exam_average_score(exam_id),
            'highest_score': dao.get_exam_highest_score(exam_id)
        }

    user_results = None
    highest_score = 0
    has_result = False
    user_rating = None

    if current_user.is_authenticated:
        user_results = utils.get_user_exam_results(current_user.id, exam_id)
        highest_score = utils.get_highest_score(current_user.id, exam_id)
        student = dao.get_student_by_user_id(current_user.id)
        if student:
            has_result = dao.has_exam_result(student.id, exam_id)
            user_rating = dao.get_user_rating(current_user.id, exam_id)

    rating_stats = dao.get_exam_rating_stats(exam_id)

    return render_template('examdetail.html',
                           exam=exam,
                           stats=stats,
                           question_count=question_count,
                           comments_pagination=comments_pagination,
                           user_results=user_results,
                           session=session_obj,
                           highest_score=highest_score,
                           has_result=has_result,
                           ranking_pagination=ranking_pagination,
                           ranking_stats=ranking_stats,
                           rating_stats=rating_stats,
                           user_rating=user_rating)


@app.route('/api/exam/<int:exam_id>/qr-code')
def generate_exam_qr(exam_id):
    exam = dao.get_exam_by_id(exam_id)
    if not exam:
        return jsonify({'error': 'Đề thi không tồn tại'}), 404

    exam_url = request.url_root + f'examdetail?id={exam_id}'

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4,)
    qr.add_data(exam_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return jsonify({
        'success': True,
        'qr_image': f'data:image/png;base64,{img_base64}',
        'exam_url': exam_url,
        'exam_name': exam.exam_name
    })


@app.route('/add-exam-comment', methods=['POST'])
@login_required
def add_exam_comment():
    exam_id = request.form.get('exam_id', type=int)
    content = request.form.get('content', '').strip()

    if not exam_id or not content:
        flash('Vui lòng điền đầy đủ thông tin đánh giá!', 'error')
        return redirect(url_for('exam_detail', id=exam_id))

    exam = dao.get_exam_by_id(exam_id)
    if not exam:
        flash('Đề thi không tồn tại!', 'error')
        return redirect(url_for('index'))

    if utils.add_exam_comment(current_user.id, exam_id, content):
        flash('Đánh giá của bạn đã được gửi thành công!', 'success')
    else:
        flash('Có lỗi xảy ra khi gửi đánh giá!', 'error')

    return redirect(url_for('exam_detail', id=exam_id))


@app.route('/api/exam/<int:exam_id>/rating', methods=['POST'])
@login_required
def rate_exam(exam_id):
    try:
        data = request.get_json()
        rating_value = data.get('rating')
        if not rating_value or rating_value not in [1, 2, 3, 4, 5]:
            return jsonify({'error': 'Đánh giá phải từ 1 đến 5 sao'}), 400

        exam = dao.get_exam_by_id(exam_id)
        if not exam:
            return jsonify({'error': 'Đề thi không tồn tại'}), 404

        student = dao.get_student_by_user_id(current_user.id)
        if not student:
            return jsonify({'error': 'Không tìm thấy thông tin học sinh'}), 404

        has_result = dao.has_exam_result(student.id, exam_id)
        if not has_result:
            return jsonify({'error': 'Bạn phải làm bài thi trước khi đánh giá'}), 400

        success = dao.add_or_update_rating(current_user.id, exam_id, rating_value)
        if success:
            stats = dao.get_exam_rating_stats(exam_id)
            return jsonify({
                'success': True,
                'message': 'Đánh giá thành công!',
                'stats': stats
            })
        else:
            return jsonify({'error': 'Có lỗi xảy ra khi đánh giá'}), 500
    except Exception as e:
        print(f"Error in rate_exam: {e}")
        return jsonify({'error': 'Có lỗi xảy ra'}), 500


@app.route('/api/exam/<int:exam_id>/rating-stats')
def get_exam_rating_stats(exam_id):
    try:
        stats = dao.get_exam_rating_stats(exam_id)

        user_rating = None
        if current_user.is_authenticated:
            user_rating = dao.get_user_rating(current_user.id, exam_id)

        return jsonify({
            'success': True,
            'stats': stats,
            'user_rating': user_rating
        })
    except Exception as e:
        print(f"Error getting rating stats: {e}")
        return jsonify({'error': 'Có lỗi xảy ra'}), 500


@app.route('/api/user/<int:user_id>/exam/<int:exam_id>/rating')
def get_user_exam_rating(user_id, exam_id):
    try:
        rating = dao.get_user_rating(user_id, exam_id)
        return jsonify({
            'success': True,
            'rating': rating
        })
    except Exception as e:
        print(f"Error getting user rating: {e}")
        return jsonify({'success': False, 'rating': None})


@app.route('/account', methods=['GET'])
@login_required
def account_detail():
    user_id = session.get('_user_id')
    user = dao.get_user_by_id(user_id)
    student = Student.query.filter_by(user_id=user_id).first()
    if '_user_id' not in session:
        return redirect(url_for('login'))

    return render_template('account.html', user=user, student=student)


@app.route('/update-account', methods=['POST'])
@login_required
def update_account():
    regex_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    regex_username = r'^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9]{6,20}$'

    try:
        user_id = session.get('_user_id')
        username = request.form.get('username').strip()
        name = request.form.get('name').strip()
        email = request.form.get('email').strip().lower()
        gender = request.form.get('gender')

        has_error = False

        if not all([username, name, email, gender]):
            flash('Vui lòng điền đầy đủ thông tin!', 'error')
            has_error = True
        if username:
            if not re.fullmatch(regex_username, username):
                flash('Tên tài khoản phải có 6-20 ký tự, bao gồm cả chữ và số!', 'error')
                has_error = True
            elif dao.existence_check(User, 'username', username):
                existing_user = User.query.filter(User.username == username, User.id != user_id).first()
                if existing_user:
                    flash('Tên tài khoản này đã tồn tại!', 'error')
                    has_error = True
        if email:
            if not re.fullmatch(regex_email, email):
                flash('Email không hợp lệ! Vui lòng nhập đúng định dạng.', 'error')
                has_error = True
            elif dao.check_email_exists(email, user_id):
                flash('Email đã tồn tại trong hệ thống!', 'error')
                has_error = True
        if name:
            if len(name) < 2 or len(name) > 50:
                flash('Tên phải có 2-50 ký tự!', 'error')
                has_error = True
            elif any(char.isdigit() or char in '!@#$%^&*()_+=[]{}|;:"<>,.?/~`' for char in name):
                flash('Tên không được chứa số hoặc ký tự đặc biệt!', 'error')
                has_error = True
            elif name.isspace():
                flash('Tên không được chỉ chứa khoảng trắng!', 'error')
                has_error = True
        if gender and gender not in ['Male', 'Female']:
            flash('Giới tính không hợp lệ!', 'error')
            has_error = True
        if has_error:
            return redirect(url_for('account_detail'))
        if utils.update_user_info(user_id, username, name, email, gender):
            flash('Cập nhật thông tin thành công!', 'success')
        else:
            flash('Có lỗi xảy ra khi cập nhật thông tin!', 'error')

        return redirect(url_for('account_detail'))

    except Exception as e:
        print(f"Lỗi chỉnh sửa thông tin: {e}")
        flash('Có lỗi hệ thống xảy ra. Vui lòng thử lại!', 'error')
        return redirect(url_for('account_detail'))


@app.route('/update-avatar', methods=['POST'])
@login_required
def update_avatar():
    user_id = session.get('_user_id')

    if 'avatar' not in request.files:
        flash('Vui lòng chọn ảnh!', 'error')
        return redirect(url_for('account_detail'))

    file = request.files['avatar']

    if file.filename == '':
        flash('Vui lòng chọn ảnh!', 'error')
        return redirect(url_for('account_detail'))

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        flash('Chỉ chấp nhận file ảnh (PNG, JPG, JPEG, GIF)!', 'error')
        return redirect(url_for('account_detail'))

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > app.config['MAX_CONTENT_LENGTH']:
        flash('Kích thước file quá lớn! Vui lòng chọn ảnh dưới 5MB.', 'error')
        return redirect(url_for('account_detail'))

    avatar_url = utils.upload_avatar_to_cloudinary(file)

    if avatar_url:
        if utils.update_user_avatar(user_id, avatar_url):
            flash('Cập nhật ảnh đại diện thành công!', 'success')
        else:
            flash('Có lỗi xảy ra khi cập nhật ảnh đại diện!', 'error')
    else:
        flash('Có lỗi xảy ra khi tải ảnh lên!', 'error')

    return redirect(url_for('account_detail'))


def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()

        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    err_message = ''
    success_message = ''

    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            err_message = 'Vui lòng nhập email!'
        elif '@' not in email:
            err_message = 'Email không hợp lệ!'
        else:
            user = dao.get_user_by_email(email)
            if user:
                otp = utils.generate_otp()

                session['otp'] = otp
                session['otp_email'] = email
                session['otp_expires'] = (datetime.now() + timedelta(minutes=10)).timestamp()

                email_body = f"""
                        <html>
                        <body>
                            <h2>Mã OTP đặt lại mật khẩu</h2>
                            <p>Xin chào {user.name},</p>
                            <p>Bạn đã yêu cầu đặt lại mật khẩu cho tài khoản LmaoQuiz của mình.</p>
                            <p>Mã OTP của bạn là: <strong style="font-size: 18px; color: #384AD5;">{otp}</strong></p>
                            <p>Mã này sẽ hết hạn sau 10 phút.</p>
                            <p>Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.</p>
                            <p>Trân trọng,<br>Đội ngũ LmaoQuiz</p>
                        </body>
                        </html>
                    """

                if send_email(email, 'Mã OTP đặt lại mật khẩu - LmaoQuiz', email_body):
                    success_message = 'Mã OTP đã được gửi đến email của bạn! Vui lòng kiểm tra và nhập mã OTP.'
                    session['step'] = 'verify_otp'
                    return redirect(url_for('verify_otp'))
                else:
                    err_message = 'Có lỗi xảy ra khi gửi email. Vui lòng thử lại sau!'
            else:
                err_message = 'Email không tồn tại trong hệ thống!'

    return render_template('forgot-password.html', err_message=err_message, success_message=success_message)


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'otp' not in session:
        return redirect(url_for('forgot_password'))

    err_message = ''
    success_message = ''

    current_time = datetime.now().timestamp()
    expire_time = session.get('otp_expires', 0)
    remaining_seconds = max(0, int(expire_time - current_time))

    if request.method == 'POST':
        user_otp = request.form.get('otp')

        if not user_otp:
            err_message = 'Vui lòng nhập mã OTP!'
        elif remaining_seconds <= 0:
            err_message = 'Mã OTP đã hết hạn! Vui lòng yêu cầu mã mới.'
            session.pop('otp', None)
            session.pop('otp_email', None)
            session.pop('otp_expires', None)
        elif user_otp != session.get('otp'):
            err_message = 'Mã OTP không chính xác!'
        else:
            session['step'] = 'reset_password'
            return redirect(url_for('reset_password'))

    return render_template('verify-otp.html', err_message=err_message, success_message=success_message, remaining_seconds=remaining_seconds)


@app.route('/api/otp-time-remaining')
def otp_time_remaining():
    if 'otp' not in session:
        return jsonify({'remaining': 0, 'expired': True})

    current_time = datetime.now().timestamp()
    expire_time = session.get('otp_expires', 0)
    remaining_seconds = max(0, int(expire_time - current_time))

    return jsonify({
        'remaining': remaining_seconds,
        'expired': remaining_seconds <= 0
    })


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'otp' not in session or session.get('step') != 'reset_password':
        return redirect(url_for('forgot_password'))

    err_message = ''
    success_message = ''

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if not new_password:
            err_message = 'Vui lòng nhập mật khẩu mới!'
        elif len(new_password) < 3:
            err_message = 'Mật khẩu phải có ít nhất 3 ký tự!'
        elif new_password != confirm_password:
            err_message = 'Mật khẩu xác nhận không khớp!'
        else:
            user = dao.get_user_by_email(session.get('otp_email'))
            if user and utils.update_password(user.id, new_password):
                session.pop('otp', None)
                session.pop('otp_email', None)
                session.pop('otp_expires', None)
                session.pop('step', None)

                flash('Đặt lại mật khẩu thành công!', 'success')
                return redirect(url_for('login'))
            else:
                err_message = 'Có lỗi xảy ra khi đặt lại mật khẩu!'

    return render_template('reset-password.html', err_message=err_message, success_message=success_message)


@app.route('/subjects')
def subjects():
    search_query = request.args.get('search', '', type=str)
    sort_by = request.args.get('sort', 'name', type=str)
    filter_has_exam = request.args.get('filter_exam', '', type=str)

    subjects_with_exams = dao.get_all_subjects_with_exams(
        search_query=search_query.strip() if search_query else None,
        sort_by=sort_by,
        filter_has_exam=filter_has_exam
    )

    subjects_tree = {}
    all_subjects = dao.get_all_subjects()

    for subject in all_subjects:
        category = get_subject_category(subject.subject_name)
        if category not in subjects_tree:
            subjects_tree[category] = []
        subjects_tree[category].append(subject)

    return render_template('subjects.html', subjects_with_exams=subjects_with_exams, subjects_tree=subjects_tree, search_query=search_query, sort_by=sort_by, filter_has_exam=filter_has_exam)


def get_subject_category(subject_name):
    subject_lower = subject_name.lower()

    if any(keyword in subject_lower for keyword in ['toán', 'math', 'algebra', 'geometry']):
        return 'Toán học & Khoa học tính toán'
    elif any(keyword in subject_lower for keyword in ['văn', 'literature', 'ngữ văn', 'tiếng việt']):
        return 'Ngữ văn & Văn học'
    elif any(keyword in subject_lower for keyword in ['english', 'tiếng anh', 'anh văn', 'tiếng']):
        return 'Ngoại ngữ'
    elif any(keyword in subject_lower for keyword in ['vật lý', 'physics']) and not any(keyword in subject_lower for keyword in ['địa lý', 'geography']):
        return 'Vật lý'
    elif any(keyword in subject_lower for keyword in ['địa lý', 'địa', 'geography']) and not any(keyword in subject_lower for keyword in ['vật lý', 'physics']):
        return 'Địa lý'
    elif any(keyword in subject_lower for keyword in ['hóa', 'chemistry', 'hóa học']):
        return 'Hóa học'
    elif any(keyword in subject_lower for keyword in ['sinh', 'biology', 'sinh học']):
        return 'Sinh học'
    elif any(keyword in subject_lower for keyword in ['sử', 'history', 'lịch sử']):
        return 'Lịch sử'
    elif any(keyword in subject_lower for keyword in ['tin học', 'computer', 'cntt', 'it']):
        return 'Tin học & Công nghệ'
    elif any(keyword in subject_lower for keyword in ['giáo dục', 'GDCD', 'giáo dục công dân']):
        return 'Giáo dục công dân'
    else:
        return 'Môn học khác'


@app.route('/doing-exam/<int:exam_id>')
@login_required
def doing_exam(exam_id):
    exam = dao.get_exam_by_id(exam_id)
    if not exam:
        flash('Đề thi này đã bị xóa hoặc không tồn tại! Bạn không thể làm bài thi này.', 'error')
        return redirect(url_for('index'))

    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        flash('Không tìm thấy thông tin học sinh!', 'error')
        return redirect(url_for('index'))

    can_take, attempts = dao.check_exam_attempts_limit(student.id, exam_id)
    if not can_take:
        flash(f'Bạn đã thi quá {attempts} lần trong 24 giờ qua. Vui lòng thử lại sau.', 'error')
        return redirect(url_for('exam_detail', id=exam_id))

    is_creator = (current_user.id == exam.user_id)

    if is_creator and not request.args.get('confirmed'):
        flash('Lưu ý: Bạn là người tạo đề thi này. Kết quả của bạn sẽ không xuất hiện trong bảng xếp hạng để đảm bảo tính công bằng.','info')

    existing_session = dao.get_exam_session(student.id, exam_id)

    restart = request.args.get('restart', False)
    if restart and existing_session and not existing_session.is_completed:
        db.session.delete(existing_session)
        db.session.commit()
        existing_session = None

    if not existing_session:
        session_obj = utils.create_exam_session(student.id, exam_id)
        if not session_obj:
            flash('Không thể khởi tạo phiên thi!', 'error')
            return redirect(url_for('index'))
    else:
        session_obj = existing_session

    remaining_time = dao.get_remaining_time_with_session(student.id, exam_id, exam.duration)

    if remaining_time <= 0:
        utils.complete_exam_session(session_obj)
        flash('Thời gian làm bài đã hết!', 'warning')
        return redirect(url_for('index'))

    # Gửi event WebSocket
    if current_user.is_authenticated and hasattr(current_user, 'student'):
        if ws_client.connected:
            ws_client.send_event({
                'type': 'join_exam',
                'exam_id': exam_id,
                'student_id': current_user.student.id
            })

    return render_template('doing-exam.html',
                           exam=exam,
                           remaining_time=remaining_time,
                           has_saved_progress=len(session_obj.user_answers) if session_obj.user_answers else 0,
                           session_data={
                               'current_question_index': session_obj.current_question_index,
                               'user_answers': session_obj.user_answers or {},
                               'is_paused': session_obj.is_paused,
                               'isolations_count': session_obj.isolations_count or 0
                           })


@app.route('/api/exam/<int:exam_id>/remaining-time')
@login_required
def get_exam_remaining_time(exam_id):
    exam = dao.get_exam_by_id(exam_id)
    if not exam:
        return jsonify({'error': 'Đề thi không tồn tại'}), 404

    student = dao.get_student_by_user_id(current_user.id)
    remaining_time = dao.get_remaining_time_with_session(student.id, exam_id, exam.duration)

    return jsonify({
        'remaining_time': remaining_time,
        'expired': remaining_time <= 0
    })


@app.route('/api/exam/<int:exam_id>/pause', methods=['POST'])
@login_required
def pause_exam(exam_id):
    data = request.get_json()
    current_question_index = data.get('current_question_index', 0)
    user_answers = data.get('user_answers', {})

    student = dao.get_student_by_user_id(current_user.id)

    if utils.pause_exam_session(student.id, exam_id, current_question_index, user_answers):
        return jsonify({'success': True, 'message': 'Đã tạm dừng bài thi'})
    else:
        return jsonify({'error': 'Không thể tạm dừng bài thi'}), 500


@app.route('/api/exam/<int:exam_id>/resume', methods=['POST'])
@login_required
def resume_exam(exam_id):
    student = dao.get_student_by_user_id(current_user.id)

    if utils.resume_exam_session(student.id, exam_id):
        return jsonify({'success': True, 'message': 'Đã tiếp tục bài thi'})
    else:
        return jsonify({'error': 'Không thể tiếp tục bài thi'}), 500


@app.route('/api/exam/<int:exam_id>/save-progress', methods=['POST'])
@login_required
def save_exam_progress(exam_id):
    data = request.get_json()
    current_question_index = data.get('current_question_index', 0)
    user_answers = data.get('user_answers', {})

    student = dao.get_student_by_user_id(current_user.id)

    if utils.save_exam_progress(student.id, exam_id, current_question_index, user_answers):
        return jsonify({'success': True, 'message': 'Lưu tiến trình thành công!'})
    else:
        return jsonify({'error': 'Không thể lưu tiến trình'}), 500


@app.route('/api/exam/<int:exam_id>/save-and-exit', methods=['POST'])
@login_required
def save_and_exit_exam(exam_id):
    try:
        data = request.get_json()
        current_question_index = data.get('current_question_index', 0)
        user_answers = data.get('user_answers', {})

        student = dao.get_student_by_user_id(current_user.id)
        if not student:
            return jsonify({'error': 'Không tìm thấy thông tin học sinh'}), 404

        if utils.pause_exam_session(student.id, exam_id, current_question_index, user_answers):
            return jsonify({
                'success': True,
                'message': 'Đã lưu bài thi thành công!',
                'redirect_url': url_for('index', message='saved', type='success')
            })
        else:
            return jsonify({'error': 'Không thể lưu bài thi'}), 500

    except Exception as e:
        print(f"Lỗi save and exit: {e}")
        return jsonify({'error': 'Có lỗi xảy ra khi lưu bài thi'}), 500


@app.route('/api/exam/<int:exam_id>/questions')
@login_required
def get_exam_questions(exam_id):
    exam = dao.get_exam_by_id(exam_id)
    if not exam:
        return jsonify({'error': 'Đề thi không tồn tại'}), 404

    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        return jsonify({'error': 'Không tìm thấy thông tin học sinh'}), 404

    session_obj = dao.get_exam_session(student.id, exam_id)

    if session_obj and session_obj.question_order and session_obj.answer_orders:
        questions_data = utils.get_ordered_questions_for_session(exam_id, session_obj.question_order, session_obj.answer_orders)
    else:
        questions_data = dao.get_exam_questions_with_answers(exam_id)

    return jsonify({
        'exam': {
            'id': exam.id,
            'exam_name': exam.exam_name,
            'duration': exam.duration,
            'subject_name': exam.subject.subject_name,
            'question_count': len(questions_data)
        },
        'questions': questions_data
    })


@app.route('/api/exam/<int:exam_id>/restart', methods=['POST'])
@login_required
def restart_exam(exam_id):
    try:
        student = dao.get_student_by_user_id(current_user.id)
        if not student:
            return jsonify({'error': 'Không tìm thấy thông tin học sinh'}), 404

        existing_session = dao.get_exam_session(student.id, exam_id)
        if existing_session and not existing_session.is_completed:
            db.session.delete(existing_session)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Đã reset bài thi thành công!'
        })

    except Exception as e:
        print(f"Lỗi restart exam: {e}")
        db.session.rollback()
        return jsonify({'error': 'Có lỗi xảy ra khi reset bài thi'}), 500


@app.route('/api/exam/<int:exam_id>/log-violation', methods=['POST'])
@login_required
def log_exam_violation(exam_id):
    try:
        data = request.get_json()
        violation_type = data.get('type')
        details = data.get('details', {})

        student = dao.get_student_by_user_id(current_user.id)
        if not student:
            return jsonify({'error': 'Không tìm thấy học sinh!'}), 404

        dao.log_suspicious_activity(student.id, exam_id, violation_type, details)

        session_obj = dao.get_exam_session(student.id, exam_id)
        if not session_obj:
            return jsonify({'success': False, 'error': 'Session not found'}), 404

        session_obj.isolations_count = (session_obj.isolations_count or 0) + 1

        if session_obj.isolations_count >= 2:
            session_obj.is_terminated = True
            session_obj.is_completed = True
            db.session.commit()
            return jsonify({
                'terminated': True,
                'message': 'Bài thi đã bị kết thúc do vi phạm quá nhiều lần',
                'isolations_count': session_obj.isolations_count
            })

        db.session.commit()
        return jsonify({
            'success': True,
            'terminated': False,
            'isolations_count': session_obj.isolations_count
        })

    except Exception as e:
        print(f"Error in log_violation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/exam/<int:exam_id>/check-violations')
@login_required
def check_violations(exam_id):
    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        return jsonify({'error': 'Không tìm thấy học sinh!'}), 404

    session_obj = dao.get_exam_session(student.id, exam_id)
    if not session_obj:
        return jsonify({'isolations_count': 0, 'is_terminated': False})

    return jsonify({
        'isolations_count': session_obj.isolations_count or 0,
        'is_terminated': session_obj.is_terminated or False
    })


@app.route('/api/exam/submit', methods=['POST'])
@login_required
def submit_exam():
    data = request.get_json()
    exam_id = data.get('exam_id')
    answers = data.get('answers', {})
    time_taken = data.get('time_taken', 0)

    if not exam_id:
        return jsonify({'error': 'Thiếu thông tin đề thi'}), 400

    exam = dao.get_exam_by_id(exam_id)
    if not exam:
        return jsonify({'error': 'Đề thi không tồn tại'}), 404

    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        return jsonify({'error': 'Không tìm thấy thông tin học sinh'}), 404

    session_obj = dao.get_exam_session(student.id, exam_id)
    if not session_obj or session_obj.is_completed:
        return jsonify({'error': 'Session không hợp lệ hoặc đã hoàn thành'}), 400

    is_creator = (current_user.id == exam.user_id)
    remaining_time = dao.get_remaining_time_with_session(student.id, exam_id, exam.duration)
    if remaining_time <= 0:
        actual_time_taken = exam.duration * 60
    else:
        actual_time_taken = (exam.duration * 60) - remaining_time

    score = utils.calculate_exam_score(exam_id, answers)
    result_id = utils.save_exam_result(student.id, exam_id, score, answers, actual_time_taken)

    # Gửi event WebSocket
    if current_user.is_authenticated and hasattr(current_user, 'student'):
        if ws_client.connected:
            ws_client.send_event({
                'type': 'submit_exam',
                'exam_id': exam_id,
                'student_id': current_user.student.id,
                'score': score
            })

    if result_id:
        utils.complete_exam_session(session_obj)
        NotificationService.send_exam_result_notification(student.id, exam_id, score)
        NotificationService.send_improvement_suggestion(student.id)
        success_message = ('Bài thi đã được chấm điểm! (Kết quả không tham gia xếp hạng vì bạn là người tạo đề)' if is_creator else 'Bài thi đã được chấm điểm thành công!')

        return jsonify({
            'success': True,
            'score': score,
            'result_id': result_id,
            'is_creator': is_creator,
            'message': success_message,
            'redirect_url': url_for('view_exam_result', result_id=result_id, time_taken=time_taken)
        })
    else:
        return jsonify({'error': 'Lỗi khi lưu kết quả'}), 500


@app.route('/api/get-current-student-id')
@login_required
def get_current_student_id():
    student = dao.get_student_by_user_id(current_user.id)
    if student:
        return jsonify({'student_id': student.id})
    return jsonify({'error': 'Student not found'}), 404


@app.route('/exam-result/<int:result_id>')
@login_required
def view_exam_result(result_id):
    student = db.session.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        flash('Không có quyền truy cập!', 'error')
        return redirect(url_for('index'))

    result_data = dao.get_exam_result_with_details(result_id, student.id)

    if not result_data:
        flash('Kết quả thi không tồn tại!', 'error')
        return redirect(url_for('index'))

    if not result_data['result'].exam:
        result_data['questions_with_answers'] = None

    return render_template('exam-result.html', result=result_data['result'], questions_with_answers=result_data['questions_with_answers'])


@app.route('/api/exam-result/charts/<int:result_id>')
@login_required
def get_exam_result_charts(result_id):
    try:
        result = dao.get_exam_result_by_id(result_id)
        if not result:
            return jsonify({'error': 'Không tìm thấy kết quả!'}), 404

        current_student = dao.get_student_by_user_id(current_user.id)
        if not current_student or current_student.id != result.student_id:
            return jsonify({'error': 'Không có quyền truy cập!'}), 403

        try:
            previous_results = dao.get_student_exam_results_by_exam(current_student.id, result.exam_id)
        except:
            previous_results = [result]

        comparison_labels = []
        comparison_scores = []
        for i, prev_result in enumerate(previous_results[-5:], 1):
            comparison_labels.append(f'Lần {i}')
            comparison_scores.append(prev_result.score)

        try:
            questions_analysis = dao.get_exam_result_questions_analysis(result_id)
            correct_count = sum(1 for q in questions_analysis if q.get('is_correct', False))
            incorrect_count = len(questions_analysis) - correct_count
        except Exception as e:
            print(f"Error in questions analysis: {e}")
            if result.user_answers:
                questions = dao.get_exam_questions_with_answers(result.exam_id)
                correct_count = 0
                for question in questions:
                    user_answer_id = result.user_answers.get(str(question['id']))
                    if user_answer_id:
                        correct_answer = next((a for a in question['answers'] if a['is_correct']), None)
                        if correct_answer and int(user_answer_id) == correct_answer['id']:
                            correct_count += 1
                incorrect_count = len(questions) - correct_count
            else:
                correct_count = 0
                incorrect_count = 1

        time_efficiency = 100
        if result.time_taken and result.exam.duration:
            time_efficiency = min(100, (result.exam.duration * 60 - result.time_taken) / (result.exam.duration * 60) * 100)

        accuracy = (correct_count / (correct_count + incorrect_count) * 100) if (correct_count + incorrect_count) > 0 else 0

        overall_efficiency = 100
        if result.time_taken and result.time_taken > 0 and result.exam.duration:
            time_ratio = result.time_taken / (result.exam.duration * 60)
            overall_efficiency = min(100, result.score / time_ratio) if time_ratio > 0 else 100
        return jsonify({
            'score_comparison': {
                'labels': comparison_labels,
                'data': comparison_scores
            },
            'question_analysis': {
                'labels': ['Đúng', 'Sai'],
                'data': [correct_count, incorrect_count]
            },
            'performance_radar': {
                'labels': ['Điểm số', 'Thời gian', 'Độ chính xác', 'Hiệu quả'],
                'data': [
                    result.score,
                    time_efficiency,
                    accuracy,
                    min(100, overall_efficiency)
                ]
            }
        })
    except Exception as e:
        print(f"Error in get_exam_result_charts: {e}")
        return jsonify({'error': f'Lỗi server: {str(e)}'}), 500


@app.route('/exam-history')
@login_required
def exam_history():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    selected_subject = request.args.get('subject', '', type=str)
    score_filter = request.args.get('score_filter', '', type=str)

    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        flash('Không tìm thấy thông tin học sinh!', 'error')
        return redirect(url_for('index'))

    pagination = dao.get_exam_history_with_pagination(
        student_id=student.id,
        page=page,
        per_page=10,
        search_query=search_query,
        selected_subject=selected_subject,
        score_filter=score_filter
    )

    subjects = dao.get_all_subjects()

    return render_template('exam-history.html', exam_results=pagination.items, pagination=pagination, search_query=search_query, selected_subject=selected_subject, score_filter=score_filter, subjects=subjects)


@app.route('/api/exam-history/charts/<int:user_id>')
@login_required
def get_exam_history_charts(user_id):
    if current_user.id != user_id:
        return jsonify({'error': 'Không có quyền truy cập!'}), 403

    current_student = dao.get_student_by_user_id(user_id)
    if not current_student:
        return jsonify({'error': 'Không tìm thấy thông tin học sinh!'}), 404

    results = db.session.query(ExamResult).outerjoin(Exam).outerjoin(Subject).filter(ExamResult.student_id == current_student.id).order_by(ExamResult.taken_exam).all()

    if not results:
        return jsonify({
            'score_trend': {'labels': [], 'data': []},
            'subject_performance': {'labels': [], 'data': []},
            'score_distribution': {'labels': [], 'data': []},
            'monthly_stats': {'labels': [], 'data': []},
            'time_performance': {'labels': [], 'efficiency': [], 'scores': []}
        })

    score_trend_labels = []
    score_trend_data = []
    for result in results[-20:]:
        score_trend_labels.append(result.taken_exam.strftime('%d/%m'))
        score_trend_data.append(result.score)

    subject_scores = {}
    for result in results:
        if result.exam and result.exam.subject:
            subject_name = result.exam.subject.subject_name
        elif result.exam_name:
            subject_name = f"{result.exam_name} (Đã xóa)"
        else:
            subject_name = "Đề thi đã xóa"

        if subject_name not in subject_scores:
            subject_scores[subject_name] = []
        subject_scores[subject_name].append(result.score)

    subject_labels = list(subject_scores.keys())
    subject_avg_scores = [sum(scores) / len(scores) for scores in subject_scores.values()]
    score_ranges = {
        'Xuất sắc (≥80)': len([r for r in results if r.score >= 80]),
        'Khá tốt (65-79)': len([r for r in results if 65 <= r.score < 80]),
        'Đạt yêu cầu (50-64)': len([r for r in results if 50 <= r.score < 65]),
        'Cần cố gắng (<50)': len([r for r in results if r.score < 50])
    }

    monthly_stats = {}
    for result in results:
        month_key = result.taken_exam.strftime('%m/%Y')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {'total': 0, 'sum_score': 0}
        monthly_stats[month_key]['total'] += 1
        monthly_stats[month_key]['sum_score'] += result.score

    monthly_labels = list(monthly_stats.keys())[-12:]
    monthly_avg_scores = [monthly_stats[month]['sum_score'] / monthly_stats[month]['total'] for month in monthly_labels]

    time_labels = []
    time_efficiency = []
    time_scores = []
    for result in results[-15:]:
        if result.time_taken and result.exam and result.exam.duration:
            exam_name = result.exam.exam_name
            time_labels.append(exam_name[:20] + '...' if len(exam_name) > 20 else exam_name)
            time_ratio = result.time_taken / (result.exam.duration * 60)
            time_efficiency.append(round(result.score / time_ratio, 1) if time_ratio > 0 else 0)
            time_scores.append(result.score)
        elif result.exam_name:
            exam_name = result.exam_name + " (Đã xóa)"
            time_labels.append(exam_name[:20] + '...' if len(exam_name) > 20 else exam_name)
            time_efficiency.append(0)
            time_scores.append(result.score)

    return jsonify({
        'score_trend': {
            'labels': score_trend_labels,
            'data': score_trend_data
        },
        'subject_performance': {
            'labels': subject_labels,
            'data': subject_avg_scores
        },
        'score_distribution': {
            'labels': list(score_ranges.keys()),
            'data': list(score_ranges.values())
        },
        'monthly_stats': {
            'labels': monthly_labels,
            'data': monthly_avg_scores
        },
        'time_performance': {
            'labels': time_labels,
            'efficiency': time_efficiency,
            'scores': time_scores
        }
    })


@app.route('/user-exams')
@login_required
def user_exams():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)

    exams_pagination = dao.get_user_created_exams_with_pagination(
        creator_id=current_user.id,
        page=page,
        per_page=app.config['PAGE_SIZE'],
        search_query=search_query.strip() if search_query else None
    )

    exams_with_stats = []
    for exam in exams_pagination.items:
        stats = utils.get_exam_stats(exam.id)
        question_count = utils.count_exam_questions(exam.id)

        exams_with_stats.append({
            'exam': exam,
            'stats': stats,
            'question_count': question_count
        })

    return render_template('user-exams.html', exams=exams_with_stats, pagination=exams_pagination, search_query=search_query)


@app.route('/create-exam', methods=['GET', 'POST'])
@login_required
def create_exam():
    if request.method == 'POST':
        data = request.get_json()
        exam_name = data.get('exam_name', '').strip()
        subject_id = data.get('subject_id')
        duration = data.get('duration')
        questions_data = data.get('questions', [])

        if not exam_name or not subject_id or not duration or not questions_data:
            flash('Vui lòng điền đầy đủ thông tin!', 'error')
            return jsonify({'error': 'Vui lòng điền đầy đủ thông tin'}), 400

        if len(questions_data) < 1:
            flash('Đề thi phải có ít nhất 1 câu hỏi', 'error')
            return jsonify({'error': 'Đề thi phải có ít nhất 1 câu hỏi'}), 400

        #Validate
        for i, question in enumerate(questions_data):
            if not question.get('question_title', '').strip():
                flash(f'Câu hỏi {i + 1} không được để trống', 'error')
                return jsonify({'error': f'Câu hỏi {i + 1} không được để trống'}), 400

            answers = question.get('answers', [])
            if len(answers) < 2:
                flash(f'Câu hỏi {i + 1} phải có ít nhất 2 đáp án', 'error')
                return jsonify({'error': f'Câu hỏi {i + 1} phải có ít nhất 2 đáp án'}), 400

            has_correct = any(answer.get('is_correct') for answer in answers)
            if not has_correct:
                flash(f'Câu hỏi {i + 1} phải có ít nhất 1 đáp án đúng', 'error')
                return jsonify({'error': f'Câu hỏi {i + 1} phải có ít nhất 1 đáp án đúng'}), 400

        exam_id = utils.create_exam(current_user.id, exam_name, subject_id, duration, questions_data)

        if exam_id:
            flash('Tạo đề thi thành công!', 'success')
            return jsonify({
                'success': True,
                'message': 'Tạo đề thi thành công!',
                'exam_id': exam_id,
                'redirect_url': url_for('user_exams')
            })
        else:
            flash('Có lỗi xảy ra khi tạo đề thi', 'error')
            return jsonify({'error': 'Có lỗi xảy ra khi tạo đề thi'}), 500

    subjects = dao.get_all_subjects()
    return render_template('create-exam.html', subjects=subjects)


@app.route('/edit-exam/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def edit_exam(exam_id):
    exam_data = dao.get_user_exam_for_edit(exam_id, current_user.id)

    if not exam_data:
        flash('Không tìm thấy đề thi hoặc bạn không có quyền chỉnh sửa!', 'error')
        return redirect(url_for('user_exams'))

    if request.method == 'POST':
        data = request.get_json()
        exam_name = data.get('exam_name', '').strip()
        subject_id = data.get('subject_id')
        duration = data.get('duration')
        questions_data = data.get('questions', [])

        if not exam_name or not subject_id or not duration or not questions_data:
            flash('Vui lòng điền đầy đủ thông tin', 'error')
            return jsonify({'error': 'Vui lòng điền đầy đủ thông tin'}), 400

        if len(questions_data) < 1:
            flash('Đề thi phải có ít nhất 1 câu hỏi', 'error')
            return jsonify({'error': 'Đề thi phải có ít nhất 1 câu hỏi'}), 400

        #Validate
        for i, question in enumerate(questions_data):
            if not question.get('question_title', '').strip():
                flash(f'Câu hỏi {i + 1} không được để trống', 'error')
                return jsonify({'error': f'Câu hỏi {i + 1} không được để trống'}), 400

            answers = question.get('answers', [])
            if len(answers) < 2:
                flash(f'Câu hỏi {i + 1} phải có ít nhất 2 đáp án', 'error')
                return jsonify({'error': f'Câu hỏi {i + 1} phải có ít nhất 2 đáp án'}), 400

            has_correct = any(answer.get('is_correct') for answer in answers)
            if not has_correct:
                flash(f'Câu hỏi {i + 1} phải có ít nhất 1 đáp án đúng', 'error')
                return jsonify({'error': f'Câu hỏi {i + 1} phải có ít nhất 1 đáp án đúng'}), 400

        if utils.update_exam(exam_id, current_user.id, exam_name, subject_id, duration, questions_data):
            flash('Cập nhật đề thi thành công!', 'success')
            return jsonify({
                'success': True,
                'message': 'Cập nhật đề thi thành công!',
                'redirect_url': url_for('user_exams')
            })
        else:
            flash('Có lỗi xảy ra khi cập nhật đề thi', 'error')
            return jsonify({'error': 'Có lỗi xảy ra khi cập nhật đề thi'}), 500

    subjects = dao.get_all_subjects()
    return render_template('edit-exam.html', exam_data=exam_data, subjects=subjects)


@app.route('/delete-exam/<int:exam_id>', methods=['POST'])
@login_required
def delete_exam(exam_id):
    if utils.delete_user_exam(exam_id, current_user.id):
        flash('Xóa đề thi thành công!', 'success')
    else:
        flash('Có lỗi xảy ra khi xóa đề thi!', 'error')

    return redirect(url_for('user_exams'))


@app.route('/create-random-exam', methods=['GET', 'POST'])
@login_required
def create_random_exam():
    if request.method == 'POST':
        data = request.get_json()
        exam_name = data.get('exam_name', '').strip()
        subject_id = data.get('subject_id')
        duration = data.get('duration')
        question_count = data.get('question_count', 10)

        # Validation
        if not exam_name or not subject_id or not duration:
            flash('Vui lòng điền đầy đủ thông tin', 'error')
            return jsonify({'error': 'Vui lòng điền đầy đủ thông tin'}), 400

        if question_count < 1:
            flash('Số câu hỏi phải lớn hơn 0', 'error')
            return jsonify({'error': 'Số câu hỏi phải lớn hơn 0'}), 400

        if question_count > 50:
            flash('Số câu hỏi không được vượt quá 50', 'error')
            return jsonify({'error': 'Số câu hỏi không được vượt quá 50'}), 400

        subject = dao.get_subject_by_id(subject_id)
        if not subject:
            flash('Môn học không tồn tại', 'error')
            return jsonify({'error': 'Môn học không tồn tại'}), 400

        exam_id, error_message = utils.create_random_exam(
            current_user.id, exam_name, subject_id, duration, question_count
        )

        if exam_id:
            flash('Tạo đề thi ngẫu nhiên thành công!', 'success')
            return jsonify({
                'success': True,
                'message': 'Tạo đề thi ngẫu nhiên thành công!',
                'exam_id': exam_id,
                'redirect_url': url_for('user_exams')
            })
        else:
            flash('Có lỗi xảy ra khi tạo đề thi', 'error')
            return jsonify({'error': error_message or 'Có lỗi xảy ra khi tạo đề thi'}), 500

    subjects = dao.get_all_subjects()
    return render_template('create-random-exam.html', subjects=subjects)


@app.route('/api/subject/<int:subject_id>/questions-count')
@login_required
def get_subject_questions_count(subject_id):
    try:
        count = dao.get_questions_count_by_subject(subject_id)
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Có lỗi xảy ra khi lấy thông tin'
        }), 500


@app.route('/recommendations')
@login_required
def recommendations():
    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        flash('Không tìm thấy thông tin học sinh!', 'error')
        return redirect(url_for('index'))

    analysis = recommendation_engine.analyze_student_performance(student.id)
    recommendations = recommendation_engine.recommend_study_materials(student.id)
    overall_ranking = recommendation_engine.get_student_ranking(student.id)
    monthly_ranking = recommendation_engine.get_student_ranking(student.id, 'month')
    subject_ranking = None
    if analysis and analysis.get('worst_subject'):
        subject_ranking = recommendation_engine.get_subject_ranking(student.id, analysis['worst_subject'])

    leaderboard = recommendation_engine.get_leaderboard(limit=10)
    badges = recommendation_engine.get_achievement_badges(student.id)
    return render_template('recommendations.html',
                           student=student,
                           analysis=analysis,
                           recommendations=recommendations,
                           overall_ranking=overall_ranking,
                           monthly_ranking=monthly_ranking,
                           subject_ranking=subject_ranking,
                           leaderboard=leaderboard,
                           badges=badges)


@app.route('/api/recommendations')
@login_required
def api_recommendations():
    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        return jsonify({'error': 'Không tìm thấy thông tin học sinh!'}), 404

    recommendations = recommendation_engine.recommend_study_materials(student.id)
    return jsonify({'recommendations': recommendations})


@app.route('/api/student-ranking/<int:student_id>')
@login_required
def get_student_ranking(student_id):
    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    timeframe = request.args.get('timeframe', 'all')
    ranking = recommendation_engine.get_student_ranking(student_id, timeframe)
    return jsonify(ranking)


@app.route('/api/subject-ranking/<int:student_id>')
@login_required
def get_subject_ranking(student_id):
    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    subject_name = request.args.get('subject')
    ranking = recommendation_engine.get_subject_ranking(student_id, subject_name)
    return jsonify(ranking)


@app.route('/api/leaderboard')
@login_required
def get_leaderboard():
    timeframe = request.args.get('timeframe', 'all')
    subject_id = request.args.get('subject_id', type=int)
    limit = request.args.get('limit', 20, type=int)

    leaderboard = recommendation_engine.get_leaderboard(limit, timeframe, subject_id)
    return jsonify({'leaderboard': leaderboard})


@app.route('/api/achievement-badges/<int:student_id>')
@login_required
def get_achievement_badges(student_id):
    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    badges = recommendation_engine.get_achievement_badges(student_id)
    return jsonify({'badges': badges})


@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')


@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    try:
        data = request.get_json()
        message = data.get('message', '')
        user_id = data.get('user_id')
        if not message.strip():
            return jsonify({'response': 'Bạn chưa nhập tin nhắn nào. Hãy thử hỏi tôi điều gì đó! 😊'})

        response = smart_chatbot.process_message(message, user_id)
        return jsonify({
            'response': response,
            'status': 'success'
        })
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({
            'response': 'Xin lỗi, tôi đang gặp sự cố. Bạn có thể thử lại sau không? 🤖💭',
            'status': 'error'
        }), 500


@app.route('/api/study-plan/<int:student_id>')
@login_required
def get_study_plan(student_id):
    if current_user.role not in [Role.ADMIN] and current_user.id != student_id:
        return jsonify({'error': 'Unauthorized'}), 403

    study_plan = generate_personalized_study_plan.delay(student_id)
    return jsonify({'message': 'Kế hoạch học tập đã được tạo!', 'task_id': study_plan.id})


@app.route('/api/study-plan-status/<task_id>')
@login_required
def check_study_plan_status(task_id):
    try:
        result = AsyncResult(task_id)
        if result.ready():
            return jsonify({
                'status': 'completed',
                'result': result.result
            })
        else:
            return jsonify({'status': 'pending'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    init_notification_scheduler(app)
    ws_client.start()
    app.run(debug=True)
