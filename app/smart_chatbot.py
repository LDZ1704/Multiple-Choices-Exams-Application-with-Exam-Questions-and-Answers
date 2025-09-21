import google.generativeai as genai
from app import dao, app


class SmartChatBot:
    def __init__(self):
        # Lấy API key từ config
        api_key = app.config.get('GOOGLE_GEMINI_API_KEY')
        if not api_key:
            raise ValueError("Google Gemini API key not configured")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        self.system_context = """
                Bạn là trợ lý giáo dục AI thông minh cho hệ thống thi trực tuyến LmaoQuiz.

                Vai trò của bạn:
                - Trả lời mọi câu hỏi của học sinh một cách tự nhiên và hữu ích
                - Giải thích kiến thức học tập, công thức, khái niệm
                - Hỗ trợ tìm đề thi khi được hỏi
                - Đưa ra lời khuyên học tập cá nhân hóa khi có thông tin người dùng

                Phong cách giao tiếp:
                - Trả lời bằng tiếng Việt
                - Thân thiện, nhiệt tình
                - Sử dụng emoji phù hợp
                - Giải thích rõ ràng, dễ hiểu
                - Khuyến khích tinh thần học tập

                Lưu ý: Bạn có thể trả lời mọi câu hỏi, không chỉ giới hạn trong việc tìm đề thi hay phân tích kết quả.
            """

    def process_message(self, message, user_id=None):
        try:
            intent = self.analyze_intent(message)
            user_context = self.get_user_context(user_id) if user_id else {}
            prompt = self.build_prompt(message, user_context)
            response = self.model.generate_content(prompt)
            if intent == 'find_exam':
                return self.handle_find_exam(message, user_context)
            elif intent == 'recommend_study':
                return self.handle_recommend_study(user_id, user_context)
            elif intent == 'analyze_performance':
                return self.handle_analyze_performance(user_id)
            elif intent == 'knowledge_question':
                return self.handle_knowledge_question(message)
            else:
                return response.text


        except Exception as e:
            print(f"Chatbot error: {e}")
            return "Xin lỗi, tôi đang gặp sự cố. Bạn có thể thử lại sau không? 😊"

    def build_prompt(self, message, user_context):
        prompt = f"{self.system_context}\n\n"

        if user_context:
            prompt += f"Thông tin học sinh:\n"
            if user_context.get('avg_score'):
                prompt += f"- Điểm trung bình: {user_context['avg_score']:.1f}\n"
            if user_context.get('subjects'):
                prompt += f"- Các môn đã thi: {', '.join(user_context['subjects'])}\n"
            if user_context.get('total_exams'):
                prompt += f"- Tổng số bài thi: {user_context['total_exams']}\n"
            prompt += "\n"

        if self.is_asking_about_exams(message):
            available_subjects = self.get_available_subjects()
            if available_subjects:
                prompt += f"Các môn học có đề thi: {', '.join(available_subjects)}\n\n"

        prompt += f"Học sinh hỏi: \"{message}\"\n\n"
        prompt += "Hãy trả lời một cách tự nhiên, hữu ích và phù hợp với ngữ cảnh."

        return prompt

    def is_asking_about_exams(self, message):
        exam_keywords = ['đề thi', 'bài thi', 'tìm', 'kiếm', 'có đề', 'môn nào']
        return any(keyword in message.lower() for keyword in exam_keywords)

    def get_available_subjects(self):
        try:
            subjects = dao.get_all_subjects()
            return [subject.subject_name for subject in subjects]
        except:
            return []

    def get_user_context(self, user_id):
        try:
            student = dao.get_student_by_user_id(user_id)
            if not student:
                return {}

            recent_results = dao.get_exam_history_with_pagination(student.id, page=1, per_page=10).items
            if recent_results:
                avg_score = sum(r.score for r in recent_results) / len(recent_results)
                subjects = list(set([r.exam.subject.subject_name for r in recent_results]))
            else:
                avg_score = 0
                subjects = []
            return {
                'student_id': student.id,
                'recent_results': recent_results,
                'avg_score': avg_score,
                'subjects': subjects,
                'total_exams': len(recent_results)
            }
        except Exception as e:
            print(f"Error getting user context: {e}")
            return {}

    def analyze_intent(self, message):
        message_lower = message.lower()

        if any(word in message_lower for word in ['đề thi', 'bài thi', 'tìm', 'kiếm']):
            return 'find_exam'
        if any(word in message_lower for word in ['đề xuất', 'gợi ý', 'học', 'ôn tập']):
            return 'recommend_study'
        if any(word in message_lower for word in ['phân tích', 'kết quả', 'điểm', 'thống kê']):
            return 'analyze_performance'
        if any(word in message_lower for word in ['là gì', 'tại sao', 'như thế nào', 'giải thích']):
            return 'knowledge_question'

        return 'general_chat'

    def handle_find_exam(self, message, user_context):
        subjects_map = {
            'toán': ['toán', 'math', 'mathematics'],
            'văn': ['văn', 'ngữ văn', 'literature'],
            'anh': ['anh', 'tiếng anh', 'english'],
            'lý': ['lý', 'vật lý', 'physics'],
            'hóa': ['hóa', 'hóa học', 'chemistry'],
            'sinh': ['sinh', 'sinh học', 'biology'],
            'sử': ['sử', 'lịch sử', 'history'],
            'địa': ['địa', 'địa lý', 'geography']
        }

        found_subject = None
        message_lower = message.lower()

        for subject, keywords in subjects_map.items():
            if any(keyword in message_lower for keyword in keywords):
                found_subject = subject
                break

        if found_subject:
            exams = dao.get_exams_by_subject_name(found_subject)

            if exams:
                response = f"📚 Tôi tìm thấy {len(exams)} đề thi môn {found_subject.upper()}:\n\n"
                for i, exam in enumerate(exams[:5], 1):
                    stats = self.get_exam_stats(exam.id)
                    response += f"{i}. **{exam.exam_name}**\n"
                    response += f"   ⏱️ {exam.duration} phút | 📊 {stats['avg_score']:.1f} điểm TB\n\n"

                if user_context.get('avg_score'):
                    if user_context['avg_score'] < 60:
                        response += "💡 *Gợi ý: Bạn nên bắt đầu với những đề dễ trước nhé!*"
                    elif user_context['avg_score'] > 80:
                        response += "🎯 *Tuyệt vời! Bạn có thể thử thách bản thân với những đề khó hơn.*"

                return response
            else:
                return f"😔 Xin lỗi, hiện tại chưa có đề thi môn {found_subject.upper()}. Bạn có thể thử môn khác không?"
        else:
            popular_exams = dao.get_popular_exams(limit=5)
            response = "🔍 Tôi không rõ bạn muốn tìm đề thi môn nào. Đây là những đề thi phổ biến:\n\n"

            for i, exam in enumerate(popular_exams, 1):
                response += f"{i}. {exam.exam_name} - {exam.subject.subject_name}\n"

            response += "\n💬 Bạn có thể nói cụ thể hơn như 'Tìm đề thi Toán' không?"
            return response

    def handle_recommend_study(self, user_id, user_context):
        if not user_id:
            return "🔐 Bạn cần đăng nhập để tôi có thể đưa ra đề xuất cá nhân hóa nhé!"

        if not user_context.get('recent_results'):
            return "📝 Bạn chưa có kết quả thi nào. Hãy thử làm một vài đề thi để tôi có thể đưa ra lời khuyên phù hợp!"

        avg_score = user_context['avg_score']
        subjects = user_context['subjects']

        response = f"📈 **Phân tích học tập của bạn:**\n"
        response += f"• Điểm trung bình: {avg_score:.1f}\n"
        response += f"• Số môn đã thi: {len(subjects)}\n\n"

        response += "🎯 **Đề xuất cho bạn:**\n"

        if avg_score < 50:
            response += "• 📚 Ôn tập lại kiến thức cơ bản\n"
            response += "• 🎯 Tập trung vào những câu hỏi dễ trước\n"
            response += "• ⏰ Dành thêm thời gian ôn tập mỗi ngày\n"
        elif avg_score < 70:
            response += "• 📖 Làm thêm bài tập nâng cao\n"
            response += "• 🔄 Ôn lại những phần còn yếu\n"
            response += "• 📝 Thực hành nhiều đề thi thử\n"
        else:
            response += "• 🏆 Thử thách với đề thi khó hơn\n"
            response += "• 🎓 Mở rộng sang môn học mới\n"
            response += "• 📊 Duy trì phong độ tốt\n"

        if len(subjects) < 3:
            response += f"\n💡 *Gợi ý thêm: Bạn có thể thử các môn Toán, Văn, Anh để phát triển toàn diện!*"

        return response

    def handle_analyze_performance(self, user_id):
        if not user_id:
            return "🔐 Bạn cần đăng nhập để xem phân tích kết quả học tập!"

        try:
            from app.recommendation_engine import recommendation_engine
            student = dao.get_student_by_user_id(user_id)

            if not student:
                return "❌ Không tìm thấy thông tin học sinh."

            analysis = recommendation_engine.analyze_student_performance(student.id)

            if not analysis:
                return "📝 Bạn chưa có kết quả thi nào để phân tích. Hãy làm một vài đề thi trước nhé!"

            response = "📊 **Báo cáo phân tích chi tiết:**\n\n"
            response += f"📈 **Tổng quan:**\n"
            response += f"• Tổng số bài thi: {analysis['total_exams']}\n"
            response += f"• Điểm trung bình: {analysis['average_score']:.1f}\n"
            response += f"• Môn học tốt nhất: {analysis['best_subject']}\n"
            response += f"• Cần cải thiện: {analysis['worst_subject']}\n\n"

            response += f"📉 **Xu hướng:** "
            if analysis['improvement_trend'] == 'improving':
                response += "📈 Đang tiến bộ tốt! 🎉\n"
            elif analysis['improvement_trend'] == 'declining':
                response += "📉 Cần nỗ lực thêm! 💪\n"
            else:
                response += "📊 Ổn định\n"

            if analysis.get('weak_areas'):
                response += f"\n🎯 **Lĩnh vực cần chú ý:**\n"
                for area in analysis['weak_areas'][:3]:
                    response += f"• {area}\n"

            response += f"\n💡 *Đề xuất: Hãy tập trung vào môn {analysis['worst_subject']} và những lĩnh vực yếu để cải thiện kết quả!*"

            return response

        except Exception as e:
            print(f"Error analyzing performance: {e}")
            return "❌ Có lỗi xảy ra khi phân tích. Vui lòng thử lại sau!"

    def handle_knowledge_question(self, message):
        try:
            prompt = f"""
                {self.system_context}

                Học sinh hỏi: "{message}"

                Hãy trả lời một cách:
                - Chính xác và dễ hiểu
                - Phù hợp với học sinh
                - Có ví dụ cụ thể nếu cần
                - Khuyến khích học tập
                - Không quá 200 từ
            """

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            print(f"Gemini API error: {e}")
            return "🤔 Đây là câu hỏi hay! Tôi sẽ tìm hiểu và trả lời bạn sau nhé. Trong thời gian này, bạn có thể tham khảo sách giáo khoa hoặc hỏi giáo viên!"

    def get_exam_stats(self, exam_id):
        try:
            results = dao.get_exam_results_by_exam_id(exam_id)
            if results:
                avg_score = sum(r.score for r in results) / len(results)
                return {'avg_score': avg_score, 'total_attempts': len(results)}
            else:
                return {'avg_score': 0, 'total_attempts': 0}
        except:
            return {'avg_score': 0, 'total_attempts': 0}


smart_chatbot = SmartChatBot()