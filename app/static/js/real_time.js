class RealTimeManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.currentUserId = null;
        this.userType = null;
    }

    connect(userId, userType) {
        if (this.isConnected && this.currentUserId === userId) {
            return;
        }

        this.currentUserId = userId;
        this.userType = userType;

        try {
            this.socket = new WebSocket('ws://localhost:8765');

            this.socket.onopen = () => {
                this.isConnected = true;
                this.send({
                    type: 'connect',
                    client_id: `${userType}_${userId}`,
                    user_id: userId,
                    user_type: userType
                });

                if (userType === 'admin') {
                    this.send({ type: 'request_stats' });
                }
            };

            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };

            this.socket.onclose = () => {
                this.isConnected = false;
            };

        } catch (error) {
            console.error('WebSocket connection failed:', error);
        }
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'stats_update':
                this.updateAdminStats(data);
                break;
            case 'admin_notification':
                this.addAdminNotification(data.title, data.message, data.timestamp);
                break;
        }
    }

    joinExam(examId, studentId) {
        this.send({
            type: 'join_exam',
            exam_id: examId,
            student_id: studentId
        });
    }

    updateExamProgress(examId, studentId, currentQuestion) {
        this.send({
            type: 'exam_progress',
            exam_id: examId,
            student_id: studentId,
            current_question: currentQuestion
        });
    }

    submitExam(examId, studentId, score) {
        this.send({
            type: 'submit_exam',
            exam_id: examId,
            student_id: studentId,
            score: score
        });
    }

    updateAdminStats(data) {
        const elements = {
            'online-users': data.online_users || 0,
            'active-sessions': data.active_sessions || 0,
            'completed-today': data.completed_today || 0
        };

        Object.keys(elements).forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = elements[id];
            }
        });
    }

    addAdminNotification(title, message, timestamp) {
        const notificationArea = document.getElementById('admin-notifications');
        if (notificationArea) {
            const waitingMsg = document.getElementById('waiting-connection');
            if (waitingMsg) {
                waitingMsg.remove();
            }

            const notification = document.createElement('div');
            notification.className = 'alert alert-info alert-sm mb-2';
            notification.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${title}:</strong><br>
                        <small>${message}</small>
                    </div>
                    <small class="text-muted">${new Date(timestamp).toLocaleTimeString()}</small>
                </div>
            `;
            notificationArea.insertBefore(notification, notificationArea.firstChild);

            while (notificationArea.children.length > 10) {
                notificationArea.removeChild(notificationArea.lastChild);
            }
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            this.isConnected = false;
            this.currentUserId = null;
        }
    }
}

if (typeof window !== 'undefined') {
    window.globalRealTimeManager = window.globalRealTimeManager || new RealTimeManager();
}

document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('realtimeToggle')) {
        if (typeof window.currentUserId !== 'undefined' &&
            window.currentUserId &&
            window.currentUserId !== 'null' &&
            window.currentUserId !== null) {

            if (!window.globalRealTimeManager.isConnected) {
                window.globalRealTimeManager.connect(window.currentUserId, window.userType || 'student');
            }
            window.realTimeManager = window.globalRealTimeManager;
        }
    }
});

window.addEventListener('beforeunload', function() {
    if (window.location.href.includes('/logout')) {
        if (window.globalRealTimeManager) {
            window.globalRealTimeManager.disconnect();
        }
    }
});

const style = document.createElement('style');
style.textContent = `
    .alert-sm {
        padding: 0.375rem 0.75rem;
        font-size: 0.875rem;
    }
    #admin-notifications {
        max-height: 400px;
        overflow-y: auto;
    }
`;
document.head.appendChild(style);