# 📚 Multiple Choices Exams Application

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Hệ thống thi trắc nghiệm trực tuyến với kho đề thi và đáp án**

[Tính năng](#-tính-năng) • [Cài đặt](#-cài-đặt) • [Sử dụng](#-sử-dụng) • [Demo](#-demo) • [Đóng góp](#-đóng-góp)

</div>

---

## 📋 Mục lục

- [Giới thiệu](#-giới-thiệu)
- [Tính năng](#-tính-năng)
- [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Cấu hình](#-cấu-hình)
- [Sử dụng](#-sử-dụng)
- [Screenshots](#-screenshots)
- [Đóng góp](#-đóng-góp)

---

## 🎯 Giới thiệu

Dự án này được phát triển nhằm tạo ra một hệ thống thi trắc nghiệm trực tuyến hiện đại cho mọi đối tượng, giúp:

- **Sinh viên**: Rèn luyện kiến thức thông qua việc làm bài thi trắc nghiệm với giao diện thân thiện, đóng góp các đề thi.
- **Quản trị viên**: Giám sát hệ thống, quản lý người dùng và tạo báo cáo thống kê chi tiết, quản lý đề thi, câu hỏi, đánh giá điểm của người dùng.

### 🎓 Ngữ cảnh sử dụng

Hệ thống khắc phục các vấn đề truyền thống trong việc tổ chức thi:
- ⏱️ **Tiết kiệm thời gian**: Tự động chấm điểm và tạo đề thi
- 📊 **Quản lý hiệu quả**: Lưu trữ và phân loại câu hỏi, đề thi một cách khoa học
- 🔒 **Bảo mật**: Ngăn chặn rò rỉ đề thi và gian lận
- 📈 **Phân tích**: Thống kê chi tiết về kết quả học tập

---

## ✨ Tính năng

### 👨‍🎓 Dành cho Sinh viên
- ✅ Thi trực tuyến với giới hạn thời gian
- 📝 Xem kết quả ngay sau khi nộp bài
- 🔄 Xem lại bài thi đã làm
- 📊 Theo dõi lịch sử làm bài và tiến độ học tập
- 🎯 Luyện tập với các đề thi mẫu 
- 📚 Đóng góp thêm đề thi, câu hỏi
- ⚙️ Tạo đề thi tự động theo tiêu chí:
  - Số lượng câu hỏi
  - Mức độ khó (dễ, trung bình, khó)
  - Phân bổ theo chủ đề

### 👨‍💼 Dành cho Admin
- 👥 Quản lý người dùng (thêm, sửa, xóa, phân quyền)
- 📖 Quản lý đề thi, câu hỏi.
- 📖 Quản lý môn học và học phần
- 📊 Xem thống kê và báo cáo tổng quan
- 🔐 Cấu hình bảo mật hệ thống

---

## 🛠 Công nghệ sử dụng

### Backend
- **Framework**: Flask 2.3+
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login + hashlib
- **Database**: MySQL 8.0+
- **Task Queue**: Celery (đang phát triển)

### Frontend
- **UI Framework**: Bootstrap 5.3
- **JavaScript**: Vanilla JS + jQuery
- **Icons**: Font Awesome 6
- **Charts**: Chart.js (cho thống kê)

### DevOps & Tools
- **Version Control**: Git/GitHub
- **Container**: Docker (đang phát triển)
- **Web Server**: Gunicorn + Nginx (đang phát triển)
- **Testing**: pytest (đang phát triển)

---

## 🏗 Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────┐
│                   Client (Browser)                   │
│              Bootstrap 5 + JavaScript                │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/HTTPS
┌──────────────────────▼──────────────────────────────┐
│                  Flask Application                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Routes     │  │   Models     │  │   Utils    │ │
│  │  (Views)     │  │ (SQLAlchemy) │  │  (Helpers) │ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              MySQL Database Server                   │
│     (users, exams, questions, results, etc.)        │
└─────────────────────────────────────────────────────┘
```

### 📊 Database Schema

```sql
users ──┬── exam_results
        │
subjects ──┬── questions ──┬── answers
           │               │
           └── exams ──────┴── exam_questions
```

---

## 🚀 Cài đặt

### Yêu cầu hệ thống
- Python 3.0 hoặc cao hơn
- MySQL 8.0 hoặc cao hơn
- pip (Python package manager)
- virtualenv (khuyến nghị)

### Bước 1: Clone repository

```bash
git clone https://github.com/LDZ1704/Multiple-Choices-Exams-Application.git
cd Multiple-Choices-Exams-Application
```

### Bước 2: Tạo môi trường ảo

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình database

```bash
# Tạo database trong MySQL
mysql -u root -p
CREATE DATABASE exam_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;
```

### Bước 5: Cấu hình environment variables

Tạo file `.env` trong thư mục gốc:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URI=mysql://username:password@localhost/exam_system
```

### Bước 6: Khởi tạo database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Bước 7: Chạy ứng dụng

```bash
# Development mode
flask run

# Production mode
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

Truy cập: `http://localhost:5000`

---

## ⚙️ Cấu hình

### Tài khoản mặc định

Sau khi cài đặt, hệ thống tạo sẵn các tài khoản demo:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Student | student1 | 123      |

⚠️ **Lưu ý**: Đổi mật khẩu ngay sau lần đăng nhập đầu tiên!

## 📖 Sử dụng

### 1. Đăng nhập hệ thống

Truy cập `/login` và nhập username/password

### 2. Sinh viên tạo đề thi

```
Dashboard → Đề thi của bạn → Thêm đề thi mới
```

1. Nhập tên đề thi
2. Chọn môn học
3. Nhập thời gian thi
4. Nhập nội dung câu hỏi
5. Thêm các đáp án và đánh dấu đáp án đúng

### 3. Tạo đề thi

```
Dashboard → Quản lý đề thi → Tạo đề thi mới
```

**Tạo thủ công:**
- Chọn từng câu hỏi để thêm vào đề

**Tạo tự động:**
- Chọn số lượng câu theo mức độ
- Hệ thống tự động chọn câu phù hợp

### 4. Sinh viên làm bài thi

```
Dashboard → Danh sách đề thi → Bắt đầu thi
```

- Đếm ngược thời gian tự động
- Lưu đáp án tự động
- Nộp bài trước khi hết giờ

---

## 📸 Screenshots

### 🏠 Trang chủ
![Homepage](docs/images/homepage.png)

### 📝 Giao diện thi
![Exam Interface](docs/images/exam-interface.png)

### 📊 Thống kê kết quả
![Statistics Dashboard](docs/images/statistics.png)

---

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! 

### Cách đóng góp:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

### Quy tắc coding:
- Tuân thủ PEP 8 style guide
- Viết docstrings cho functions/classes
- Thêm unit tests cho features mới
- Cập nhật documentation khi cần

---

## 👥 Tác giả

**LDZ1704**
- GitHub: [@LDZ1704](https://github.com/LDZ1704)
- Email: lamn9049@gmail.com

---

## 📞 Liên hệ & Hỗ trợ

- 🐛 Báo lỗi: [GitHub Issues](https://github.com/LDZ1704/Multiple-Choices-Exams-Application/issues)
- 💬 Thảo luận: [GitHub Discussions](https://github.com/LDZ1704/Multiple-Choices-Exams-Application/discussions)
- 📧 Email: lamn9049@gmail.com

---

<div align="center">

**⭐ Nếu thấy dự án hữu ích, hãy cho một ngôi sao nhé! ⭐**

Made with ❤️ by LDZ1704

</div>