import hashlib
from datetime import datetime, timedelta
from urllib import request
from urllib.parse import urlparse, urljoin
from flask import session
from sqlalchemy import or_
from app.models import User, Student, Admin, Exam, Subject, ExamResult, Question, Answer, ExamQuestions, Comment, \
    Chapter, ExamSession, SuspiciousActivity, Rating
from app import db, utils
from sqlalchemy import func, desc, asc, and_
from notification_service import NotificationService


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
    return query.first() is not None


def get_exams_with_pagination(page=1, per_page=6, search_query=None):
    query = db.session.query(Exam).join(Subject)
    if search_query:
        query = query.filter(
            or_(
                Exam.exam_name.contains(search_query),
                Subject.subject_name.contains(search_query)
            )
        )
    query = query.order_by(Exam.createAt.desc())
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


def get_exam_by_id(exam_id):
    return Exam.query.get(exam_id)


def count_exams_by_subject(subject_id):
    return Exam.query.filter_by(subject_id=subject_id).count()


def get_all_subjects_with_exams(search_query=None, sort_by='name', filter_has_exam=''):
    query = db.session.query(Subject).outerjoin(Exam)

    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(or_(Subject.subject_name.ilike(search_pattern), Exam.exam_name.ilike(search_pattern)))

    query = query.group_by(Subject.id)

    if filter_has_exam == 'yes':
        query = query.having(func.count(Exam.id) > 0)
    elif filter_has_exam == 'no':
        query = query.having(func.count(Exam.id) == 0)
    if sort_by == 'exam_count':
        query = query.order_by(desc(func.count(Exam.id)))
    elif sort_by == 'newest':
        query = query.order_by(desc(Subject.id))
    else:
        query = query.order_by(asc(Subject.subject_name))

    subjects = query.all()

    result = []
    for subject in subjects:
        exams_query = Exam.query.filter_by(subject_id=subject.id)

        if search_query:
            exams_query = exams_query.filter(Exam.exam_name.ilike(f"%{search_query}%"))

        exams = exams_query.order_by(desc(Exam.createAt)).limit(12).all()

        exam_data_list = []
        for exam in exams:
            stats = utils.get_exam_stats(exam.id)
            question_count = utils.count_exam_questions(exam.id)
            exam_data_list.append({
                'exam': exam,
                'stats': stats,
                'question_count': question_count
            })

        result.append({
            'subject': subject,
            'exams': exam_data_list,
            'exam_count': len(exams)
        })

    return result


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
        count = db.session.query(Question).join(ExamQuestions, Question.id == ExamQuestions.question_id).filter(ExamQuestions.exam_id == exam_id).count()
        return count
    except Exception as e:
        print(f"Lỗi khi đếm câu hỏi: {e}")
        return 0


def get_student_exam_result(student_id, exam_id):
    try:
        result = db.session.query(ExamResult).filter(ExamResult.student_id == student_id, ExamResult.exam_id == exam_id).order_by(ExamResult.taken_exam.desc()).first()
        return result

    except Exception as e:
        print(f"Lỗi khi lấy kết quả: {e}")
        return None


def get_student_exam_results(student_id):
    return db.session.query(ExamResult).join(Exam).join(Subject).filter(ExamResult.student_id == student_id).order_by(ExamResult.taken_exam).all()


def get_student_exam_results_by_exam(student_id, exam_id):
    return db.session.query(ExamResult).filter(ExamResult.student_id == student_id, ExamResult.exam_id == exam_id).order_by(ExamResult.taken_exam).all()


def get_exam_result_questions_analysis(result_id):
    try:
        result = get_exam_result_by_id(result_id)
        if not result:
            return []

        questions = get_exam_questions_with_answers(result.exam_id)
        if not questions:
            return []

        analysis = []
        for question in questions:
            try:
                user_answer_id = None
                if result.user_answers and str(question['id']) in result.user_answers:
                    user_answer_id = result.user_answers[str(question['id'])]

                correct_answer = next((a for a in question['answers'] if a['is_correct']), None)
                is_correct = False
                if user_answer_id and correct_answer:
                    try:
                        is_correct = int(user_answer_id) == correct_answer['id']
                    except (ValueError, TypeError):
                        is_correct = False

                analysis.append({
                    'question_id': question['id'],
                    'question_title': question['question_title'],
                    'is_correct': is_correct,
                    'user_answer_id': user_answer_id
                })
            except Exception as e:
                print(f"Error processing question {question.get('id', 'unknown')}: {e}")
                continue
        return analysis
    except Exception as e:
        print(f"Error in get_exam_result_questions_analysis: {e}")
        return []


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
    query = db.session.query(ExamResult).outerjoin(Exam).outerjoin(Subject).filter(ExamResult.student_id == student_id)

    if search_query and search_query.strip():
        query = query.filter(
            or_(
                ExamResult.exam_name.contains(search_query.strip()),
                Exam.exam_name.contains(search_query.strip()),
                Subject.subject_name.contains(search_query.strip())
            )
        )

    if selected_subject:
        query = query.filter(Subject.id == selected_subject)

    if score_filter:
        if score_filter == 'Giỏi':
            query = query.filter(ExamResult.score >= 80)
        elif score_filter == 'Khá':
            query = query.filter(ExamResult.score >= 65, ExamResult.score < 80)
        elif score_filter == 'Trung bình':
            query = query.filter(ExamResult.score >= 50, ExamResult.score < 65)
        elif score_filter == 'Yếu':
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
        result = (db.session.query(ExamResult).filter(ExamResult.id == result_id, ExamResult.student_id == student_id).first())
        if not result:
            return None

        if not result.exam:
            return {
                'result': result,
                'questions_with_answers': []
            }

        session_obj = (db.session.query(ExamSession)
                       .filter(ExamSession.student_id == student_id, ExamSession.exam_id == result.exam_id, ExamSession.is_completed == True)
                       .order_by(ExamSession.start_time.desc())
                       .first())

        if session_obj and session_obj.question_order and session_obj.answer_orders:
            questions_data = utils.get_ordered_questions_for_session(result.exam_id, session_obj.question_order, session_obj.answer_orders)
        else:
            questions_data = get_exam_questions_with_answers(result.exam_id)

        questions_with_answers = []
        user_answers = result.user_answers or {}

        for question_data in questions_data:
            user_answer_id = user_answers.get(str(question_data['id']))

            correct_answer = next((a for a in question_data['answers'] if a['is_correct']), None)
            is_correct = user_answer_id == correct_answer['id'] if correct_answer and user_answer_id else False

            questions_with_answers.append({
                'question': question_data,
                'answers': question_data['answers'],
                'user_answer_id': user_answer_id,
                'correct_answer_id': correct_answer['id'] if correct_answer else None,
                'is_correct': is_correct
            })

        return {
            'result': result,
            'questions_with_answers': questions_with_answers
        }

    except Exception as e:
        print(f"Error getting exam result: {e}")
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


def get_user_exam_for_edit(exam_id, creator_id):
    try:
        exam = db.session.query(Exam).filter(Exam.id == exam_id, Exam.user_id == creator_id).first()

        if not exam:
            return None

        questions_data = get_exam_questions_with_answers(exam_id)

        return {
            'exam': exam,
            'questions': questions_data
        }

    except Exception as e:
        print(f"Lỗi lấy đề thi để sửa: {e}")
        return None


def get_user_created_exams_with_pagination(creator_id, page=1, per_page=6, search_query=None):
    query = db.session.query(Exam).join(Subject).filter(Exam.user_id == creator_id)

    if search_query:
        query = query.filter(or_(Exam.exam_name.contains(search_query), Subject.subject_name.contains(search_query)))

    query = query.order_by(Exam.createAt.desc())

    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


def get_random_questions_by_subject(subject_id, limit=50):
    try:
        chapters = db.session.query(Chapter).filter(Chapter.subject_id == subject_id).all()
        chapter_ids = [chapter.id for chapter in chapters]

        if not chapter_ids:
            return []

        questions = db.session.query(Question).filter(Question.chapter_id.in_(chapter_ids)).order_by(db.func.random()).limit(limit).all()

        return questions
    except Exception as e:
        print(f"Lỗi lấy câu hỏi ngẫu nhiên: {e}")
        return []


def get_answers_by_question_id(question_id):
    try:
        answers = db.session.query(Answer).filter(
            Answer.question_id == question_id
        ).order_by(Answer.id).all()
        return answers
    except Exception as e:
        print(f"Lỗi lấy đáp án: {e}")
        return []


def get_questions_count_by_subject(subject_id):
    try:
        chapters = db.session.query(Chapter).filter(Chapter.subject_id == subject_id).all()
        chapter_ids = [chapter.id for chapter in chapters]

        if not chapter_ids:
            return 0

        count = db.session.query(Question).filter(
            Question.chapter_id.in_(chapter_ids)
        ).count()

        return count
    except Exception as e:
        print(f"Lỗi đếm câu hỏi: {e}")
        return 0


def get_exam_session(student_id, exam_id):
    return db.session.query(ExamSession).filter(ExamSession.student_id == student_id, ExamSession.exam_id == exam_id, ExamSession.is_completed == False).first()


def get_remaining_time_with_session(student_id, exam_id, exam_duration_minutes):
    try:
        session_obj = get_exam_session(student_id, exam_id)
        if not session_obj:
            return exam_duration_minutes * 60

        current_time = datetime.now()
        elapsed_time = (current_time - session_obj.start_time).total_seconds()

        if session_obj.is_paused and session_obj.pause_time:
            elapsed_time = (session_obj.pause_time - session_obj.start_time).total_seconds()

        elapsed_time -= session_obj.total_paused_duration

        total_seconds = exam_duration_minutes * 60
        remaining_seconds = max(0, total_seconds - int(elapsed_time))

        return remaining_seconds
    except Exception as e:
        print(f"Lỗi tính thời gian còn lại: {e}")
        return exam_duration_minutes * 60


def has_unfinished_exam_session(student_id, exam_id):
    try:
        session_obj = get_exam_session(student_id, exam_id)
        if session_obj and not session_obj.is_completed:
            has_progress = (session_obj.current_question_index > 0 or
                          (session_obj.user_answers and len(session_obj.user_answers) > 0))
            return has_progress
        return False
    except Exception as e:
        print(f"Lỗi kiểm tra session: {e}")
        return False


def has_exam_result(student_id, exam_id):
    try:
        result = db.session.query(ExamResult).filter(ExamResult.student_id == student_id, ExamResult.exam_id == exam_id).first()
        return result is not None
    except Exception as e:
        print(f"Lỗi khi kiểm tra kết quả: {e}")
        return False


def get_exam_ranking_with_pagination(exam_id, page=1, per_page=20):
    exam = get_exam_by_id(exam_id)
    if not exam:
        return None

    creator_user_id = exam.user_id

    query = db.session.query(
        ExamResult.id,
        ExamResult.student_id,
        ExamResult.score,
        ExamResult.taken_exam,
        ExamResult.time_taken,
        User.name,
        User.avatar,
        func.row_number().over(order_by=[ExamResult.score.desc(), ExamResult.taken_exam.asc()]).label('rank')
    ).select_from(ExamResult) \
        .outerjoin(Student, ExamResult.student_id == Student.id) \
        .outerjoin(User, Student.user_id == User.id) \
        .filter(
        and_(ExamResult.exam_id == exam_id, ExamResult.is_first_attempt == True, or_(User.id != creator_user_id, User.id.is_(None)))
    ).order_by(ExamResult.score.desc(), ExamResult.taken_exam.asc())

    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


def get_exam_highest_score(exam_id):
    exam = get_exam_by_id(exam_id)
    if not exam:
        return 0

    creator_user_id = exam.user_id

    result = db.session.query(func.max(ExamResult.score)) \
        .outerjoin(Student, ExamResult.student_id == Student.id) \
        .outerjoin(User, Student.user_id == User.id) \
        .filter(and_(ExamResult.exam_id == exam_id, ExamResult.is_first_attempt == True, or_(User.id != creator_user_id, User.id.is_(None)))).scalar()

    return result if result else 0


def count_exam_participants(exam_id):
    exam = get_exam_by_id(exam_id)
    if not exam:
        return 0

    creator_user_id = exam.user_id

    return db.session.query(ExamResult.student_id) \
        .outerjoin(Student, ExamResult.student_id == Student.id) \
        .outerjoin(User, Student.user_id == User.id) \
        .filter(and_(ExamResult.exam_id == exam_id, ExamResult.is_first_attempt == True, or_(User.id != creator_user_id, User.id.is_(None)))).distinct().count()


def get_exam_average_score(exam_id):
    exam = get_exam_by_id(exam_id)
    if not exam:
        return 0

    creator_user_id = exam.user_id
    result = db.session.query(func.avg(ExamResult.score)) \
        .outerjoin(Student, ExamResult.student_id == Student.id) \
        .outerjoin(User, Student.user_id == User.id) \
        .filter(and_(ExamResult.exam_id == exam_id, ExamResult.is_first_attempt == True, or_(User.id != creator_user_id, User.id.is_(None)))).scalar()
    return round(result, 1) if result else 0


def get_exams_by_subject_name(subject_name):
    return db.session.query(Exam).join(Subject).filter(Subject.subject_name.ilike(f'%{subject_name}%')).limit(10).all()


def search_exams_and_subjects(query):
    results = []
    exams = db.session.query(Exam).filter(or_(Exam.exam_name.ilike(f'%{query}%'), Exam.subject.has(Subject.subject_name.ilike(f'%{query}%')))).limit(5).all()
    for exam in exams:
        results.append({
            'name': exam.exam_name,
            'type': 'exam',
            'url': f'/examdetail?id={exam.id}'
        })

    subjects = db.session.query(Subject).filter(Subject.subject_name.ilike(f'%{query}%')).limit(3).all()
    for subject in subjects:
        results.append({
            'name': subject.subject_name,
            'type': 'subject',
            'url': f'/subjects?search={subject.subject_name}'
        })
    return results


def get_popular_exams(limit=5):
    return db.session.query(Exam).join(ExamResult).group_by(Exam.id).order_by(db.func.count(ExamResult.id).desc()).limit(limit).all()


def get_exam_results_by_exam_id(exam_id):
    return ExamResult.query.filter_by(exam_id=exam_id).all()


def get_total_students():
    return Student.query.count()


def get_total_exams():
    return Exam.query.count()

def get_total_exam_attempts():
    return ExamResult.query.count()


def get_average_score():
    result = db.session.query(func.avg(ExamResult.score)).scalar()
    return round(result, 1) if result else 0


def get_new_students_count(date):
    return Student.query.filter(func.date(Student.created_at) == date).count()


def get_attempts_count(date):
    return ExamResult.query.filter(func.date(ExamResult.taken_exam) == date).count()


def get_active_exams_count():
    return Exam.query.filter(Exam.is_active == True).count()


def get_top_exams_with_stats():
    exams = db.session.query(Exam).join(Subject).all()
    exam_stats = []

    for exam in exams:
        results = ExamResult.query.filter_by(exam_id=exam.id).all()
        if results:
            total_attempts = len(results)
            avg_score = sum(r.score for r in results) / total_attempts
            completion_rate = 100  # Simplified

            if avg_score >= 80:
                difficulty = 'easy'
            elif avg_score >= 60:
                difficulty = 'medium'
            else:
                difficulty = 'hard'

            exam.stats = {
                'total_attempts': total_attempts,
                'avg_score': round(avg_score, 1),
                'completion_rate': completion_rate,
                'difficulty': difficulty
            }
            exam_stats.append(exam)

    return sorted(exam_stats, key=lambda x: x.stats['total_attempts'], reverse=True)[:10]


def get_activity_data(start_date, end_date):
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)

    attempts = []
    new_users = []

    for date_str in dates:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        attempt_count = ExamResult.query.filter(func.date(ExamResult.taken_exam) == date_obj).count()
        attempts.append(attempt_count)

        user_count = Student.query.filter(func.date(Student.created_at) == date_obj).count()
        new_users.append(user_count)

    return {
        'dates': dates,
        'attempts': attempts,
        'new_users': new_users
    }


def get_score_distribution():
    results = ExamResult.query.all()
    if not results:
        return [0, 0, 0, 0]

    weak = len([r for r in results if r.score < 50])
    average = len([r for r in results if 50 <= r.score < 65])
    good = len([r for r in results if 65 <= r.score < 80])
    excellent = len([r for r in results if r.score >= 80])

    return [weak, average, good, excellent]


def get_subject_statistics():
    subjects = Subject.query.all()
    names = []
    attempts = []
    avg_scores = []

    for subject in subjects:
        exams = Exam.query.filter_by(subject_id=subject.id).all()
        if exams:
            exam_ids = [e.id for e in exams]
            results = ExamResult.query.filter(ExamResult.exam_id.in_(exam_ids)).all()

            if results:
                names.append(subject.subject_name)
                attempts.append(len(results))
                avg_scores.append(round(sum(r.score for r in results) / len(results), 1))

    return {
        'names': names,
        'attempts': attempts,
        'avg_scores': avg_scores
    }


def get_active_exam_sessions():
    recent = datetime.now() - timedelta(minutes=30)
    return ExamResult.query.filter(ExamResult.taken_exam >= recent).count()


def get_recent_exam_results(limit=10):
    return ExamResult.query.join(Exam).order_by(desc(ExamResult.taken_exam)).limit(limit).all()


def get_detailed_exam_stats(exam_id):
    exam = get_exam_by_id(exam_id)
    results = get_exam_results_by_exam_id(exam_id=exam_id).all()

    if not results:
        return {'error': 'No data available'}

    total_attempts = len(results)
    avg_score = sum(r.score for r in results) / total_attempts
    avg_time = 25  # Simplified
    completion_rate = 95  # Simplified

    score_ranges = {
        'labels': ['0-20', '21-40', '41-60', '61-80', '81-100'],
        'counts': [
            len([r for r in results if 0 <= r.score <= 20]),
            len([r for r in results if 21 <= r.score <= 40]),
            len([r for r in results if 41 <= r.score <= 60]),
            len([r for r in results if 61 <= r.score <= 80]),
            len([r for r in results if 81 <= r.score <= 100])
        ]
    }

    difficult_questions = [
        {
            'question': 'Sample difficult question 1',
            'correct_rate': 25,
            'difficulty': 'Hard'
        },
        {
            'question': 'Sample difficult question 2',
            'correct_rate': 35,
            'difficulty': 'Hard'
        }
    ]

    return {
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1),
        'avg_time': avg_time,
        'completion_rate': completion_rate,
        'score_ranges': score_ranges,
        'difficult_questions': difficult_questions
    }


def get_or_create_exam_session(student_id, exam_id):
    try:
        session_obj = db.session.query(ExamSession).filter(ExamSession.student_id == student_id, ExamSession.exam_id == exam_id, ExamSession.is_completed == False).first()

        if not session_obj:
            session_obj = ExamSession(
                student_id=student_id,
                exam_id=exam_id,
                start_time=datetime.now(),
                isolations_count=0,
                is_paused=False,
                is_completed=False
            )
            db.session.add(session_obj)
            db.session.commit()

        return session_obj
    except Exception as e:
        print(f"Error getting/creating session: {e}")
        return None


def check_exam_attempts_limit(student_id, exam_id, limit_hours=24, max_attempts=3):
    time_limit = datetime.now() - timedelta(hours=limit_hours)
    attempts = db.session.query(ExamResult).filter(ExamResult.student_id == student_id, ExamResult.exam_id == exam_id, ExamResult.taken_exam >= time_limit).count()
    return attempts < max_attempts, attempts


def log_suspicious_activity(student_id, exam_id, activity_type, details=None):
    try:
        log_entry = SuspiciousActivity(
            student_id=student_id,
            exam_id=exam_id,
            activity_type=activity_type,
            details=details,
            timestamp=datetime.now()
        )
        db.session.add(log_entry)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error logging suspicious activity: {e}")
        return False


def get_suspicious_activities(exam_id, student_id=None):
    query = db.session.query(SuspiciousActivity).filter(SuspiciousActivity.exam_id == exam_id)
    if student_id:
        query = query.filter(SuspiciousActivity.student_id == student_id)
    return query.order_by(SuspiciousActivity.timestamp.desc()).all()


def update_exam_session_violations(session_id, isolations_count):
    try:
        session_obj = db.session.query(ExamSession).get(session_id)
        if session_obj:
            session_obj.isolations_count = isolations_count
            if isolations_count >= 2:
                session_obj.is_completed = True
                session_obj.is_terminated = True
            db.session.commit()
            return True
    except Exception as e:
        print(f"Error updating violations: {e}")
    return False


def terminate_exam_session(student_id, exam_id):
    try:
        session_obj = db.session.query(ExamSession).filter(ExamSession.student_id == student_id, ExamSession.exam_id == exam_id, ExamSession.is_completed == False).first()

        if session_obj and session_obj.isolations_count >= 2:
            session_obj.is_completed = True
            session_obj.is_terminated = True
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"Error terminating exam session: {e}")
        return False


def create_exam_notification(exam_id):
    try:
        NotificationService.send_new_exam_notification(exam_id)
        return True
    except Exception as e:
        print(f"Error creating exam notification: {e}")
        return False


def get_student_study_streak(student_id):
    try:
        current_date = datetime.now().date()
        streak_days = 0
        for i in range(30):
            check_date = current_date - timedelta(days=i)
            has_activity = ExamResult.query.filter(ExamResult.student_id == student_id, func.date(ExamResult.taken_exam) == check_date).first()
            if has_activity:
                streak_days += 1
            else:
                break

        return streak_days
    except Exception as e:
        print(f"Error getting study streak: {e}")
        return 0


def get_weak_subjects_for_student(student_id):
    try:
        subject_scores = db.session.query(Subject.id, Subject.subject_name, func.avg(ExamResult.score).label('avg_score')
        ).join(Exam).join(ExamResult).filter(ExamResult.student_id == student_id
        ).group_by(Subject.id).all()

        weak_subjects = []
        for subject_id, subject_name, avg_score in subject_scores:
            if avg_score < 40:
                weak_subjects.append({
                    'id': subject_id,
                    'name': subject_name,
                    'avg_score': round(avg_score, 1)
                })

        return sorted(weak_subjects, key=lambda x: x['avg_score'])
    except Exception as e:
        print(f"Error getting weak subjects: {e}")
        return []


def check_milestone_achievement(student_id):
    try:
        total_exams = ExamResult.query.filter_by(student_id=student_id).count()
        milestones = [10, 25, 50, 100, 200] #chuỗi bài thi

        for milestone in milestones:
            if total_exams == milestone:
                student = Student.query.get(student_id)
                NotificationService.create_notification(
                    user_id=student.user_id,
                    title=f"Chúc mừng! Đạt {milestone} bài thi",
                    message=f"Bạn đã hoàn thành {milestone} bài thi! Đây là một thành tích đáng tự hào. Hãy tiếp tục phấn đấu!",
                    notification_type='achievement'
                )
                break

        recent_results = ExamResult.query.filter_by(student_id=student_id).order_by(ExamResult.taken_exam.desc()).limit(5).all()

        if len(recent_results) == 5:
            all_above_90 = all(r.score >= 90 for r in recent_results)
            if all_above_90:
                student = Student.query.get(student_id)
                NotificationService.create_notification(
                    user_id=student.user_id,
                    title="Xuất sắc! 5 bài liên tiếp trên 90 điểm",
                    message="Bạn đã đạt 90+ điểm cho 5 bài thi gần nhất. Thật tuyệt vời!",
                    notification_type='achievement'
                )

        return True
    except Exception as e:
        print(f"Error checking milestone: {e}")
        return False


def add_or_update_rating(user_id, exam_id, rating_value):
    try:
        existing_rating = db.session.query(Rating).filter_by(user_id=user_id, exam_id=exam_id).first()
        if existing_rating:
            existing_rating.rating = rating_value
            existing_rating.updated_at = datetime.now()
        else:
            new_rating = Rating(user_id=user_id, exam_id=exam_id, rating=rating_value)
            db.session.add(new_rating)

        db.session.commit()
        return True
    except Exception as e:
        print(f"Error adding/updating rating: {e}")
        db.session.rollback()
        return False


def get_user_rating(user_id, exam_id):
    try:
        rating = db.session.query(Rating).filter_by(user_id=user_id, exam_id=exam_id).first()
        return rating.rating if rating else None
    except Exception as e:
        print(f"Error getting user rating: {e}")
        return None


def get_exam_rating_stats(exam_id):
    try:
        ratings = db.session.query(Rating).filter_by(exam_id=exam_id).all()
        if not ratings:
            return {
                'average_rating': 0,
                'total_ratings': 0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

        total_ratings = len(ratings)
        total_score = sum(r.rating for r in ratings)
        average_rating = round(total_score / total_ratings, 1)

        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            distribution[rating.rating] += 1

        return {
            'average_rating': average_rating,
            'total_ratings': total_ratings,
            'rating_distribution': distribution
        }
    except Exception as e:
        print(f"Error getting exam rating stats: {e}")
        return {
            'average_rating': 0,
            'total_ratings': 0,
            'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        }