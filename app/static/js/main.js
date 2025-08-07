document.addEventListener('DOMContentLoaded', function() {
    //Tự động ẩn sau 5s thông báo
    setTimeout(function () {
        const flashAlerts = document.querySelectorAll('.flash-alert');
        flashAlerts.forEach(alert => {
            alert.classList.remove('show');
            setTimeout(() => {
                alert.remove();
            }, 300);
        });
    }, 5000);
});

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