import datetime
from enum import Enum as RoleEnum
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, TEXT, JSON, Float
from sqlalchemy.orm import relationship
import hashlib
from app import app, db


class Role(RoleEnum):
    ADMIN = 1
    STUDENT = 2


class Base(db.Model):
    __abstract__ = True
    __table_args__ = {'extend_existing': True}
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
    createdAt = Column(DateTime, default=datetime.datetime.now)
    updateAt = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    student = relationship("Student", back_populates="user", uselist=False)
    admin = relationship("Admin", back_populates="user", uselist=False)
    comments = relationship("Comment", back_populates="user")
    exams = relationship("Exam", back_populates="user")


class Student(Base):
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, unique=True)

    user = relationship("User", back_populates="student")
    exam_results = relationship("ExamResult", back_populates="student")


class Admin(Base):
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, unique=True)

    user = relationship("User", back_populates="admin")


class Subject(Base):
    subject_name = Column(String(100), nullable=False)
    description = Column(TEXT, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    last_modified_by = Column(String(100), nullable=True)
    last_modified_at = Column(DateTime, default=datetime.datetime.now)

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
    createAt = Column(DateTime, nullable=False, default=datetime.datetime.now)
    is_active = Column(Boolean, nullable=False, default=1)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    subject = relationship("Subject", back_populates="exams")
    user = relationship("User", back_populates="exams")
    exam_results = relationship("ExamResult", back_populates="exam")
    exam_questions = relationship("ExamQuestions", back_populates="exam")
    comments = relationship("Comment", back_populates="exam")


class Question(Base):
    question_title = Column(String(500), nullable=False, unique=True)
    createBy = Column(String(50), nullable=False)
    createAt = Column(DateTime, nullable=False, default=datetime.datetime.now)
    chapter_id = Column(Integer, ForeignKey('chapter.id'), nullable=False)

    chapter = relationship("Chapter", back_populates="questions")
    answers = relationship("Answer", back_populates="question")
    exam_questions = relationship("ExamQuestions", back_populates="question")


class Answer(Base):
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False)
    answer_text = Column(String(100), nullable=False, unique=False)
    is_correct = Column(Boolean, nullable=False, default=0)
    explanation = Column(String(200), nullable=True)
    createBy = Column(String(50), nullable=False)

    question = relationship("Question", back_populates="answers")


class ExamResult(Base):
    student_id = Column(Integer, ForeignKey('student.id', ondelete='SET NULL'), nullable=True)
    exam_id = Column(Integer, ForeignKey('exam.id', ondelete='SET NULL'), nullable=True)
    student_name = Column(String(100), nullable=True)
    exam_name = Column(String(100), nullable=True)
    score = Column(Integer, nullable=False, default=0)
    taken_exam = Column(DateTime, nullable=False, default=datetime.datetime.now)
    time_taken = Column(Integer, nullable=True, default=0)  #(giây)
    user_answers = Column(JSON)
    is_first_attempt = Column(Boolean, default=True)
    difficulty_level = Column(String(20))
    time_efficiency = Column(Float)

    student = relationship("Student", back_populates="exam_results")
    exam = relationship("Exam", back_populates="exam_results")


class ExamQuestions(Base):
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False)
    number_of_questions = Column(Integer, nullable=False, default=0)

    exam = relationship("Exam", back_populates="exam_questions")
    question = relationship("Question", back_populates="exam_questions")


class ExamSession(Base):
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.datetime.now)
    pause_time = Column(DateTime, nullable=True)
    resume_time = Column(DateTime, nullable=True)
    total_paused_duration = Column(Integer, default=0)  #seconds
    current_question_index = Column(Integer, default=0)
    user_answers = Column(JSON, default=dict)
    question_order = Column(JSON, default=[])
    answer_orders = Column(JSON, default={})
    is_paused = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    isolations_count = Column(Integer, default=0)
    is_terminated = Column(Boolean, default=False)
    window_focus_lost_count = Column(Integer, default=0)

    student = relationship("Student")
    exam = relationship("Exam")


class Comment(Base):
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    content = Column(TEXT, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    exam = relationship("Exam", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Rating(Base):
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'exam_id', name='unique_user_exam_rating'),
        {'extend_existing': True}
    )

    user = relationship("User")
    exam = relationship("Exam")


class StudyRecommendation(Base):
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)
    recommendation_type = Column(String(50), nullable=False)  #'material', 'exam', 'topic'
    content = Column(JSON, nullable=False)
    priority = Column(Integer, default=1)  #1=high, 2=medium, 3=low
    is_viewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now)

    student = relationship("Student")


class LearningPath(Base):
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subject.id'), nullable=False)
    current_level = Column(String(20), default='beginner')  #beginner, intermediate, advanced
    progress_percentage = Column(Integer, default=0)
    target_score = Column(Integer, default=80)
    estimated_completion_days = Column(Integer)

    student = relationship("Student")
    subject = relationship("Subject")


class SuspiciousActivity(Base):
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)

    student = relationship("Student")
    exam = relationship("Exam")


class Notification(Base):
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(TEXT, nullable=False)
    notification_type = Column(String(50), default='info')  # info, warning, success, reminder, result, suggestion, new_exam
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now)

    user = relationship("User")
    exam = relationship("Exam")


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        # DỮ LIỆU MẪU CHO DATABASE
        # Tạo records cho User
        admin_user = User(
            name="Lâm",
            username="admin",
            password=str(hashlib.md5('admin'.encode('utf-8')).hexdigest()),
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
                email="2251052057lam@ou.edu.vn",
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
            ),
            User(
                name="Dương Thị D",
                username="student4",
                password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                email="student4@gmail.com",
                role=Role.STUDENT,
                gender="Female"
            ),
            User(
                name="Võ Thị E",
                username="student5",
                password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                email="student5@gmail.com",
                role=Role.STUDENT,
                gender="Female"
            ),
            User(
                name="Đinh Văn F",
                username="student6",
                password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                email="student6@gmail.com",
                role=Role.STUDENT,
                gender="Male"
            ),
            User(
                name="Lò Văn G",
                username="student7",
                password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
                email="student7@gmail.com",
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
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Vật lý",
                description="Môn học về các hiện tượng vật lý",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Hóa học",
                description="Môn học về các phản ứng hóa học",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Tiếng Anh",
                description="Môn học về ngôn ngữ Anh",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Lịch sử",
                description="Môn học về lịch sử Việt Nam và thế giới",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Địa lý",
                description="Môn học về địa lý tự nhiên và kinh tế",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Sinh học",
                description="Môn học về các quá trình sinh học",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Ngữ Văn",
                description="Môn học về tiếng Việt",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Giáo dục công dân",
                description="Môn học về bản chất con người",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Công nghệ",
                description="Môn học về máy móc",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Tin học",
                description="Môn học về máy tính",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Âm nhạc",
                description="Môn học về âm thanh và giai điệu",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Mĩ thuật",
                description="Môn học về cách vẽ và nhìn nhận thế giới",
                created_by=admin_user.name
            ),
            Subject(
                subject_name="Tiếng Pháp",
                description="Môn học về France",
                created_by=admin_user.name
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

            # Tiếng Anh
            Chapter(chapter_name="Grammar", subject_id=subjects[3].id),
            Chapter(chapter_name="Vocabulary", subject_id=subjects[3].id),
            Chapter(chapter_name="Reading", subject_id=subjects[3].id),

            # Lịch sử
            Chapter(chapter_name="Lịch sử cổ đại", subject_id=subjects[4].id),
            Chapter(chapter_name="Lịch sử cận đại", subject_id=subjects[4].id),
            Chapter(chapter_name="Lịch sử hiện đại", subject_id=subjects[4].id),

            # Địa lý
            Chapter(chapter_name="Địa lý tự nhiên", subject_id=subjects[5].id),
            Chapter(chapter_name="Địa lý kinh tế", subject_id=subjects[5].id),
            Chapter(chapter_name="Địa lý dân cư", subject_id=subjects[5].id),

            # Sinh học
            Chapter(chapter_name="Tế bào học", subject_id=subjects[6].id),
            Chapter(chapter_name="Di truyền học", subject_id=subjects[6].id),
            Chapter(chapter_name="Sinh thái học", subject_id=subjects[6].id),

            # Ngữ Văn
            Chapter(chapter_name="Văn học Việt Nam", subject_id=subjects[7].id),
            Chapter(chapter_name="Văn học nước ngoài", subject_id=subjects[7].id),
            Chapter(chapter_name="Tiếng Việt", subject_id=subjects[7].id),

            # Giáo dục công dân
            Chapter(chapter_name="Công dân và pháp luật", subject_id=subjects[8].id),
            Chapter(chapter_name="Công dân và kinh tế", subject_id=subjects[8].id),
            Chapter(chapter_name="Giá trị đạo đức", subject_id=subjects[8].id),

            # Công nghệ
            Chapter(chapter_name="Cơ khí", subject_id=subjects[9].id),
            Chapter(chapter_name="Điện tử", subject_id=subjects[9].id),
            Chapter(chapter_name="Nông nghiệp", subject_id=subjects[9].id),

            # Tin học
            Chapter(chapter_name="Lập trình", subject_id=subjects[10].id),
            Chapter(chapter_name="Mạng máy tính", subject_id=subjects[10].id),
            Chapter(chapter_name="Cơ sở dữ liệu", subject_id=subjects[10].id),

            # Âm nhạc
            Chapter(chapter_name="Lý thuyết âm nhạc", subject_id=subjects[11].id),
            Chapter(chapter_name="Nhạc cụ", subject_id=subjects[11].id),
            Chapter(chapter_name="Thanh nhạc", subject_id=subjects[11].id),

            # Mĩ thuật
            Chapter(chapter_name="Hội họa", subject_id=subjects[12].id),
            Chapter(chapter_name="Điêu khắc", subject_id=subjects[12].id),
            Chapter(chapter_name="Mỹ thuật ứng dụng", subject_id=subjects[12].id),

            # Tiếng Pháp
            Chapter(chapter_name="Ngữ pháp tiếng Pháp", subject_id=subjects[13].id),
            Chapter(chapter_name="Từ vựng tiếng Pháp", subject_id=subjects[13].id),
            Chapter(chapter_name="Văn hóa Pháp", subject_id=subjects[13].id)
        ]

        for chapter in chapters:
            db.session.add(chapter)

        db.session.commit()

        # Tạo Questions
        questions = [
            # Toán học - Đại số
            Question(question_title="2 + 2 = ?", createBy=admin_user.name, chapter_id=chapters[0].id),
            Question(question_title="Nghiệm của phương trình x² - 4 = 0 là:", createBy=admin_user.name,
                     chapter_id=chapters[0].id),

            # Vật lý - Cơ học
            Question(question_title="Công thức tính vận tốc là:", createBy=admin_user.name, chapter_id=chapters[3].id),
            Question(question_title="Gia tốc trọng trường trên Trái Đất là:", createBy=admin_user.name,
                     chapter_id=chapters[3].id),

            # Hóa học - Hóa vô cơ
            Question(question_title="Công thức hóa học của nước là:", createBy=admin_user.name, chapter_id=chapters[6].id),

            # Toán học - Đại số (thêm)
            Question(question_title="3x + 5 = 14, x = ?", createBy=admin_user.name, chapter_id=chapters[0].id),
            Question(question_title="√16 = ?", createBy=admin_user.name, chapter_id=chapters[0].id),
            Question(question_title="2³ = ?", createBy=admin_user.name, chapter_id=chapters[0].id),

            # Toán học - Hình học
            Question(question_title="Diện tích hình vuông cạnh 5cm là:", createBy=admin_user.name,
                     chapter_id=chapters[1].id),
            Question(question_title="Chu vi hình tròn bán kính 7cm là:", createBy=admin_user.name,
                     chapter_id=chapters[1].id),
            Question(question_title="Thể tích hình lập phương cạnh 3cm là:", createBy=admin_user.name,
                     chapter_id=chapters[1].id),

            # Toán học - Giải tích
            Question(question_title="Đạo hàm của x² là:", createBy=admin_user.name, chapter_id=chapters[2].id),
            Question(question_title="∫x dx = ?", createBy=admin_user.name, chapter_id=chapters[2].id),

            # Vật lý - Cơ học (thêm)
            Question(question_title="Định luật Newton thứ nhất nói về:", createBy=admin_user.name,
                     chapter_id=chapters[3].id),
            Question(question_title="Công thức tính động lượng là:", createBy=admin_user.name, chapter_id=chapters[3].id),

            # Vật lý - Nhiệt học
            Question(question_title="Nhiệt độ sôi của nước ở áp suất tiêu chuẩn:", createBy=admin_user.name,
                     chapter_id=chapters[4].id),
            Question(question_title="Đơn vị đo nhiệt lượng là:", createBy=admin_user.name, chapter_id=chapters[4].id),

            # Vật lý - Điện học
            Question(question_title="Định luật Ohm có dạng:", createBy=admin_user.name, chapter_id=chapters[5].id),
            Question(question_title="Điện trở của dây dẫn phụ thuộc vào:", createBy=admin_user.name,
                     chapter_id=chapters[5].id),

            # Hóa học - Hóa vô cơ (thêm)
            Question(question_title="Số oxi hóa của H trong H₂O là:", createBy=admin_user.name, chapter_id=chapters[6].id),
            Question(question_title="Axit mạnh nhất trong các axit sau:", createBy=admin_user.name,
                     chapter_id=chapters[6].id),

            # Hóa học - Hóa hữu cơ
            Question(question_title="Công thức phân tử của methane là:", createBy=admin_user.name,
                     chapter_id=chapters[7].id),
            Question(question_title="Ancol etylic có công thức:", createBy=admin_user.name, chapter_id=chapters[7].id),

            # Tiếng Anh - Grammar
            Question(question_title="Choose the correct form: 'I ___ to school yesterday'", createBy=admin_user.name,
                     chapter_id=chapters[8].id),
            Question(question_title="Which is correct: 'He ___ English very well'", createBy=admin_user.name,
                     chapter_id=chapters[8].id),

            # Tiếng Anh - Vocabulary
            Question(question_title="What does 'beautiful' mean?", createBy=admin_user.name, chapter_id=chapters[9].id),
            Question(question_title="The opposite of 'big' is:", createBy=admin_user.name, chapter_id=chapters[9].id),

            # Tiếng Anh - Reading
            Question(question_title="In the sentence 'The cat is sleeping', what is the subject?", createBy=admin_user.name,
                     chapter_id=chapters[10].id),
            Question(question_title="What tense is used in 'I am reading a book'?", createBy=admin_user.name,
                     chapter_id=chapters[10].id),

            # Lịch sử - Lịch sử cổ đại
            Question(question_title="Nước Văn Lang được thành lập vào thời gian nào?", createBy=admin_user.name,
                     chapter_id=chapters[11].id),
            Question(question_title="Ai là người sáng lập ra nước Âu Lạc?", createBy=admin_user.name,
                     chapter_id=chapters[11].id),

            # Lịch sử - Lịch sử cận đại
            Question(question_title="Cuộc khởi nghĩa Tây Sơn diễn ra vào thế kỷ nào?", createBy=admin_user.name,
                     chapter_id=chapters[12].id),
            Question(question_title="Ai là hoàng đế cuối cùng của triều Nguyễn?", createBy=admin_user.name,
                     chapter_id=chapters[12].id),

            # Lịch sử - Lịch sử hiện đại
            Question(question_title="Cách mạng tháng Tám diễn ra vào năm nào?", createBy=admin_user.name,
                     chapter_id=chapters[13].id),
            Question(question_title="Chiến dịch Điện Biên Phủ kết thúc vào ngày nào?", createBy=admin_user.name,
                     chapter_id=chapters[13].id),

            # Địa lý - Địa lý tự nhiên
            Question(question_title="Núi cao nhất Việt Nam là:", createBy=admin_user.name, chapter_id=chapters[14].id),
            Question(question_title="Sông dài nhất Việt Nam là:", createBy=admin_user.name, chapter_id=chapters[14].id),

            # Địa lý - Địa lý kinh tế
            Question(question_title="Khu vực kinh tế trọng điểm phía Nam là:", createBy=admin_user.name,
                     chapter_id=chapters[15].id),
            Question(question_title="Cây trồng chủ yếu ở ĐBSCL là:", createBy=admin_user.name, chapter_id=chapters[15].id),

            # Địa lý - Địa lý dân cư
            Question(question_title="Dân số Việt Nam hiện tại khoảng:", createBy=admin_user.name,
                     chapter_id=chapters[16].id),
            Question(question_title="Thành phố có dân số đông nhất Việt Nam là:", createBy=admin_user.name,
                     chapter_id=chapters[16].id),

            # Sinh học - Tế bào học
            Question(question_title="Bào quan nào chứa DNA trong tế bào?", createBy=admin_user.name,
                     chapter_id=chapters[17].id),
            Question(question_title="Quá trình phân chia tế bào được gọi là:", createBy=admin_user.name,
                     chapter_id=chapters[17].id),

            # Sinh học - Di truyền học
            Question(question_title="Gen là gì?", createBy=admin_user.name, chapter_id=chapters[18].id),
            Question(question_title="DNA có cấu trúc như thế nào?", createBy=admin_user.name, chapter_id=chapters[18].id),

            # Sinh học - Sinh thái học
            Question(question_title="Chuỗi thức ăn bắt đầu từ:", createBy=admin_user.name, chapter_id=chapters[19].id),
            Question(question_title="Hiệu ứng nhà kính do đâu gây ra?", createBy=admin_user.name,
                     chapter_id=chapters[19].id)
        ]

        for question in questions:
            db.session.add(question)

        db.session.commit()

        # Tạo Answers
        answers = [
            # Câu hỏi 1: 2 + 2 = ?
            Answer(question_id=questions[0].id, answer_text="3", is_correct=False, createBy='admin'),
            Answer(question_id=questions[0].id, answer_text="4", is_correct=True, createBy='admin'),
            Answer(question_id=questions[0].id, answer_text="5", is_correct=False, createBy='admin'),
            Answer(question_id=questions[0].id, answer_text="6", is_correct=False, createBy='admin'),

            # Câu hỏi 2: Nghiệm của phương trình x² - 4 = 0
            Answer(question_id=questions[1].id, answer_text="x = ±2", is_correct=True, createBy='admin'),
            Answer(question_id=questions[1].id, answer_text="x = ±4", is_correct=False, createBy='admin'),
            Answer(question_id=questions[1].id, answer_text="x = 2", is_correct=False, createBy='admin'),
            Answer(question_id=questions[1].id, answer_text="x = -2", is_correct=False, createBy='admin'),

            # Câu hỏi 3: Công thức tính vận tốc
            Answer(question_id=questions[2].id, answer_text="v = s/t", is_correct=True, createBy='admin'),
            Answer(question_id=questions[2].id, answer_text="v = s*t", is_correct=False, createBy='admin'),
            Answer(question_id=questions[2].id, answer_text="v = t/s", is_correct=False, createBy='admin'),
            Answer(question_id=questions[2].id, answer_text="v = s+t", is_correct=False, createBy='admin'),

            # Câu hỏi 4: Gia tốc trọng trường
            Answer(question_id=questions[3].id, answer_text="9.8 m/s²", is_correct=True, createBy='admin'),
            Answer(question_id=questions[3].id, answer_text="10 m/s²", is_correct=False, createBy='admin'),
            Answer(question_id=questions[3].id, answer_text="9.6 m/s²", is_correct=False, createBy='admin'),
            Answer(question_id=questions[3].id, answer_text="8 m/s²", is_correct=False, createBy='admin'),

            # Câu hỏi 5: Công thức hóa học của nước
            Answer(question_id=questions[4].id, answer_text="H2O", is_correct=True, createBy='admin'),
            Answer(question_id=questions[4].id, answer_text="H2O2", is_correct=False, createBy='admin'),
            Answer(question_id=questions[4].id, answer_text="HO", is_correct=False, createBy='admin'),
            Answer(question_id=questions[4].id, answer_text="H3O", is_correct=False, createBy='admin'),

            # Câu hỏi 6: 3x + 5 = 14
            Answer(question_id=questions[5].id, answer_text="x = 3", is_correct=True, createBy='admin'),
            Answer(question_id=questions[5].id, answer_text="x = 4", is_correct=False, createBy='admin'),
            Answer(question_id=questions[5].id, answer_text="x = 5", is_correct=False, createBy='admin'),
            Answer(question_id=questions[5].id, answer_text="x = 2", is_correct=False, createBy='admin'),

            # Câu hỏi 7: √16 = ?
            Answer(question_id=questions[6].id, answer_text="4", is_correct=True, createBy='admin'),
            Answer(question_id=questions[6].id, answer_text="8", is_correct=False, createBy='admin'),
            Answer(question_id=questions[6].id, answer_text="16", is_correct=False, createBy='admin'),
            Answer(question_id=questions[6].id, answer_text="2", is_correct=False, createBy='admin'),

            # Câu hỏi 8: 2³ = ?
            Answer(question_id=questions[7].id, answer_text="8", is_correct=True, createBy='admin'),
            Answer(question_id=questions[7].id, answer_text="6", is_correct=False, createBy='admin'),
            Answer(question_id=questions[7].id, answer_text="9", is_correct=False, createBy='admin'),
            Answer(question_id=questions[7].id, answer_text="12", is_correct=False, createBy='admin'),

            # Câu hỏi 9: Diện tích hình vuông cạnh 5cm
            Answer(question_id=questions[8].id, answer_text="25 cm²", is_correct=True, createBy='admin'),
            Answer(question_id=questions[8].id, answer_text="20 cm²", is_correct=False, createBy='admin'),
            Answer(question_id=questions[8].id, answer_text="10 cm²", is_correct=False, createBy='admin'),
            Answer(question_id=questions[8].id, answer_text="15 cm²", is_correct=False, createBy='admin'),

            # Câu hỏi 10: Chu vi hình tròn bán kính 7cm
            Answer(question_id=questions[9].id, answer_text="44 cm", is_correct=True, createBy='admin'),
            Answer(question_id=questions[9].id, answer_text="14 cm", is_correct=False, createBy='admin'),
            Answer(question_id=questions[9].id, answer_text="22 cm", is_correct=False, createBy='admin'),
            Answer(question_id=questions[9].id, answer_text="28 cm", is_correct=False, createBy='admin'),

            # Câu hỏi 11: Thể tích hình lập phương cạnh 3cm
            Answer(question_id=questions[10].id, answer_text="27 cm³", is_correct=True, createBy='admin'),
            Answer(question_id=questions[10].id, answer_text="9 cm³", is_correct=False, createBy='admin'),
            Answer(question_id=questions[10].id, answer_text="18 cm³", is_correct=False, createBy='admin'),
            Answer(question_id=questions[10].id, answer_text="36 cm³", is_correct=False, createBy='admin'),

            # Câu hỏi 12: Đạo hàm của x²
            Answer(question_id=questions[11].id, answer_text="2x", is_correct=True, createBy='admin'),
            Answer(question_id=questions[11].id, answer_text="x²", is_correct=False, createBy='admin'),
            Answer(question_id=questions[11].id, answer_text="x", is_correct=False, createBy='admin'),
            Answer(question_id=questions[11].id, answer_text="2x²", is_correct=False, createBy='admin'),

            # Câu hỏi 13: ∫x dx = ?
            Answer(question_id=questions[12].id, answer_text="x²/2 + C", is_correct=True, createBy='admin'),
            Answer(question_id=questions[12].id, answer_text="x² + C", is_correct=False, createBy='admin'),
            Answer(question_id=questions[12].id, answer_text="2x + C", is_correct=False, createBy='admin'),
            Answer(question_id=questions[12].id, answer_text="x + C", is_correct=False, createBy='admin'),

            # Câu hỏi 14: Định luật Newton thứ nhất
            Answer(question_id=questions[13].id, answer_text="Quán tính", is_correct=True, createBy='admin'),
            Answer(question_id=questions[13].id, answer_text="Gia tốc", is_correct=False, createBy='admin'),
            Answer(question_id=questions[13].id, answer_text="Tác dụng phản tác dụng", is_correct=False, createBy='admin'),
            Answer(question_id=questions[13].id, answer_text="Hấp dẫn", is_correct=False, createBy='admin'),

            # Câu hỏi 15: Công thức tính động lượng
            Answer(question_id=questions[14].id, answer_text="p = mv", is_correct=True, createBy='admin'),
            Answer(question_id=questions[14].id, answer_text="p = ma", is_correct=False, createBy='admin'),
            Answer(question_id=questions[14].id, answer_text="p = Ft", is_correct=False, createBy='admin'),
            Answer(question_id=questions[14].id, answer_text="p = mv²", is_correct=False, createBy='admin'),

            # Câu hỏi 16: Nhiệt độ sôi của nước
            Answer(question_id=questions[15].id, answer_text="100°C", is_correct=True, createBy='admin'),
            Answer(question_id=questions[15].id, answer_text="0°C", is_correct=False, createBy='admin'),
            Answer(question_id=questions[15].id, answer_text="50°C", is_correct=False, createBy='admin'),
            Answer(question_id=questions[15].id, answer_text="200°C", is_correct=False, createBy='admin'),

            Answer(question_id=questions[16].id, answer_text="Oát (W)", is_correct=True, createBy='admin'),
            Answer(question_id=questions[16].id, answer_text="Gam (g)", is_correct=False, createBy='admin'),
            Answer(question_id=questions[16].id, answer_text="Giây (s)", is_correct=False, createBy='admin'),
            Answer(question_id=questions[16].id, answer_text="Jun (J)", is_correct=False, createBy='admin'),

            Answer(question_id=questions[17].id, answer_text="V= R/I", is_correct=False, createBy='admin'),
            Answer(question_id=questions[17].id, answer_text="R = V.I", is_correct=False, createBy='admin'),
            Answer(question_id=questions[17].id, answer_text="I = R/V", is_correct=False, createBy='admin'),
            Answer(question_id=questions[17].id, answer_text="V = I.R", is_correct=True, createBy='admin'),

            Answer(question_id=questions[18].id, answer_text="Cường độ dòng điện chạy qua dây.", is_correct=False, createBy='admin'),
            Answer(question_id=questions[18].id, answer_text="Hiệu điện thế giữa hai đầu dây.", is_correct=False, createBy='admin'),
            Answer(question_id=questions[18].id, answer_text="Vật liệu, chiều dài và tiết diện của dây.",
                   is_correct=True, createBy='admin'),
            Answer(question_id=questions[18].id, answer_text="Thời gian dòng điện chạy qua dây.", is_correct=False, createBy='admin'),

            Answer(question_id=questions[19].id, answer_text="0", is_correct=False, createBy='admin'),
            Answer(question_id=questions[19].id, answer_text="+1", is_correct=True, createBy='admin'),
            Answer(question_id=questions[19].id, answer_text="-1", is_correct=False, createBy='admin'),
            Answer(question_id=questions[19].id, answer_text="+2", is_correct=False, createBy='admin'),

            Answer(question_id=questions[20].id, answer_text="HCl", is_correct=True, createBy='admin'),
            Answer(question_id=questions[20].id, answer_text="H₂CO₃", is_correct=False, createBy='admin'),
            Answer(question_id=questions[20].id, answer_text="CH₃COOH", is_correct=False, createBy='admin'),
            Answer(question_id=questions[20].id, answer_text="H₂S", is_correct=False, createBy='admin'),

            Answer(question_id=questions[21].id, answer_text="CH₄", is_correct=True, createBy='admin'),
            Answer(question_id=questions[21].id, answer_text="C₂H₆", is_correct=False, createBy='admin'),
            Answer(question_id=questions[21].id, answer_text="C₂H₄", is_correct=False, createBy='admin'),
            Answer(question_id=questions[21].id, answer_text="C₃H₈", is_correct=False, createBy='admin'),

            Answer(question_id=questions[22].id, answer_text="C₂H₆O", is_correct=True, createBy='admin'),
            Answer(question_id=questions[22].id, answer_text="C₂H₄O₂", is_correct=False, createBy='admin'),
            Answer(question_id=questions[22].id, answer_text="C₂H₆", is_correct=False, createBy='admin'),
            Answer(question_id=questions[22].id, answer_text="CH₃OH", is_correct=False, createBy='admin'),

            Answer(question_id=questions[23].id, answer_text="go", is_correct=False, createBy='admin'),
            Answer(question_id=questions[23].id, answer_text="gone", is_correct=False, createBy='admin'),
            Answer(question_id=questions[23].id, answer_text="went", is_correct=True, createBy='admin'),
            Answer(question_id=questions[23].id, answer_text="going", is_correct=False, createBy='admin'),

            Answer(question_id=questions[24].id, answer_text="speak", is_correct=False, createBy='admin'),
            Answer(question_id=questions[24].id, answer_text="speaks", is_correct=True, createBy='admin'),
            Answer(question_id=questions[24].id, answer_text="speaking", is_correct=False, createBy='admin'),
            Answer(question_id=questions[24].id, answer_text="spoken", is_correct=False, createBy='admin'),

            Answer(question_id=questions[25].id, answer_text="Ugly", is_correct=False, createBy='admin'),
            Answer(question_id=questions[25].id, answer_text="Pretty", is_correct=True, createBy='admin'),
            Answer(question_id=questions[25].id, answer_text="Dirty", is_correct=False, createBy='admin'),
            Answer(question_id=questions[25].id, answer_text="Bad", is_correct=False, createBy='admin'),

            Answer(question_id=questions[26].id, answer_text="Large", is_correct=False, createBy='admin'),
            Answer(question_id=questions[26].id, answer_text="Huge", is_correct=False, createBy='admin'),
            Answer(question_id=questions[26].id, answer_text="Tiny", is_correct=True, createBy='admin'),
            Answer(question_id=questions[26].id, answer_text="Tall", is_correct=False, createBy='admin'),

            Answer(question_id=questions[27].id, answer_text="is sleeping", is_correct=False, createBy='admin'),
            Answer(question_id=questions[27].id, answer_text="The cat", is_correct=True, createBy='admin'),
            Answer(question_id=questions[27].id, answer_text="sleeping", is_correct=False, createBy='admin'),
            Answer(question_id=questions[27].id, answer_text="is", is_correct=False, createBy='admin'),

            Answer(question_id=questions[28].id, answer_text="Past Simple", is_correct=False, createBy='admin'),
            Answer(question_id=questions[28].id, answer_text="Present Simple", is_correct=False, createBy='admin'),
            Answer(question_id=questions[28].id, answer_text="Present Continuous", is_correct=True, createBy='admin'),
            Answer(question_id=questions[28].id, answer_text="Future Simple", is_correct=False, createBy='admin'),

            Answer(question_id=questions[29].id, answer_text="Thế kỷ VII trước Công nguyên", is_correct=True, createBy='admin'),
            Answer(question_id=questions[29].id, answer_text="Thế kỷ III trước Công nguyên", is_correct=False, createBy='admin'),
            Answer(question_id=questions[29].id, answer_text="Năm 1000 sau Công nguyên", is_correct=False, createBy='admin'),
            Answer(question_id=questions[29].id, answer_text="Thế kỷ I sau Công nguyên", is_correct=False, createBy='admin'),

            Answer(question_id=questions[30].id, answer_text="An Dương Vương", is_correct=True, createBy='admin'),
            Answer(question_id=questions[30].id, answer_text="Hùng Vương", is_correct=False, createBy='admin'),
            Answer(question_id=questions[30].id, answer_text="Triệu Đà", is_correct=False, createBy='admin'),
            Answer(question_id=questions[30].id, answer_text="Ngô Quyền", is_correct=False, createBy='admin'),

            Answer(question_id=questions[31].id, answer_text="Thế kỷ XVIII", is_correct=True, createBy='admin'),
            Answer(question_id=questions[31].id, answer_text="Thế kỷ XVII", is_correct=False, createBy='admin'),
            Answer(question_id=questions[31].id, answer_text="Thế kỷ XIX", is_correct=False, createBy='admin'),
            Answer(question_id=questions[31].id, answer_text="Thế kỷ XVI", is_correct=False, createBy='admin'),

            Answer(question_id=questions[32].id, answer_text="Bảo Đại", is_correct=True, createBy='admin'),
            Answer(question_id=questions[32].id, answer_text="Gia Long", is_correct=False, createBy='admin'),
            Answer(question_id=questions[32].id, answer_text="Minh Mạng", is_correct=False, createBy='admin'),
            Answer(question_id=questions[32].id, answer_text="Tự Đức", is_correct=False, createBy='admin'),

            # Câu hỏi Lịch sử - Cách mạng tháng Tám
            Answer(question_id=questions[33].id, answer_text="1945", is_correct=True, createBy='admin'),
            Answer(question_id=questions[33].id, answer_text="1946", is_correct=False, createBy='admin'),
            Answer(question_id=questions[33].id, answer_text="1944", is_correct=False, createBy='admin'),
            Answer(question_id=questions[33].id, answer_text="1943", is_correct=False, createBy='admin'),

            Answer(question_id=questions[34].id, answer_text="7 tháng 5 năm 1954", is_correct=True, createBy='admin'),
            Answer(question_id=questions[34].id, answer_text="2 tháng 9 năm 1945", is_correct=False, createBy='admin'),
            Answer(question_id=questions[34].id, answer_text="30 tháng 4 năm 1975", is_correct=False, createBy='admin'),
            Answer(question_id=questions[34].id, answer_text="20 tháng 7 năm 1954", is_correct=False, createBy='admin'),

            # Câu hỏi Địa lý - Núi cao nhất Việt Nam
            Answer(question_id=questions[35].id, answer_text="Fansipan", is_correct=True, createBy='admin'),
            Answer(question_id=questions[35].id, answer_text="Phu Si Lung", is_correct=False, createBy='admin'),
            Answer(question_id=questions[35].id, answer_text="Ngoc Linh", is_correct=False, createBy='admin'),
            Answer(question_id=questions[35].id, answer_text="Bach Ma", is_correct=False, createBy='admin'),

            Answer(question_id=questions[36].id, answer_text="Sông Hồng", is_correct=False, createBy='admin'),
            Answer(question_id=questions[36].id, answer_text="Sông Đồng Nai", is_correct=True, createBy='admin'),
            Answer(question_id=questions[36].id, answer_text="Sông Cửu Long", is_correct=False, createBy='admin'),
            Answer(question_id=questions[36].id, answer_text="Sông Mê Kông", is_correct=False, createBy='admin'),

            Answer(question_id=questions[37].id,
                   answer_text="TP. Hồ Chí Minh, Bình Dương, Đồng Nai và Bà Rịa - Vũng Tàu", is_correct=True, createBy='admin'),
            Answer(question_id=questions[37].id, answer_text="Hà Nội, Hải Phòng, Quảng Ninh và Bắc Ninh",
                   is_correct=False, createBy='admin'),
            Answer(question_id=questions[37].id, answer_text="Đà Nẵng, Thừa Thiên Huế, Quảng Nam và Quảng Ngãi",
                   is_correct=False, createBy='admin'),
            Answer(question_id=questions[37].id, answer_text="Cần Thơ, An Giang, Kiên Giang và Sóc Trăng",
                   is_correct=False, createBy='admin'),

            Answer(question_id=questions[38].id, answer_text="Lúa", is_correct=True, createBy='admin'),
            Answer(question_id=questions[38].id, answer_text="Ngô", is_correct=False, createBy='admin'),
            Answer(question_id=questions[38].id, answer_text="Cao su", is_correct=False, createBy='admin'),
            Answer(question_id=questions[38].id, answer_text="Cà phê", is_correct=False, createBy='admin'),

            Answer(question_id=questions[39].id, answer_text="khoảng 100 triệu", is_correct=False, createBy='admin'),
            Answer(question_id=questions[39].id, answer_text="khoảng 100,3 triệu", is_correct=False, createBy='admin'),
            Answer(question_id=questions[39].id, answer_text="khoảng 101,1 triệu", is_correct=False, createBy='admin'),
            Answer(question_id=questions[39].id, answer_text="khoảng 101,6 triệu", is_correct=True, createBy='admin'),

            Answer(question_id=questions[40].id, answer_text="Hà Nội", is_correct=False, createBy='admin'),
            Answer(question_id=questions[40].id, answer_text="TP. Hồ Chí Minh", is_correct=True, createBy='admin'),
            Answer(question_id=questions[40].id, answer_text="Cần Thơ", is_correct=False, createBy='admin'),
            Answer(question_id=questions[40].id, answer_text="Hải Phòng", is_correct=False, createBy='admin'),

            # Câu hỏi Sinh học - Bào quan chứa DNA
            Answer(question_id=questions[41].id, answer_text="Nhân tế bào", is_correct=True, createBy='admin'),
            Answer(question_id=questions[41].id, answer_text="Ti thể", is_correct=False, createBy='admin'),
            Answer(question_id=questions[41].id, answer_text="Ribosome", is_correct=False, createBy='admin'),
            Answer(question_id=questions[41].id, answer_text="Lysosome", is_correct=False, createBy='admin'),

            Answer(question_id=questions[42].id, answer_text="Thụ tinh", is_correct=False, createBy='admin'),
            Answer(question_id=questions[42].id, answer_text="Nguyên phân", is_correct=True, createBy='admin'),
            Answer(question_id=questions[42].id, answer_text="Tiêu hóa", is_correct=False, createBy='admin'),
            Answer(question_id=questions[42].id, answer_text="Trao đổi chất", is_correct=False, createBy='admin'),

            Answer(question_id=questions[43].id, answer_text="Một loại tế bào", is_correct=False, createBy='admin'),
            Answer(question_id=questions[43].id, answer_text="Một đoạn ADN mang thông tin di truyền", is_correct=True, createBy='admin'),
            Answer(question_id=questions[43].id, answer_text="Một loại protein", is_correct=False, createBy='admin'),
            Answer(question_id=questions[43].id, answer_text="Một bào quan trong tế bào", is_correct=False, createBy='admin'),

            Answer(question_id=questions[44].id, answer_text="Chuỗi xoắn kép", is_correct=True, createBy='admin'),
            Answer(question_id=questions[44].id, answer_text="Dạng hình cầu", is_correct=False, createBy='admin'),
            Answer(question_id=questions[44].id, answer_text="Chuỗi xoắn đơn", is_correct=False, createBy='admin'),
            Answer(question_id=questions[44].id, answer_text="Mạch thẳng không xoắn", is_correct=False, createBy='admin'),

            Answer(question_id=questions[45].id, answer_text="Động vật ăn thịt", is_correct=False, createBy='admin'),
            Answer(question_id=questions[45].id, answer_text="Sinh vật phân giải", is_correct=False, createBy='admin'),
            Answer(question_id=questions[45].id, answer_text="Sinh vật sản xuất", is_correct=True, createBy='admin'),
            Answer(question_id=questions[45].id, answer_text="Động vật ăn cỏ", is_correct=False, createBy='admin'),

            Answer(question_id=questions[46].id, answer_text="Sự hấp thụ nước của thực vật", is_correct=False, createBy='admin'),
            Answer(question_id=questions[46].id, answer_text="Sự phát triển của tầng ozone", is_correct=False, createBy='admin'),
            Answer(question_id=questions[46].id, answer_text="Sự gia tăng khí CO₂ và các khí gây giữ nhiệt",
                   is_correct=True, createBy='admin'),
            Answer(question_id=questions[46].id, answer_text="Sự giảm nhiệt độ toàn cầu", is_correct=False, createBy='admin')
        ]

        for answer in answers:
            db.session.add(answer)

        db.session.commit()

        # Tạo Exams
        exams = [
            Exam(
                exam_name="Kiểm tra Toán học giữa kỳ",
                subject_id=subjects[0].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=1),
                end_time=datetime.datetime.now() + datetime.timedelta(days=1, hours=1.5),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Vật lý cuối kỳ",
                subject_id=subjects[1].id,
                duration=5,
                start_time=datetime.datetime.now() + datetime.timedelta(days=7),
                end_time=datetime.datetime.now() + datetime.timedelta(days=7, hours=2),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Hóa học 15 phút",
                subject_id=subjects[2].id,
                duration=5,
                start_time=datetime.datetime.now() + datetime.timedelta(days=3),
                end_time=datetime.datetime.now() + datetime.timedelta(days=3, minutes=15),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Toán học tổng hợp",
                subject_id=subjects[0].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=2),
                end_time=datetime.datetime.now() + datetime.timedelta(days=2, hours=2),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Vật lý cơ bản",
                subject_id=subjects[1].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=4),
                end_time=datetime.datetime.now() + datetime.timedelta(days=4, hours=1.5),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Hóa học tổng hợp",
                subject_id=subjects[2].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=5),
                end_time=datetime.datetime.now() + datetime.timedelta(days=5, minutes=75),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="English Basic Test",
                subject_id=subjects[3].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=6),
                end_time=datetime.datetime.now() + datetime.timedelta(days=6, hours=1),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Lịch sử Việt Nam",
                subject_id=subjects[4].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=8),
                end_time=datetime.datetime.now() + datetime.timedelta(days=8, minutes=45),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Địa lý Việt Nam",
                subject_id=subjects[5].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=9),
                end_time=datetime.datetime.now() + datetime.timedelta(days=9, hours=1),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Sinh học cơ bản",
                subject_id=subjects[6].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=10),
                end_time=datetime.datetime.now() + datetime.timedelta(days=10, hours=1.5),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Toán học nâng cao",
                subject_id=subjects[0].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=12),
                end_time=datetime.datetime.now() + datetime.timedelta(days=12, hours=2.5),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Vật lý nâng cao",
                subject_id=subjects[1].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=14),
                end_time=datetime.datetime.now() + datetime.timedelta(days=14, hours=3),
                createBy=admin_user.name,
                user_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra tổng hợp đa môn",
                subject_id=subjects[0].id,
                duration=10,
                start_time=datetime.datetime.now() + datetime.timedelta(days=15),
                end_time=datetime.datetime.now() + datetime.timedelta(days=15, hours=2),
                createBy=admin_user.name,
                user_id=admin_record.id
            )
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

            # Đề thi 1: Toán học tổng hợp (10 câu)
            ExamQuestions(exam_id=exams[3].id, question_id=questions[0].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[3].id, question_id=questions[1].id, number_of_questions=2),
            ExamQuestions(exam_id=exams[3].id, question_id=questions[5].id, number_of_questions=3),
            ExamQuestions(exam_id=exams[3].id, question_id=questions[6].id, number_of_questions=4),
            ExamQuestions(exam_id=exams[3].id, question_id=questions[7].id, number_of_questions=5),
            ExamQuestions(exam_id=exams[3].id, question_id=questions[8].id, number_of_questions=6),
            ExamQuestions(exam_id=exams[3].id, question_id=questions[9].id, number_of_questions=7),
            ExamQuestions(exam_id=exams[3].id, question_id=questions[10].id, number_of_questions=8),
            ExamQuestions(exam_id=exams[3].id, question_id=questions[11].id, number_of_questions=9),
            ExamQuestions(exam_id=exams[3].id, question_id=questions[12].id, number_of_questions=10),

            # Đề thi 2: Vật lý cơ bản (10 câu)
            ExamQuestions(exam_id=exams[4].id, question_id=questions[2].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[4].id, question_id=questions[3].id, number_of_questions=2),
            ExamQuestions(exam_id=exams[4].id, question_id=questions[13].id, number_of_questions=3),
            ExamQuestions(exam_id=exams[4].id, question_id=questions[14].id, number_of_questions=4),
            ExamQuestions(exam_id=exams[4].id, question_id=questions[15].id, number_of_questions=5),
            ExamQuestions(exam_id=exams[4].id, question_id=questions[16].id, number_of_questions=6),
            ExamQuestions(exam_id=exams[4].id, question_id=questions[17].id, number_of_questions=7),
            ExamQuestions(exam_id=exams[4].id, question_id=questions[18].id, number_of_questions=8),
            ExamQuestions(exam_id=exams[4].id, question_id=questions[19].id, number_of_questions=9),
            ExamQuestions(exam_id=exams[4].id, question_id=questions[20].id, number_of_questions=10),

            # Đề thi 3: Hóa học tổng hợp (10 câu)
            ExamQuestions(exam_id=exams[5].id, question_id=questions[4].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[5].id, question_id=questions[19].id, number_of_questions=2),
            ExamQuestions(exam_id=exams[5].id, question_id=questions[20].id, number_of_questions=3),
            ExamQuestions(exam_id=exams[5].id, question_id=questions[21].id, number_of_questions=4),
            ExamQuestions(exam_id=exams[5].id, question_id=questions[22].id, number_of_questions=5),
            ExamQuestions(exam_id=exams[5].id, question_id=questions[0].id, number_of_questions=6),
            ExamQuestions(exam_id=exams[5].id, question_id=questions[1].id, number_of_questions=7),
            ExamQuestions(exam_id=exams[5].id, question_id=questions[2].id, number_of_questions=8),
            ExamQuestions(exam_id=exams[5].id, question_id=questions[3].id, number_of_questions=9),
            ExamQuestions(exam_id=exams[5].id, question_id=questions[5].id, number_of_questions=10),

            # Đề thi 4: Tiếng Anh cơ bản (10 câu)
            ExamQuestions(exam_id=exams[6].id, question_id=questions[23].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[6].id, question_id=questions[24].id, number_of_questions=2),
            ExamQuestions(exam_id=exams[6].id, question_id=questions[25].id, number_of_questions=3),
            ExamQuestions(exam_id=exams[6].id, question_id=questions[26].id, number_of_questions=4),
            ExamQuestions(exam_id=exams[6].id, question_id=questions[27].id, number_of_questions=5),
            ExamQuestions(exam_id=exams[6].id, question_id=questions[28].id, number_of_questions=6),
            ExamQuestions(exam_id=exams[6].id, question_id=questions[0].id, number_of_questions=7),
            ExamQuestions(exam_id=exams[6].id, question_id=questions[1].id, number_of_questions=8),
            ExamQuestions(exam_id=exams[6].id, question_id=questions[2].id, number_of_questions=9),
            ExamQuestions(exam_id=exams[6].id, question_id=questions[3].id, number_of_questions=10),

            # Đề thi 5: Lịch sử Việt Nam (10 câu)
            ExamQuestions(exam_id=exams[7].id, question_id=questions[29].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[7].id, question_id=questions[30].id, number_of_questions=2),
            ExamQuestions(exam_id=exams[7].id, question_id=questions[31].id, number_of_questions=3),
            ExamQuestions(exam_id=exams[7].id, question_id=questions[32].id, number_of_questions=4),
            ExamQuestions(exam_id=exams[7].id, question_id=questions[33].id, number_of_questions=5),
            ExamQuestions(exam_id=exams[7].id, question_id=questions[0].id, number_of_questions=6),
            ExamQuestions(exam_id=exams[7].id, question_id=questions[1].id, number_of_questions=7),
            ExamQuestions(exam_id=exams[7].id, question_id=questions[2].id, number_of_questions=8),
            ExamQuestions(exam_id=exams[7].id, question_id=questions[3].id, number_of_questions=9),
            ExamQuestions(exam_id=exams[7].id, question_id=questions[4].id, number_of_questions=10),

            # Đề thi 6: Địa lý Việt Nam (10 câu)
            ExamQuestions(exam_id=exams[8].id, question_id=questions[34].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[8].id, question_id=questions[35].id, number_of_questions=2),
            ExamQuestions(exam_id=exams[8].id, question_id=questions[36].id, number_of_questions=3),
            ExamQuestions(exam_id=exams[8].id, question_id=questions[37].id, number_of_questions=4),
            ExamQuestions(exam_id=exams[8].id, question_id=questions[38].id, number_of_questions=5),
            ExamQuestions(exam_id=exams[8].id, question_id=questions[39].id, number_of_questions=6),
            ExamQuestions(exam_id=exams[8].id, question_id=questions[5].id, number_of_questions=7),
            ExamQuestions(exam_id=exams[8].id, question_id=questions[6].id, number_of_questions=8),
            ExamQuestions(exam_id=exams[8].id, question_id=questions[7].id, number_of_questions=9),
            ExamQuestions(exam_id=exams[8].id, question_id=questions[8].id, number_of_questions=10),

            # Đề thi 7: Sinh học cơ bản (10 câu)
            ExamQuestions(exam_id=exams[9].id, question_id=questions[40].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[9].id, question_id=questions[41].id, number_of_questions=2),
            ExamQuestions(exam_id=exams[9].id, question_id=questions[42].id, number_of_questions=3),
            ExamQuestions(exam_id=exams[9].id, question_id=questions[43].id, number_of_questions=4),
            ExamQuestions(exam_id=exams[9].id, question_id=questions[44].id, number_of_questions=5),
            ExamQuestions(exam_id=exams[9].id, question_id=questions[45].id, number_of_questions=6),
            ExamQuestions(exam_id=exams[9].id, question_id=questions[9].id, number_of_questions=7),
            ExamQuestions(exam_id=exams[9].id, question_id=questions[10].id, number_of_questions=8),
            ExamQuestions(exam_id=exams[9].id, question_id=questions[11].id, number_of_questions=9),
            ExamQuestions(exam_id=exams[9].id, question_id=questions[12].id, number_of_questions=10),

            # Đề thi 8: Toán học nâng cao (10 câu)
            ExamQuestions(exam_id=exams[10].id, question_id=questions[11].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[10].id, question_id=questions[12].id, number_of_questions=2),
            ExamQuestions(exam_id=exams[10].id, question_id=questions[8].id, number_of_questions=3),
            ExamQuestions(exam_id=exams[10].id, question_id=questions[9].id, number_of_questions=4),
            ExamQuestions(exam_id=exams[10].id, question_id=questions[10].id, number_of_questions=5),
            ExamQuestions(exam_id=exams[10].id, question_id=questions[0].id, number_of_questions=6),
            ExamQuestions(exam_id=exams[10].id, question_id=questions[1].id, number_of_questions=7),
            ExamQuestions(exam_id=exams[10].id, question_id=questions[5].id, number_of_questions=8),
            ExamQuestions(exam_id=exams[10].id, question_id=questions[6].id, number_of_questions=9),
            ExamQuestions(exam_id=exams[10].id, question_id=questions[7].id, number_of_questions=10),

            # Đề thi 9: Vật lý nâng cao (10 câu)
            ExamQuestions(exam_id=exams[11].id, question_id=questions[13].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[11].id, question_id=questions[14].id, number_of_questions=2),
            ExamQuestions(exam_id=exams[11].id, question_id=questions[15].id, number_of_questions=3),
            ExamQuestions(exam_id=exams[11].id, question_id=questions[16].id, number_of_questions=4),
            ExamQuestions(exam_id=exams[11].id, question_id=questions[17].id, number_of_questions=5),
            ExamQuestions(exam_id=exams[11].id, question_id=questions[18].id, number_of_questions=6),
            ExamQuestions(exam_id=exams[11].id, question_id=questions[2].id, number_of_questions=7),
            ExamQuestions(exam_id=exams[11].id, question_id=questions[3].id, number_of_questions=8),
            ExamQuestions(exam_id=exams[11].id, question_id=questions[11].id, number_of_questions=9),
            ExamQuestions(exam_id=exams[11].id, question_id=questions[12].id, number_of_questions=10),

            # Đề thi 10: Tổng hợp đa môn (10 câu từ các môn khác nhau)
            ExamQuestions(exam_id=exams[12].id, question_id=questions[0].id, number_of_questions=1),
            ExamQuestions(exam_id=exams[12].id, question_id=questions[2].id, number_of_questions=2),
            ExamQuestions(exam_id=exams[12].id, question_id=questions[4].id, number_of_questions=3),
            ExamQuestions(exam_id=exams[12].id, question_id=questions[23].id, number_of_questions=4),
            ExamQuestions(exam_id=exams[12].id, question_id=questions[29].id, number_of_questions=5),
            ExamQuestions(exam_id=exams[12].id, question_id=questions[34].id, number_of_questions=6),
            ExamQuestions(exam_id=exams[12].id, question_id=questions[40].id, number_of_questions=7),
            ExamQuestions(exam_id=exams[12].id, question_id=questions[5].id, number_of_questions=8),
            ExamQuestions(exam_id=exams[12].id, question_id=questions[13].id, number_of_questions=9),
            ExamQuestions(exam_id=exams[12].id, question_id=questions[19].id, number_of_questions=10)
        ]

        for eq in exam_questions:
            db.session.add(eq)

        db.session.commit()

        # Tạo comments
        comments = [
            Comment(
                exam_id=exams[0].id,
                user_id=student_users[0].id,
                content="Bài thi này khá thú vị, nhưng một số câu hơi khó!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[0].id,
                user_id=student_users[1].id,
                content="Thời gian làm bài vừa đủ, cảm ơn admin!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[1].id,
                user_id=student_users[2].id,
                content="Câu hỏi về điện học rất hay, cần thêm ví dụ thực tế.",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[1].id,
                user_id=admin_user.id,
                content="Đã cập nhật một số câu hỏi dựa trên phản hồi.",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[2].id,
                user_id=student_users[0].id,
                content="Thời gian quá ngắn, cần tăng thêm 5 phút.",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[3].id,
                user_id=student_users[1].id,
                content="Rất hài lòng với độ khó của đề thi này.",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[4].id,
                user_id=student_users[2].id,
                content="Cần giải thích thêm về công thức động lượng.",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[5].id,
                user_id=student_users[0].id,
                content="Đề thi cân bằng, nhưng có lỗi typo ở câu 5.",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[6].id,
                user_id=student_users[1].id,
                content="Phần từ vựng hơi khó, đề nghị giảm độ khó.",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[7].id,
                user_id=student_users[2].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[0].id,
                user_id=student_users[1].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[0].id,
                user_id=student_users[1].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[0].id,
                user_id=student_users[0].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[0].id,
                user_id=student_users[2].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[0].id,
                user_id=student_users[0].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[0].id,
                user_id=student_users[2].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[0].id,
                user_id=student_users[2].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[1].id,
                user_id=student_users[2].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[1].id,
                user_id=student_users[1].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
            Comment(
                exam_id=exams[1].id,
                user_id=student_users[3].id,
                content="Rất bổ ích, mong có thêm đề tương tự!",
                created_at=datetime.datetime.now()
            ),
        ]

        for comment in comments:
            db.session.add(comment)

        db.session.commit()
