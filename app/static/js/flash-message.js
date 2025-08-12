// Flash Messages JavaScript
let flashQueue = [];
let flashTimeout;

function getFlashIcon(category) {
    const icons = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'danger': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    return icons[category] || icons['info'];
}

function showFlashMessage(category, message, autoDismiss = true) {
    const flashContainer = document.getElementById('flashContainer');
    const flashOverlay = document.getElementById('flashOverlay');

    if (!flashContainer || !flashOverlay) {
        console.error('Flash message elements not found!');
        return;
    }

    if (category === 'danger') {
        category = 'error';
    }

    const messageElement = document.createElement('div');
    messageElement.className = `flash-message ${category}`;
    messageElement.innerHTML = `
        <i class="${getFlashIcon(category)} flash-icon"></i>
        <span class="flash-content">${message}</span>
        ${autoDismiss ? '<div class="flash-progress"><div class="flash-progress-bar"></div></div>' : ''}
    `;

    flashContainer.appendChild(messageElement);

    flashOverlay.classList.add('show');

    if (autoDismiss) {
        const progressBar = messageElement.querySelector('.flash-progress-bar');
        if (progressBar) {
            progressBar.style.transitionDuration = '5s';
            setTimeout(() => {
                progressBar.style.width = '100%';
            }, 100);
        }

        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.remove();
                if (flashContainer.children.length === 0) {
                    closeFlashMessages();
                }
            }
        }, 5000);
    }
}

function showMultipleMessages() {
    showFlashMessage('success', 'Thao tác đã hoàn thành thành công!', false);
    setTimeout(() => {
        showFlashMessage('info', 'Dữ liệu đã được đồng bộ!', false);
    }, 200);
    setTimeout(() => {
        showFlashMessage('warning', 'Vui lòng kiểm tra email để xác nhận!', false);
    }, 400);
}

function closeFlashMessages(event) {
    if (event && event.target !== event.currentTarget && !event.target.classList.contains('flash-close')) {
        return;
    }

    const flashOverlay = document.getElementById('flashOverlay');
    const flashContainer = document.getElementById('flashContainer');

    if (!flashOverlay || !flashContainer) {
        return;
    }

    flashOverlay.classList.remove('show');

    setTimeout(() => {
        flashContainer.innerHTML = '';
    }, 300);
}

function processFlashMessages() {
    const flaskMessages = document.getElementById('flaskMessages');
    if (flaskMessages) {
        const messages = flaskMessages.children;
        let hasMessages = false;

        for (let i = 0; i < messages.length; i++) {
            const category = messages[i].getAttribute('data-category');
            const message = messages[i].getAttribute('data-message');

            if (category && message) {
                hasMessages = true;
                setTimeout(() => {
                    showFlashMessage(category, message);
                }, i * 200);
            }
        }

        if (hasMessages) {
            console.log('Flash messages processed:', messages.length);
        }
        flaskMessages.remove();
    } else {
        console.log('No flask messages found');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Flash messages script loaded');
    processFlashMessages();
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeFlashMessages();
    }
});

window.showFlashMessage = showFlashMessage;
window.closeFlashMessages = closeFlashMessages;
window.showMultipleMessages = showMultipleMessages;