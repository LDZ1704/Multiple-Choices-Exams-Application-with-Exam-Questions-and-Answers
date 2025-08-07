import re
import os
from sqlalchemy import or_
from flask import Flask, render_template, url_for, request, redirect, session, flash, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from app import app, db, login_manager, utils
from app.models import User, Role, Student, ExamResult, Subject
from app.models import Admin as AdminModels
import app.dao as dao
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from app.admin import *


@app.context_processor
def inject_user():
    return dict(current_user=current_user, admin=admin, dao=dao)


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
    err_message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        next_page = request.args.get('next')

        user = dao.auth_user(username, password)

        if user:
            login_user(user)
            flash('Chào mừng ' + username + ' tới LmaoQuiz', 'success')

            if user.role == Role.ADMIN:
                if not dao.existence_check(AdminModels, 'user_id', user.id):
                    dao.add_admin(user)
                return redirect('/admin')
            elif user.role == Role.STUDENT:
                if not dao.existence_check(Student, 'user_id', user.id):
                    dao.add_student(user)
                return redirect(next_page) if next_page else redirect('/')

        else:
            flash('Thông tin tài khoản và mật khẩu không chính xác!', 'danger')
            err_message = 'Thông tin tài khoản và mật khẩu không chính xác!'

    return render_template('login.html', err_message=err_message)


@login_manager.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    regex_username = '^[a-zA-Z0-9]+$'
    err_message = {}
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        gender = request.form.get('gender')

        if dao.existence_check(User, 'username', username):
            err_message['err_username'] = 'Tên tài khoản này đã tồn tại!'
        if not re.fullmatch(regex_username, username):
            err_message['err_format'] = 'Tên tài khoản phải có cả chữ và số!'
        if not password.__eq__(confirm_password):
            err_message['err_password'] = 'Bạn phải xác nhận lại mật khẩu giống mật khẩu của bạn.'
        if '@' not in email:
            err_message['err_email'] = 'Email phải theo đúng định dạng (abc@example.com)!'
        elif dao.existence_check(User, 'email', email):
            err_message['err_email'] = 'Email đã tồn tại trong hệ thống!'

        if err_message:
            return render_template('register.html', err_message=err_message, username=username, name=name,
                                   gender=gender, email=email)
        else:
            data = request.form.copy()
            del data['confirm-password']
            dao.add_user(**data)
            flash('Chào mừng ' + name + ' tới LmaoQuiz', 'success')
            return redirect('/login')

    return render_template('register.html', err_message=err_message)


@app.route('/examdetail')
def exam_detail():
    exam_id = request.args.get('id', type=int)
    comment_page = request.args.get('comment_page', 1, type=int)
    session_obj = None

    if not exam_id:
        flash('Không tìm thấy đề thi!', 'error')
        return redirect(url_for('index'))

    exam = dao.get_exam_by_id(exam_id)
    if not exam:
        flash('Đề thi không tồn tại!', 'error')
        return redirect(url_for('index'))

    if current_user.is_authenticated:
        student = dao.get_student_by_user_id(current_user.id)
        if student:
            session_obj = dao.get_exam_session(student.id, exam_id)

    stats = utils.get_exam_stats(exam_id)
    question_count = utils.count_exam_questions(exam_id)

    comments_pagination = utils.get_exam_comments_with_pagination(exam_id, page=comment_page, per_page=app.config['COMMENT_SIZE'])

    user_results = None
    highest_score = 0
    has_result = False
    if current_user.is_authenticated:
        user_results = utils.get_user_exam_results(current_user.id, exam_id)
        highest_score = utils.get_highest_score(current_user.id, exam_id)
        student = dao.get_student_by_user_id(current_user.id)
        if student:
            has_result = dao.has_exam_result(student.id, exam_id)

    return render_template('examdetail.html', exam=exam, stats=stats, question_count=question_count, comments_pagination=comments_pagination, user_results=user_results, session=session_obj, highest_score=highest_score, has_result=has_result)


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
    try:
        user_id = session.get('_user_id')
        username = session.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        gender = request.form.get('gender')

        if request.method == 'POST':
            if not name or not email or not gender or not username:
                flash('Vui lòng điền đầy đủ thông tin!', 'error')
                return redirect(url_for('account_detail'))
            if '@' not in email:
                flash('Email không hợp lệ!', 'error')
                return redirect(url_for('account_detail'))
            if dao.check_email_exists(email, user_id):
                flash('Email đã tồn tại trong hệ thống!', 'error')
                return redirect(url_for('account_detail'))

            if utils.update_user_info(user_id, username, name, email, gender):
                flash('Cập nhật thông tin thành công!', 'success')
            else:
                flash('Có lỗi xảy ra khi cập nhật thông tin!', 'error')

        return redirect(url_for('account_detail'))
    except Exception as e:
        print(f"Lỗi chỉnh sửa thông tin: {e}")
        return False


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

    # Kiểm tra định dạng file
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        flash('Chỉ chấp nhận file ảnh (PNG, JPG, JPEG, GIF)!', 'error')
        return redirect(url_for('account_detail'))

    # Kiểm tra kích thước file (tối đa 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > app.config['MAX_CONTENT_LENGTH']:
        flash('Kích thước file quá lớn! Vui lòng chọn ảnh dưới 5MB.', 'error')
        return redirect(url_for('account_detail'))

    # Upload lên Cloudinary
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
    subjects_with_exams = dao.get_all_subjects_with_exams(
        search_query=search_query.strip() if search_query else None
    )
    return render_template('subjects.html', subjects_with_exams=subjects_with_exams, search_query=search_query)


@app.route('/doing-exam/<int:exam_id>')
@login_required
def doing_exam(exam_id):
    exam = dao.get_exam_by_id(exam_id)
    if not exam:
        flash('Đề thi không tồn tại!', 'error')
        return redirect(url_for('index'))

    student = dao.get_student_by_user_id(current_user.id)
    if not student:
        flash('Không tìm thấy thông tin học sinh!', 'error')
        return redirect(url_for('index'))

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

    return render_template('doing-exam.html',
                           exam=exam,
                           remaining_time=remaining_time,
                           has_saved_progress=len(session_obj.user_answers) if session_obj.user_answers else 0,
                           session_data={
                               'current_question_index': session_obj.current_question_index,
                               'user_answers': session_obj.user_answers or {},
                               'is_paused': session_obj.is_paused
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

    remaining_time = dao.get_remaining_time_with_session(student.id, exam_id, exam.duration)
    if remaining_time <= 0:
        session_obj = dao.get_exam_session(student.id, exam_id)
        if session_obj:
            utils.complete_exam_session(session_obj)
        return jsonify({'error': 'Thời gian làm bài đã hết'}), 400

    actual_time_taken = (exam.duration * 60) - remaining_time

    score = utils.calculate_exam_score(exam_id, answers)
    result_id = utils.save_exam_result(student.id, exam_id, score, answers, actual_time_taken)

    if result_id:
        session_obj = dao.get_exam_session(student.id, exam_id)
        if session_obj:
            utils.complete_exam_session(session_obj)

        return jsonify({
            'success': True,
            'score': score,
            'result_id': result_id,
            'redirect_url': url_for('view_exam_result', result_id=result_id)
        })
    else:
        return jsonify({'error': 'Lỗi khi lưu kết quả'}), 500


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

    return render_template('exam-result.html', result=result_data['result'], questions_with_answers=result_data['questions_with_answers'])


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


if __name__ == '__main__':
    app.run(debug=True)
