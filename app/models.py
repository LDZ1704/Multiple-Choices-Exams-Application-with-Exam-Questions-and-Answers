import datetime
from enum import Enum as RoleEnum
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, TEXT, JSON
from sqlalchemy.orm import relationship
import hashlib
from app import app, db


class Role(RoleEnum):
    ADMIN = 1,
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
    createdAt = Column(DateTime, default=datetime.datetime.now())
    updateAt = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

    student = relationship("Student", back_populates="user", uselist=False)
    admin = relationship("Admin", back_populates="user", uselist=False)
    comments = relationship("Comment", back_populates="user")


class Student(Base):
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, unique=True)

    user = relationship("User", back_populates="student")
    exam_results = relationship("ExamResult", back_populates="student")


class Admin(Base):
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, unique=True)

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
    comments = relationship("Comment", back_populates="exam")


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
    user_answers = db.Column(JSON)

    student = relationship("Student", back_populates="exam_results")
    exam = relationship("Exam", back_populates="exam_results")


class ExamQuestions(Base):
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False)
    number_of_questions = Column(Integer, nullable=False, default=0)

    exam = relationship("Exam", back_populates="exam_questions")
    question = relationship("Question", back_populates="exam_questions")


class Comment(Base):
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    content = Column(TEXT, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

    exam = relationship("Exam", back_populates="comments")
    user = relationship("User", back_populates="comments")


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
            ),
            Subject(
                subject_name="Tiếng Anh",
                description="Môn học về ngôn ngữ Anh",
                admin_id=admin_record.id
            ),
            Subject(
                subject_name="Lịch sử",
                description="Môn học về lịch sử Việt Nam và thế giới",
                admin_id=admin_record.id
            ),
            Subject(
                subject_name="Địa lý",
                description="Môn học về địa lý tự nhiên và kinh tế",
                admin_id=admin_record.id
            ),
            Subject(
                subject_name="Sinh học",
                description="Môn học về các quá trình sinh học",
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
        ]

        for chapter in chapters:
            db.session.add(chapter)

        db.session.commit()

        # Tạo Questions
        questions = [
            # Toán học - Đại số
            Question(question_title="2 + 2 = ?", createBy="admin", chapter_id=chapters[0].id, admin_id=admin_record.id),
            Question(question_title="Nghiệm của phương trình x² - 4 = 0 là:", createBy="admin",
                     chapter_id=chapters[0].id, admin_id=admin_record.id),

            # Vật lý - Cơ học
            Question(question_title="Công thức tính vận tốc là:", createBy="admin", chapter_id=chapters[3].id,
                     admin_id=admin_record.id),
            Question(question_title="Gia tốc trọng trường trên Trái Đất là:", createBy="admin",
                     chapter_id=chapters[3].id, admin_id=admin_record.id),

            # Hóa học - Hóa vô cơ
            Question(question_title="Công thức hóa học của nước là:", createBy="admin", chapter_id=chapters[6].id,
                     admin_id=admin_record.id),

            # Toán học - Đại số (thêm)
            Question(question_title="3x + 5 = 14, x = ?", createBy="admin", chapter_id=chapters[0].id,
                     admin_id=admin_record.id),
            Question(question_title="√16 = ?", createBy="admin", chapter_id=chapters[0].id,
                     admin_id=admin_record.id),
            Question(question_title="2³ = ?", createBy="admin", chapter_id=chapters[0].id,
                     admin_id=admin_record.id),

            # Toán học - Hình học
            Question(question_title="Diện tích hình vuông cạnh 5cm là:", createBy="admin",
                     chapter_id=chapters[1].id, admin_id=admin_record.id),
            Question(question_title="Chu vi hình tròn bán kính 7cm là:", createBy="admin",
                     chapter_id=chapters[1].id, admin_id=admin_record.id),
            Question(question_title="Thể tích hình lập phương cạnh 3cm là:", createBy="admin",
                     chapter_id=chapters[1].id, admin_id=admin_record.id),

            # Toán học - Giải tích
            Question(question_title="Đạo hàm của x² là:", createBy="admin", chapter_id=chapters[2].id,
                     admin_id=admin_record.id),
            Question(question_title="∫x dx = ?", createBy="admin", chapter_id=chapters[2].id,
                     admin_id=admin_record.id),

            # Vật lý - Cơ học (thêm)
            Question(question_title="Định luật Newton thứ nhất nói về:", createBy="admin",
                     chapter_id=chapters[3].id, admin_id=admin_record.id),
            Question(question_title="Công thức tính động lượng là:", createBy="admin", chapter_id=chapters[3].id,
                     admin_id=admin_record.id),

            # Vật lý - Nhiệt học
            Question(question_title="Nhiệt độ sôi của nước ở áp suất tiêu chuẩn:", createBy="admin",
                     chapter_id=chapters[4].id, admin_id=admin_record.id),
            Question(question_title="Đơn vị đo nhiệt lượng là:", createBy="admin", chapter_id=chapters[4].id,
                     admin_id=admin_record.id),

            # Vật lý - Điện học
            Question(question_title="Định luật Ohm có dạng:", createBy="admin", chapter_id=chapters[5].id,
                     admin_id=admin_record.id),
            Question(question_title="Điện trở của dây dẫn phụ thuộc vào:", createBy="admin",
                     chapter_id=chapters[5].id, admin_id=admin_record.id),

            # Hóa học - Hóa vô cơ (thêm)
            Question(question_title="Số oxi hóa của H trong H₂O là:", createBy="admin", chapter_id=chapters[6].id,
                     admin_id=admin_record.id),
            Question(question_title="Axit mạnh nhất trong các axit sau:", createBy="admin",
                     chapter_id=chapters[6].id, admin_id=admin_record.id),

            # Hóa học - Hóa hữu cơ
            Question(question_title="Công thức phân tử của methane là:", createBy="admin",
                     chapter_id=chapters[7].id, admin_id=admin_record.id),
            Question(question_title="Ancol etylic có công thức:", createBy="admin", chapter_id=chapters[7].id,
                     admin_id=admin_record.id),

            # Tiếng Anh - Grammar
            Question(question_title="Choose the correct form: 'I ___ to school yesterday'", createBy="admin",
                     chapter_id=chapters[8].id, admin_id=admin_record.id),
            Question(question_title="Which is correct: 'He ___ English very well'", createBy="admin",
                     chapter_id=chapters[8].id, admin_id=admin_record.id),

            # Tiếng Anh - Vocabulary
            Question(question_title="What does 'beautiful' mean?", createBy="admin", chapter_id=chapters[9].id,
                     admin_id=admin_record.id),
            Question(question_title="The opposite of 'big' is:", createBy="admin", chapter_id=chapters[9].id,
                     admin_id=admin_record.id),

            # Tiếng Anh - Reading
            Question(question_title="In the sentence 'The cat is sleeping', what is the subject?", createBy="admin",
                     chapter_id=chapters[10].id, admin_id=admin_record.id),
            Question(question_title="What tense is used in 'I am reading a book'?", createBy="admin",
                     chapter_id=chapters[10].id, admin_id=admin_record.id),

            # Lịch sử - Lịch sử cổ đại
            Question(question_title="Nước Văn Lang được thành lập vào thời gian nào?", createBy="admin",
                     chapter_id=chapters[11].id, admin_id=admin_record.id),
            Question(question_title="Ai là người sáng lập ra nước Âu Lạc?", createBy="admin",
                     chapter_id=chapters[11].id, admin_id=admin_record.id),

            # Lịch sử - Lịch sử cận đại
            Question(question_title="Cuộc khởi nghĩa Tây Sơn diễn ra vào thế kỷ nào?", createBy="admin",
                     chapter_id=chapters[12].id, admin_id=admin_record.id),
            Question(question_title="Ai là hoàng đế cuối cùng của triều Nguyễn?", createBy="admin",
                     chapter_id=chapters[12].id, admin_id=admin_record.id),

            # Lịch sử - Lịch sử hiện đại
            Question(question_title="Cách mạng tháng Tám diễn ra vào năm nào?", createBy="admin",
                     chapter_id=chapters[13].id, admin_id=admin_record.id),
            Question(question_title="Chiến dịch Điện Biên Phủ kết thúc vào ngày nào?", createBy="admin",
                     chapter_id=chapters[13].id, admin_id=admin_record.id),

            # Địa lý - Địa lý tự nhiên
            Question(question_title="Núi cao nhất Việt Nam là:", createBy="admin", chapter_id=chapters[14].id,
                     admin_id=admin_record.id),
            Question(question_title="Sông dài nhất Việt Nam là:", createBy="admin", chapter_id=chapters[14].id,
                     admin_id=admin_record.id),

            # Địa lý - Địa lý kinh tế
            Question(question_title="Khu vực kinh tế trọng điểm phía Nam là:", createBy="admin",
                     chapter_id=chapters[15].id, admin_id=admin_record.id),
            Question(question_title="Cây trồng chủ yếu ở ĐBSCL là:", createBy="admin", chapter_id=chapters[15].id,
                     admin_id=admin_record.id),

            # Địa lý - Địa lý dân cư
            Question(question_title="Dân số Việt Nam hiện tại khoảng:", createBy="admin",
                     chapter_id=chapters[16].id, admin_id=admin_record.id),
            Question(question_title="Thành phố có dân số đông nhất Việt Nam là:", createBy="admin",
                     chapter_id=chapters[16].id, admin_id=admin_record.id),

            # Sinh học - Tế bào học
            Question(question_title="Bào quan nào chứa DNA trong tế bào?", createBy="admin",
                     chapter_id=chapters[17].id, admin_id=admin_record.id),
            Question(question_title="Quá trình phân chia tế bào được gọi là:", createBy="admin",
                     chapter_id=chapters[17].id, admin_id=admin_record.id),

            # Sinh học - Di truyền học
            Question(question_title="Gen là gì?", createBy="admin", chapter_id=chapters[18].id,
                     admin_id=admin_record.id),
            Question(question_title="DNA có cấu trúc như thế nào?", createBy="admin", chapter_id=chapters[18].id,
                     admin_id=admin_record.id),

            # Sinh học - Sinh thái học
            Question(question_title="Chuỗi thức ăn bắt đầu từ:", createBy="admin", chapter_id=chapters[19].id,
                     admin_id=admin_record.id),
            Question(question_title="Hiệu ứng nhà kính do đâu gây ra?", createBy="admin",
                     chapter_id=chapters[19].id, admin_id=admin_record.id),
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

            # Câu hỏi 6: 3x + 5 = 14
            Answer(question_id=questions[5].id, answer_text="x = 3", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[5].id, answer_text="x = 4", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[5].id, answer_text="x = 5", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[5].id, answer_text="x = 2", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 7: √16 = ?
            Answer(question_id=questions[6].id, answer_text="4", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[6].id, answer_text="8", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[6].id, answer_text="16", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[6].id, answer_text="2", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 8: 2³ = ?
            Answer(question_id=questions[7].id, answer_text="8", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[7].id, answer_text="6", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[7].id, answer_text="9", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[7].id, answer_text="12", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 9: Diện tích hình vuông cạnh 5cm
            Answer(question_id=questions[8].id, answer_text="25 cm²", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[8].id, answer_text="20 cm²", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[8].id, answer_text="10 cm²", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[8].id, answer_text="15 cm²", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 10: Chu vi hình tròn bán kính 7cm
            Answer(question_id=questions[9].id, answer_text="44 cm", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[9].id, answer_text="14 cm", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[9].id, answer_text="22 cm", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[9].id, answer_text="28 cm", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 11: Thể tích hình lập phương cạnh 3cm
            Answer(question_id=questions[10].id, answer_text="27 cm³", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[10].id, answer_text="9 cm³", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[10].id, answer_text="18 cm³", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[10].id, answer_text="36 cm³", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 12: Đạo hàm của x²
            Answer(question_id=questions[11].id, answer_text="2x", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[11].id, answer_text="x²", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[11].id, answer_text="x", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[11].id, answer_text="2x²", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 13: ∫x dx = ?
            Answer(question_id=questions[12].id, answer_text="x²/2 + C", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[12].id, answer_text="x² + C", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[12].id, answer_text="2x + C", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[12].id, answer_text="x + C", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 14: Định luật Newton thứ nhất
            Answer(question_id=questions[13].id, answer_text="Quán tính", is_correct=True,
                   admin_id=admin_record.id),
            Answer(question_id=questions[13].id, answer_text="Gia tốc", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[13].id, answer_text="Tác dụng phản tác dụng", is_correct=False,
                   admin_id=admin_record.id),
            Answer(question_id=questions[13].id, answer_text="Hấp dẫn", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 15: Công thức tính động lượng
            Answer(question_id=questions[14].id, answer_text="p = mv", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[14].id, answer_text="p = ma", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[14].id, answer_text="p = Ft", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[14].id, answer_text="p = mv²", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi 16: Nhiệt độ sôi của nước
            Answer(question_id=questions[15].id, answer_text="100°C", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[15].id, answer_text="0°C", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[15].id, answer_text="50°C", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[15].id, answer_text="200°C", is_correct=False, admin_id=admin_record.id),

            Answer(question_id=questions[16].id, answer_text="100°C", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[16].id, answer_text="0°C", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[16].id, answer_text="50°C", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[16].id, answer_text="200°C", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi English - Grammar
            Answer(question_id=questions[24].id, answer_text="went", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[24].id, answer_text="go", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[24].id, answer_text="going", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[24].id, answer_text="gone", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi Lịch sử - Cách mạng tháng Tám
            Answer(question_id=questions[32].id, answer_text="1945", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[32].id, answer_text="1946", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[32].id, answer_text="1944", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[32].id, answer_text="1943", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi Địa lý - Núi cao nhất Việt Nam
            Answer(question_id=questions[34].id, answer_text="Fansipan", is_correct=True, admin_id=admin_record.id),
            Answer(question_id=questions[34].id, answer_text="Phu Si Lung", is_correct=False,
                   admin_id=admin_record.id),
            Answer(question_id=questions[34].id, answer_text="Ngoc Linh", is_correct=False,
                   admin_id=admin_record.id),
            Answer(question_id=questions[34].id, answer_text="Bach Ma", is_correct=False, admin_id=admin_record.id),

            # Câu hỏi Sinh học - Bào quan chứa DNA
            Answer(question_id=questions[40].id, answer_text="Nhân tế bào", is_correct=True,
                   admin_id=admin_record.id),
            Answer(question_id=questions[40].id, answer_text="Ti thể", is_correct=False, admin_id=admin_record.id),
            Answer(question_id=questions[40].id, answer_text="Ribosome", is_correct=False,
                   admin_id=admin_record.id),
            Answer(question_id=questions[40].id, answer_text="Lysosome", is_correct=False,
                   admin_id=admin_record.id),
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
                createBy="admin",
                admin_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Vật lý cuối kỳ",
                subject_id=subjects[1].id,
                duration=5,
                start_time=datetime.datetime.now() + datetime.timedelta(days=7),
                end_time=datetime.datetime.now() + datetime.timedelta(days=7, hours=2),
                createBy="admin",
                admin_id=admin_record.id
            ),
            Exam(
                exam_name="Kiểm tra Hóa học 15 phút",
                subject_id=subjects[2].id,
                duration=5,
                start_time=datetime.datetime.now() + datetime.timedelta(days=3),
                end_time=datetime.datetime.now() + datetime.timedelta(days=3, minutes=15),
                createBy="admin",
                admin_id=admin_record.id
            ),

            # Đề thi 1: Toán học tổng hợp
            Exam(
                exam_name="Kiểm tra Toán học tổng hợp",
                subject_id=subjects[0].id,
                duration=120,
                start_time=datetime.datetime.now() + datetime.timedelta(days=2),
                end_time=datetime.datetime.now() + datetime.timedelta(days=2, hours=2),
                createBy="admin",
                admin_id=admin_record.id
            ),
            # Đề thi 2: Vật lý cơ bản
            Exam(
                exam_name="Kiểm tra Vật lý cơ bản",
                subject_id=subjects[1].id,
                duration=90,
                start_time=datetime.datetime.now() + datetime.timedelta(days=4),
                end_time=datetime.datetime.now() + datetime.timedelta(days=4, hours=1.5),
                createBy="admin",
                admin_id=admin_record.id
            ),
            # Đề thi 3: Hóa học tổng hợp
            Exam(
                exam_name="Kiểm tra Hóa học tổng hợp",
                subject_id=subjects[2].id,
                duration=75,
                start_time=datetime.datetime.now() + datetime.timedelta(days=5),
                end_time=datetime.datetime.now() + datetime.timedelta(days=5, minutes=75),
                createBy="admin",
                admin_id=admin_record.id
            ),
            # Đề thi 4: Tiếng Anh cơ bản
            Exam(
                exam_name="English Basic Test",
                subject_id=subjects[3].id,
                duration=60,
                start_time=datetime.datetime.now() + datetime.timedelta(days=6),
                end_time=datetime.datetime.now() + datetime.timedelta(days=6, hours=1),
                createBy="admin",
                admin_id=admin_record.id
            ),
            # Đề thi 5: Lịch sử Việt Nam
            Exam(
                exam_name="Kiểm tra Lịch sử Việt Nam",
                subject_id=subjects[4].id,
                duration=45,
                start_time=datetime.datetime.now() + datetime.timedelta(days=8),
                end_time=datetime.datetime.now() + datetime.timedelta(days=8, minutes=45),
                createBy="admin",
                admin_id=admin_record.id
            ),
            # Đề thi 6: Địa lý Việt Nam
            Exam(
                exam_name="Kiểm tra Địa lý Việt Nam",
                subject_id=subjects[5].id,
                duration=60,
                start_time=datetime.datetime.now() + datetime.timedelta(days=9),
                end_time=datetime.datetime.now() + datetime.timedelta(days=9, hours=1),
                createBy="admin",
                admin_id=admin_record.id
            ),
            # Đề thi 7: Sinh học cơ bản
            Exam(
                exam_name="Kiểm tra Sinh học cơ bản",
                subject_id=subjects[6].id,
                duration=90,
                start_time=datetime.datetime.now() + datetime.timedelta(days=10),
                end_time=datetime.datetime.now() + datetime.timedelta(days=10, hours=1.5),
                createBy="admin",
                admin_id=admin_record.id
            ),
            # Đề thi 8: Toán học nâng cao
            Exam(
                exam_name="Kiểm tra Toán học nâng cao",
                subject_id=subjects[0].id,
                duration=150,
                start_time=datetime.datetime.now() + datetime.timedelta(days=12),
                end_time=datetime.datetime.now() + datetime.timedelta(days=12, hours=2.5),
                createBy="admin",
                admin_id=admin_record.id
            ),
            # Đề thi 9: Vật lý nâng cao
            Exam(
                exam_name="Kiểm tra Vật lý nâng cao",
                subject_id=subjects[1].id,
                duration=180,
                start_time=datetime.datetime.now() + datetime.timedelta(days=14),
                end_time=datetime.datetime.now() + datetime.timedelta(days=14, hours=3),
                createBy="admin",
                admin_id=admin_record.id
            ),
            # Đề thi 10: Tổng hợp các môn
            Exam(
                exam_name="Kiểm tra tổng hợp đa môn",
                subject_id=subjects[0].id,
                duration=120,
                start_time=datetime.datetime.now() + datetime.timedelta(days=15),
                end_time=datetime.datetime.now() + datetime.timedelta(days=15, hours=2),
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
            ExamQuestions(exam_id=exams[12].id, question_id=questions[0].id, number_of_questions=1),  # Toán
            ExamQuestions(exam_id=exams[12].id, question_id=questions[2].id, number_of_questions=2),  # Vật lý
            ExamQuestions(exam_id=exams[12].id, question_id=questions[4].id, number_of_questions=3),  # Hóa học
            ExamQuestions(exam_id=exams[12].id, question_id=questions[23].id, number_of_questions=4), # Tiếng Anh
            ExamQuestions(exam_id=exams[12].id, question_id=questions[29].id, number_of_questions=5),  # Lịch sử
            ExamQuestions(exam_id=exams[12].id, question_id=questions[34].id, number_of_questions=6),  # Địa lý
            ExamQuestions(exam_id=exams[12].id, question_id=questions[40].id, number_of_questions=7), # Sinh học
            ExamQuestions(exam_id=exams[12].id, question_id=questions[5].id, number_of_questions=8),  # Toán
            ExamQuestions(exam_id=exams[12].id, question_id=questions[13].id, number_of_questions=9),  # Vật lý
            ExamQuestions(exam_id=exams[12].id, question_id=questions[19].id, number_of_questions=10), # Hóa học
        ]

        for eq in exam_questions:
            db.session.add(eq)

        db.session.commit()

        # Tạo ExamResults
        exam_results = [
            ExamResult(
                student_id=student_records[0].id,
                exam_id=exams[0].id,
                score=100,
                taken_exam=datetime.datetime.now() - datetime.timedelta(days=1)
            ),
            ExamResult(
                student_id=student_records[1].id,
                exam_id=exams[0].id,
                score=50,
                taken_exam=datetime.datetime.now() - datetime.timedelta(days=1)
            ),
            ExamResult(
                student_id=student_records[2].id,
                exam_id=exams[1].id,
                score=50,
                taken_exam=datetime.datetime.now() - datetime.timedelta(days=2)
            ),
            ExamResult(
                student_id=student_records[0].id,
                exam_id=exams[2].id,
                score=0,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=2)
            ),

            # Kết quả cho đề thi 1: Toán học tổng hợp
            ExamResult(
                student_id=student_records[0].id,
                exam_id=exams[3].id,
                score=88,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=5)
            ),
            ExamResult(
                student_id=student_records[1].id,
                exam_id=exams[3].id,
                score=76,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=4)
            ),
            ExamResult(
                student_id=student_records[2].id,
                exam_id=exams[3].id,
                score=93,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=3)
            ),

            # Kết quả cho đề thi 2: Vật lý cơ bản
            ExamResult(
                student_id=student_records[0].id,
                exam_id=exams[4].id,
                score=82,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=8)
            ),
            ExamResult(
                student_id=student_records[1].id,
                exam_id=exams[4].id,
                score=90,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=7)
            ),

            # Kết quả cho đề thi 3: Hóa học tổng hợp
            ExamResult(
                student_id=student_records[2].id,
                exam_id=exams[5].id,
                score=85,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=12)
            ),
            ExamResult(
                student_id=student_records[0].id,
                exam_id=exams[5].id,
                score=79,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=10)
            ),

            # Kết quả cho đề thi 4: Tiếng Anh cơ bản
            ExamResult(
                student_id=student_records[1].id,
                exam_id=exams[6].id,
                score=87,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=15)
            ),
            ExamResult(
                student_id=student_records[2].id,
                exam_id=exams[6].id,
                score=91,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=14)
            ),

            # Kết quả cho đề thi 5: Lịch sử Việt Nam
            ExamResult(
                student_id=student_records[0].id,
                exam_id=exams[7].id,
                score=94,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=18)
            ),
            ExamResult(
                student_id=student_records[1].id,
                exam_id=exams[7].id,
                score=86,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=17)
            ),
            ExamResult(
                student_id=student_records[2].id,
                exam_id=exams[7].id,
                score=89,
                taken_exam=datetime.datetime.now() - datetime.timedelta(hours=16)
            ),
        ]

        for result in exam_results:
            db.session.add(result)

        db.session.commit()

        #Tạo comments
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
        ]

        for comment in comments:
            db.session.add(comment)

        db.session.commit()