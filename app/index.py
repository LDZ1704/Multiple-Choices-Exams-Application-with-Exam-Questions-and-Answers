import re
from flask import Flask, render_template, url_for, request, redirect, session, flash, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from app import app, db, login_manager
from app.models import User, Role
import app.dao as dao
from app.admin import *
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta


@app.context_processor
def inject_user():
    return dict(current_user=current_user)


@app.route('/')
def index():
    return (render_template('index.html'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    err_message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = dao.auth_user(username, password)

        if user:
            login_user(user)
            if user.role == Role.ADMIN:
                if not dao.existence_check(Admin, 'user_id', user.id):
                    dao.add_admin(user)
                return redirect('/admin')
            elif user.role == Role.STUDENT:
                if not dao.existence_check(Student, 'user_id', user.id):
                    dao.add_student(user)
                return redirect('/')
            else:
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
            flash('Chào mừng ' + name + ' tới LmaoQuiz', 'Đăng kí thành công!')
            return redirect('/login')

    return render_template('register.html', err_message=err_message)


@app.route('/examdetail')
def exam_detail():
    return (render_template('examdetail.html'))


@app.route('/account', methods=['GET'])
@login_required
def account_detail():
    user_id = session.get('_user_id')
    user = dao.get_user_by_id(user_id)
    student = Student.query.filter_by(user_id=user_id).first()
    if '_user_id' not in session:
        return redirect(url_for('login'))

    return render_template('account.html', user=user, student=student)


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
                otp = dao.generate_otp()

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

    if request.method == 'POST':
        user_otp = request.form.get('otp')

        if not user_otp:
            err_message = 'Vui lòng nhập mã OTP!'
        elif datetime.now().timestamp() > session.get('otp_expires', 0):
            err_message = 'Mã OTP đã hết hạn! Vui lòng yêu cầu mã mới.'
            session.pop('otp', None)
            session.pop('otp_email', None)
            session.pop('otp_expires', None)
        elif user_otp != session.get('otp'):
            err_message = 'Mã OTP không chính xác!'
        else:
            session['step'] = 'reset_password'
            return redirect(url_for('reset_password'))

    return render_template('verify-otp.html', err_message=err_message, success_message=success_message)


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
        elif len(new_password) < 8:
            err_message = 'Mật khẩu phải có ít nhất 8 ký tự!'
        elif new_password != confirm_password:
            err_message = 'Mật khẩu xác nhận không khớp!'
        else:
            user = dao.get_user_by_email(session.get('otp_email'))
            if user and dao.update_password(user.id, new_password):
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
    return (render_template('subjects.html'))


@app.route('/doing-exam')
@login_required
def doing_exam():
    return (render_template('doing-exam.html'))


if __name__ == '__main__':
    app.run(debug=True)
