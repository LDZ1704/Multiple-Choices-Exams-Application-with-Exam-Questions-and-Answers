import random
import string
import cloudinary
import cloudinary.uploader
import hashlib
from flask import session, flash
from app import app, db, dao
from app.models import User, ExamResult, ExamQuestions, Exam, Comment, Student, Question, Answer, ExamSession, \
    SuspiciousActivity, Notification
from datetime import datetime
from notification_service import NotificationService


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
        if not user:
            return False

        user.name = name
        user.username = username
        user.email = email
        user.gender = gender
        user.updateAt = datetime.now()
        db.session.commit()
        return True
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


def save_exam_result(student_id, exam_id, score, answers, time_taken_seconds):
    try:
        existing_result = ExamResult.query.filter_by(student_id=student_id, exam_id=exam_id).first()
        is_first_attempt = existing_result is None

        student = db.session.query(Student).get(student_id)
        exam = dao.get_exam_by_id(exam_id)

        student_name = None
        exam_name = None

        if student and student.user:
            student_name = student.user.name
        if exam:
            exam_name = exam.exam_name

        exam_result = ExamResult(
            student_id=student_id,
            exam_id=exam_id,
            student_name=student_name,
            exam_name=exam_name,
            score=score,
            taken_exam=datetime.now(),
            time_taken=time_taken_seconds,
            user_answers=answers, #Lưu câu trả lời của user dưới dạng JSON
            is_first_attempt=is_first_attempt
        )

        db.session.add(exam_result)
        db.session.commit()
        NotificationService.send_exam_result_notification(student_id, exam_id, score)
        dao.check_milestone_achievement(student_id)
        if score < 40:
            NotificationService.send_improvement_suggestion(student_id)

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


def create_exam(creator_id, exam_name, subject_id, duration, questions_data):
    try:
        user = dao.get_user_by_id(creator_id)

        exam = Exam(
            exam_name=exam_name,
            subject_id=subject_id,
            duration=duration,
            user_id=creator_id,
            createBy=user.name,
            createAt=datetime.now()
        )
        db.session.add(exam)
        db.session.flush()

        if exam.id:
            dao.create_exam_notification(exam.id)

        for question_data in questions_data:
            question = Question(
                question_title=question_data['question_title'],
                chapter_id=1, #default
                createBy=user.name,
                createAt=datetime.now()
            )
            db.session.add(question)
            db.session.flush()

            for answer_data in question_data['answers']:
                answer = Answer(
                    question_id=question.id,
                    answer_text=answer_data['answer_text'],
                    is_correct=answer_data['is_correct'],
                    createBy=user.name
                )
                db.session.add(answer)

            exam_question = ExamQuestions(
                exam_id=exam.id,
                question_id=question.id
            )
            db.session.add(exam_question)
        db.session.commit()
        return exam.id

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi tạo đề thi: {e}")
        return None


def update_exam(exam_id, creator_id, exam_name, subject_id, duration, questions_data):
    try:
        exam = db.session.query(Exam).filter(
            Exam.id == exam_id,
            Exam.user_id == creator_id
        ).first()

        if not exam:
            return False

        user = dao.get_user_by_id(creator_id)

        exam.exam_name = exam_name
        exam.subject_id = subject_id
        exam.duration = duration

        old_exam_questions = db.session.query(ExamQuestions).filter(
            ExamQuestions.exam_id == exam_id
        ).all()

        question_ids = [eq.question_id for eq in old_exam_questions]

        for eq in old_exam_questions:
            db.session.delete(eq)

        for question_id in question_ids:
            db.session.query(Answer).filter(Answer.question_id == question_id).delete()

        for question_id in question_ids:
            db.session.query(Question).filter(Question.id == question_id).delete()

        for question_data in questions_data:
            question = Question(
                question_title=question_data['question_title'],
                chapter_id=1,  #Default
                createBy=user.name,
                createAt=datetime.now()
            )
            db.session.add(question)
            db.session.flush()

            for answer_data in question_data['answers']:
                answer = Answer(
                    question_id=question.id,
                    answer_text=answer_data['answer_text'],
                    is_correct=answer_data['is_correct'],
                    createBy=user.name
                )
                db.session.add(answer)

            exam_question = ExamQuestions(
                exam_id=exam.id,
                question_id=question.id
            )
            db.session.add(exam_question)

        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi cập nhật đề thi: {e}")
        return False


def delete_user_exam(exam_id, creator_id):
    try:
        exam = db.session.query(Exam).filter(Exam.id == exam_id, Exam.user_id == creator_id).first()

        if not exam:
            return False

        db.session.query(Notification).filter(Notification.exam_id == exam_id).delete()
        db.session.query(ExamSession).filter(ExamSession.exam_id == exam_id).delete()
        db.session.query(SuspiciousActivity).filter(SuspiciousActivity.exam_id == exam_id).delete()
        db.session.query(ExamResult).filter(ExamResult.exam_id == exam_id).delete()
        db.session.query(Comment).filter(Comment.exam_id == exam_id).delete()
        exam_questions = db.session.query(ExamQuestions).filter(ExamQuestions.exam_id == exam_id).all()
        question_ids = [eq.question_id for eq in exam_questions]

        for eq in exam_questions:
            db.session.delete(eq)
        for question_id in question_ids:
            db.session.query(Answer).filter(Answer.question_id == question_id).delete()
        for question_id in question_ids:
            db.session.query(Question).filter(Question.id == question_id).delete()

        db.session.delete(exam)
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi xóa đề thi: {e}")
        return False


def create_random_exam(creator_id, exam_name, subject_id, duration, question_count):
    try:
        user = dao.get_user_by_id(creator_id)

        available_questions_count = dao.get_questions_count_by_subject(subject_id)
        if available_questions_count < question_count:
            flash(f"Môn học này chỉ có {available_questions_count} câu hỏi. Vui lòng chọn số câu hỏi nhỏ hơn.", 'error')
            return None

        exam = Exam(
            exam_name=exam_name,
            subject_id=subject_id,
            duration=duration,
            user_id=creator_id,
            createBy=user.name,
            createAt=datetime.now()
        )
        db.session.add(exam)
        db.session.flush()

        random_questions = dao.get_random_questions_by_subject(subject_id, question_count)

        for question in random_questions:
            answers = dao.get_answers_by_question_id(question.id)
            exam_question = ExamQuestions(
                exam_id=exam.id,
                question_id=question.id
            )
            db.session.add(exam_question)

        db.session.commit()
        return exam.id, None

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi tạo đề thi ngẫu nhiên: {e}")
        return None, "Có lỗi xảy ra khi tạo đề thi ngẫu nhiên"


def create_exam_session(student_id, exam_id):
    try:
        questions = dao.get_exam_questions_with_answers(exam_id)

        question_ids = [q['id'] for q in questions]
        random.shuffle(question_ids)

        answer_orders = {}
        for question in questions:
            answer_ids = [answer['id'] for answer in question['answers']]
            random.shuffle(answer_ids)
            answer_orders[str(question['id'])] = answer_ids

        session_obj = ExamSession(
            student_id=student_id,
            exam_id=exam_id,
            current_question_index=0,
            user_answers={},
            question_order=question_ids,
            answer_orders=answer_orders,
            is_paused=False,
            is_completed=False
        )

        db.session.add(session_obj)
        db.session.commit()
        return session_obj

    except Exception as e:
        print(f"Error creating exam session: {e}")
        db.session.rollback()
        return None


def update_exam_session(session_obj, current_question_index=None, user_answers=None, is_paused=None):
    try:
        if current_question_index is not None:
            session_obj.current_question_index = current_question_index
        if user_answers is not None:
            session_obj.user_answers = user_answers
        if is_paused is not None:
            session_obj.is_paused = is_paused
            if is_paused:
                session_obj.pause_time = datetime.now()
            else:
                if session_obj.pause_time:
                    pause_duration = (datetime.now() - session_obj.pause_time).total_seconds()
                    session_obj.total_paused_duration += int(pause_duration)
                session_obj.resume_time = datetime.now()

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi cập nhật exam session: {e}")
        return False


def complete_exam_session(session_obj):
    try:
        session_obj.is_completed = True
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi hoàn thành exam session: {e}")
        return False


def start_exam_session_db(student_id, exam_id):
    try:
        existing_session = dao.get_exam_session(student_id, exam_id)
        if existing_session:
            return existing_session

        return create_exam_session(student_id, exam_id)
    except Exception as e:
        print(f"Lỗi start exam session: {e}")
        return None


def pause_exam_session(student_id, exam_id, current_question_index, user_answers):
    try:
        session_obj = dao.get_exam_session(student_id, exam_id)
        if session_obj and not session_obj.is_paused:
            return update_exam_session(session_obj, current_question_index=current_question_index, user_answers=user_answers, is_paused=True)
        return False
    except Exception as e:
        print(f"Lỗi pause session: {e}")
        return False


def resume_exam_session(student_id, exam_id):
    try:
        session_obj = dao.get_exam_session(student_id, exam_id)
        if session_obj and session_obj.is_paused:
            return update_exam_session(session_obj, is_paused=False)
        return False
    except Exception as e:
        print(f"Lỗi resume session: {e}")
        return False


def reset_exam_session(student_id, exam_id):
    try:
        existing_session = dao.get_exam_session(student_id, exam_id)
        if existing_session and not existing_session.is_completed:
            db.session.delete(existing_session)
            db.session.commit()
            return True
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi reset exam session: {e}")
        return False


def save_exam_progress(student_id, exam_id, current_question_index, user_answers):
    try:
        session_obj = dao.get_exam_session(student_id, exam_id)
        if session_obj:
            return update_exam_session(session_obj, current_question_index=current_question_index, user_answers=user_answers)
        return False
    except Exception as e:
        print(f"Lỗi save progress: {e}")
        return False


def get_highest_score(user_id, exam_id):
    student = dao.get_student_by_user_id(user_id)
    if not student:
        return 0

    highest_result = db.session.query(ExamResult).filter(ExamResult.student_id == student.id, ExamResult.exam_id == exam_id).order_by(ExamResult.score.desc()).first()

    return highest_result.score if highest_result else 0


def get_ordered_questions_for_session(exam_id, question_order, answer_orders):
    try:
        original_questions = dao.get_exam_questions_with_answers(exam_id)

        questions_dict = {q['id']: q for q in original_questions}

        ordered_questions = []
        for question_id in question_order:
            if question_id in questions_dict:
                question = questions_dict[question_id].copy()

                if str(question_id) in answer_orders:
                    answer_order = answer_orders[str(question_id)]
                    answers_dict = {a['id']: a for a in question['answers']}
                    ordered_answers = []

                    for answer_id in answer_order:
                        if answer_id in answers_dict:
                            ordered_answers.append(answers_dict[answer_id])

                    question['answers'] = ordered_answers

                ordered_questions.append(question)

        return ordered_questions

    except Exception as e:
        print(f"Error getting ordered questions: {e}")
        return []


