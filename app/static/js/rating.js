class RatingSystem {
    constructor(examId) {
        this.examId = examId;
        this.currentRating = 0;
        this.userRating = null;
        this.isSubmitting = false;

        this.init();
    }

    init() {
        this.loadUserRatingsInComments();

        if (document.getElementById('rating-container')) {
            this.bindEvents();
            this.loadRatingStats();
        } else {
            this.loadRatingStatsOnly();
        }
    }

    bindEvents() {
        const stars = document.querySelectorAll('.star');
        const ratingContainer = document.getElementById('rating-container');

        if (!stars.length || !ratingContainer) return;

        stars.forEach(star => {
            star.addEventListener('mouseenter', (e) => {
                if (this.isSubmitting) return;
                const rating = parseInt(e.target.dataset.rating);
                this.highlightStars(rating);
            });

            star.addEventListener('mouseleave', () => {
                if (this.isSubmitting) return;
                this.highlightStars(this.userRating || 0);
            });

            star.addEventListener('click', (e) => {
                if (this.isSubmitting) return;
                const rating = parseInt(e.target.dataset.rating);
                this.submitRating(rating);
            });
        });
    }

    highlightStars(rating) {
        const stars = document.querySelectorAll('.star');
        stars.forEach((star, index) => {
            star.classList.remove('active', 'hover');
            if (index < rating) {
                star.classList.add(this.userRating === rating ? 'active' : 'hover');
            }
        });
    }

    async loadRatingStats() {
        try {
            const response = await fetch(`/api/exam/${this.examId}/rating-stats`);
            const data = await response.json();

            if (data.success) {
                this.userRating = data.user_rating;
                this.updateStatsDisplay(data.stats);
                this.highlightStars(this.userRating || 0);

                if (this.userRating) {
                    this.showMessage(`Bạn đã đánh giá ${this.userRating} sao cho đề thi này`, 'success');
                }
            }
        } catch (error) {
            console.error('Error loading rating stats:', error);
        }
    }

    async loadUserRatingsInComments() {
        const userRatingElements = document.querySelectorAll('.user-rating');

        for (const element of userRatingElements) {
            const userId = element.dataset.userId;
            try {
                const response = await fetch(`/api/user/${userId}/exam/${this.examId}/rating`);
                const data = await response.json();

                if (data.success && data.rating) {
                    element.innerHTML = this.generateSmallStarDisplay(data.rating);
                }
            } catch (error) {
                console.error('Error loading user rating:', error);
            }
        }
    }

    async submitRating(rating) {
        if (this.isSubmitting) return;

        this.isSubmitting = true;
        this.showMessage('<span class="loading-spinner"></span> Đang gửi đánh giá...', 'info');

        try {
            const response = await fetch(`/api/exam/${this.examId}/rating`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ rating: rating })
            });

            const data = await response.json();

            if (data.success) {
                this.userRating = rating;
                this.highlightStars(rating);
                this.updateStatsDisplay(data.stats);
                this.showMessage(data.message, 'success');

                // Cập nhật rating count trong tab header
                const ratingsCount = document.getElementById('ratings-count');
                if (ratingsCount) {
                    ratingsCount.textContent = data.stats.total_ratings;
                }
            } else {
                this.showMessage(data.error || 'Có lỗi xảy ra khi đánh giá', 'error');
            }
        } catch (error) {
            console.error('Error submitting rating:', error);
            this.showMessage('Có lỗi xảy ra. Vui lòng thử lại!', 'error');
        } finally {
            this.isSubmitting = false;
        }
    }

    updateStatsDisplay(stats) {
        const averageStarsContainer = document.getElementById('average-stars');
        const averageRatingText = document.getElementById('average-rating-text');
        const ratingSummary = document.getElementById('rating-summary');

        if (averageStarsContainer) {
            averageStarsContainer.innerHTML = this.generateStarDisplay(stats.average_rating);
        }

        if (averageRatingText) {
            averageRatingText.textContent = stats.average_rating;
        }

        if (ratingSummary) {
            ratingSummary.textContent = `(${stats.total_ratings} đánh giá)`;
        }
    }

    generateStarDisplay(rating) {
        let starsHtml = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= Math.floor(rating)) {
                starsHtml += '<i class="fas fa-star text-warning"></i>';
            } else if (i - 0.5 <= rating) {
                starsHtml += '<i class="fas fa-star-half-alt text-warning"></i>';
            } else {
                starsHtml += '<i class="far fa-star text-warning"></i>';
            }
        }
        return starsHtml;
    }

    generateSmallStarDisplay(rating) {
        let starsHtml = '<span class="text-warning small">';
        for (let i = 1; i <= 5; i++) {
            if (i <= rating) {
                starsHtml += '<i class="fas fa-star"></i>';
            } else {
                starsHtml += '<i class="far fa-star"></i>';
            }
        }
        starsHtml += `</span> <small class="text-muted">${rating}/5</small>`;
        return starsHtml;
    }

    showMessage(message, type) {
        const messageEl = document.getElementById('rating-message');
        if (messageEl) {
            messageEl.innerHTML = message;
            messageEl.className = `rating-message ${type}`;
            messageEl.style.display = 'block';

            if (type !== 'success') {
                setTimeout(() => {
                    messageEl.style.display = 'none';
                }, 3000);
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const examId = urlParams.get('id');

    if (examId) {
        new RatingSystem(parseInt(examId));
    }
});