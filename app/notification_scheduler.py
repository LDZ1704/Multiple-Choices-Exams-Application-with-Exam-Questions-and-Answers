from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from datetime import datetime, timedelta
from app.models import Student, ExamResult, User, Notification
from app import db
from app.notification_service import NotificationService


def init_notification_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: exam_reminder_with_context(app),
        trigger="interval",
        hours=8,
        id='daily_study_reminder'
    )

    scheduler.add_job(
        func=lambda: weekly_summary_with_context(app),
        trigger="cron",
        day_of_week=6,
        hour=20,
        minute=0,
        id='weekly_summary'
    )

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())


def exam_reminder_with_context(app):
    with app.app_context():
        send_exam_reminder()


def weekly_summary_with_context(app):
    with app.app_context():
        send_weekly_summary()


def send_exam_reminder():
    seven_days_ago = datetime.now() - timedelta(days=7)
    inactive_students = db.session.query(Student).join(User).filter(
        ~Student.id.in_(db.session.query(ExamResult.student_id).filter(ExamResult.taken_exam >= seven_days_ago))).all()

    for student in inactive_students:
        create_notification(
            user_id=student.user_id,
            title="Nhắc nhở ôn tập",
            message="Bạn chưa làm bài thi nào trong 7 ngày qua. Hãy ôn tập và thử sức với các đề thi mới nhé!",
            notification_type='reminder'
        )


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


def send_weekly_summary():
    week_ago = datetime.now() - timedelta(days=7)
    active_students = db.session.query(Student).join(ExamResult).filter(ExamResult.taken_exam >= week_ago).distinct().all()

    for student in active_students:
        weekly_results = ExamResult.query.filter(ExamResult.student_id == student.id, ExamResult.taken_exam >= week_ago).all()

        if weekly_results:
            total_exams = len(weekly_results)
            avg_score = sum(r.score for r in weekly_results) / total_exams
            best_score = max(r.score for r in weekly_results)

            message = f"""
                Tổng kết giờ học gần nhất:
                • Số bài thi đã làm: {total_exams}
                • Điểm trung bình: {avg_score:.1f}
                • Điểm cao nhất: {best_score}

                Hãy tiếp tục phát huy và học tập chăm chỉ hơn nữa!
            """

            NotificationService.create_notification(
                user_id=student.user_id,
                title="Tổng kết giờ học",
                message=message,
                notification_type='summary'
            )