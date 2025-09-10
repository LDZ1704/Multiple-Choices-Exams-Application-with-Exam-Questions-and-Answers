import asyncio
import websockets
import json
import logging
from datetime import datetime, date

user_connections = {}
user_login_status = {}
exam_sessions = {}
daily_completions = {}

today = date.today().isoformat()
if today not in daily_completions:
    daily_completions[today] = 0

realtime_stats = {
    'active_sessions': 0,
    'completed_today': 0,
    'online_users': 0
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_client(websocket):
    client_id = None
    user_id = None
    try:
        async for message in websocket:
            data = json.loads(message)

            if data['type'] == 'connect':
                client_id = data['client_id']
                user_id = data.get('user_id')
                user_type = data.get('user_type')

                if user_type in ['admin', 'student'] and user_id and str(user_id) != 'null':
                    user_id_str = str(user_id)

                    user_connections[user_id_str] = {
                        'websocket': websocket,
                        'user_type': user_type,
                        'client_id': client_id
                    }

                    # Chỉ thông báo đăng nhập lần đầu
                    if user_id_str not in user_login_status:
                        user_login_status[user_id_str] = {
                            'logged_in': True,
                            'user_type': user_type
                        }

                        realtime_stats['online_users'] = len(user_login_status)

                        await broadcast_to_admins({
                            'type': 'admin_notification',
                            'title': 'Người dùng đăng nhập',
                            'message': f'{user_type.title()} ID {user_id} đã đăng nhập',
                            'timestamp': datetime.now().isoformat()
                        })
                        await broadcast_stats_update()

            elif data['type'] == 'user_logout':
                user_id = str(data['user_id'])
                if user_id in user_login_status:
                    user_type = user_login_status[user_id]['user_type']
                    del user_login_status[user_id]

                    if user_id in user_connections:
                        del user_connections[user_id]

                    realtime_stats['online_users'] = len(user_login_status)

                    await broadcast_to_admins({
                        'type': 'admin_notification',
                        'title': 'Người dùng đăng xuất',
                        'message': f'{user_type.title()} ID {user_id} đã đăng xuất',
                        'timestamp': datetime.now().isoformat()
                    })
                    await broadcast_stats_update()

            elif data['type'] == 'join_exam':
                exam_id = str(data['exam_id'])
                student_id = str(data['student_id'])

                if exam_id not in exam_sessions:
                    exam_sessions[exam_id] = {}

                exam_sessions[exam_id][student_id] = {
                    'websocket': websocket,
                    'start_time': datetime.now()
                }

                realtime_stats['active_sessions'] = sum(len(sessions) for sessions in exam_sessions.values())

                await broadcast_to_admins({
                    'type': 'admin_notification',
                    'title': 'Bắt đầu thi',
                    'message': f'Học sinh {student_id} bắt đầu làm bài thi {exam_id}',
                    'timestamp': datetime.now().isoformat()
                })
                await broadcast_stats_update()

            elif data['type'] == 'submit_exam':
                exam_id = str(data['exam_id'])
                student_id = str(data['student_id'])
                score = data.get('score', 0)

                if exam_id in exam_sessions and student_id in exam_sessions[exam_id]:
                    del exam_sessions[exam_id][student_id]
                    if not exam_sessions[exam_id]:
                        del exam_sessions[exam_id]

                today = date.today().isoformat()
                if today not in daily_completions:
                    daily_completions[today] = 0
                daily_completions[today] += 1

                realtime_stats['active_sessions'] = sum(len(sessions) for sessions in exam_sessions.values())
                realtime_stats['completed_today'] = daily_completions[today]

                await broadcast_to_admins({
                    'type': 'admin_notification',
                    'title': 'Hoàn thành bài thi',
                    'message': f'Học sinh {student_id} hoàn thành với điểm {score}',
                    'timestamp': datetime.now().isoformat()
                })
                await broadcast_stats_update()

            elif data['type'] == 'exam_progress':
                exam_id = str(data['exam_id'])
                student_id = str(data['student_id'])
                current_question = data['current_question']

                await broadcast_to_admins({
                    'type': 'admin_notification',
                    'title': 'Tiến độ thi',
                    'message': f'Học sinh {student_id} đang làm câu {current_question}',
                    'timestamp': datetime.now().isoformat()
                })

            elif data['type'] == 'request_stats':
                await websocket.send(json.dumps({
                    'type': 'stats_update',
                    **realtime_stats,
                    'timestamp': datetime.now().isoformat()
                }))

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await cleanup_user(user_id)


async def cleanup_user(user_id):
    if user_id:
        user_id_str = str(user_id)

        if user_id_str in user_connections:
            del user_connections[user_id_str]

        # Chờ 10 giây để kiểm tra user có reconnect không
        await asyncio.sleep(10)

        # Nếu user không reconnect thì mới thông báo đăng xuất
        if user_id_str not in user_connections and user_id_str in user_login_status:
            user_type = user_login_status[user_id_str]['user_type']
            del user_login_status[user_id_str]

            realtime_stats['online_users'] = len(user_login_status)

            await broadcast_to_admins({
                'type': 'admin_notification',
                'title': 'Người dùng đăng xuất',
                'message': f'{user_type.title()} ID {user_id} đã đăng xuất',
                'timestamp': datetime.now().isoformat()
            })
            await broadcast_stats_update()


async def broadcast_to_admins(message):
    disconnected = []
    for uid, user_data in user_connections.items():
        if user_data['user_type'] == 'admin':
            try:
                await user_data['websocket'].send(json.dumps(message))
            except:
                disconnected.append(uid)

    for uid in disconnected:
        if uid in user_connections:
            del user_connections[uid]
        realtime_stats['online_users'] = len(user_login_status)


async def broadcast_stats_update():
    await broadcast_to_admins({
        'type': 'stats_update',
        **realtime_stats,
        'timestamp': datetime.now().isoformat()
    })


async def main():
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())