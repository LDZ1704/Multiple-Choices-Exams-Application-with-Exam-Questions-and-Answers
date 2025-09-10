from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from app.models import User, Student, Exam, ExamResult, Notification, ExamSession
from app import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app import app


class NotificationService:
    @staticmethod
    def create_notification(user_id, title, message, notification_type='info', exam_id=None):
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            exam_id=exam_id,
            created_at=datetime.now()
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def get_user_notifications(user_id, page=1, per_page=10, unread_only=False):
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def mark_as_read(notification_id, user_id):
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_all_as_read(user_id):
        Notification.query.filter_by(user_id=user_id).update({'is_read': True})
        db.session.commit()

    @staticmethod
    def get_unread_count(user_id):
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def send_exam_reminder():
        seven_days_ago = datetime.now() - timedelta(days=7)

        inactive_students = db.session.query(Student).join(User).filter(
            ~Student.id.in_(db.session.query(ExamResult.student_id).filter(ExamResult.taken_exam >= seven_days_ago)
            )
        ).all()

        for student in inactive_students:
            NotificationService.create_notification(
                user_id=student.user_id,
                title="Nhắc nhở ôn tập",
                message="Bạn chưa làm bài thi nào trong 7 ngày qua. Hãy ôn tập và thử sức với các đề thi mới nhé!",
                notification_type='reminder'
            )

    @staticmethod
    def send_exam_result_notification(student_id, exam_id, score):
        student = Student.query.get(student_id)
        exam = Exam.query.get(exam_id)

        if student and exam:
            existing = Notification.query.filter_by(user_id=student.user_id, notification_type='result', exam_id=exam_id).filter(
                Notification.created_at >= datetime.now() - timedelta(minutes=1)
            ).first()

            if existing:
                return
            grade = "Xuất sắc" if score >= 90 else "Giỏi" if score >= 80 else "Khá" if score >= 50 else "Trung bình" if score >= 20 else "Yếu"

            NotificationService.create_notification(
                user_id=student.user_id,
                title=f"Kết quả thi: {exam.exam_name}",
                message=f"Bạn đã đạt {score} điểm ({grade}) trong bài thi {exam.exam_name}. Chúc mừng!",
                notification_type='result',
                exam_id=exam_id
            )

    @staticmethod
    def send_improvement_suggestion(student_id):
        student = Student.query.get(student_id)
        if not student:
            return
        recent_suggestion = Notification.query.filter_by(user_id=student.user_id, notification_type='suggestion').filter(
            Notification.created_at >= datetime.now() - timedelta(minutes=1)
        ).first()

        if recent_suggestion:
            return
        recent_results = ExamResult.query.filter_by(student_id=student_id).order_by(ExamResult.taken_exam.desc()).limit(5).all()

        if len(recent_results) >= 3:
            scores = [r.score for r in recent_results]
            avg_score = sum(scores) / len(scores)

            if avg_score < 50:
                message = "Kết quả của bạn cần cải thiện. Hãy ôn tập kỹ hơn và làm thêm các đề thi cùng chủ đề!"
            elif avg_score < 80:
                message = "Bạn đang tiến bộ tốt! Hãy tiếp tục luyện tập để đạt điểm cao hơn."
            else:
                message = "Kết quả xuất sắc! Hãy thử thách bản thân với các đề thi khó hơn."

            NotificationService.create_notification(
                user_id=student.user_id,
                title="Gợi ý học tập",
                message=message,
                notification_type='suggestion'
            )

    @staticmethod
    def send_new_exam_notification(exam_id):
        exam = Exam.query.get(exam_id)
        if not exam:
            return

        students = Student.query.join(User).all()

        for student in students:
            NotificationService.create_notification(
                user_id=student.user_id,
                title="Đề thi mới",
                message=f"Đề thi mới '{exam.exam_name}' môn {exam.subject.subject_name} đã được thêm. Hãy thử sức ngay!",
                notification_type='new_exam',
                exam_id=exam_id
            )

    @staticmethod
    def send_email_notification(to_email, subject, message):
        try:
            msg = MIMEMultipart()
            msg['From'] = app.config['MAIL_USERNAME']
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'html'))

            server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False