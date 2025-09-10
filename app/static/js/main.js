document.addEventListener('DOMContentLoaded', function() {
    //Chức năng scroll-to-top
    const scrollToTopBtn = document.getElementById('scrollToTop');

    if (scrollToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                scrollToTopBtn.style.display = 'block';
            } else {
                scrollToTopBtn.style.display = 'none';
            }
        });

        scrollToTopBtn.addEventListener('click', function(e) {
            e.preventDefault();

            const scrollToTop = () => {
                const currentScroll = window.pageYOffset;
                if (currentScroll > 10) {
                    window.requestAnimationFrame(scrollToTop);
                    window.scrollTo(0, currentScroll - (currentScroll / 8));
                } else {
                    window.scrollTo(0, 0);
                }
            };
            scrollToTop();
        });
    }

    //Ấn enter để search
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.form.submit();
            }
        });
    }

    window.USER_ID = window.currentUserId || null;
    window.isTyping = false;
    window.chatOpen = false;
});

//Chức năng search
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('input[name="search"]');
    const searchForm = document.querySelector('form');

    if (searchInput) {
        //Tự động tập trung vào ô search khi load trang
        if (searchInput.value) {
            searchInput.focus();
            searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
        }

        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchForm.submit();
            }
        });

        //Xóa search khi ấn esc
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                searchInput.value = '';
                searchInput.blur();
            }
        });
    }

    // Lấy search query từ URL hoặc input
    const urlParams = new URLSearchParams(window.location.search);
    const searchQuery = urlParams.get('search') || (searchInput ? searchInput.value : '');

    if (searchQuery) {
        highlightSearchResults(searchQuery);
    }

    function highlightSearchResults(query) {
        if (!query.trim()) return;

        const elements = document.querySelectorAll('.card-title, .fw-bold');

        const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedQuery})`, 'gi');

        elements.forEach(element => {
            if (element.textContent.toLowerCase().includes(query.toLowerCase())) {
                element.innerHTML = element.textContent.replace(regex, '<mark class="bg-warning">$1</mark>');
            }
        });
    }
});

//Avatar trang account.html
document.addEventListener('DOMContentLoaded', function() {
    const avatarInput = document.getElementById('avatar-input');
    const avatarForm = document.getElementById('avatar-form');
    const avatarPreview = document.getElementById('avatar-preview');

    if (avatarInput && avatarForm && avatarPreview) {
        avatarInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    avatarPreview.src = e.target.result;
                };
                reader.readAsDataURL(file);

                avatarForm.submit();
            }
        });
    }
});

//Chức năng cho trang account.html
window.toggleEdit = function() {
    const inputs = document.querySelectorAll('#account-form input:not([name="role"]), #account-form select');
    const editBtn = document.getElementById('edit-btn');
    const actionButtons = document.getElementById('action-buttons');

    if (inputs.length > 0 && editBtn && actionButtons) {
        inputs.forEach(input => {
            input.disabled = false;
        });

        editBtn.style.display = 'none';
        actionButtons.style.display = 'block';
    }
};

window.cancelEdit = function() {
    const inputs = document.querySelectorAll('#account-form input, #account-form select');
    const editBtn = document.getElementById('edit-btn');
    const actionButtons = document.getElementById('action-buttons');
    const accountForm = document.getElementById('account-form');

    if (inputs.length > 0 && editBtn && actionButtons && accountForm) {
        inputs.forEach(input => {
            input.disabled = true;
        });

        editBtn.style.display = 'block';
        actionButtons.style.display = 'none';

        accountForm.reset();
        location.reload();
    }
};

//Trang OTP
document.addEventListener('DOMContentLoaded', function() {
    const otpInput = document.getElementById('otp');

    if (otpInput) {
        // Chỉ cho phép nhập số
        otpInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
        });

        // Lấy thời gian còn lại từ template variable (cần được truyền từ server)
        const remainingSecondsElement = document.querySelector('[data-remaining-seconds]');
        let countdownTime = remainingSecondsElement ?
            parseInt(remainingSecondsElement.dataset.remainingSeconds) : 0;

        // Thời gian ban đầu để tính progress bar
        const initialTime = countdownTime;

        const countdownTimer = document.getElementById('countdown-timer');
        const countdownContainer = document.getElementById('countdown-container');
        const expiredContainer = document.getElementById('expired-container');
        const otpForm = document.getElementById('otp-form');
        const verifyBtn = document.getElementById('verify-btn');
        const resendLink = document.getElementById('resend-link');
        const progressBar = document.getElementById('countdown-progress-bar');
        const countdownCard = countdownContainer?.querySelector('.countdown-card');

        if (countdownTimer && countdownContainer && expiredContainer && otpForm && verifyBtn && resendLink) {
            function updateCountdown() {
                const minutes = Math.floor(countdownTime / 60);
                const seconds = countdownTime % 60;

                // Định dạng hiển thị mm:ss
                const displayMinutes = minutes.toString().padStart(2, '0');
                const displaySeconds = seconds.toString().padStart(2, '0');

                countdownTimer.textContent = `${displayMinutes}:${displaySeconds}`;

                // Cập nhật progress bar
                if (progressBar && initialTime > 0) {
                    const progress = (countdownTime / initialTime) * 100;
                    progressBar.style.width = `${progress}%`;
                }

                // Thay đổi style theo thời gian còn lại
                if (countdownCard) {
                    countdownCard.className = 'countdown-card';
                    if (countdownTime <= 60) { // Dưới 1 phút - nguy hiểm
                        countdownCard.classList.add('danger');
                    } else if (countdownTime <= 300) { // Dưới 5 phút - cảnh báo
                        countdownCard.classList.add('warning');
                    }
                }

                if (countdownTime <= 0) {
                    // Hết thời gian
                    countdownContainer.style.display = 'none';
                    expiredContainer.style.display = 'block';

                    // Vô hiệu hóa form
                    otpInput.disabled = true;
                    verifyBtn.disabled = true;
                    verifyBtn.textContent = 'Mã OTP đã hết hạn';
                    verifyBtn.style.background = '#6c757d';

                    // Thay đổi text của link gửi lại
                    resendLink.innerHTML = '← Yêu cầu mã OTP mới';

                    clearInterval(countdownInterval);

                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    countdownTime--;
                }
            }

            //Nếu từ đầu đã hết hạn
            if (countdownTime <= 0) {
                countdownContainer.style.display = 'none';
                expiredContainer.style.display = 'block';
                otpInput.disabled = true;
                verifyBtn.disabled = true;
                verifyBtn.textContent = 'Mã OTP đã hết hạn';
                verifyBtn.style.background = '#6c757d';
                resendLink.innerHTML = '← Yêu cầu mã OTP mới';
            } else {
                // Khởi tạo đếm ngược
                updateCountdown();
                const countdownInterval = setInterval(updateCountdown, 1000);
            }

            // Xử lý submit form
            otpForm.addEventListener('submit', function(e) {
                if (countdownTime <= 0) {
                    e.preventDefault();
                    alert('Mã OTP đã hết hạn. Vui lòng yêu cầu mã mới.');
                    return false;
                }
            });

            // Tự động focus vào input OTP
            otpInput.focus();

            // Sync với server mỗi 30 giây để đảm bảo chính xác
            setInterval(() => {
                if (typeof countdownTime !== 'undefined' && countdownTime > 0) {
                    fetch('/api/otp-time-remaining')
                        .then(response => response.json())
                        .then(data => {
                            if (data.expired && countdownTime > 0) {
                                // Server báo đã hết hạn nhưng client chưa
                                countdownTime = 0;
                                updateCountdown();
                            } else if (!data.expired) {
                                const diff = Math.abs(countdownTime - data.remaining);
                                // Chênh lệch quá 5 giây thì sync
                                if (diff > 5) {
                                    countdownTime = data.remaining;
                                }
                            }
                        })
                        .catch(error => console.log('Sync error:', error));
                }
            }, 30000); // Sync mỗi 30 giây
        }
    }
});

function copyToClipboard() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(function() {
        alert('Đã sao chép link!');
    }).catch(function(err) {
        console.error('Không thể sao chép: ', err);
    });
}

// Thêm hiệu ứng khi trang load
document.addEventListener('DOMContentLoaded', function() {
    const notifications = document.querySelectorAll('.notification-box');
    notifications.forEach((notification, index) => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(20px)';
        setTimeout(() => {
            notification.style.transition = 'all 0.6s ease';
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, index * 200);
    });
});

// Thêm hiệu ứng ripple khi click
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('login-link')) {
        const ripple = document.createElement('span');
        const rect = e.target.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
        ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
        ripple.classList.add('ripple');

        const rippleStyle = document.createElement('style');
        rippleStyle.textContent = `
            .ripple {
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.6);
                transform: scale(0);
                animation: ripple-animation 0.6s linear;
                pointer-events: none;
            }
            @keyframes ripple-animation {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
        `;

        if (!document.querySelector('.ripple-style')) {
            rippleStyle.classList.add('ripple-style');
            document.head.appendChild(rippleStyle);
        }

        e.target.style.position = 'relative';
        e.target.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Xử lý cho pagination trong index.html
    const paginationLinks = document.querySelectorAll('.pagination a[href*="page="]');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const examSection = document.querySelector('section.py-5:last-of-type');
            if (examSection) {
                const sectionTop = examSection.offsetTop - 100;
                sessionStorage.setItem('examSectionPosition', sectionTop);
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Xử lý cho comment pagination trong examdetail.html
    document.addEventListener('click', function(e) {
        if (e.target.matches('#comments-pagination a[href*="comment_page="], #comments-pagination a[href*="comment_page="] *')) {
            e.preventDefault();

            const linkElement = e.target.closest('a[href*="comment_page="]');
            if (!linkElement) return;

            const url = new URL(linkElement.href);
            const page = url.searchParams.get('comment_page');
            const examId = new URLSearchParams(window.location.search).get('id');

            fetch(`/examdetail?id=${examId}&comment_page=${page}`)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newCommentsSection = doc.querySelector('#reviews');
                    document.querySelector('#reviews').innerHTML = newCommentsSection.innerHTML;

                    const reviewsTabLink = document.getElementById('reviews-tab');
                    if (reviewsTabLink && !reviewsTabLink.classList.contains('active')) {
                        reviewsTabLink.click();
                    }

                    const reviewsTab = document.getElementById('reviews');
                    if (reviewsTab) {
                        const tabPosition = reviewsTab.offsetTop - 120;
                        window.scrollTo({
                            top: tabPosition,
                            behavior: 'smooth'
                        });
                    }

                    window.history.pushState({}, '', url);
                }).catch(error => console.error('Lỗi khi tải bình luận:', error));
        }
    });
});

// Khôi phục vị trí scroll khi trang load
window.addEventListener('load', function() {
    // Xử lý cho index.html
    const examSectionPosition = sessionStorage.getItem('examSectionPosition');
    if (examSectionPosition) {
        setTimeout(() => {
            window.scrollTo({
                top: parseInt(examSectionPosition),
                behavior: 'smooth'
            });
            sessionStorage.removeItem('examSectionPosition');
        }, 100);
    }

    // Xử lý cho examdetail.html
    const commentScrollPosition = sessionStorage.getItem('scrollToComments');
    if (commentScrollPosition) {
        setTimeout(() => {
            window.scrollTo({
                top: parseInt(commentScrollPosition),
                behavior: 'smooth'
            });
            sessionStorage.removeItem('scrollToComments');
        }, 150);
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const allPaginationLinks = document.querySelectorAll('.pagination .page-link[href]');

    allPaginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
            this.style.pointerEvents = 'none';

            setTimeout(() => {
                this.innerHTML = originalText;
                this.style.pointerEvents = 'auto';
            }, 2000);
        });
    });
});

document.getElementById('togglePassword').addEventListener('click', function() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('toggleIcon');


    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.className = 'bi bi-eye-slash';
    } else {
        passwordInput.type = 'password';
        toggleIcon.className = 'bi bi-eye';
    }
});

document.getElementById('togglePassword2').addEventListener('click', function() {
    const passwordInput = document.getElementById('confirm-password');
        const toggleIcon2 = document.getElementById('toggleIcon2');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon2.className = 'bi bi-eye-slash';
    } else {
        passwordInput.type = 'password';
        toggleIcon2.className = 'bi bi-eye';
    }
});

//Chức năng cho chatbot
function toggleChat() {
    const chatWindow = document.getElementById('chatWindow');
    const chatToggle = document.getElementById('chatToggle');
    const notificationBadge = document.getElementById('notificationBadge');

    chatOpen = !chatOpen;

    if (chatOpen) {
        chatWindow.classList.add('show');
        chatToggle.classList.add('active');
        chatToggle.innerHTML = '<i class="bi bi-x-lg"></i>';
        if (notificationBadge) notificationBadge.style.display = 'none';

        setTimeout(() => {
            document.getElementById('messageInput').focus();
        }, 300);
    } else {
        chatWindow.classList.remove('show');
        chatToggle.classList.remove('active');
        chatToggle.innerHTML = '<i class="bi bi-chat-dots-fill"></i><div class="notification-badge" id="notificationBadge" style="display: none;"></div>';
    }
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
}

function addMessage(content, isUser = false) {
    const messagesContainer = document.getElementById('chatMessages');
    const welcomeMessage = messagesContainer.querySelector('.welcome-message');

    if (welcomeMessage && welcomeMessage.style.display !== 'none') {
        welcomeMessage.style.display = 'none';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;

    const now = new Date();
    const timeStr = now.getHours().toString().padStart(2, '0') + ':' +
                   now.getMinutes().toString().padStart(2, '0');

    messageDiv.innerHTML = `
        <div class="message-bubble">
            ${content.replace(/\n/g, '<br>')}
        </div>
        <div class="message-time">${timeStr}</div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTyping() {
    if (!isTyping) {
        isTyping = true;
        document.getElementById('typingIndicator').style.display = 'block';
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

function hideTyping() {
    isTyping = false;
    document.getElementById('typingIndicator').style.display = 'none';
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const message = input.value.trim();

    if (!message) return;

    input.disabled = true;
    sendButton.disabled = true;

    addMessage(message, true);
    input.value = '';
    input.style.height = 'auto';

    try {
        showTyping();

        const response = await fetch('/api/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: USER_ID
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        setTimeout(() => {
            hideTyping();
            addMessage(data.response);
        }, 1000);

    } catch (error) {
        console.error('Chatbot error:', error);
        hideTyping();
        addMessage('Xin lỗi, có lỗi xảy ra khi kết nối với trợ lý AI. Vui lòng thử lại sau!');
    } finally {
        setTimeout(() => {
            input.disabled = false;
            sendButton.disabled = false;
            input.focus();
        }, 1500);
    }
}

function sendQuickMessage(message) {
    const input = document.getElementById('messageInput');
    input.value = message;
    sendMessage();
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

setTimeout(() => {
    if (!chatOpen && USER_ID) {
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            badge.style.display = 'flex';
        }
    }
}, 5000);

//Notifications
document.addEventListener('DOMContentLoaded', function() {
    initializeNotifications();
});

function initializeNotifications() {
    const notificationDropdown = document.getElementById('notificationDropdown');
    const notificationBadge = document.getElementById('notification-badge');

    if (notificationDropdown) {
        notificationDropdown.addEventListener('click', function(e) {
            e.preventDefault();
            toggleNotificationDropdown(e);
        });
    }

    if (notificationBadge) {
        updateNotificationCount();
        setInterval(updateNotificationCount, 30000);
    }

    document.addEventListener('click', function(event) {
        const dropdown = document.getElementById('notificationDropdownMenu');
        const toggle = document.getElementById('notificationDropdown');

        if (!dropdown.contains(event.target) && !toggle.contains(event.target)) {
            dropdown.style.display = 'none';
        }
    });
}

function loadRecentNotifications() {
    const listContainer = document.getElementById('notification-list');
    if (!listContainer) {
        return;
    }
    listContainer.innerHTML = '<div class="notification-loading"><div class="spinner-border spinner-border-sm"></div><span class="ms-2">Đang tải...</span></div>';

    fetch('/api/notifications/recent')
        .then(response => response.json())
        .then(data => {
            if (!data.notifications || data.notifications.length === 0) {
                listContainer.innerHTML = `
                    <div class="empty-notifications">
                        <i class="bi bi-bell-slash"></i>
                        <div class="mt-2">Không có thông báo mới</div>
                    </div>
                `;
                return;
            }
            listContainer.innerHTML = '';
            data.notifications.forEach(notification => {
                const item = document.createElement('div');
                item.className = `notification-item ${!notification.is_read ? 'notification-unread' : ''}`;
                const iconClass = getNotificationIcon(notification.type);
                const message = notification.message || '';
                const displayMessage = message.length > 80 ? message.substring(0, 80) + '...' : message;
                item.innerHTML = `
                    <div class="notification-content">
                        <div class="notification-icon ${notification.type}">
                            <i class="bi ${iconClass}"></i>
                        </div>
                        <div class="notification-body">
                            <div class="notification-title">${escapeHtml(notification.title || 'Thông báo')}</div>
                            <div class="notification-message">${escapeHtml(displayMessage)}</div>
                            <div class="notification-time">
                                <i class="bi bi-clock"></i>
                                ${notification.created_at}
                            </div>
                        </div>
                        ${!notification.is_read ? '<div class="notification-badge">Mới</div>' : ''}
                    </div>
                `;
                item.onclick = () => {
                    if (!notification.is_read) {
                        markNotificationAsRead(notification.id);
                    }
                    if (notification.exam_id) {
                        window.location.href = `/examdetail?id=${notification.exam_id}`;
                    }
                };
                listContainer.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Error loading notifications:', error);
            listContainer.innerHTML = `
                <div class="empty-notifications">
                    <i class="bi bi-bell-slash"></i>
                    <div class="mt-2">Lỗi tải thông báo</div>
                </div>
            `;
        });
}

function getNotificationIcon(type) {
    switch(type) {
        case 'result': return 'bi-trophy';
        case 'reminder': return 'bi-clock';
        case 'suggestion': return 'bi-lightbulb';
        case 'new_exam': return 'bi-file-earmark-plus';
        default: return 'bi-info-circle';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTimeAgo(dateString) {
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Vừa xong';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} phút trước`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} giờ trước`;
        return date.toLocaleDateString('vi-VN');
    } catch (error) {
        return dateString;
    }
}

function updateNotificationCount() {
    const badge = document.getElementById('notification-badge');
    if (!badge) {
        return;
    }

    fetch('/api/notifications/unread-count')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(error => console.error('Error updating notification count:', error));
}

function markNotificationAsRead(notificationId) {
    fetch(`/api/notifications/mark-read/${notificationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const badge = document.getElementById('notification-badge');
            if (badge) {
                const currentCount = parseInt(badge.textContent) || 0;
                const newCount = Math.max(0, currentCount - 1);
                if (newCount === 0) {
                    badge.style.display = 'none';
                } else {
                    badge.textContent = newCount;
                }
            }
            loadRecentNotifications();
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
    });
}

function markAllNotificationsAsRead() {
    fetch('/api/notifications/mark-all-read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const badge = document.getElementById('notification-badge');
            if (badge) {
                badge.style.display = 'none';
            }
            loadRecentNotifications();
        }
    })
    .catch(error => {
        console.error('Error marking all notifications as read:', error);
    });
}

function toggleNotificationDropdown(event) {
    event.preventDefault();
    event.stopPropagation();

    const dropdown = document.getElementById('notificationDropdownMenu');
    const isVisible = dropdown.style.display === 'block';

    if (isVisible) {
        dropdown.style.display = 'none';
    } else {
        dropdown.style.display = 'block';
        loadRecentNotifications();
    }
}

document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('notificationDropdownMenu');
    const toggle = document.getElementById('notificationDropdown');

    if (dropdown && toggle && !dropdown.contains(event.target) && !toggle.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});