// Admin Dashboard JavaScript
class AdminDashboard {
    constructor() {
        this.init();
    }

    init() {
        this.initSidebar();
        this.initCharts();
        this.initTooltips();
        this.initFormValidation();
        this.initTableFeatures();
    }

    // Sidebar Management
    initSidebar() {
        // Sidebar toggle for mobile
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                document.getElementById('sidebar').classList.toggle('show');
            });
        }

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (event) => {
            const sidebar = document.getElementById('sidebar');
            const toggle = document.getElementById('sidebarToggle');

            if (window.innerWidth <= 768 &&
                sidebar && sidebar.classList.contains('show') &&
                !sidebar.contains(event.target) &&
                (!toggle || !toggle.contains(event.target))) {
                sidebar.classList.remove('show');
            }
        });

        // Active navigation highlight
        this.setActiveNavigation();
    }

    setActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.sidebar .nav-link');

        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    // Chart Management
    initCharts() {
        if (typeof Chart !== 'undefined') {
            this.initActivityChart();
            this.initScoreChart();
            this.initSubjectChart();
        }
    }

    initActivityChart() {
        const activityCtx = document.getElementById('activityChart');
        if (!activityCtx) return;

        this.activityChart = new Chart(activityCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Lượt thi',
                    data: [],
                    borderColor: '#384AD5',
                    backgroundColor: 'rgba(56, 74, 213, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Người dùng mới',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    initScoreChart() {
        const scoreCtx = document.getElementById('scoreChart');
        if (!scoreCtx) return;

        this.scoreChart = new Chart(scoreCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Yếu (<40)', 'Trung bình (40-65)', 'Khá (65-80)', 'Giỏi (≥80)'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#ef4444',
                        '#f59e0b',
                        '#3b82f6',
                        '#10b981'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    initSubjectChart() {
        const subjectCtx = document.getElementById('subjectChart');
        if (!subjectCtx) return;

        this.subjectChart = new Chart(subjectCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Lượt thi',
                    data: [],
                    backgroundColor: 'rgba(56, 74, 213, 0.8)',
                    borderColor: '#384AD5',
                    borderWidth: 1,
                    yAxisID: 'y'
                }, {
                    label: 'Điểm trung bình',
                    data: [],
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    type: 'line',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }

    // Analytics Data Loading
    loadAnalyticsData(range = '7d') {
        fetch(`/admin/analytics_reports/analytics-data?range=${range}`)
            .then(response => response.json())
            .then(data => {
                if (this.activityChart) {
                    this.activityChart.data.labels = data.activity.dates;
                    this.activityChart.data.datasets[0].data = data.activity.exam_attempts;
                    this.activityChart.data.datasets[1].data = data.activity.new_users;
                    this.activityChart.update();
                }

                if (this.scoreChart) {
                    this.scoreChart.data.datasets[0].data = data.score_distribution;
                    this.scoreChart.update();
                }

                if (this.subjectChart) {
                    this.subjectChart.data.labels = data.subjects.names;
                    this.subjectChart.data.datasets[0].data = data.subjects.attempts;
                    this.subjectChart.data.datasets[1].data = data.subjects.avg_scores;
                    this.subjectChart.update();
                }
            })
            .catch(error => console.error('Error loading analytics data:', error));
    }

    // Form Validation
    initFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            const requiredFields = form.querySelectorAll('[required]');

            form.addEventListener('submit', (e) => {
                let isValid = true;

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        field.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        field.classList.remove('is-invalid');
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                    this.showAlert('Vui lòng điền đầy đủ các trường bắt buộc', 'warning');
                }
            });

            // Remove validation on input
            requiredFields.forEach(field => {
                field.addEventListener('input', function() {
                    if (this.value.trim()) {
                        this.classList.remove('is-invalid');
                    }
                });
            });
        });

        // Auto-resize textareas
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
        });
    }

    // Table Features
    initTableFeatures() {
        this.initSelectAll();
        this.initRowSelection();
        this.initExpandableText();
        this.initImageThumbnails();
    }

    initSelectAll() {
        const selectAll = document.getElementById('selectAll');
        if (selectAll) {
            selectAll.addEventListener('change', () => {
                const checkboxes = document.querySelectorAll('.row-checkbox');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = selectAll.checked;
                });
                this.updateSelectedCount();
            });
        }
    }

    initRowSelection() {
        const checkboxes = document.querySelectorAll('.row-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateSelectedCount();
            });
        });
        this.updateSelectedCount();
    }

    updateSelectedCount() {
        const selectedCountElement = document.getElementById('selectedCount');
        if (selectedCountElement) {
            const checkboxes = document.querySelectorAll('.row-checkbox:checked');
            selectedCountElement.textContent = checkboxes.length;
        }
    }

    initExpandableText() {
        window.toggleText = (button) => {
            const container = button.closest('.expandable-text');
            const preview = container.querySelector('.text-preview');
            const full = container.querySelector('.text-full');

            if (full.classList.contains('d-none')) {
                preview.classList.add('d-none');
                full.classList.remove('d-none');
                button.textContent = 'Thu gọn';
            } else {
                preview.classList.remove('d-none');
                full.classList.add('d-none');
                button.textContent = 'Xem thêm';
            }
        };
    }

    initImageThumbnails() {
        const thumbnails = document.querySelectorAll('.img-thumbnail');
        thumbnails.forEach(img => {
            img.style.cursor = 'pointer';
            img.addEventListener('click', function() {
                const modal = document.createElement('div');
                modal.className = 'modal fade';
                modal.innerHTML = `
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Xem hình ảnh</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body text-center">
                                <img src="${this.src}" class="img-fluid" alt="Image">
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
                modal.addEventListener('hidden.bs.modal', () => {
                    document.body.removeChild(modal);
                });
            });
        });
    }

    // Tooltips
    initTooltips() {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    // Utility Functions
    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.content-wrapper');
        if (container) {
            container.insertBefore(alert, container.firstChild);

            // Auto-hide after 5 seconds
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 5000);
        }
    }

    changePageSize(size) {
        const url = new URL(window.location);
        url.searchParams.set('page_size', size);
        url.searchParams.delete('page');
        window.location.href = url.toString();
    }

    applyFilter(index, operation, arg, checked) {
        const url = new URL(window.location);
        const paramName = `flt${index}_${operation}`;

        if (checked) {
            url.searchParams.set(paramName, arg);
        } else {
            url.searchParams.delete(paramName);
        }

        url.searchParams.delete('page');
        window.location.href = url.toString();
    }

    executeBulkAction(action, name) {
        const checkboxes = document.querySelectorAll('.row-checkbox:checked');

        if (checkboxes.length === 0) {
            this.showAlert('Vui lòng chọn ít nhất một mục', 'warning');
            return;
        }

        if (!confirm(`Bạn có chắc chắn muốn thực hiện "${name}" cho ${checkboxes.length} mục đã chọn?`)) {
            return;
        }

        const form = document.createElement('form');
        form.method = 'POST';
        form.action = window.location.pathname + '/action';

        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = action;
        form.appendChild(actionInput);

        checkboxes.forEach(checkbox => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'rowid';
            input.value = checkbox.value;
            form.appendChild(input);
        });

        const urlInput = document.createElement('input');
        urlInput.type = 'hidden';
        urlInput.name = 'url';
        urlInput.value = window.location.href;
        form.appendChild(urlInput);

        document.body.appendChild(form);
        form.submit();
    }

    togglePassword(button) {
        const input = button.previousElementSibling;
        const icon = button.querySelector('i');

        if (input.type === 'password') {
            input.type = 'text';
            icon.className = 'bi bi-eye-slash';
        } else {
            input.type = 'password';
            icon.className = 'bi bi-eye';
        }
    }

    changeTimeRange(range) {
        this.loadAnalyticsData(range);

        // Update dropdown text
        const dropdownButton = document.querySelector('.dropdown-toggle');
        if (dropdownButton) {
            const rangeText = range === '7d' ? '7 ngày' : range === '30d' ? '30 ngày' : '90 ngày';
            dropdownButton.innerHTML = `<i class="bi bi-calendar-range me-2"></i>${rangeText}`;
        }
    }

    exportData() {
        window.open('/admin/analytics_reports/export-analytics', '_blank');
    }

    exportTableData() {
        const table = document.getElementById('examStatsTable');
        if (!table) return;

        let csv = [];

        // Get headers
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent);
        csv.push(headers.join(','));

        // Get data
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        rows.forEach(row => {
            const cols = Array.from(row.querySelectorAll('td')).map(td => {
                return td.textContent.replace(/,/g, ';').replace(/\n/g, ' ').trim();
            });
            csv.push(cols.join(','));
        });

        // Download
        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'exam_statistics.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Global Functions
window.toggleSelectAll = function() {
    const selectAll = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('.row-checkbox');

    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAll.checked;
    });

    adminDashboard.updateSelectedCount();
};

window.changePageSize = function(size) {
    adminDashboard.changePageSize(size);
};

window.applyFilter = function(index, operation, arg, checked) {
    adminDashboard.applyFilter(index, operation, arg, checked);
};

window.executeBulkAction = function(action, name) {
    adminDashboard.executeBulkAction(action, name);
};

window.togglePassword = function(button) {
    adminDashboard.togglePassword(button);
};

window.changeTimeRange = function(range) {
    adminDashboard.changeTimeRange(range);
};

window.exportData = function() {
    adminDashboard.exportData();
};

window.exportTableData = function() {
    adminDashboard.exportTableData();
};

window.clearAllFilters = function() {
    const url = new URL(window.location);

    const keysToRemove = [];
    for (const [key, value] of url.searchParams.entries()) {
        if (key.startsWith('flt')) {
            keysToRemove.push(key);
        }
    }

    keysToRemove.forEach(key => url.searchParams.delete(key));
    url.searchParams.delete('page');

    window.location.href = url.toString();
};

// Initialize when DOM is loaded
let adminDashboard;
document.addEventListener('DOMContentLoaded', function() {
    adminDashboard = new AdminDashboard();

    // Load analytics data if on analytics page
    if (window.location.pathname.includes('analytics_reports')) {
        adminDashboard.loadAnalyticsData('7d');
    }
});