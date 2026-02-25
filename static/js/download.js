// Download Page Logic
// URL validation, download management, progress polling

class DownloadManager {
    constructor() {
        this.currentTaskId = null;
        this.progressInterval = null;
        this.pollInterval = 2000; // Poll every 2 seconds
        this.pollFailureCount = 0;
        this.activeDownloadsInterval = null;
        this.activeDownloadsPollInterval = 3000; // Poll active downloads every 3 seconds
        
        this.init();
    }

    init() {
        this.attachEventListeners();
        this.loadFileTypeFilters();
        this.checkActiveDownloads(); // Check for active downloads on page load
        this.startActiveDownloadsPolling(); // Start polling for all active downloads
        this.setupMultiUrlMode(); // Setup multi-URL functionality
    }

    setupMultiUrlMode() {
        this.isMultiUrlMode = false;
        
        // Toggle button
        const toggleBtn = document.getElementById('toggleMultiUrlBtn');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleMultiUrlMode());
        }
        
        // Textarea input for counting URLs
        const textarea = document.getElementById('urlTextarea');
        if (textarea) {
            textarea.addEventListener('input', () => this.updateUrlCount());
        }
        
        // Multi download button
        const multiBtn = document.getElementById('startMultiBtn');
        if (multiBtn) {
            multiBtn.addEventListener('click', () => this.startMultiDownload());
        }
        
        // Clear completed button
        const clearBtn = document.getElementById('clearCompletedBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearCompletedDownloads());
        }
    }
    
    toggleMultiUrlMode() {
        this.isMultiUrlMode = !this.isMultiUrlMode;
        
        const singleInput = document.getElementById('singleUrlInput');
        const multiInput = document.getElementById('multiUrlInput');
        const startBtn = document.getElementById('startBtn');
        const multiBtn = document.getElementById('startMultiBtn');
        const toggleBtn = document.getElementById('toggleMultiUrlBtn');
        
        if (this.isMultiUrlMode) {
            // Switch to multi-URL mode
            if (singleInput) singleInput.style.display = 'none';
            if (multiInput) multiInput.style.display = 'block';
            if (startBtn) startBtn.style.display = 'none';
            if (multiBtn) multiBtn.style.display = 'block';
            if (toggleBtn) {
                toggleBtn.innerHTML = '<i class="bi bi-dash-circle"></i> Single URL';
            }
            this.updateUrlCount();
        } else {
            // Switch to single-URL mode
            if (singleInput) singleInput.style.display = 'block';
            if (multiInput) multiInput.style.display = 'none';
            if (startBtn) startBtn.style.display = 'block';
            if (multiBtn) multiBtn.style.display = 'none';
            if (toggleBtn) {
                toggleBtn.innerHTML = '<i class="bi bi-plus-circle"></i> Multi URL';
            }
        }
    }
    
    updateUrlCount() {
        const textarea = document.getElementById('urlTextarea');
        const countSpan = document.getElementById('urlCount');
        const multiBtn = document.getElementById('startMultiBtn');
        
        if (!textarea || !countSpan) return;
        
        const urls = this.parseMultiUrls(textarea.value);
        countSpan.textContent = urls.length;
        
        // Disable button if no valid URLs
        if (multiBtn) {
            multiBtn.disabled = urls.length === 0;
        }
    }
    
    parseMultiUrls(text) {
        if (!text) return [];
        
        // Split by newlines and filter valid URLs
        const lines = text.split('\n');
        const urls = [];
        
        for (let line of lines) {
            const url = line.trim();
            if (url && Utils.isValidKemonoUrl(url)) {
                urls.push(url);
            }
        }
        
        return urls;
    }

    attachEventListeners() {
        // Form submit
        const form = document.getElementById('downloadForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startDownload();
            });
        }

        // Start download button
        const startBtn = document.getElementById('startBtn');
        if (startBtn) {
            startBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.startDownload();
            });
        }

        // Pause button
        const pauseBtn = document.getElementById('pauseBtn');
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.pauseDownload());
        }

        // Resume button
        const resumeBtn = document.getElementById('resumeBtn');
        if (resumeBtn) {
            resumeBtn.addEventListener('click', () => this.resumeDownload());
        }

        // Cancel button
        const cancelBtn = document.getElementById('cancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelDownload());
        }

        // URL input validation
        const urlInput = document.getElementById('urlInput');
        if (urlInput) {
            urlInput.addEventListener('input', Utils.debounce(() => {
                this.validateUrl();
            }, 500));
        }

        // File type checkboxes
        const filterAll = document.getElementById('filterAll');
        if (filterAll) {
            filterAll.addEventListener('change', (e) => {
                if (e.target.checked) {
                    // Uncheck other filters when "All" is selected
                    document.querySelectorAll('input[type="checkbox"]:not(#filterAll)').forEach(cb => {
                        cb.checked = false;
                    });
                }
                this.saveFileTypeFilters();
            });
        }

        // Other filter checkboxes
        document.querySelectorAll('input[type="checkbox"]:not(#filterAll)').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    // Uncheck "All" when specific filter is selected
                    const allCheckbox = document.getElementById('filterAll');
                    if (allCheckbox) allCheckbox.checked = false;
                }
                this.saveFileTypeFilters();
            });
        });
    }

    validateUrl() {
        const urlInput = document.getElementById('urlInput');
        const url = urlInput.value.trim();

        if (!url) {
            urlInput.classList.remove('is-valid', 'is-invalid');
            return false;
        }

        if (!Utils.isValidUrl(url)) {
            urlInput.classList.remove('is-valid');
            urlInput.classList.add('is-invalid');
            return false;
        }

        if (!Utils.isValidKemonoUrl(url)) {
            urlInput.classList.remove('is-valid');
            urlInput.classList.add('is-invalid');
            return false;
        }

        urlInput.classList.remove('is-invalid');
        urlInput.classList.add('is-valid');
        return true;
    }

    getSelectedFileTypes() {
        const selected = [];
        
        // Check if "All" is selected
        const filterAll = document.getElementById('filterAll');
        if (filterAll && filterAll.checked) {
            return ['all'];
        }
        
        // Get specific filters
        const filters = ['filterImages', 'filterVideos', 'filterArchives', 'filterAudio'];
        filters.forEach(filterId => {
            const checkbox = document.getElementById(filterId);
            if (checkbox && checkbox.checked) {
                selected.push(checkbox.value);
            }
        });
        
        return selected.length > 0 ? selected : ['all'];
    }

    saveFileTypeFilters() {
        const selected = this.getSelectedFileTypes();
        localStorage.setItem('fileTypeFilters', JSON.stringify(selected));
    }

    loadFileTypeFilters() {
        const saved = localStorage.getItem('fileTypeFilters');
        if (saved) {
            try {
                const filters = JSON.parse(saved);
                
                if (filters.includes('all')) {
                    const filterAll = document.getElementById('filterAll');
                    if (filterAll) filterAll.checked = true;
                } else {
                    const filterMap = {
                        'images': 'filterImages',
                        'videos': 'filterVideos',
                        'archives': 'filterArchives',
                        'audio': 'filterAudio'
                    };
                    
                    filters.forEach(filter => {
                        const checkbox = document.getElementById(filterMap[filter]);
                        if (checkbox) checkbox.checked = true;
                    });
                }
            } catch (e) {
                console.error('Error loading file type filters:', e);
            }
        }
    }

    async startDownload() {
        if (!this.validateUrl()) {
            Toast.error('Iltimos, to\'g\'ri URL manzilini kiriting');
            return;
        }

        const url = document.getElementById('urlInput').value.trim();
        const fileTypes = this.getSelectedFileTypes();

        const startBtn = document.getElementById('startBtn');
        Utils.showLoading(startBtn);

        try {
            const response = await Ajax.post('/download/start', {
                url: url,
                filters: fileTypes
            });

            if (response.success) {
                this.currentTaskId = response.task_id;
                this.saveActiveTask(); // Save to localStorage
                Toast.success('Yuklab olish boshlandi');
                this.showProgressSection();
                this.startProgressPolling();
                this.updateButtonStates('downloading');
            } else {
                Toast.error(response.error || 'Yuklab olishni boshlashda xatolik');
            }
        } catch (error) {
            console.error('Start download error:', error);
            Toast.error('Serverga ulanishda xatolik');
        } finally {
            Utils.hideLoading(startBtn);
        }
    }
    
    async startMultiDownload() {
        const textarea = document.getElementById('urlTextarea');
        if (!textarea) return;
        
        const urls = this.parseMultiUrls(textarea.value);
        
        if (urls.length === 0) {
            Toast.error('Iltimos, kamida bitta to\'g\'ri URL kiriting');
            return;
        }
        
        const fileTypes = this.getSelectedFileTypes();
        const multiBtn = document.getElementById('startMultiBtn');
        
        Utils.showLoading(multiBtn);
        
        try {
            const response = await Ajax.post('/download/start-multi', {
                urls: urls,
                filters: fileTypes
            });
            
            if (response.success) {
                const count = response.task_ids ? response.task_ids.length : 0;
                Toast.success(`${count} ta yuklab olish boshlandi`);
                
                // Clear textarea
                textarea.value = '';
                this.updateUrlCount();
                
                // Reload active downloads
                this.loadActiveDownloads();
            } else {
                Toast.error(response.error || 'Yuklab olishni boshlashda xatolik');
            }
        } catch (error) {
            console.error('Start multi download error:', error);
            Toast.error('Serverga ulanishda xatolik');
        } finally {
            Utils.hideLoading(multiBtn);
        }
    }

    async pauseDownload() {
        if (!this.currentTaskId) return;

        const pauseBtn = document.getElementById('pauseBtn');
        Utils.showLoading(pauseBtn);

        try {
            const response = await Ajax.post(`/download/pause/${this.currentTaskId}`);
            
            if (response.success) {
                Toast.info('Yuklab olish to\'xtatildi');
                this.stopProgressPolling();
                this.updateButtonStates('paused');
            } else {
                Toast.error(response.error || 'To\'xtatishda xatolik');
            }
        } catch (error) {
            console.error('Pause download error:', error);
            Toast.error('Serverga ulanishda xatolik');
        } finally {
            Utils.hideLoading(pauseBtn);
        }
    }

    async resumeDownload() {
        if (!this.currentTaskId) return;

        const resumeBtn = document.getElementById('resumeBtn');
        Utils.showLoading(resumeBtn);

        try {
            const response = await Ajax.post(`/download/resume/${this.currentTaskId}`);
            
            if (response.success) {
                Toast.success('Yuklab olish davom ettirildi');
                this.startProgressPolling();
                this.updateButtonStates('downloading');
            } else {
                Toast.error(response.error || 'Davom ettirishda xatolik');
            }
        } catch (error) {
            console.error('Resume download error:', error);
            Toast.error('Serverga ulanishda xatolik');
        } finally {
            Utils.hideLoading(resumeBtn);
        }
    }

    async cancelDownload() {
        if (!this.currentTaskId) return;

        if (!confirm('Yuklab olishni bekor qilmoqchimisiz?')) {
            return;
        }

        const cancelBtn = document.getElementById('cancelBtn');
        Utils.showLoading(cancelBtn);

        try {
            const response = await Ajax.post(`/download/cancel/${this.currentTaskId}`);
            
            if (response.success) {
                Toast.warning('Yuklab olish bekor qilindi');
                this.stopProgressPolling();
                this.hideProgressSection();
                this.resetDownloadForm();
                this.clearActiveTask(); // Clear from localStorage
                this.updateButtonStates('idle');
            } else {
                Toast.error(response.error || 'Bekor qilishda xatolik');
            }
        } catch (error) {
            console.error('Cancel download error:', error);
            Toast.error('Serverga ulanishda xatolik');
        } finally {
            Utils.hideLoading(cancelBtn);
        }
    }

    startProgressPolling() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }

        // Reset failure count
        this.pollFailureCount = 0;

        this.progressInterval = setInterval(() => {
            this.updateProgress();
        }, this.pollInterval);

        // Initial update
        this.updateProgress();
    }

    stopProgressPolling() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    async updateProgress() {
        if (!this.currentTaskId) {
            this.stopProgressPolling();
            return;
        }

        try {
            const response = await Ajax.get(`/api/progress/${this.currentTaskId}`);
            
            if (response.success && response.progress) {
                const progress = response.progress;
                this.renderProgress(progress);

                // Check if completed
                if (progress.status === 'completed') {
                    this.stopProgressPolling();
                    this.clearActiveTask(); // Clear from localStorage
                    Toast.success('Yuklab olish tugadi!');
                    this.updateButtonStates('completed');
                    setTimeout(() => {
                        this.hideProgressSection();
                        this.resetDownloadForm();
                    }, 3000);
                } else if (progress.status === 'failed') {
                    this.stopProgressPolling();
                    this.clearActiveTask(); // Clear from localStorage
                    const errorMsg = progress.error || 'Noma\'lum xatolik';
                    Toast.error('Yuklab olishda xatolik: ' + errorMsg);
                    this.updateButtonStates('failed');
                }
            } else {
                // If progress not found, stop polling
                console.warn('Progress not found for task:', this.currentTaskId);
            }
        } catch (error) {
            console.error('Progress update error:', error);
            // Don't show error toast on every poll failure
            // But stop polling after too many failures
            if (!this.pollFailureCount) this.pollFailureCount = 0;
            this.pollFailureCount++;
            
            if (this.pollFailureCount > 5) {
                this.stopProgressPolling();
                Toast.error('Serverga ulanishda xatolik');
                this.updateButtonStates('failed');
            }
        }
    }

    renderProgress(progress) {
        if (!progress) {
            console.warn('Progress is null or undefined');
            return;
        }

        // Update progress bar
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const progressPercent = document.getElementById('progressPercent');
        
        if (progressBar) {
            const percent = progress.percent || 0;
            progressBar.style.width = percent + '%';
            progressBar.setAttribute('aria-valuenow', percent);
            if (progressText) progressText.textContent = Math.round(percent) + '%';
            if (progressPercent) progressPercent.textContent = Math.round(percent) + '%';
        }

        // Update file count
        const fileCount = document.getElementById('fileCount');
        if (fileCount) {
            const downloaded = progress.downloaded_files || progress.downloaded || 0;
            const total = progress.total_files || progress.total || 0;
            fileCount.textContent = `${downloaded} / ${total}`;
        }

        // Update current file
        const currentFile = document.getElementById('currentFile');
        if (currentFile) {
            if (progress.current_file) {
                currentFile.textContent = progress.current_file;
            } else {
                currentFile.textContent = '-';
            }
        }
        
        // Update status badge
        const statusBadge = document.getElementById('statusBadge');
        if (statusBadge) {
            const statusMap = {
                'pending': { text: 'Kutilmoqda...', class: 'bg-secondary' },
                'downloading': { text: 'Yuklanmoqda...', class: 'bg-primary' },
                'paused': { text: 'To\'xtatilgan', class: 'bg-warning' },
                'completed': { text: 'Tugadi', class: 'bg-success' },
                'failed': { text: 'Xatolik', class: 'bg-danger' },
                'cancelled': { text: 'Bekor qilindi', class: 'bg-secondary' }
            };
            
            const status = statusMap[progress.status] || statusMap['pending'];
            statusBadge.textContent = status.text;
            statusBadge.className = 'badge ' + status.class;
        }
    }

    showProgressSection() {
        const section = document.getElementById('progressSection');
        if (section) {
            section.classList.add('active');
            section.style.display = 'block';
        }
    }

    hideProgressSection() {
        const section = document.getElementById('progressSection');
        if (section) {
            section.classList.remove('active');
            section.style.display = 'none';
        }
    }

    resetDownloadForm() {
        const urlInput = document.getElementById('urlInput');
        if (urlInput) {
            urlInput.value = '';
            urlInput.classList.remove('is-valid', 'is-invalid');
        }

        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const progressPercent = document.getElementById('progressPercent');
        
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', 0);
        }
        if (progressText) progressText.textContent = '0%';
        if (progressPercent) progressPercent.textContent = '0%';

        const fileCount = document.getElementById('fileCount');
        if (fileCount) fileCount.textContent = '0 / 0';

        const currentFile = document.getElementById('currentFile');
        if (currentFile) currentFile.textContent = '-';
    }

    updateButtonStates(state) {
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const resumeBtn = document.getElementById('resumeBtn');
        const cancelBtn = document.getElementById('cancelBtn');

        switch (state) {
            case 'idle':
                if (startBtn) startBtn.disabled = false;
                if (pauseBtn) pauseBtn.disabled = true;
                if (resumeBtn) resumeBtn.style.display = 'none';
                if (cancelBtn) cancelBtn.disabled = true;
                break;
            case 'downloading':
                if (startBtn) startBtn.disabled = true;
                if (pauseBtn) {
                    pauseBtn.disabled = false;
                    pauseBtn.style.display = 'inline-block';
                }
                if (resumeBtn) resumeBtn.style.display = 'none';
                if (cancelBtn) cancelBtn.disabled = false;
                break;
            case 'paused':
                if (startBtn) startBtn.disabled = true;
                if (pauseBtn) pauseBtn.style.display = 'none';
                if (resumeBtn) {
                    resumeBtn.disabled = false;
                    resumeBtn.style.display = 'inline-block';
                }
                if (cancelBtn) cancelBtn.disabled = false;
                break;
            case 'completed':
            case 'failed':
                if (startBtn) startBtn.disabled = false;
                if (pauseBtn) pauseBtn.disabled = true;
                if (resumeBtn) resumeBtn.style.display = 'none';
                if (cancelBtn) cancelBtn.disabled = true;
                break;
        }
    }

    async checkActiveDownloads() {
        // Check localStorage for active task
        const savedTaskId = localStorage.getItem('activeDownloadTask');
        
        if (savedTaskId) {
            try {
                // Check if task is still active
                const response = await Ajax.get(`/api/progress/${savedTaskId}`);
                
                if (response.success && response.progress) {
                    const progress = response.progress;
                    
                    // If download is still active, resume polling
                    if (progress.status === 'downloading' || progress.status === 'pending') {
                        this.currentTaskId = savedTaskId;
                        this.showProgressSection();
                        this.renderProgress(progress);
                        this.startProgressPolling();
                        this.updateButtonStates('downloading');
                        
                        Toast.info('Yuklab olish davom ettirilmoqda...');
                    } else if (progress.status === 'paused') {
                        this.currentTaskId = savedTaskId;
                        this.showProgressSection();
                        this.renderProgress(progress);
                        this.updateButtonStates('paused');
                        
                        Toast.info('Yuklab olish to\'xtatilgan. Davom ettirish uchun Resume bosing.');
                    } else {
                        // Completed or failed - clear localStorage
                        localStorage.removeItem('activeDownloadTask');
                    }
                }
            } catch (error) {
                console.error('Error checking active downloads:', error);
                // Clear invalid task from localStorage
                localStorage.removeItem('activeDownloadTask');
            }
        }
    }

    saveActiveTask() {
        if (this.currentTaskId) {
            localStorage.setItem('activeDownloadTask', this.currentTaskId);
        }
    }

    clearActiveTask() {
        localStorage.removeItem('activeDownloadTask');
        this.currentTaskId = null;
    }

    // ===== Active Downloads Management =====
    
    startActiveDownloadsPolling() {
        // Clear existing interval
        if (this.activeDownloadsInterval) {
            clearInterval(this.activeDownloadsInterval);
        }
        
        // Start polling
        this.activeDownloadsInterval = setInterval(() => {
            this.loadActiveDownloads();
        }, this.activeDownloadsPollInterval);
        
        // Initial load
        this.loadActiveDownloads();
    }
    
    stopActiveDownloadsPolling() {
        if (this.activeDownloadsInterval) {
            clearInterval(this.activeDownloadsInterval);
            this.activeDownloadsInterval = null;
        }
    }
    
    async loadActiveDownloads() {
        try {
            const response = await Ajax.get('/api/downloads/active');
            
            if (response.success && response.downloads) {
                this.renderActiveDownloads(response.downloads);
            }
        } catch (error) {
            console.error('Error loading active downloads:', error);
        }
    }
    
    renderActiveDownloads(downloads) {
        const container = document.getElementById('activeDownloadsList');
        const noDownloadsMsg = document.getElementById('noDownloadsMessage');
        const countBadge = document.getElementById('activeDownloadsCount');
        const clearBtn = document.getElementById('clearCompletedBtn');
        
        if (!container) return;
        
        // Filter active downloads (exclude only cancelled and deleted)
        const activeDownloads = Object.entries(downloads).filter(([taskId, download]) => {
            return download.status !== 'cancelled' && download.status !== 'deleted';
        });
        
        // Count completed downloads
        const completedCount = activeDownloads.filter(([_, download]) => {
            return download.status === 'completed' || download.status === 'failed';
        }).length;
        
        // Update count badge
        if (countBadge) {
            countBadge.textContent = activeDownloads.length;
        }
        
        // Show/hide clear completed button
        if (clearBtn) {
            clearBtn.style.display = completedCount > 0 ? 'block' : 'none';
        }
        
        // Show/hide no downloads message
        if (activeDownloads.length === 0) {
            if (noDownloadsMsg) {
                noDownloadsMsg.style.display = 'block';
            }
            // Clear container except the message
            Array.from(container.children).forEach(child => {
                if (child.id !== 'noDownloadsMessage') {
                    child.remove();
                }
            });
            return;
        }
        
        if (noDownloadsMsg) {
            noDownloadsMsg.style.display = 'none';
        }
        
        // Track existing cards
        const existingCards = new Set();
        Array.from(container.querySelectorAll('.download-card')).forEach(card => {
            existingCards.add(card.dataset.taskId);
        });
        
        // Render each download
        activeDownloads.forEach(([taskId, download]) => {
            const existingCard = container.querySelector(`[data-task-id="${taskId}"]`);
            
            if (existingCard) {
                // Update existing card
                this.updateDownloadCard(taskId, download);
            } else {
                // Create new card
                const card = this.createDownloadCard(taskId, download);
                container.appendChild(card);
            }
        });
        
        // Remove cards that are no longer active
        Array.from(container.querySelectorAll('.download-card')).forEach(card => {
            const taskId = card.dataset.taskId;
            const stillActive = activeDownloads.some(([id]) => id === taskId);
            if (!stillActive) {
                card.remove();
            }
        });
    }
    
    createDownloadCard(taskId, download) {
        const card = document.createElement('div');
        card.className = `card download-card status-${download.status}`;
        card.dataset.taskId = taskId;
        
        const statusMap = {
            'pending': { text: 'Pending', class: 'bg-secondary' },
            'downloading': { text: 'Downloading', class: 'bg-primary' },
            'paused': { text: 'Paused', class: 'bg-warning' },
            'completed': { text: 'Completed', class: 'bg-success' },
            'failed': { text: 'Failed', class: 'bg-danger' }
        };
        
        const status = statusMap[download.status] || statusMap['pending'];
        const percent = download.progress_percent || 0;
        const downloaded = download.downloaded_files || 0;
        const total = download.total_files || 0;
        
        // Truncate URL
        const url = download.url || '';
        const truncatedUrl = url.length > 60 ? url.substring(0, 60) + '...' : url;
        
        // Get post/artist name from URL
        const urlParts = url.split('/');
        const postName = urlParts[urlParts.length - 1] || 'Unknown';
        
        card.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="flex-grow-1">
                        <h6 class="card-title mb-1">${this.escapeHtml(postName)}</h6>
                        <div class="download-url" title="${this.escapeHtml(url)}">${this.escapeHtml(truncatedUrl)}</div>
                    </div>
                    <span class="badge ${status.class} ms-2">${status.text}</span>
                </div>
                
                <div class="progress mb-2" style="height: 20px;">
                    <div class="progress-bar progress-bar-striped ${download.status === 'downloading' ? 'progress-bar-animated' : ''}" 
                         role="progressbar" 
                         style="width: ${percent}%"
                         data-progress-bar>
                        <span>${Math.round(percent)}%</span>
                    </div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <small class="text-muted">Files: <span data-file-count>${downloaded} / ${total}</span></small>
                    <small class="download-speed" data-speed style="display: none;">0 KB/s</small>
                </div>
                
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted text-truncate" data-current-file style="max-width: 60%;">
                        ${download.current_file || 'Preparing...'}
                    </small>
                    
                    <div class="btn-group btn-group-sm" role="group">
                        ${download.status === 'downloading' ? `
                            <button class="btn btn-warning" data-action="pause" data-task-id="${taskId}">
                                <i class="bi bi-pause"></i>
                            </button>
                        ` : ''}
                        ${download.status === 'paused' ? `
                            <button class="btn btn-success" data-action="resume" data-task-id="${taskId}">
                                <i class="bi bi-play"></i>
                            </button>
                        ` : ''}
                        ${download.status !== 'completed' && download.status !== 'failed' ? `
                            <button class="btn btn-danger" data-action="cancel" data-task-id="${taskId}">
                                <i class="bi bi-x"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-secondary" data-action="delete" data-task-id="${taskId}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Attach event listeners
        this.attachCardEventListeners(card, taskId);
        
        return card;
    }
    
    updateDownloadCard(taskId, download) {
        const card = document.querySelector(`[data-task-id="${taskId}"]`);
        if (!card) return;
        
        // Update status class
        card.className = `card download-card status-${download.status}`;
        
        // Update progress bar
        const progressBar = card.querySelector('[data-progress-bar]');
        if (progressBar) {
            const percent = download.progress_percent || 0;
            progressBar.style.width = percent + '%';
            progressBar.querySelector('span').textContent = Math.round(percent) + '%';
            
            // Update animation
            if (download.status === 'downloading') {
                progressBar.classList.add('progress-bar-animated');
            } else {
                progressBar.classList.remove('progress-bar-animated');
            }
        }
        
        // Update file count
        const fileCount = card.querySelector('[data-file-count]');
        if (fileCount) {
            const downloaded = download.downloaded_files || 0;
            const total = download.total_files || 0;
            fileCount.textContent = `${downloaded} / ${total}`;
        }
        
        // Update current file
        const currentFile = card.querySelector('[data-current-file]');
        if (currentFile) {
            currentFile.textContent = download.current_file || 'Preparing...';
        }
        
        // Update status badge
        const statusMap = {
            'pending': { text: 'Pending', class: 'bg-secondary' },
            'downloading': { text: 'Downloading', class: 'bg-primary' },
            'paused': { text: 'Paused', class: 'bg-warning' },
            'completed': { text: 'Completed', class: 'bg-success' },
            'failed': { text: 'Failed', class: 'bg-danger' }
        };
        
        const badge = card.querySelector('.badge');
        if (badge) {
            const status = statusMap[download.status] || statusMap['pending'];
            badge.className = `badge ${status.class} ms-2`;
            badge.textContent = status.text;
        }
        
        // Update buttons based on status
        const btnGroup = card.querySelector('.btn-group');
        if (btnGroup) {
            btnGroup.innerHTML = '';
            
            if (download.status === 'downloading') {
                btnGroup.innerHTML += `
                    <button class="btn btn-warning" data-action="pause" data-task-id="${taskId}">
                        <i class="bi bi-pause"></i>
                    </button>
                `;
            }
            
            if (download.status === 'paused') {
                btnGroup.innerHTML += `
                    <button class="btn btn-success" data-action="resume" data-task-id="${taskId}">
                        <i class="bi bi-play"></i>
                    </button>
                `;
            }
            
            // Show cancel button only for active downloads
            if (download.status !== 'completed' && download.status !== 'failed') {
                btnGroup.innerHTML += `
                    <button class="btn btn-danger" data-action="cancel" data-task-id="${taskId}">
                        <i class="bi bi-x"></i>
                    </button>
                `;
            }
            
            // Always show delete button
            btnGroup.innerHTML += `
                <button class="btn btn-secondary" data-action="delete" data-task-id="${taskId}">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            
            // Re-attach event listeners
            this.attachCardEventListeners(card, taskId);
        }
    }
    
    attachCardEventListeners(card, taskId) {
        // Pause button
        const pauseBtn = card.querySelector('[data-action="pause"]');
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.handleCardAction('pause', taskId));
        }
        
        // Resume button
        const resumeBtn = card.querySelector('[data-action="resume"]');
        if (resumeBtn) {
            resumeBtn.addEventListener('click', () => this.handleCardAction('resume', taskId));
        }
        
        // Cancel button
        const cancelBtn = card.querySelector('[data-action="cancel"]');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.handleCardAction('cancel', taskId));
        }
        
        // Delete button
        const deleteBtn = card.querySelector('[data-action="delete"]');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.handleCardAction('delete', taskId));
        }
    }
    
    async handleCardAction(action, taskId) {
        try {
            let response;
            
            switch (action) {
                case 'pause':
                    response = await Ajax.post(`/download/pause/${taskId}`);
                    if (response.success) {
                        Toast.info('Download paused');
                    }
                    break;
                    
                case 'resume':
                    response = await Ajax.post(`/download/resume/${taskId}`);
                    if (response.success) {
                        Toast.success('Download resumed');
                    }
                    break;
                    
                case 'cancel':
                    if (!confirm('Cancel this download?')) return;
                    response = await Ajax.post(`/download/cancel/${taskId}`);
                    if (response.success) {
                        Toast.warning('Download cancelled');
                        // Remove card immediately
                        const card = document.querySelector(`[data-task-id="${taskId}"]`);
                        if (card) card.remove();
                    }
                    break;
                    
                case 'delete':
                    if (!confirm('Delete this download from the list?')) return;
                    response = await Ajax.post(`/download/delete/${taskId}`);
                    if (response.success) {
                        Toast.info('Download removed');
                        // Remove card immediately
                        const card = document.querySelector(`[data-task-id="${taskId}"]`);
                        if (card) card.remove();
                    }
                    break;
            }
            
            if (response && !response.success) {
                Toast.error(response.error || 'Action failed');
            }
            
            // Reload active downloads
            this.loadActiveDownloads();
            
        } catch (error) {
            console.error(`Error handling ${action}:`, error);
            Toast.error('Server connection error');
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async clearCompletedDownloads() {
        const container = document.getElementById('activeDownloadsList');
        if (!container) return;
        
        const completedCards = container.querySelectorAll('.download-card.status-completed, .download-card.status-failed');
        
        if (completedCards.length === 0) return;
        
        if (!confirm(`${completedCards.length} ta tugallangan yuklab olishni o'chirmoqchimisiz?`)) {
            return;
        }
        
        const deletePromises = [];
        completedCards.forEach(card => {
            const taskId = card.dataset.taskId;
            deletePromises.push(
                Ajax.post(`/download/delete/${taskId}`)
                    .then(() => {
                        card.remove();
                    })
                    .catch(error => {
                        console.error(`Error deleting ${taskId}:`, error);
                    })
            );
        });
        
        await Promise.all(deletePromises);
        Toast.success('Tugallangan yuklab olishlar o\'chirildi');
        this.loadActiveDownloads();
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('urlInput')) {
        window.downloadManager = new DownloadManager();
    }
});
