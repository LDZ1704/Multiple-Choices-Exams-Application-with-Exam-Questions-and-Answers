import numpy as np
import requests
from googleapiclient.discovery import build
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import pandas as pd
from sqlalchemy import func
from app import db
from app.models import ExamResult, Exam, Subject, Question, Answer, ExamQuestions, Student, User
from datetime import datetime, timedelta


class RecommendationEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.kmeans = KMeans(n_clusters=5, random_state=42)

    def analyze_student_performance(self, student_id):
        results = db.session.query(ExamResult).filter(ExamResult.student_id == student_id).all()

        if not results:
            return None

        performance_data = []
        for result in results:
            exam = result.exam
            performance_data.append({
                'exam_id': exam.id,
                'subject_id': exam.subject_id,
                'subject_name': exam.subject.subject_name,
                'score': result.score,
                'time_taken': result.time_taken,
                'date': result.taken_exam
            })

        df = pd.DataFrame(performance_data)

        analysis = {
            'total_exams': len(results),
            'average_score': df['score'].mean(),
            'best_subject': df.groupby('subject_name')['score'].mean().idxmax(),
            'worst_subject': df.groupby('subject_name')['score'].mean().idxmin(),
            'improvement_trend': self.calculate_improvement_trend(df),
            'weak_areas': self.identify_weak_areas(student_id, df),
            'study_pattern': self.analyze_study_pattern(df)
        }

        return analysis

    def calculate_improvement_trend(self, df):
        df_sorted = df.sort_values('date')
        recent_scores = df_sorted.tail(5)['score'].mean()
        earlier_scores = df_sorted.head(5)['score'].mean()

        if recent_scores > earlier_scores:
            return 'improving'
        elif recent_scores < earlier_scores:
            return 'declining'
        else:
            return 'stable'

    def identify_weak_areas(self, student_id, performance_df):
        weak_subjects = performance_df[performance_df['score'] < 60]['subject_name'].unique()

        weak_topics = []
        for subject in weak_subjects:
            wrong_questions = self.get_wrong_questions(student_id, subject)
            topics = self.extract_topics_from_questions(wrong_questions)
            weak_topics.extend(topics)

        return list(set(weak_topics))

    def get_wrong_questions(self, student_id, subject_name):
        results = db.session.query(ExamResult).join(Exam).join(Subject).filter(ExamResult.student_id == student_id, Subject.subject_name == subject_name).all()

        wrong_questions = []
        for result in results:
            if result.user_answers:
                questions = db.session.query(Question).join(ExamQuestions).filter(ExamQuestions.exam_id == result.exam_id).all()

                for question in questions:
                    user_answer_id = result.user_answers.get(str(question.id))
                    correct_answer = db.session.query(Answer).filter(Answer.question_id == question.id, Answer.is_correct == True).first()

                    if not user_answer_id or (correct_answer and int(user_answer_id) != correct_answer.id):
                        wrong_questions.append(question.question_title)

        return wrong_questions

    def extract_topics_from_questions(self, questions):
        if not questions:
            return []

        vectorized = self.vectorizer.fit_transform(questions)
        feature_names = self.vectorizer.get_feature_names_out()

        if len(questions) >= 5:
            clusters = self.kmeans.fit_predict(vectorized)

            topics = []
            for i in range(self.kmeans.n_clusters):
                cluster_questions = [q for j, q in enumerate(questions) if clusters[j] == i]
                if cluster_questions:
                    cluster_vectorized = self.vectorizer.transform(cluster_questions)
                    mean_vector = cluster_vectorized.mean(axis=0).A1
                    top_indices = mean_vector.argsort()[-3:][::-1]
                    topic = ' '.join([feature_names[idx] for idx in top_indices])
                    topics.append(topic)

            return topics
        else:
            return [' '.join(questions[:3])]

    def recommend_study_materials(self, student_id):
        analysis = self.analyze_student_performance(student_id)
        if not analysis:
            return []

        recommendations = []

        weak_subject = analysis['worst_subject']
        recommendations.extend(self.get_study_materials_for_subject(weak_subject))

        for topic in analysis['weak_areas']:
            materials = self.search_materials_by_topic(topic)
            recommendations.extend(materials)

        practice_exams = self.recommend_practice_exams(student_id, weak_subject)
        recommendations.extend(practice_exams)

        return recommendations[:10]

    def get_study_materials_for_subject(self, subject_name):
        materials = []
        try:
            url = f"https://www.googleapis.com/books/v1/volumes?q={subject_name}+giáo+trình&maxResults=5"
            response = requests.get(url)
            books = response.json().get('items', [])

            for book in books:
                volume_info = book.get('volumeInfo', {})
                materials.append({
                    'type': 'book',
                    'title': volume_info.get('title', 'N/A'),
                    'authors': ', '.join(volume_info.get('authors', [])),
                    'description': volume_info.get('description', '')[:200],
                    'link': volume_info.get('infoLink', '#')
                })
        except:
            pass

        try:
            youtube = build('youtube', 'v3', developerKey='AIzaSyADy2hvEAHa3QEEOePUQAxxeOuw24H31iw')

            search_response = youtube.search().list(
                q=f"{subject_name} bài giảng",
                part='snippet',
                type='video',
                maxResults=5,
                videoDuration='medium'
            ).execute()

            for item in search_response['items']:
                materials.append({
                    'type': 'video',
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'description': item['snippet']['description'][:200],
                    'link': f"https://youtube.com/watch?v={item['id']['videoId']}"
                })
        except:
            pass

        return materials

    def search_materials_by_topic(self, topic):
        materials = []
        return materials

    def recommend_practice_exams(self, student_id, subject_name):
        subject = db.session.query(Subject).filter(Subject.subject_name == subject_name).first()

        if not subject:
            return []

        completed_exams = db.session.query(ExamResult.exam_id).filter(ExamResult.student_id == student_id).subquery()

        recommended_exams = db.session.query(Exam).filter(Exam.subject_id == subject.id, ~Exam.id.in_(completed_exams)).limit(5).all()

        recommendations = []
        for exam in recommended_exams:
            recommendations.append({
                'type': 'practice_exam',
                'title': exam.exam_name,
                'subject': exam.subject.subject_name,
                'duration': exam.duration,
                'link': f'/examdetail?id={exam.id}',
                'difficulty': self.estimate_exam_difficulty(exam.id)
            })

        return recommendations

    def estimate_exam_difficulty(self, exam_id):
        results = db.session.query(ExamResult).filter(ExamResult.exam_id == exam_id).all()

        if not results:
            return 'medium'

        avg_score = sum(r.score for r in results) / len(results)

        if avg_score >= 80:
            return 'easy'
        elif avg_score >= 60:
            return 'medium'
        else:
            return 'hard'

    def analyze_study_pattern(self, df):
        df['date'] = pd.to_datetime(df['date'])
        df['hour'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek

        pattern = {
            'preferred_time': df.groupby('hour').size().idxmax(),
            'preferred_day': df.groupby('day_of_week').size().idxmax(),
            'study_frequency': len(df) / ((df['date'].max() - df['date'].min()).days + 1),
            'consistency_score': self.calculate_consistency(df)
        }

        return pattern

    def calculate_consistency(self, df):
        df_sorted = df.sort_values('date')
        gaps = [(df_sorted.iloc[i]['date'] - df_sorted.iloc[i - 1]['date']).days for i in range(1, len(df_sorted))]

        if not gaps:
            return 0

        # Điểm nhất quán dựa trên độ lệch chuẩn của khoảng cách giữa các lần thi
        std_gap = np.std(gaps)
        max_gap = max(gaps)

        consistency = max(0, (30 - std_gap) / 30)  # Chuẩn hóa về 0-1
        return consistency

    def get_student_ranking(self, student_id, timeframe='all'):
        query = db.session.query(ExamResult.student_id, func.avg(ExamResult.score).label('avg_score'), func.count(ExamResult.id).label('exam_count'))

        if timeframe == 'month':
            cutoff_date = datetime.now() - timedelta(days=30)
            query = query.filter(ExamResult.taken_exam >= cutoff_date)
        elif timeframe == 'week':
            cutoff_date = datetime.now() - timedelta(days=7)
            query = query.filter(ExamResult.taken_exam >= cutoff_date)

        results = query.group_by(ExamResult.student_id).order_by(func.avg(ExamResult.score).desc()).all()
        if not results:
            return {
                'rank': None,
                'total_students': 0,
                'avg_score': None
            }

        for rank, (sid, avg_score, exam_count) in enumerate(results, 1):
            if sid == student_id:
                return {
                    'rank': rank,
                    'total_students': len(results),
                    'avg_score': round(float(avg_score), 1)
                }
        return {
            'rank': None,
            'total_students': len(results),
            'avg_score': None
        }

    def get_subject_ranking(self, student_id, subject_name=None):
        if not subject_name:
            return None

        subject = db.session.query(Subject).filter(Subject.subject_name == subject_name).first()
        if not subject:
            return None

        query = db.session.query(ExamResult.student_id, func.avg(ExamResult.score).label('avg_score')).join(Exam).filter(Exam.subject_id == subject.id)
        results = query.group_by(ExamResult.student_id).order_by(func.avg(ExamResult.score).desc()).all()
        if not results:
            return None

        for rank, (sid, avg_score) in enumerate(results, 1):
            if sid == student_id:
                return {
                    'subject': subject_name,
                    'rank': rank,
                    'total_students': len(results),
                    'avg_score': round(float(avg_score), 1)
                }
        return None

    def get_leaderboard(self, limit=20, timeframe='all', subject_id=None):
        query = db.session.query(
            ExamResult.student_id,
            func.avg(ExamResult.score).label('avg_score'),
            func.count(ExamResult.id).label('exam_count'),
            func.max(ExamResult.score).label('highest_score')
        ).join(Student).join(User)

        if timeframe == 'month':
            cutoff_date = datetime.now() - timedelta(days=30)
            query = query.filter(ExamResult.taken_exam >= cutoff_date)
        elif timeframe == 'week':
            cutoff_date = datetime.now() - timedelta(days=7)
            query = query.filter(ExamResult.taken_exam >= cutoff_date)

        if subject_id:
            query = query.join(Exam).filter(Exam.subject_id == subject_id)

        results = query.group_by(ExamResult.student_id).order_by(func.avg(ExamResult.score).desc()).limit(limit).all()
        leaderboard = []
        for i, (student_id, avg_score, exam_count, highest_score) in enumerate(results):
            student = db.session.query(Student).filter(Student.id == student_id).first()
            if student:
                user = db.session.query(User).filter(User.id == student.user_id).first()
                leaderboard.append({
                    'rank': i + 1,
                    'student_name': user.name if user else 'Unknown',
                    'avatar': user.avatar if user else None,
                    'avg_score': round(avg_score, 1),
                    'exam_count': exam_count,
                    'highest_score': highest_score
                })
        return leaderboard

    def get_achievement_badges(self, student_id):
        badges = []
        results = db.session.query(ExamResult).filter(ExamResult.student_id == student_id).all()
        if not results:
            return badges

        scores = [r.score for r in results]
        avg_score = sum(scores) / len(scores)
        if avg_score >= 90:
            badges.append({
                'name': 'Xuất Sắc',
                'icon': 'fas fa-trophy',
                'color': 'gold',
                'description': 'Điểm trung bình >= 90'
            })
        elif avg_score >= 80:
            badges.append({
                'name': 'Giỏi',
                'icon': 'fas fa-medal',
                'color': 'silver',
                'description': 'Điểm trung bình >= 80'
            })
        perfect_scores = [r for r in results if r.score == 100]
        if len(perfect_scores) >= 5:
            badges.append({
                'name': 'Hoàn Hảo',
                'icon': 'fas fa-star',
                'color': 'gold',
                'description': '5+ bài thi đạt 100 điểm'
            })
        recent_results = sorted(results, key=lambda x: x.taken_exam)[-10:]
        if len(recent_results) >= 5:
            consistent = all(r.score >= 70 for r in recent_results)
            if consistent:
                badges.append({
                    'name': 'Nhất Quán',
                    'icon': 'fas fa-chart-line',
                    'color': 'blue',
                    'description': 'Điểm ổn định >= 70 trong 5 bài gần nhất'
                })
        if len(results) >= 50:
            badges.append({
                'name': 'Siêng Năng',
                'icon': 'fas fa-graduation-cap',
                'color': 'green',
                'description': 'Hoàn thành 50+ bài thi'
            })
        return badges


recommendation_engine = RecommendationEngine()