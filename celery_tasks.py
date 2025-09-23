from celery import Celery
from datetime import datetime, timedelta
import requests
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config.get('broker_url'),
        backend=app.config.get('result_backend')
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# Import app và các models sau khi định nghĩa make_celery để tránh circular import
def get_app_context():
    from app import app, db
    from app.models import User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam
    from app.recommendation_engine import recommendation_engine
    return app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine


celery = None


# Beat schedule sẽ được cấu hình sau khi celery được khởi tạo
def configure_beat_schedule(celery_instance):
    celery_instance.conf.beat_schedule = {
        'generate-daily-recommendations': {
            'task': 'celery_tasks.generate_daily_recommendations',
            'schedule': 3600.0,
        },
        'send-study-reminders': {
            'task': 'celery_tasks.send_study_reminders',
            'schedule': 86400.0,
        },
        'analyze-learning-patterns': {
            'task': 'celery_tasks.analyze_learning_patterns',
            'schedule': 21600.0,
        },
        'cleanup-old-sessions': {
            'task': 'celery_tasks.cleanup_old_sessions',
            'schedule': 43200.0,
        }
    }


def generate_daily_recommendations():
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    with app.app_context():
        students = db.session.query(Student).all()

        for student in students:
            try:
                today = datetime.now().date()
                existing = db.session.query(StudyRecommendation).filter(StudyRecommendation.student_id == student.id, StudyRecommendation.created_at >= today).first()

                if existing:
                    continue

                recommendations = recommendation_engine.recommend_study_materials(student.id)

                if recommendations:
                    for rec in recommendations[:3]:  # Top 3
                        study_rec = StudyRecommendation(
                            student_id=student.id,
                            recommendation_type=rec['type'],
                            content=rec,
                            priority=1 if rec['type'] == 'practice_exam' else 2
                        )
                        db.session.add(study_rec)

                db.session.commit()
                print(f"Generated recommendations for student {student.id}")

            except Exception as e:
                print(f"Error generating recommendations for student {student.id}: {e}")
                db.session.rollback()


def send_study_reminders():
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    with app.app_context():
        cutoff_date = datetime.now() - timedelta(days=3)
        inactive_students = db.session.query(Student).join(User).filter(
            Student.id.in_(
                db.session.query(ExamResult.student_id).filter(
                    ExamResult.taken_exam < cutoff_date
                ).group_by(ExamResult.student_id).having(
                    db.func.max(ExamResult.taken_exam) < cutoff_date
                )
            )
        ).all()
        
        for student in inactive_students:
            try:
                user = student.user
                if user.email:
                    send_reminder_email.delay(user.email, user.name)
                    print(f"Sent reminder to {user.email}")

            except Exception as e:
                print(f"Error sending reminder to student {student.id}: {e}")


def send_reminder_email(email, name):
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    try:
        if not all([app.config.get('MAIL_USERNAME'), app.config.get('MAIL_PASSWORD'), 
                   app.config.get('MAIL_SERVER'), app.config.get('MAIL_PORT')]):
            print("Email configuration missing")
            return False
            
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = email
        msg['Subject'] = 'Đã lâu rồi bạn không học! - LmaoQuiz'

        base_url = app.config.get('BASE_URL', 'http://localhost:5000')
        body = f"""
        <html>
        <body>
            <h2>Xin chào {name}!</h2>
            <p>Chúng tôi nhận thấy bạn đã không hoạt động trên LmaoQuiz trong một thời gian.</p>

            <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>🎯 Hãy tiếp tục hành trình học tập của bạn:</h3>
                <ul>
                    <li>📚 Làm thêm đề thi mới</li>
                    <li>💡 Xem đề xuất học tập cá nhân</li>
                    <li>📊 Theo dõi tiến độ học tập</li>
                </ul>
            </div>

            <p><a href="{base_url}" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Tiếp tục học tập</a></p>

            <p>Chúc bạn học tập hiệu quả!</p>
            <p>Đội ngũ LmaoQuiz</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def analyze_learning_patterns():
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    with app.app_context():
        students = db.session.query(Student).all()
        for student in students:
            try:
                analysis = recommendation_engine.analyze_student_performance(student.id)
                if analysis:
                    update_learning_path.delay(student.id, analysis)
                    if analysis.get('improvement_trend') == 'declining':
                        send_motivation_message.delay(student.user_id)
            except Exception as e:
                print(f"Error analyzing patterns for student {student.id}: {e}")


def update_learning_path(student_id, analysis):
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    with app.app_context():
        try:
            worst_subject = analysis.get('worst_subject')
            if not worst_subject:
                return

            subject = db.session.query(Subject).filter(Subject.subject_name == worst_subject).first()
            if not subject:
                return

            learning_path = db.session.query(LearningPath).filter(LearningPath.student_id == student_id, LearningPath.subject_id == subject.id).first()
            if not learning_path:
                learning_path = LearningPath(student_id=student_id, subject_id=subject.id)
                db.session.add(learning_path)

            avg_score = analysis.get('average_score', 0)
            if avg_score < 50:
                learning_path.current_level = 'beginner'
                learning_path.estimated_completion_days = 30
            elif avg_score < 75:
                learning_path.current_level = 'intermediate'
                learning_path.estimated_completion_days = 20
            else:
                learning_path.current_level = 'advanced'
                learning_path.estimated_completion_days = 10

            total_exams = analysis.get('total_exams', 0)
            subject_exams = db.session.query(Exam).filter(Exam.subject_id == subject.id).count()
            if subject_exams > 0:
                learning_path.progress_percentage = min(100, (total_exams / subject_exams) * 100)

            db.session.commit()
            print(f"Updated learning path for student {student_id}")

        except Exception as e:
            print(f"Error updating learning path: {e}")
            db.session.rollback()


def send_motivation_message(user_id):
    motivation_messages = [
        "💪 Đừng bỏ cuộc! Mỗi thất bại là một bước tiến!",
        "🌟 Bạn đang tiến bộ, hãy kiên trì nhé!",
        "📚 Thành công đến từ sự kiên trì. Tiếp tục cố gắng!",
        "🎯 Tập trung vào những gì bạn có thể cải thiện!"
    ]

    message = random.choice(motivation_messages)

    # Gửi qua WebSocket nếu user online
    # Hoặc lưu vào database để hiển thị khi user login

    print(f"Sent motivation message to user {user_id}: {message}")


def cleanup_old_sessions():
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    with app.app_context():
        try:
            cutoff_date = datetime.now() - timedelta(days=7)

            old_sessions = db.session.query(ExamSession).filter(ExamSession.start_time < cutoff_date, ExamSession.is_completed == True).all()
            for session in old_sessions:
                db.session.delete(session)

            db.session.commit()
            print(f"Cleaned up {len(old_sessions)} old sessions")

        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            db.session.rollback()


def process_exam_analytics():
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    with app.app_context():
        try:
            exams = db.session.query(Exam).all()
            for exam in exams:
                results = db.session.query(ExamResult).filter(ExamResult.exam_id == exam.id).all()

                if len(results) >= 5:
                    avg_score = sum(r.score for r in results) / len(results)

                    for result in results:
                        if not result.difficulty_level:
                            if avg_score >= 80:
                                result.difficulty_level = 'easy'
                            elif avg_score >= 60:
                                result.difficulty_level = 'medium'
                            else:
                                result.difficulty_level = 'hard'

                    for result in results:
                        if result.time_taken and result.time_taken > 0:
                            result.time_efficiency = result.score / (result.time_taken / 60)

            db.session.commit()
            print("Updated exam analytics")

        except Exception as e:
            print(f"Error processing analytics: {e}")
            db.session.rollback()


def sync_external_resources():
    try:
        sync_google_books_data.delay()
        sync_youtube_educational_content.delay()
    except Exception as e:
        print(f"Error syncing external resources: {e}")


def sync_google_books_data():
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    subjects = ['toán học', 'ngữ văn', 'tiếng anh', 'vật lý', 'hóa học', 'sinh học']

    for subject in subjects:
        try:
            api_key = app.config.get('GOOGLE_BOOKS_API_KEY')

            url = f"https://www.googleapis.com/books/v1/volumes?q={subject}+giáo+trình&maxResults=10&key={api_key}"
            response = requests.get(url)

            if response.status_code == 200:
                books = response.json().get('items', [])

                # Lưu vào cache hoặc database
                cache_key = f"books_{subject}"
                # Redis cache implementation
                # redis_client.setex(cache_key, 86400, json.dumps(books))  # Cache 1 ngày

                print(f"Synced {len(books)} books for {subject}")
        except Exception as e:
            print(f"Error syncing books for {subject}: {e}")


def sync_youtube_educational_content():
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    try:
        youtube_api_key = app.config.get('YOUTUBE_API_KEY')
            
        youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        subjects = ['toán học', 'ngữ văn', 'tiếng anh', 'vật lý', 'hóa học']

        for subject in subjects:
            search_response = youtube.search().list(
                q=f"{subject} bài giảng",
                part='snippet',
                type='video',
                maxResults=5,
                videoDuration='medium',
                order='relevance'
            ).execute()

            videos = search_response.get('items', [])

            # Cache videos
            cache_key = f"videos_{subject}"
            # redis_client.setex(cache_key, 86400, json.dumps(videos))

            print(f"Synced {len(videos)} videos for {subject}")

    except Exception as e:
        print(f"Error syncing YouTube content: {e}")


def generate_personalized_study_plan(student_id):
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    with app.app_context():
        try:
            student = db.session.query(Student).get(student_id)
            if not student:
                return

            analysis = recommendation_engine.analyze_student_performance(student_id)
            if not analysis:
                return

            study_plan = {
                'student_id': student_id,
                'created_at': datetime.now().isoformat(),
                'duration_weeks': 4,
                'weekly_goals': [],
                'daily_targets': {},
                'recommended_exams': [],
                'focus_areas': analysis.get('weak_areas', [])
            }

            current_avg = analysis.get('average_score', 0)
            target_improvement = min(20, 80 - current_avg)  # Cải thiện tối đa 20 điểm

            for week in range(1, 5):
                weekly_goal = {
                    'week': week,
                    'target_score': current_avg + (target_improvement * week / 4),
                    'recommended_exams': 3,
                    'study_hours': 5 + week,
                    'focus_subject': analysis.get('worst_subject')
                }
                study_plan['weekly_goals'].append(weekly_goal)

            # Lưu study plan
            cache_key = f"study_plan_{student_id}"
            # redis_client.setex(cache_key, 2592000, json.dumps(study_plan))  # Cache 30 ngày

            print(f"Generated study plan for student {student_id}")
            return study_plan

        except Exception as e:
            print(f"Error generating study plan: {e}")
            return None


def send_weekly_progress_report(student_id):
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    with app.app_context():
        try:
            student = db.session.query(Student).get(student_id)
            if not student:
                return

            week_ago = datetime.now() - timedelta(days=7)
            weekly_results = db.session.query(ExamResult).filter(ExamResult.student_id == student_id, ExamResult.taken_exam >= week_ago).all()

            if not weekly_results:
                return

            total_exams = len(weekly_results)
            avg_score = sum(r.score for r in weekly_results) / total_exams
            total_time = sum(r.time_taken for r in weekly_results if r.time_taken)

            report = {
                'week_range': f"{week_ago.strftime('%d/%m')} - {datetime.now().strftime('%d/%m')}",
                'total_exams': total_exams,
                'average_score': round(avg_score, 1),
                'total_time_hours': round(total_time / 3600, 1),
                'subjects_practiced': list(set([r.exam.subject.subject_name for r in weekly_results])),
                'improvement': 'positive' if avg_score > 70 else 'needs_work'
            }

            send_progress_report_email.delay(student.user.email, student.user.name, report)

        except Exception as e:
            print(f"Error sending progress report: {e}")


def send_progress_report_email(email, name, report):
    app, db, User, Student, ExamResult, StudyRecommendation, LearningPath, ExamSession, Subject, Exam, recommendation_engine = get_app_context()
    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = email
        msg['Subject'] = f'Báo cáo tiến độ tuần ({report["week_range"]}) - LmaoQuiz'

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #007bff;">📊 Báo cáo tiến độ học tập</h2>
                <p>Xin chào <strong>{name}</strong>!</p>

                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>🎯 Thành tích tuần này ({report['week_range']}):</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 10px 0;">📝 <strong>{report['total_exams']}</strong> bài thi đã hoàn thành</li>
                        <li style="margin: 10px 0;">📈 Điểm trung bình: <strong>{report['average_score']}</strong></li>
                        <li style="margin: 10px 0;">⏰ Tổng thời gian học: <strong>{report['total_time_hours']}</strong> giờ</li>
                        <li style="margin: 10px 0;">📚 Môn học đã luyện tập: <strong>{', '.join(report['subjects_practiced'])}</strong></li>
                    </ul>
                </div>

                {"<div style='color: green;'>🎉 Tuyệt vời! Bạn đang có tiến bộ rất tốt!</div>" if report['improvement'] == 'positive' else "<div style='color: orange;'>💪 Hãy cố gắng thêm để đạt kết quả tốt hơn!</div>"}

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{app.config.get('BASE_URL', '#')}/recommendations" 
                       style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
                        Xem đề xuất học tập
                    </a>
                </div>

                <p>Tiếp tục cố gắng và chúc bạn học tập hiệu quả!</p>
                <p><em>Đội ngũ LmaoQuiz</em></p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()

        print(f"Sent progress report to {email}")
        return True

    except Exception as e:
        print(f"Error sending progress report email: {e}")
        return False


# Function để đăng ký tất cả các task với celery instance
def register_celery_tasks(celery_instance):
    global celery
    celery = celery_instance

    # Đăng ký các task
    celery.task(generate_daily_recommendations)
    celery.task(send_study_reminders)
    celery.task(send_reminder_email)
    celery.task(analyze_learning_patterns)
    celery.task(update_learning_path)
    celery.task(send_motivation_message)
    celery.task(cleanup_old_sessions)
    celery.task(process_exam_analytics)
    celery.task(sync_external_resources)
    celery.task(sync_google_books_data)
    celery.task(sync_youtube_educational_content)
    celery.task(generate_personalized_study_plan)
    celery.task(send_weekly_progress_report)
    celery.task(send_progress_report_email)
    
    # Cấu hình beat schedule
    configure_beat_schedule(celery_instance)