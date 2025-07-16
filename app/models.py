import datetime
from enum import Enum as RoleEnum
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, TEXT
from sqlalchemy.orm import relationship
import hashlib
from app import app, db


class Role(RoleEnum):
    ADMIN = 1,
    STUDENT = 2


class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)


class User(Base, UserMixin):
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    avatar = Column(String(100),
                    default="https://res.cloudinary.com/denmq54ke/image/upload/v1752161601/login_register_d1oj9t.png")
    role = Column(Enum(Role), default=Role.STUDENT)
    gender = Column(String(6), nullable=False)
    createdAt = Column(DateTime, default=datetime.datetime.now())
    updateAt = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

    student = relationship("Student", back_populates="user", uselist=False)
    admin = relationship("Admin", back_populates="user", uselist=False)


class Student(Base):
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    user = relationship("User", back_populates="student")
    exam_results = relationship("ExamResult", back_populates="student")


class Admin(Base):
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    user = relationship("User", back_populates="admin")
    subjects = relationship("Subject", back_populates="admin")
    exams = relationship("Exam", back_populates="admin")
    questions = relationship("Question", back_populates="admin")
    answers = relationship("Answer", back_populates="admin")


class Subject(Base):
    subject_name = Column(String(100), nullable=False)
    description = Column(TEXT, nullable=True)
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=False)

    admin = relationship("Admin", back_populates="subjects")
    chapters = relationship("Chapter", back_populates="subject")
    exams = relationship("Exam", back_populates="subject")


class Chapter(Base):
    chapter_name = Column(String(50), nullable=False)
    subject_id = Column(Integer, ForeignKey('subject.id'), nullable=False)

    subject = relationship("Subject", back_populates="chapters")
    questions = relationship("Question", back_populates="chapter")


class Exam(Base):
    exam_name = Column(String(50), nullable=False)
    subject_id = Column(Integer, ForeignKey('subject.id'), nullable=False)
    duration = Column(Integer, nullable=False)  # minutes
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    createBy = Column(String(50), nullable=False)
    createAt = Column(DateTime, nullable=False, default=datetime.datetime.now())
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=False)

    subject = relationship("Subject", back_populates="exams")
    admin = relationship("Admin", back_populates="exams")
    exam_results = relationship("ExamResult", back_populates="exam")
    exam_questions = relationship("ExamQuestions", back_populates="exam")


class Question(Base):
    question_title = Column(String(100), nullable=False, unique=True)
    createBy = Column(String(50), nullable=False)
    createAt = Column(DateTime, nullable=False, default=datetime.datetime.now())
    chapter_id = Column(Integer, ForeignKey('chapter.id'), nullable=False)
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=False)

    chapter = relationship("Chapter", back_populates="questions")
    admin = relationship("Admin", back_populates="questions")
    answers = relationship("Answer", back_populates="question")
    exam_questions = relationship("ExamQuestions", back_populates="question")


class Answer(Base):
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False)
    answer_text = Column(String(50), nullable=False, unique=False)
    is_correct = Column(Boolean, nullable=False, default=0)
    explanation = Column(String(200), nullable=True)
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=False)

    question = relationship("Question", back_populates="answers")
    admin = relationship("Admin", back_populates="answers")


class ExamResult(Base):
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    score = Column(Integer, nullable=False, default=0)
    taken_exam = Column(DateTime, nullable=False, default=datetime.datetime.now())

    student = relationship("Student", back_populates="exam_results")
    exam = relationship("Exam", back_populates="exam_results")


class ExamQuestions(Base):
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False)
    number_of_questions = Column(Integer, nullable=False, default=0)

    exam = relationship("Exam", back_populates="exam_questions")
    question = relationship("Question", back_populates="exam_questions")


if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()
        db.create_all()

        #DỮ LIỆU MẪU CHO DATABASE
        # Tạo records cho User
        admin_user = User(
            name="Lâm",
            username="admin",
            password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
            email="lamn9049@gmail.com",
            role=Role.ADMIN,
            gender="Male"
        )
        db.session.add(admin_user)

        student_users = [
            User(
                name="Nguyễn Văn A",
                username="student1",
                password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                email="lamn10049@gmail.com",
                role=Role.STUDENT,
                gender="Male"
            ),
            User(
                name="Trần Thị B",
                username="student2",
                password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                email="student2@example.com",
                role=Role.STUDENT,
                gender="Female"
            ),
            User(
                name="Lê Văn C",
                username="student3",
                password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                email="student3@example.com",
                role=Role.STUDENT,
                gender="Male"
            )
        ]
        for user in student_users:
            db.session.add(user)

        db.session.commit()

        # Tạo records cho bảng Admin và Student
        admin_record = Admin(user_id=admin_user.id)
        db.session.add(admin_record)

        student_records = []
        for i, user in enumerate(student_users):
            student = Student(user_id=user.id)
            student_records.append(student)
            db.session.add(student)

        db.session.commit()

        # Tạo subjects
        subjects = [
            Subject(
                subject_name="Toán học",
                description="Môn học về các khái niệm toán học cơ bản",
                admin_id=admin_record.id
            ),
            Subject(
                subject_name="Vật lý",
                description="Môn học về các hiện tượng vật lý",
                admin_id=admin_record.id
            ),
            Subject(
                subject_name="Hóa học",
                description="Môn học về các phản ứng hóa học",
                admin_id=admin_record.id
            )
        ]
        for subject in subjects:
            db.session.add(subject)

        db.session.commit()

        # Tạo Chapters
        chapters = [
            # Toán học
            Chapter(chapter_name="Đại số", subject_id=subjects[0].id),
            Chapter(chapter_name="Hình học", subject_id=subjects[0].id),
            Chapter(chapter_name="Giải tích", subject_id=subjects[0].id),

            # Vật lý
            Chapter(chapter_name="Cơ học", subject_id=subjects[1].id),
            Chapter(chapter_name="Nhiệt học", subject_id=subjects[1].id),
            Chapter(chapter_name="Điện học", subject_id=subjects[1].id),

            # Hóa học
            Chapter(chapter_name="Hóa vô cơ", subject_id=subjects[2].id),
            Chapter(chapter_name="Hóa hữu cơ", subject_id=subjects[2].id),
        ]

        for chapter in chapters:
            db.session.add(chapter)

        db.session.commit()

        # Tạo Questions
        questions = [
            # Toán học - Đại số
            Question(
                question_title="2 + 2 = ?",
                createBy="admin",
                chapter_id=chapters[0].id,
                admin_id=admin_record.id
            ),
            Question(
                question_title="Nghiệm của phương trình x² - 4 = 0 là:",
                createBy="admin",
                chapter_id=chapters[0].id,
                admin_id=admin_record.id
            ),

            # Vật lý - Cơ học
            Question(
                question_title="Công thức tính vận tốc là:",
                createBy="admin",
                chapter_id=chapters[3].id,
                admin_id=admin_record.id
            ),
            Question(
                question_title="Gia tốc trọng trường trên Trái Đất là:",
                createBy="admin",
                chapter_id=chapters[3].id,
                admin_id=admin_record.id
            ),

            # Hóa học - Hóa vô cơ
            Question(
                question_title="Công thức hóa học của nước là:",
                createBy="admin",
                chapter_id=chapters[6].id,
                admin_id=admin_record.id
            ),
        ]

        for question in questions:
            db.session.add(question)

        db.session.commit()

        # Tạo Answers
        answers = [
            # Câu hỏi 1: 2 + 2 = ?
            Answer(question_id=questions[0].id, answer_text="3", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[0].id, answer_text="4", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[0].id, answer_text="5", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[0].id, answer_text="6", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 2: Nghiệm của phương trình x² - 4 = 0
            Answer(question_id=questions[1].id, answer_text="x = ±2", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[1].id, answer_text="x = ±4", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[1].id, answer_text="x = 2", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[1].id, answer_text="x = -2", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 3: Công thức tính vận tốc
            Answer(question_id=questions[2].id, answer_text="v = s/t", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[2].id, answer_text="v = s*t", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[2].id, answer_text="v = t/s", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[2].id, answer_text="v = s+t", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 4: Gia tốc trọng trường
            Answer(question_id=questions[3].id, answer_text="9.8 m/s²", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[3].id, answer_text="10 m/s²", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[3].id, answer_text="9.6 m/s²", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[3].id, answer_text="8 m/s²", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 5: Công thức hóa học của nước
            Answer(question_id=questions[4].id, answer_text="H2O", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[4].id, answer_text="H2O2", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[4].id, answer_text="HO", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[4].id, answer_text="H3O", is_correct=False, admin_id=admin_record.id),
        ]

        for answer in answers:
            db.session.add(answer)

        db.session.commit()

        # Tạo Exams
        exams = [
            Exam(
                exam_name="Kiểm tra Toán học giữa kỳ",
                subject_id=subjects[0].id,
                duration=90,  # 90 phút
                start_time=datetime.datetime.now() + datetime.timedelta(days=1),
                end_time=datetime.datetime.now() + datetime.timedelta(days=1, hours=1.5),
                createBy="admin",
                admin_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Vật lý cuối kỳ",
                subject_id=subjects[1].id,
                duration=120,  # 120 phút
                start_time=datetime.datetime.now() + datetime.timedelta(days=7),
                end_time=datetime.datetime.now() + datetime.timedelta(days=7, hours=2),
                createBy="admin",
                admin_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Hóa học 15 phút",
                subject_id=subjects[2].id,
                duration=15,  # 15 phút
                start_time=datetime.datetime.now() + datetime.timedelta(days=3),
                end_time=datetime.datetime.now() + datetime.timedelta(days=3, minutes=15),
                createBy="admin",
                admin_id=admin_record.id
            ),
        ]

        for exam in exams:
            db.session.add(exam)

        db.session.commit()

        # Tạo ExamQuestions
        exam_questions = [
            # Exam 1 - Toán học
            ExamQuestions(exam_id=exams[0].id, question_id=questions[0].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[0].id, question_id=questions[1].id, number_of_questions=2),

            # Exam 2 - Vật lý
            ExamQuestions(exam_id=exams[1].id, question_id=questions[2].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[1].id, question_id=questions[3].id, number_of_questions=2),

            # Exam 3 - Hóa học
            ExamQuestions(exam_id=exams[2].id, question_id=questions[4].id, number_of_questions=1),
        ]

        for eq in exam_questions:
            db.session.add(eq)

        db.session.commit()

        # Tạo ExamResults
        exam_results = [
            ExamResult(
                student_id=student_records[0].id,
                exam_id=exams[0].id,
                score=85,
                taken_exam=datetime.datetime.now() - datetime.timedelta(days=1)
            ),
            ExamResult(
                student_id=student_records[1].id,
                exam_id=exams[0].id,
                score=92,
                taken_exam=datetime.datetime.now() - datetime.timedelta(days=1)
            ),
            ExamResult(
                student_id=student_records[2].id,
                exam_id=exams[1].id,
                score=78,
                taken_exam=datetime.datetime.now() - datetime.timedelta(days=2)
            ),
            ExamResult(
                student_id=student_records[0].id,
                exam_id=exams[2].id,
                score=95,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=2)
            ),
        ]

        for result in exam_results:
            db.session.add(result)

        db.session.commit()