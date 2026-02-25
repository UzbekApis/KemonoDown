// Library Page Logic
// Lazy loading images, filter handlers, delete confirmation, file preview

class LibraryManager {
    constructor() {
        this.currentFilter = 'all';
        this.currentSort = 'date_desc';
        this.lazyLoadObserver = null;
        this.files = [];
        this.init();
    }

    init() {
        this.loadFiles();
        this.attachEventListeners();
        this.loadFilterPreferences();
    }
    
    async loadFiles() {
        console.log('Loading files from API...');
        try {
            const response = await Ajax.get('/library/files');
            console.log('API Response:', response);
            
            if (response.success) {
                this.files = response.files || [];
                console.log(`Loaded ${this.files.length} files`);
                this.renderFiles();
                if (this.files.length > 0) {
                    Toast.success(`${this.files.length} ta fayl yuklandi`);
                }
            } else {
                console.error('API Error:', response.error);
                Toast.error('Fayllarni yuklashda xatolik');
            }
        } catch (error) {
            console.error('Load files error:', error);
            Toast.error('Serverga ulanishda xatolik');
        }
    }
    
    renderFiles() {
        let container = document.querySelector('.library-grid');
        
        // If library-grid doesn't exist, create it
        if (!container) {
            const libraryContainer = document.getElementById('libraryContainer');
            if (!libraryContainer) {
                console.error('Library container not found');
                return;
            }
            
            // Clear existing content
            libraryContainer.innerHTML = '';
            
            // Create library-grid
            container = document.createElement('div');
            container.className = 'library-grid';
            libraryContainer.appendChild(container);
        }
        
        if (this.files.length === 0) {
            container.parentElement.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="bi bi-inbox display-1 text-muted"></i>
                    <p class="mt-3 text-muted">Hech qanday fayl topilmadi</p>
                    <p class="text-muted">Yuklab olish sahifasidan fayllarni yuklab oling</p>
                    <a href="/download" class="btn btn-primary">
                        <i class="bi bi-download"></i> Yuklab olishni boshlash
                    </a>
                </div>
            `;
            return;
        }
        
        // Group files by post
        const postGroups = this.groupFilesByPost();
        
        container.innerHTML = '';
        
        // Render each post group
        postGroups.forEach(group => {
            const postCard = this.createPostCard(group);
            container.appendChild(postCard);
        });
        
        this.initLazyLoading();
        this.updateFileCount();
    }
    
    groupFilesByPost() {
        const groups = {};
        
        this.files.forEach(file => {
            const postKey = file.post_id || 'unknown';
            if (!groups[postKey]) {
                groups[postKey] = {
                    post_id: file.post_id,
                    post_title: file.post_title || 'Unknown Post',
                    service: file.service,
                    user_id: file.user_id,
                    files: []
                };
            }
            groups[postKey].files.push(file);
        });
        
        return Object.values(groups);
    }
    
    createPostCard(group) {
        const card = document.createElement('div');
        card.className = 'post-card';
        card.setAttribute('data-post-id', group.post_id);
        
        // Get first file as thumbnail
        const firstFile = group.files[0];
        const thumbnailUrl = firstFile.thumbnail_path 
            ? `/library/thumbnail/${firstFile.id}` 
            : `/library/file/${firstFile.id}/view`;
        
        card.innerHTML = `
            <div class="card library-item h-100">
                <div class="position-relative">
                    <span class="badge bg-primary file-type-badge">${group.files.length} files</span>
                    <img src="${thumbnailUrl}" class="card-img-top library-thumbnail" 
                         style="height: 200px; object-fit: cover;"
                         alt="${this.escapeHtml(group.post_title)}">
                </div>
                <div class="card-body p-3">
                    <h6 class="card-title text-truncate mb-2" title="${this.escapeHtml(group.post_title)}">
                        ${this.escapeHtml(group.post_title)}
                    </h6>
                    <p class="card-text small text-muted mb-3">
                        <i class="bi bi-person"></i> ${group.service}/${group.user_id}<br>
                        <i class="bi bi-files"></i> ${group.files.length} files
                    </p>
                    <div class="d-grid gap-2">
                        <a href="/view_gallery/${group.post_id}" class="btn btn-primary btn-sm">
                            <i class="bi bi-images"></i> Gallery
                        </a>
                        <button class="btn btn-outline-secondary btn-sm view-post-btn">
                            <i class="bi bi-eye"></i> Ko'rish
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add click event to view button
        const viewBtn = card.querySelector('.view-post-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('View button clicked for post:', group.post_title);
                this.showPostFiles(group);
            });
        }
        
        return card;
    }
    
    showPostFiles(group) {
        console.log('Showing post files:', group);
        
        // Always use the ZIP check version
        this.showPostFilesWithZipCheck(group);
    }
    
    createPostFilesModal() {
        const modalHTML = `
            <div class="modal fade" id="post-files-modal" tabindex="-1" aria-labelledby="post-files-modal-title" aria-hidden="true">
                <div class="modal-dialog modal-xl modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="post-files-modal-title">Post Files</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="post-files-modal-body">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Yopish</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        return document.getElementById('post-files-modal');
    }
    
    createFileCard(file) {
        const card = document.createElement('div');
        card.className = 'file-card';
        card.setAttribute('data-file-id', file.id);
        card.setAttribute('data-file-type', file.file_type);
        card.setAttribute('data-name', file.filename);
        card.setAttribute('data-artist', file.user_id || '');
        card.setAttribute('data-date', file.downloaded_at);
        card.setAttribute('data-size', file.file_size || 0);
        
        const thumbnailUrl = file.thumbnail_path 
            ? `/library/thumbnail/${file.id}` 
            : `/library/file/${file.id}/view`;
        
        card.innerHTML = `
            <div class="card library-item">
                <span class="badge bg-primary file-type-badge">${file.file_type || 'unknown'}</span>
                <img src="${thumbnailUrl}" class="card-img-top library-thumbnail lazy" 
                     data-src="${thumbnailUrl}" alt="${file.filename}">
                <div class="card-body">
                    <h6 class="card-title text-truncate" title="${file.filename}">${file.filename}</h6>
                    <p class="card-text small text-muted">
                        ${file.post_title || 'Unknown Post'}<br>
                        ${this.formatFileSize(file.file_size)}
                    </p>
                    <div class="btn-group btn-group-sm w-100">
                        <a href="/library/file/${file.id}/view" class="btn btn-outline-primary" target="_blank">
                            <i class="bi bi-eye"></i>
                        </a>
                        <a href="/library/file/${file.id}/download" class="btn btn-outline-success">
                            <i class="bi bi-download"></i>
                        </a>
                        <button class="btn btn-outline-danger delete-file-btn" 
                                data-file-id="${file.id}" data-file-name="${file.filename}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        return card;
    }
    
    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    attachEventListeners() {
        // Scan library button
        const scanBtn = document.getElementById('scanLibraryBtn');
        if (scanBtn) {
            scanBtn.addEventListener('click', () => {
                this.loadFiles();
            });
        }

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.currentTarget.getAttribute('data-filter');
                this.applyFilter(filter);
            });
        });

        // Sort dropdown
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.applySort(e.target.value);
            });
        }

        // Delete buttons (event delegation)
        document.addEventListener('click', (e) => {
            if (e.target.closest('.delete-file-btn')) {
                const btn = e.target.closest('.delete-file-btn');
                const fileId = btn.getAttribute('data-file-id');
                const fileName = btn.getAttribute('data-file-name');
                this.showDeleteConfirmation(fileId, fileName);
            }
        });

        // Search input
        const searchInput = document.getElementById('library-search');
        if (searchInput) {
            searchInput.addEventListener('input', Utils.debounce(() => {
                this.performSearch();
            }, 500));
        }
    }

    initLazyLoading() {
        // Intersection Observer for lazy loading images
        const options = {
            root: null,
            rootMargin: '50px',
            threshold: 0.01
        };

        this.lazyLoadObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.getAttribute('data-src');
                    
                    if (src) {
                        img.src = src;
                        img.removeAttribute('data-src');
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                }
            });
        }, options);

        // Observe all lazy images
        document.querySelectorAll('img.lazy').forEach(img => {
            this.lazyLoadObserver.observe(img);
        });
    }

    applyFilter(filter) {
        this.currentFilter = filter;
        this.saveFilterPreferences();

        // Update active button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-filter') === filter) {
                btn.classList.add('active');
            }
        });

        // Filter file cards
        const cards = document.querySelectorAll('.file-card');
        cards.forEach(card => {
            const fileType = card.getAttribute('data-file-type');
            
            if (filter === 'all') {
                card.style.display = '';
            } else if (fileType === filter) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });

        this.updateFileCount();
    }

    applySort(sortType) {
        this.currentSort = sortType;
        this.saveFilterPreferences();

        const container = document.querySelector('.file-grid');
        if (!container) return;

        const cards = Array.from(container.querySelectorAll('.file-card'));
        
        cards.sort((a, b) => {
            switch (sortType) {
                case 'date_desc':
                    return new Date(b.getAttribute('data-date')) - new Date(a.getAttribute('data-date'));
                case 'date_asc':
                    return new Date(a.getAttribute('data-date')) - new Date(b.getAttribute('data-date'));
                case 'name_asc':
                    return a.getAttribute('data-name').localeCompare(b.getAttribute('data-name'));
                case 'name_desc':
                    return b.getAttribute('data-name').localeCompare(a.getAttribute('data-name'));
                case 'size_desc':
                    return parseInt(b.getAttribute('data-size')) - parseInt(a.getAttribute('data-size'));
                case 'size_asc':
                    return parseInt(a.getAttribute('data-size')) - parseInt(b.getAttribute('data-size'));
                default:
                    return 0;
            }
        });

        // Re-append sorted cards
        cards.forEach(card => container.appendChild(card));
    }

    performSearch() {
        const searchInput = document.getElementById('library-search');
        const query = searchInput.value.toLowerCase().trim();

        const cards = document.querySelectorAll('.file-card');
        cards.forEach(card => {
            const fileName = card.getAttribute('data-name').toLowerCase();
            const artistName = card.getAttribute('data-artist').toLowerCase();
            
            if (fileName.includes(query) || artistName.includes(query)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });

        this.updateFileCount();
    }

    updateFileCount() {
        const visibleCards = document.querySelectorAll('.file-card:not([style*="display: none"])');
        const countElement = document.getElementById('file-count');
        
        if (countElement) {
            countElement.textContent = `${visibleCards.length} fayl`;
        }
    }

    showDeleteConfirmation(fileId, fileName) {
        const modal = document.getElementById('delete-modal');
        if (!modal) {
            // Create modal if it doesn't exist
            this.createDeleteModal();
        }

        const modalTitle = document.getElementById('delete-modal-title');
        const modalBody = document.getElementById('delete-modal-body');
        const confirmBtn = document.getElementById('confirm-delete-btn');

        if (modalTitle) {
            modalTitle.textContent = 'Faylni o\'chirish';
        }

        if (modalBody) {
            modalBody.innerHTML = `
                <p>Ushbu faylni o'chirmoqchimisiz?</p>
                <p class="text-muted"><strong>${this.escapeHtml(fileName)}</strong></p>
                <p class="text-danger"><small>Bu amalni qaytarib bo'lmaydi!</small></p>
            `;
        }

        if (confirmBtn) {
            // Remove old listeners
            const newBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
            
            // Add new listener
            newBtn.addEventListener('click', () => {
                this.deleteFile(fileId);
            });
        }

        // Show modal
        const bsModal = new bootstrap.Modal(document.getElementById('delete-modal'));
        bsModal.show();
    }

    createDeleteModal() {
        const modalHTML = `
            <div class="modal fade" id="delete-modal" tabindex="-1" aria-labelledby="delete-modal-title" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="delete-modal-title">Faylni o'chirish</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="delete-modal-body">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Bekor qilish</button>
                            <button type="button" class="btn btn-danger" id="confirm-delete-btn">O'chirish</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    async deleteFile(fileId) {
        const confirmBtn = document.getElementById('confirm-delete-btn');
        Utils.showLoading(confirmBtn);

        try {
            const response = await Ajax.delete(`/api/library/${fileId}`);
            
            if (response.success) {
                Toast.success('Fayl o\'chirildi');
                
                // Remove card from DOM
                const card = document.querySelector(`.file-card[data-file-id="${fileId}"]`);
                if (card) {
                    card.remove();
                }
                
                this.updateFileCount();
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('delete-modal'));
                if (modal) modal.hide();
            } else {
                Toast.error(response.error || 'Faylni o\'chirishda xatolik');
            }
        } catch (error) {
            console.error('Delete file error:', error);
            Toast.error('Serverga ulanishda xatolik');
        } finally {
            Utils.hideLoading(confirmBtn);
        }
    }

    showFilePreview(filePath, fileName, fileType) {
        const modal = document.getElementById('preview-modal');
        if (!modal) {
            this.createPreviewModal();
        }

        const modalTitle = document.getElementById('preview-modal-title');
        const modalBody = document.getElementById('preview-modal-body');

        if (modalTitle) {
            modalTitle.textContent = fileName;
        }

        if (modalBody) {
            modalBody.innerHTML = this.generatePreviewContent(filePath, fileType);
        }

        // Show modal
        const bsModal = new bootstrap.Modal(document.getElementById('preview-modal'));
        bsModal.show();
    }

    createPreviewModal() {
        const modalHTML = `
            <div class="modal fade" id="preview-modal" tabindex="-1" aria-labelledby="preview-modal-title" aria-hidden="true">
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="preview-modal-title">Fayl ko'rinishi</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body text-center" id="preview-modal-body">
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    generatePreviewContent(filePath, fileType) {
        const escapedPath = this.escapeHtml(filePath);
        
        switch (fileType) {
            case 'image':
                return `<img src="${escapedPath}" class="img-fluid" alt="Preview" style="max-height: 70vh;">`;
            
            case 'video':
                return `
                    <video controls class="w-100" style="max-height: 70vh;">
                        <source src="${escapedPath}" type="video/mp4">
                        Brauzeringiz video ko'rsatishni qo'llab-quvvatlamaydi.
                    </video>
                `;
            
            case 'audio':
                return `
                    <audio controls class="w-100">
                        <source src="${escapedPath}" type="audio/mpeg">
                        Brauzeringiz audio ko'rsatishni qo'llab-quvvatlamaydi.
                    </audio>
                `;
            
            default:
                return `
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle me-2"></i>
                        Ushbu fayl turini ko'rib bo'lmaydi
                    </div>
                    <a href="${escapedPath}" class="btn btn-primary" download>
                        <i class="bi bi-download me-2"></i>Yuklab olish
                    </a>
                `;
        }
    }

    saveFilterPreferences() {
        localStorage.setItem('libraryFilter', this.currentFilter);
        localStorage.setItem('librarySort', this.currentSort);
    }

    loadFilterPreferences() {
        const savedFilter = localStorage.getItem('libraryFilter');
        const savedSort = localStorage.getItem('librarySort');

        if (savedFilter) {
            this.applyFilter(savedFilter);
        }

        if (savedSort) {
            const sortSelect = document.getElementById('sort-select');
            if (sortSelect) {
                sortSelect.value = savedSort;
                this.applySort(savedSort);
            }
        }
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
    
    // ===== Gallery Viewer =====
    
    openGallery(files, currentIndex = 0) {
        this.galleryFiles = files;
        this.currentGalleryIndex = currentIndex;
        
        const modal = new bootstrap.Modal(document.getElementById('galleryModal'));
        modal.show();
        
        this.showMedia(currentIndex);
        this.renderThumbnailStrip();
        this.attachGalleryEventListeners();
    }
    
    showMedia(index) {
        if (index < 0 || index >= this.galleryFiles.length) return;
        
        this.currentGalleryIndex = index;
        const file = this.galleryFiles[index];
        
        // Update counter and filename
        document.getElementById('galleryCounter').textContent = `${index + 1} / ${this.galleryFiles.length}`;
        document.getElementById('galleryFileName').textContent = file.filename;
        
        // Hide all viewers
        document.getElementById('galleryImage').style.display = 'none';
        document.getElementById('galleryVideo').style.display = 'none';
        document.getElementById('galleryOther').style.display = 'none';
        
        // Show appropriate viewer
        if (file.file_type === 'image') {
            const img = document.getElementById('galleryImage');
            img.src = `/library/file/${file.id}`;
            img.style.display = 'block';
            img.classList.remove('zoomed');
        } else if (file.file_type === 'video') {
            const video = document.getElementById('galleryVideo');
            const source = video.querySelector('source');
            source.src = `/library/file/${file.id}`;
            video.load();
            video.style.display = 'block';
        } else {
            const other = document.getElementById('galleryOther');
            const link = document.getElementById('downloadFileLink');
            link.href = `/library/file/${file.id}`;
            link.download = file.filename;
            other.style.display = 'block';
        }
        
        // Update active thumbnail
        this.updateActiveThumbnail(index);
        
        // Preload next/prev
        this.preloadMedia(index - 1);
        this.preloadMedia(index + 1);
    }
    
    nextMedia() {
        if (this.currentGalleryIndex < this.galleryFiles.length - 1) {
            this.showMedia(this.currentGalleryIndex + 1);
        }
    }
    
    prevMedia() {
        if (this.currentGalleryIndex > 0) {
            this.showMedia(this.currentGalleryIndex - 1);
        }
    }
    
    closeGallery() {
        const modalEl = document.getElementById('galleryModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
        
        // Stop video if playing
        const video = document.getElementById('galleryVideo');
        video.pause();
    }
    
    renderThumbnailStrip() {
        const strip = document.getElementById('thumbnailStrip');
        strip.innerHTML = '';
        
        this.galleryFiles.forEach((file, index) => {
            const thumb = document.createElement('img');
            
            if (file.file_type === 'image') {
                thumb.src = file.thumbnail_path || `/library/file/${file.id}`;
            } else if (file.file_type === 'video') {
                thumb.src = file.thumbnail_path || 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2280%22 height=%2280%22%3E%3Crect width=%2280%22 height=%2280%22 fill=%22%23333%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2230%22 fill=%22%23fff%22%3E▶%3C/text%3E%3C/svg%3E';
            } else {
                thumb.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2280%22 height=%2280%22%3E%3Crect width=%2280%22 height=%2280%22 fill=%22%23555%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2220%22 fill=%22%23fff%22%3E📄%3C/text%3E%3C/svg%3E';
            }
            
            thumb.alt = file.filename;
            thumb.dataset.index = index;
            thumb.loading = 'lazy';
            
            if (index === this.currentGalleryIndex) {
                thumb.classList.add('active');
            }
            
            thumb.addEventListener('click', () => this.showMedia(index));
            strip.appendChild(thumb);
        });
    }
    
    updateActiveThumbnail(index) {
        const thumbs = document.querySelectorAll('#thumbnailStrip img');
        thumbs.forEach((thumb, i) => {
            if (i === index) {
                thumb.classList.add('active');
                thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            } else {
                thumb.classList.remove('active');
            }
        });
    }
    
    preloadMedia(index) {
        if (index < 0 || index >= this.galleryFiles.length) return;
        
        const file = this.galleryFiles[index];
        if (file.file_type === 'image') {
            const img = new Image();
            img.src = `/library/file/${file.id}`;
        }
    }
    
    attachGalleryEventListeners() {
        // Remove old listeners
        const prevBtn = document.getElementById('prevMediaBtn');
        const nextBtn = document.getElementById('nextMediaBtn');
        const closeBtn = document.getElementById('closeGalleryBtn');
        const galleryImage = document.getElementById('galleryImage');
        
        // Clone to remove old listeners
        const newPrevBtn = prevBtn.cloneNode(true);
        const newNextBtn = nextBtn.cloneNode(true);
        const newCloseBtn = closeBtn.cloneNode(true);
        
        prevBtn.replaceWith(newPrevBtn);
        nextBtn.replaceWith(newNextBtn);
        closeBtn.replaceWith(newCloseBtn);
        
        // Add new listeners
        newPrevBtn.addEventListener('click', () => this.prevMedia());
        newNextBtn.addEventListener('click', () => this.nextMedia());
        newCloseBtn.addEventListener('click', () => this.closeGallery());
        
        // Image zoom
        galleryImage.addEventListener('click', (e) => {
            e.target.classList.toggle('zoomed');
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', this.handleGalleryKeyboard.bind(this));
        
        // Touch swipe (basic)
        let touchStartX = 0;
        const galleryBody = document.getElementById('galleryBody');
        
        galleryBody.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
        });
        
        galleryBody.addEventListener('touchend', (e) => {
            const touchEndX = e.changedTouches[0].clientX;
            const diff = touchStartX - touchEndX;
            
            if (Math.abs(diff) > 50) {
                if (diff > 0) {
                    this.nextMedia();
                } else {
                    this.prevMedia();
                }
            }
        });
    }
    
    handleGalleryKeyboard(e) {
        const modalEl = document.getElementById('galleryModal');
        if (!modalEl.classList.contains('show')) return;
        
        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.prevMedia();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.nextMedia();
                break;
            case 'Escape':
                e.preventDefault();
                this.closeGallery();
                break;
        }
    }
    
    // ===== Media Type Filter =====
    
    filterMediaByType(files, type) {
        if (type === 'all') return files;
        return files.filter(f => f.file_type === type);
    }
    
    showPostMediaModal(postId) {
        // Get all files for this post
        const postFiles = this.files.filter(f => f.post_id === postId);
        
        if (postFiles.length === 0) {
            Toast.warning('Bu postda fayllar topilmadi');
            return;
        }
        
        // Show modal with media type filter if 10+ files
        const modal = document.getElementById('fileDetailsModal');
        const filterDiv = document.getElementById('mediaTypeFilter');
        const gridDiv = document.getElementById('filePreviewGrid');
        
        if (postFiles.length >= 10) {
            filterDiv.style.display = 'block';
            this.setupMediaTypeFilter(postFiles);
        } else {
            filterDiv.style.display = 'none';
        }
        
        // Render files
        this.renderPostMediaGrid(postFiles);
        
        // Update post info
        const firstFile = postFiles[0];
        document.getElementById('detailPostTitle').textContent = firstFile.post_title || 'Unknown';
        document.getElementById('detailTotalFiles').textContent = postFiles.length;
        document.getElementById('detailService').textContent = firstFile.service || '-';
        document.getElementById('detailArtist').textContent = firstFile.user_id || '-';
        document.getElementById('detailPost').textContent = firstFile.post_id || '-';
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
    
    setupMediaTypeFilter(files) {
        // Count by type
        const counts = {
            all: files.length,
            image: files.filter(f => f.file_type === 'image').length,
            video: files.filter(f => f.file_type === 'video').length,
            archive: files.filter(f => f.file_type === 'archive').length,
            audio: files.filter(f => f.file_type === 'audio').length
        };
        
        // Update badges
        document.getElementById('countAll').textContent = counts.all;
        document.getElementById('countImages').textContent = counts.image;
        document.getElementById('countVideos').textContent = counts.video;
        document.getElementById('countArchives').textContent = counts.archive;
        document.getElementById('countAudio').textContent = counts.audio;
        
        // Attach filter handlers
        const filterBtns = document.querySelectorAll('#mediaTypeFilter button');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const filterType = btn.dataset.filter;
                
                // Update active state
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Filter and render
                const filtered = this.filterMediaByType(files, filterType);
                this.renderPostMediaGrid(filtered);
            });
        });
    }
    
    renderPostMediaGrid(files) {
        const grid = document.getElementById('filePreviewGrid');
        grid.innerHTML = '';
        
        files.forEach((file, index) => {
            const col = document.createElement('div');
            col.className = 'col-6 col-md-4 col-lg-3';
            
            const item = document.createElement('div');
            item.className = 'file-preview-item';
            item.addEventListener('click', () => {
                // Close details modal
                const detailsModal = bootstrap.Modal.getInstance(document.getElementById('fileDetailsModal'));
                if (detailsModal) detailsModal.hide();
                
                // Open gallery
                setTimeout(() => {
                    this.openGallery(files, index);
                }, 300);
            });
            
            let content = '';
            if (file.file_type === 'image') {
                content = `<img src="/library/file/${file.id}" alt="${this.escapeHtml(file.filename)}" loading="lazy">`;
            } else if (file.file_type === 'video') {
                content = `<img src="${file.thumbnail_path || 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22150%22 height=%22150%22%3E%3Crect width=%22150%22 height=%22150%22 fill=%22%23333%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2250%22 fill=%22%23fff%22%3E▶%3C/text%3E%3C/svg%3E'}" alt="${this.escapeHtml(file.filename)}">`;
            } else {
                content = `<div class="bg-secondary d-flex align-items-center justify-content-center" style="height: 150px;"><i class="bi bi-file-earmark display-4 text-white"></i></div>`;
            }
            
            item.innerHTML = `
                ${content}
                <div class="file-type-overlay">
                    <i class="bi bi-${this.getFileTypeIcon(file.file_type)}"></i>
                </div>
            `;
            
            col.appendChild(item);
            grid.appendChild(col);
        });
    }
    
    getFileTypeIcon(type) {
        const icons = {
            'image': 'image',
            'video': 'camera-video',
            'archive': 'file-zip',
            'audio': 'music-note',
            'other': 'file-earmark'
        };
        return icons[type] || icons['other'];
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('libraryContainer')) {
        window.libraryManager = new LibraryManager();
    }
});
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on library page
    const libraryContainer = document.getElementById('libraryContainer');
    if (libraryContainer) {
        console.log('Initializing Library Manager...');
        window.libraryManager = new LibraryManager();
    }
});


// Override showPostFiles to fetch ZIP files from API
LibraryManager.prototype.showPostFilesWithZipCheck = LibraryManager.prototype.showPostFiles;
LibraryManager.prototype.showPostFiles = async function(group) {
    console.log('Showing post files with ZIP check:', group);
    
    // Create modal
    const modal = document.getElementById('post-files-modal') || this.createPostFilesModal();
    const modalTitle = document.getElementById('post-files-modal-title');
    const modalBody = document.getElementById('post-files-modal-body');
    
    if (modalTitle) {
        modalTitle.textContent = group.post_title;
    }
    
    if (modalBody) {
        modalBody.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3 text-muted">Checking for ZIP files...</p>
            </div>
        `;
    }
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Get service, user_id, post_id from first file
    const firstFile = group.files[0];
    if (!firstFile || !firstFile.service || !firstFile.user_id || !firstFile.post_id) {
        // No API info, just show existing files
        this.renderFilesInModal(group.files, modalBody);
        return;
    }
    
    try {
        // Fetch ZIP files from our backend (which calls Kemono API)
        const response = await fetch(`/library/post/${firstFile.service}/${firstFile.user_id}/${firstFile.post_id}/zip-files`);
        
        if (!response.ok) {
            throw new Error('API request failed');
        }
        
        const data = await response.json();
        
        console.log('ZIP files response:', data);
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to fetch ZIP files');
        }
        
        const zipFiles = data.zip_files || [];
        console.log('ZIP files found:', zipFiles.length, zipFiles);
        
        // Combine existing files with ZIP files from API
        const allFiles = [...group.files];
        
        // Add ZIP files that are not already in the list
        zipFiles.forEach(zipFile => {
            const zipName = zipFile.name;
            const alreadyExists = allFiles.some(f => f.filename === zipName);
            
            if (!alreadyExists) {
                console.log('Adding virtual ZIP file:', zipName);
                // Add as virtual file
                allFiles.push({
                    id: null,
                    filename: zipName,
                    file_type: 'archive',
                    file_size: 0,
                    original_url: zipFile.url,
                    is_virtual: true
                });
            }
        });
        
        console.log('Total files to display:', allFiles.length);
        
        // Render all files
        this.renderFilesInModal(allFiles, modalBody);
        
    } catch (error) {
        console.error('Error fetching ZIP files from API:', error);
        // Just show existing files on error
        this.renderFilesInModal(group.files, modalBody);
    }
};

LibraryManager.prototype.renderFilesInModal = function(files, modalBody) {
    if (!modalBody) return;
    
    modalBody.innerHTML = `
        <div class="row g-3">
            ${files.map(file => {
                const isImage = file.file_type === 'image';
                const isVideo = file.file_type === 'video';
                const isArchive = file.file_type === 'archive';
                const isVirtual = file.is_virtual || false;
                
                let mediaPreview = '';
                if (isImage) {
                    mediaPreview = `<img src="/library/file/${file.id}/view" 
                         class="card-img-top" 
                         style="height: 150px; object-fit: cover;"
                         alt="${this.escapeHtml(file.filename)}">`;
                } else if (isVideo) {
                    mediaPreview = `<video class="card-img-top" style="height: 150px; object-fit: cover;">
                        <source src="/library/file/${file.id}/view" type="video/mp4">
                    </video>`;
                } else if (isArchive) {
                    mediaPreview = `<div class="card-img-top bg-warning d-flex align-items-center justify-content-center" style="height: 150px;">
                        <i class="bi bi-file-zip display-4 text-white"></i>
                    </div>`;
                } else {
                    mediaPreview = `<div class="card-img-top bg-secondary d-flex align-items-center justify-content-center" style="height: 150px;">
                        <i class="bi bi-file-earmark display-4 text-white"></i>
                    </div>`;
                }
                
                // For ZIP files with original_url, show download from Kemono button
                let actionButtons = '';
                if (isArchive && file.original_url) {
                    actionButtons = `
                        <div class="btn-group btn-group-sm w-100 mt-2">
                            <a href="${this.escapeHtml(file.original_url)}" 
                               class="btn btn-warning" target="_blank">
                                <i class="bi bi-download"></i> Download from Kemono
                            </a>
                            ${!isVirtual ? `<button class="btn btn-outline-danger delete-file-btn" 
                                    data-file-id="${file.id}" 
                                    data-file-name="${this.escapeHtml(file.filename)}">
                                <i class="bi bi-trash"></i>
                            </button>` : ''}
                        </div>
                    `;
                } else if (!isVirtual) {
                    actionButtons = `
                        <div class="btn-group btn-group-sm w-100 mt-2">
                            <a href="/library/file/${file.id}/view" 
                               class="btn btn-outline-primary" target="_blank">
                                <i class="bi bi-eye"></i>
                            </a>
                            <a href="/library/file/${file.id}/download" 
                               class="btn btn-outline-success">
                                <i class="bi bi-download"></i>
                            </a>
                            <button class="btn btn-outline-danger delete-file-btn" 
                                    data-file-id="${file.id}" 
                                    data-file-name="${this.escapeHtml(file.filename)}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    `;
                }
                
                return `
                <div class="col-md-4 col-sm-6">
                    <div class="card h-100">
                        ${mediaPreview}
                        <div class="card-body p-2">
                            <p class="card-text small text-truncate mb-1" title="${this.escapeHtml(file.filename)}">
                                ${this.escapeHtml(file.filename)}
                            </p>
                            <small class="text-muted">${this.formatFileSize(file.file_size)}</small>
                            ${actionButtons}
                        </div>
                    </div>
                </div>
                `;
            }).join('')}
        </div>
    `;
};


// ZIP Files Tab Handler
document.addEventListener('DOMContentLoaded', () => {
    const zipsTab = document.getElementById('zips-tab');
    if (zipsTab) {
        zipsTab.addEventListener('shown.bs.tab', async () => {
            await loadZipFiles();
        });
    }
});

async function loadZipFiles() {
    const container = document.getElementById('zipFilesContainer');
    if (!container) return;
    
    // Show loading
    container.innerHTML = `
        <div class="text-center text-muted py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Yuklanmoqda...</span>
            </div>
            <p class="mt-3">ZIP fayllar yuklanmoqda...</p>
        </div>
    `;
    
    try {
        // Get all files from library
        const response = await Ajax.get('/library/files');
        
        if (!response.success || !response.files) {
            container.innerHTML = `
                <div class="alert alert-danger text-center">
                    <i class="bi bi-exclamation-triangle"></i> Fayllarni yuklashda xatolik
                </div>
            `;
            return;
        }
        
        // Group files by post
        const postGroups = {};
        response.files.forEach(file => {
            const postKey = `${file.service}/${file.user_id}/${file.post_id}`;
            if (!postGroups[postKey]) {
                postGroups[postKey] = {
                    service: file.service,
                    user_id: file.user_id,
                    post_id: file.post_id,
                    post_title: file.post_title || 'Unknown Post',
                    thumbnail: file.thumbnail_path
                };
            }
        });
        
        // Load ZIP files for each post
        const posts = Object.values(postGroups);
        
        if (posts.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="bi bi-inbox display-1"></i>
                    <p class="mt-3">Hech qanday post topilmadi</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '<div class="library-grid" id="zipGrid"></div>';
        const zipGrid = document.getElementById('zipGrid');
        
        let totalZips = 0;
        
        for (const post of posts) {
            try {
                const zipResponse = await Ajax.get(`/library/post/${post.service}/${post.user_id}/${post.post_id}/zip-files`);
                
                if (zipResponse.success && zipResponse.zip_files && zipResponse.zip_files.length > 0) {
                    totalZips += zipResponse.zip_files.length;
                    
                    // Update post info with API data
                    const postInfo = {
                        service: post.service,
                        user_id: post.user_id,
                        post_id: post.post_id,
                        post_title: zipResponse.post_title || post.post_title,
                        thumbnail: zipResponse.thumbnail || post.thumbnail
                    };
                    
                    // Render each ZIP file
                    zipResponse.zip_files.forEach(zipFile => {
                        const zipCard = createZipCard(zipFile, postInfo);
                        zipGrid.appendChild(zipCard);
                    });
                }
            } catch (error) {
                console.error(`Error loading ZIP files for post ${post.post_id}:`, error);
            }
        }
        
        if (totalZips === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="bi bi-file-zip display-1"></i>
                    <p class="mt-3">Hech qanday ZIP fayl topilmadi</p>
                </div>
            `;
        } else {
            Toast.success(`${totalZips} ta ZIP fayl topildi`);
        }
        
    } catch (error) {
        console.error('Load ZIP files error:', error);
        container.innerHTML = `
            <div class="alert alert-danger text-center">
                <i class="bi bi-exclamation-triangle"></i> Serverga ulanishda xatolik
            </div>
        `;
    }
}

function createZipCard(zipFile, post) {
    const card = document.createElement('div');
    card.className = 'library-item';
    
    const zipName = zipFile.name || 'Unknown.zip';
    const zipUrl = zipFile.url;
    
    // Get thumbnail - use post thumbnail from API
    let thumbnailHtml;
    if (post.thumbnail) {
        thumbnailHtml = `<img src="${post.thumbnail}" class="library-thumbnail" alt="${zipName}" loading="lazy" onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\'library-thumbnail bg-secondary d-flex align-items-center justify-content-center\\'><i class=\\'bi bi-file-zip display-4 text-white\\'></i></div>';">`;
    } else {
        thumbnailHtml = `
            <div class="library-thumbnail bg-secondary d-flex align-items-center justify-content-center">
                <i class="bi bi-file-zip display-4 text-white"></i>
            </div>
        `;
    }
    
    card.innerHTML = `
        <div class="card h-100">
            <div class="position-relative">
                <span class="badge bg-warning file-type-badge">
                    <i class="bi bi-file-zip"></i> ZIP
                </span>
                ${thumbnailHtml}
            </div>
            <div class="card-body p-2">
                <h6 class="card-title text-truncate mb-1" style="font-size: 0.85rem;" title="${zipName}">
                    ${zipName}
                </h6>
                <small class="text-muted d-block text-truncate" style="font-size: 0.75rem;">
                    <i class="bi bi-folder"></i> ${post.post_title}
                </small>
                <small class="text-muted d-block text-truncate" style="font-size: 0.7rem;">
                    <i class="bi bi-person"></i> ${post.service}/${post.user_id}
                </small>
                <div class="mt-2">
                    <a href="${zipUrl}" class="btn btn-sm btn-primary w-100" download>
                        <i class="bi bi-download"></i> Download
                    </a>
                </div>
            </div>
        </div>
    `;
    
    return card;
}
