import hashlib
from datetime import datetime
from urllib import request
from urllib.parse import urlparse, urljoin
from flask import session
from sqlalchemy import or_
from app.models import User, Student, Admin, Exam, Subject, ExamResult, Question, Answer, ExamQuestions
from app import db, utils


def auth_user(username, password, role=None):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())

    u = User.query.filter(User.username.__eq__(username),
                          User.password.__eq__(password))
    if role:
        u = u.filter(User.role.__eq__(role))

    return u.first()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def existence_check(table, attribute, value):
    return table.query.filter(getattr(table, attribute).__eq__(value)).first()


def add_user(name, username, password, email, gender):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = User(name=name, username=username, password=password, email=email, gender=gender)
    db.session.add(user)
    db.session.commit()


def add_student(user):
    student = Student(user_id=user.id)
    db.session.add(student)
    db.session.commit()


def add_admin(user):
    admin = Admin(user_id=user.id)
    db.session.add(admin)
    db.session.commit()


def check_email_exists(email, exclude_user_id=None):
    query = get_user_by_email(email)
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    return query is not None


def get_exams_with_pagination(page=1, per_page=6, search_query=None):
    query = db.session.query(Exam).join(Subject)

    if search_query:
        query = query.filter(
            or_(
                Exam.exam_name.contains(search_query),
                Subject.subject_name.contains(search_query)
            )
        )

    # Sắp xếp theo thời gian tạo mới nhất
    query = query.order_by(Exam.createAt.desc())

    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


def get_exam_by_id(exam_id):
    return Exam.query.get(exam_id)


def get_all_subjects_with_exams(search_query=None):
    subjects = db.session.query(Subject).all()
    subjects_with_exams = []

    for subject in subjects:
        exams_query = db.session.query(Exam).filter_by(subject_id=subject.id)

        if search_query:
            exams_query = exams_query.filter(Exam.exam_name.contains(search_query))

        exams = exams_query.order_by(Exam.createAt.desc()).all()
        exams_with_stats = []

        for exam in exams:
            stats = utils.get_exam_stats(exam.id)
            question_count = utils.count_exam_questions(exam.id)
            exams_with_stats.append({
                'exam': exam,
                'stats': stats,
                'question_count': question_count
            })

        if not search_query or exams:
            subjects_with_exams.append({
                'subject': subject,
                'exams': exams_with_stats,
                'exam_count': len(exams)
            })

    if search_query:
        matching_subjects = db.session.query(Subject).filter(
            Subject.subject_name.contains(search_query)
        ).all()

        for subject in matching_subjects:
            already_added = any(s['subject'].id == subject.id for s in subjects_with_exams)

            if not already_added:
                exams = db.session.query(Exam).filter_by(subject_id=subject.id).order_by(Exam.createAt.desc()).all()
                exams_with_stats = []

                for exam in exams:
                    stats = utils.get_exam_stats(exam.id)
                    question_count = utils.count_exam_questions(exam.id)
                    exams_with_stats.append({
                        'exam': exam,
                        'stats': stats,
                        'question_count': question_count
                    })

                subjects_with_exams.append({
                    'subject': subject,
                    'exams': exams_with_stats,
                    'exam_count': len(exams)
                })

    return subjects_with_exams


def get_subject_by_id(subject_id):
    return Subject.query.get(subject_id)


def get_student_by_user_id(user_id):
    return Student.query.filter_by(user_id=user_id).first()

def get_exam_result_by_id(result_id):
    return ExamResult.query.get(result_id)


def get_exam_questions_with_answers(exam_id):
    try:
        questions = db.session.query(Question).join(
            ExamQuestions, Question.id == ExamQuestions.question_id
        ).filter(
            ExamQuestions.exam_id == exam_id
        ).order_by(Question.id).all()

        result = []
        for question in questions:
            answers = db.session.query(Answer).filter(
                Answer.question_id == question.id
            ).order_by(Answer.id).all()

            question_data = {
                'id': question.id,
                'question_title': question.question_title,
                'answers': [{
                    'id': answer.id,
                    'answer_text': answer.answer_text,
                    'is_correct': answer.is_correct
                } for answer in answers]
            }

            result.append(question_data)

        return result
    except Exception as e:
        print(f"Lỗi khi lấy câu hỏi: {e}")
        return []


def get_exam_questions_count(exam_id):
    try:
        count = db.session.query(Question).join(
            ExamQuestions, Question.id == ExamQuestions.question_id
        ).filter(ExamQuestions.exam_id == exam_id).count()

        return count
    except Exception as e:
        print(f"Lỗi khi đếm câu hỏi: {e}")
        return 0


def get_student_exam_result(student_id, exam_id):
    try:
        result = db.session.query(ExamResult).filter(
            ExamResult.student_id == student_id,
            ExamResult.exam_id == exam_id
        ).first()

        return result

    except Exception as e:
        print(f"Lỗi khi lấy kết quả: {e}")
        return None


def get_remaining_time(user_id, exam_id, exam_duration_minutes):
    try:
        session_key = f'exam_{exam_id}_start_time'

        if session_key not in session:
            return exam_duration_minutes * 60

        start_time = session[session_key]
        current_time = datetime.now().timestamp()
        elapsed_seconds = int(current_time - start_time)
        total_seconds = exam_duration_minutes * 60
        remaining_seconds = max(0, total_seconds - elapsed_seconds)

        return remaining_seconds
    except Exception as e:
        print(f"Lỗi khi tính thời gian còn lại: {e}")
        return exam_duration_minutes * 60


def get_exam_history_with_pagination(student_id, page=1, per_page=10, search_query=None, selected_subject=None, score_filter=None):
    query = db.session.query(ExamResult).join(Exam).join(Subject).filter(
        ExamResult.student_id == student_id
    )

    if search_query and search_query.strip():
        query = query.filter(
            or_(
                Exam.exam_name.contains(search_query.strip()),
                Subject.subject_name.contains(search_query.strip())
            )
        )

    if selected_subject:
        query = query.filter(Subject.id == selected_subject)

    if score_filter:
        if score_filter == 'excellent':
            query = query.filter(ExamResult.score >= 80)
        elif score_filter == 'good':
            query = query.filter(ExamResult.score >= 65, ExamResult.score < 80)
        elif score_filter == 'average':
            query = query.filter(ExamResult.score >= 50, ExamResult.score < 65)
        elif score_filter == 'poor':
            query = query.filter(ExamResult.score < 50)

    query = query.order_by(ExamResult.taken_exam.desc())

    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def get_all_subjects():
    return db.session.query(Subject).all()


def get_exam_result_with_details(result_id, student_id=None):
    try:
        query = db.session.query(ExamResult).filter(ExamResult.id == result_id)

        if student_id:
            query = query.filter(ExamResult.student_id == student_id)

        result = query.first()

        if not result:
            return None

        questions_with_answers = get_exam_questions_with_user_answers(result.exam_id, result.id)

        return {
            'result': result,
            'questions_with_answers': questions_with_answers
        }

    except Exception as e:
        print(f"Lỗi khi lấy kết quả chi tiết: {e}")
        return None


def get_exam_questions_with_user_answers(exam_id, result_id):
    try:
        result = db.session.query(ExamResult).get(result_id)
        if not result:
            return []

        user_answers = {}
        if hasattr(result, 'user_answers') and result.user_answers:
            user_answers = result.user_answers

        query = db.session.query(
            Question,
            Answer
        ).join(
            ExamQuestions, Question.id == ExamQuestions.question_id
        ).join(
            Answer, Question.id == Answer.question_id
        ).filter(
            ExamQuestions.exam_id == exam_id
        ).order_by(Question.id, Answer.id).all()

        questions_dict = {}
        for question, answer in query:
            if question.id not in questions_dict:
                user_answer_id = user_answers.get(str(question.id))
                correct_answer = None

                for q, a in query:
                    if q.id == question.id and a.is_correct:
                        correct_answer = a
                        break

                questions_dict[question.id] = {
                    'question': question,
                    'answers': [],
                    'user_answer_id': int(user_answer_id) if user_answer_id else None,
                    'correct_answer_id': correct_answer.id if correct_answer else None,
                    'is_correct': (int(user_answer_id) == correct_answer.id) if (
                                user_answer_id and correct_answer) else False
                }

            questions_dict[question.id]['answers'].append(answer)

        return list(questions_dict.values())

    except Exception as e:
        print(f"Lỗi khi lấy câu hỏi với câu trả lời: {e}")
        return []


def get_user_answer_for_result(result_id):
    try:
        result = db.session.query(ExamResult).get(result_id)
        if result and hasattr(result, 'user_answers'):
            return result.user_answers
        return {}
    except Exception as e:
        print(f"Lỗi khi lấy câu trả lời user: {e}")
        return {}