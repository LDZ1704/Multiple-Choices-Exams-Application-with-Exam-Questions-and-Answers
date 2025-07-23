import random
import string
import cloudinary
import cloudinary.uploader
import hashlib
from flask import session
from app import app, db, dao
from app.models import User, ExamResult, ExamQuestions, Exam, Comment, Student, Question, Answer
from datetime import datetime


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def update_password(user_id, new_password):
    user = User.query.get(user_id)
    if user:
        user.password = str(hashlib.md5(new_password.encode('utf-8')).hexdigest())
        user.updateAt = datetime.now()
        db.session.commit()
        return True
    return False


def update_user_info(user_id, username, name, email, gender):
    try:
        user = dao.get_user_by_id(user_id)
        if user:
            user.name = name
            user.username = username
            user.email = email
            user.gender = gender
            user.updateAt = datetime.now()
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi cập nhật thông tin: {e}")
        return False


def update_user_avatar(user_id, avatar_url):
    try:
        user = dao.get_user_by_id(user_id)
        if user:
            user.avatar = avatar_url
            user.updateAt = datetime.now()
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi cập nhật avatar: {e}")
        return False


def upload_avatar_to_cloudinary(file):
    try:
        result = cloudinary.uploader.upload(
            file,
            folder="avatars",
            transformation=[
                {"width": 200, "height": 200, "crop": "fill"},
                {"quality": "auto"},
                {"fetch_format": "auto"}
            ]
        )
        return result['secure_url']
    except Exception as e:
        print(f"Lỗi upload ảnh: {e}")
        return None


def count_exam_questions(exam_id):
    return db.session.query(ExamQuestions).filter_by(exam_id=exam_id).count()


def get_exam_stats(exam_id):
    results = db.session.query(ExamResult).filter_by(exam_id=exam_id).all()

    total_attempts = len(results)
    avg_score = sum(result.score for result in results) / total_attempts if total_attempts > 0 else 0

    return {
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1)
    }


def get_exam_comments_with_pagination(exam_id, page=1, per_page=5):
    query = db.session.query(Comment).join(User).filter(
        Comment.exam_id == exam_id
    ).order_by(Comment.created_at.desc())

    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


def get_user_exam_results(user_id, exam_id):
    student = db.session.query(Student).filter(Student.user_id == user_id).first()
    if not student:
        return []

    results = db.session.query(ExamResult).filter(
        ExamResult.student_id == student.id,
        ExamResult.exam_id == exam_id
    ).order_by(ExamResult.taken_exam.desc()).all()

    return results


def add_exam_comment(user_id, exam_id, content):
    try:
        comment = Comment(
            user_id=user_id,
            exam_id=exam_id,
            content=content,
            created_at=datetime.now()
        )

        db.session.add(comment)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi thêm đánh giá: {e}")
        return False


def calculate_exam_score(exam_id, user_answers):
    try:
        total_questions = 0
        correct_answers = 0

        questions = db.session.query(Question).join(
            ExamQuestions, Question.id == ExamQuestions.question_id
        ).filter(ExamQuestions.exam_id == exam_id).all()

        for question in questions:
            total_questions += 1

            correct_answer = db.session.query(Answer).filter(
                Answer.question_id == question.id,
                Answer.is_correct == True
            ).first()

            user_answer_id = user_answers.get(str(question.id))
            if user_answer_id and correct_answer and int(user_answer_id) == correct_answer.id:
                correct_answers += 1

        if total_questions == 0:
            return 0
        score = round((correct_answers / total_questions) * 100, 1)
        return score

    except Exception as e:
        print(f"Lỗi khi tính điểm: {e}")
        return 0


def save_exam_result(student_id, exam_id, score, answers, time_taken):
    try:
        exam_result = ExamResult(
            student_id=student_id,
            exam_id=exam_id,
            score=score,
            taken_exam=datetime.now(),
            user_answers=answers  #Lưu câu trả lời của user dưới dạng JSON
        )

        db.session.add(exam_result)
        db.session.commit()

        return exam_result.id

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi lưu kết quả: {e}")
        return None


def format_exam_duration(minutes):
    try:
        hours = minutes // 60
        mins = minutes % 60

        if hours > 0:
            return f"{hours}h{mins}m" if mins > 0 else f"{hours}h"
        else:
            return f"{mins}m"

    except Exception as e:
        return f"{minutes}m"


def start_exam_session(user_id, exam_id):
    try:
        session_key = f'exam_{exam_id}_start_time'

        if session_key not in session:
            session[session_key] = datetime.now().timestamp()
            session.permanent = True

        return session[session_key]
    except Exception as e:
        print(f"Lỗi khi bắt đầu exam session: {e}")
        return None


def clear_exam_session(user_id, exam_id):
    try:
        session_key = f'exam_{exam_id}_start_time'
        session.pop(session_key, None)
        return True
    except Exception as e:
        print(f"Lỗi khi xóa exam session: {e}")
        return False