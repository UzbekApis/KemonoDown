// Search Page Logic
// Search form submission, results rendering, download handlers

class SearchManager {
    constructor() {
        this.currentResults = [];
        this.currentTab = 'artist'; // Track current tab
        this.postSelectorModalInstance = null; // Store modal instance
        this.selectedPosts = new Set(); // Track selected posts
        this.currentPage = 1; // Current page for post search
        this.currentQuery = ''; // Current search query
        this.postsPerPage = 50; // Posts per page (API returns 50)
        this.init();
    }

    init() {
        this.attachEventListeners();
        this.setupMultiSelect();
    }

    attachEventListeners() {
        // Artist search form
        const artistForm = document.getElementById('artistSearchForm');
        if (artistForm) {
            artistForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.performArtistSearch();
            });
        }

        // Post search form
        const postForm = document.getElementById('postSearchForm');
        if (postForm) {
            postForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.currentPage = 1; // Reset to page 1
                this.performPostSearch();
            });
        }

        // Tab change tracking
        const tabs = document.querySelectorAll('#searchTabs button[data-bs-toggle="tab"]');
        tabs.forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                this.currentTab = e.target.id.includes('artist') ? 'artist' : 'post';
            });
        });
        
        // Pagination buttons
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.loadPreviousPage());
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.loadNextPage());
        }
    }

    async performArtistSearch() {
        const query = document.getElementById('artistSearchInput').value.trim();

        if (!query) {
            Toast.warning('Iltimos, artist nomini kiriting');
            return;
        }

        const searchBtn = document.querySelector('#artistSearchForm button[type="submit"]');
        Utils.showLoading(searchBtn);

        this.showLoadingState('artistResults');

        try {
            const response = await Ajax.post('/search/artist', {
                query: query
            });

            if (response.success) {
                this.currentResults = response.results || [];
                this.renderArtistResults(this.currentResults);
                
                if (this.currentResults.length === 0) {
                    Toast.info('Hech narsa topilmadi');
                }
            } else {
                Toast.error(response.error || 'Qidiruvda xatolik');
                this.showErrorState('artistResults');
            }
        } catch (error) {
            console.error('Artist search error:', error);
            Toast.error('Serverga ulanishda xatolik');
            this.showErrorState('artistResults');
        } finally {
            Utils.hideLoading(searchBtn);
        }
    }

    async performPostSearch(page = null) {
        const query = document.getElementById('postSearchInput').value.trim();
        const service = document.getElementById('serviceFilter').value;

        if (!query) {
            Toast.warning('Iltimos, qidiruv so\'zini kiriting');
            return;
        }
        
        // Store query for pagination
        this.currentQuery = query;
        
        // Use provided page or current page
        if (page !== null) {
            this.currentPage = page;
        }
        
        // Calculate offset (API uses 50 step)
        const offset = (this.currentPage - 1) * this.postsPerPage;

        const searchBtn = document.querySelector('#postSearchForm button[type="submit"]');
        Utils.showLoading(searchBtn);

        this.showLoadingState('postResultsGrid');

        try {
            const response = await Ajax.post('/search/post', {
                query: query,
                service: service,
                limit: this.postsPerPage,
                offset: offset
            });

            if (response.success) {
                this.currentResults = response.results || [];
                console.log('Post search results:', this.currentResults);
                this.renderPostResults(this.currentResults);
                this.updatePaginationControls();
                
                if (this.currentResults.length === 0) {
                    if (this.currentPage === 1) {
                        Toast.info('Hech narsa topilmadi');
                    } else {
                        Toast.info('Boshqa natija yo\'q');
                    }
                } else {
                    Toast.success(`${this.currentResults.length} ta post topildi (Sahifa ${this.currentPage})`);
                }
            } else {
                Toast.error(response.error || 'Qidiruvda xatolik');
                this.showErrorState('postResultsGrid');
            }
        } catch (error) {
            console.error('Post search error:', error);
            Toast.error('Serverga ulanishda xatolik');
            this.showErrorState('postResultsGrid');
        } finally {
            Utils.hideLoading(searchBtn);
        }
    }
    
    loadNextPage() {
        this.currentPage++;
        this.performPostSearch(this.currentPage);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    loadPreviousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.performPostSearch(this.currentPage);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
    
    updatePaginationControls() {
        const paginationControls = document.getElementById('paginationControls');
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        const pageInfo = document.getElementById('pageInfo');
        
        if (paginationControls && this.currentResults.length > 0) {
            paginationControls.style.display = 'flex';
            
            // Update page info
            if (pageInfo) {
                pageInfo.textContent = `Page ${this.currentPage}`;
            }
            
            // Update prev button
            if (prevBtn) {
                prevBtn.disabled = this.currentPage === 1;
            }
            
            // Update next button (disable if less than 50 results)
            if (nextBtn) {
                nextBtn.disabled = this.currentResults.length < this.postsPerPage;
            }
        } else if (paginationControls) {
            paginationControls.style.display = 'none';
        }
    }

    showLoadingState(containerId) {
        const resultsContainer = document.getElementById(containerId);
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Yuklanmoqda...</span>
                    </div>
                    <p class="mt-3 text-muted">Qidirilmoqda...</p>
                </div>
            `;
        }
    }

    showErrorState(containerId) {
        const resultsContainer = document.getElementById(containerId);
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="alert alert-danger text-center" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Qidiruvda xatolik yuz berdi
                </div>
            `;
        }
    }

    renderArtistResults(results) {
        const resultsContainer = document.getElementById('artistResults');
        if (!resultsContainer) return;

        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="alert alert-info text-center" role="alert">
                    <i class="bi bi-info-circle-fill me-2"></i>
                    Hech narsa topilmadi
                </div>
            `;
            return;
        }

        let html = '<div class="row">';
        
        results.forEach(artist => {
            html += this.renderArtistCard(artist);
        });

        html += '</div>';
        resultsContainer.innerHTML = html;

        // Attach download handlers
        this.attachArtistDownloadHandlers();
    }

    renderPostResults(results) {
        const resultsGrid = document.getElementById('postResultsGrid');
        const placeholder = document.getElementById('postSearchPlaceholder');
        
        if (!resultsGrid) return;
        
        // Hide placeholder
        if (placeholder) placeholder.style.display = 'none';

        if (results.length === 0) {
            resultsGrid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info text-center" role="alert">
                        <i class="bi bi-info-circle-fill me-2"></i>
                        Hech narsa topilmadi
                    </div>
                </div>
            `;
            return;
        }

        let html = '';
        
        results.forEach(post => {
            html += this.renderPostCard(post);
        });

        resultsGrid.innerHTML = html;

        // Attach download handlers
        this.attachPostDownloadHandlers();
        
        // Attach checkbox handlers
        this.attachCheckboxHandlers();
    }

    renderArtistCard(artist) {
        const artistName = this.escapeHtml(artist.name || 'Unknown Artist');
        const artistId = artist.id || '';
        const service = artist.service || 'kemono';
        const indexed = artist.indexed || 0;
        const profileUrl = `https://kemono.cr/${service}/user/${artistId}`;
        const avatarUrl = `https://kemono.cr/icons/${service}/${artistId}`;
        const firstLetter = artistName.charAt(0).toUpperCase();

        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card search-result-card h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center mb-3">
                            <div class="position-relative me-3" style="width: 60px; height: 60px;">
                                <img src="${avatarUrl}" 
                                     alt="${artistName}" 
                                     class="artist-avatar" 
                                     style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover; position: absolute;"
                                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                <div class="bg-primary text-white d-flex align-items-center justify-content-center" 
                                     style="width: 60px; height: 60px; border-radius: 50%; font-size: 24px; font-weight: bold; display: none;">
                                    ${firstLetter}
                                </div>
                            </div>
                            <div class="flex-grow-1">
                                <h6 class="mb-1">${artistName}</h6>
                                <small class="text-muted">
                                    <span class="badge bg-primary">${service}</span>
                                </small>
                            </div>
                        </div>
                        <div class="mb-2">
                            <small class="text-muted d-block">
                                <i class="bi bi-file-post"></i> ${indexed} posts indexed
                            </small>
                            <small class="text-muted d-block">
                                <i class="bi bi-hash"></i> ID: ${artistId}
                            </small>
                        </div>
                        <div class="d-grid gap-2">
                            <button class="btn btn-sm btn-primary select-posts-btn" 
                                    data-service="${service}"
                                    data-user-id="${artistId}"
                                    data-name="${artistName}">
                                <i class="bi bi-check2-square"></i> Select Posts
                            </button>
                            <button class="btn btn-sm btn-outline-primary download-artist-btn" 
                                    data-url="${this.escapeHtml(profileUrl)}"
                                    data-name="${artistName}"
                                    data-service="${service}"
                                    data-user-id="${artistId}">
                                <i class="bi bi-download"></i> Download All
                            </button>
                            <a href="${this.escapeHtml(profileUrl)}" 
                               target="_blank" 
                               class="btn btn-sm btn-outline-secondary">
                                <i class="bi bi-box-arrow-up-right"></i> View Profile
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderPostCard(post) {
        const postTitle = this.escapeHtml(post.title || 'Untitled Post');
        const artistName = this.escapeHtml(post.user || 'Unknown');
        const service = post.service || 'kemono';
        const postId = post.id || '';
        const published = post.published ? new Date(post.published).toLocaleDateString() : 'Unknown';
        const postUrl = `https://kemono.cr/${service}/user/${artistName}/post/${postId}`;
        
        // Get thumbnail from file or first attachment
        let thumbnailUrl = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%25%22 height=%22200%22%3E%3Crect width=%22100%25%22 height=%22200%22 fill=%22%23ddd%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2224%22 fill=%22%23999%22%3ENo Image%3C/text%3E%3C/svg%3E';
        
        if (post.file && post.file.path) {
            thumbnailUrl = `https://kemono.cr/data${post.file.path}`;
        } else if (post.attachments && post.attachments.length > 0) {
            thumbnailUrl = `https://kemono.cr/data${post.attachments[0].path}`;
        }

        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card search-result-card h-100" data-post-url="${this.escapeHtml(postUrl)}">
                    <div class="position-relative">
                        <img src="${thumbnailUrl}" 
                             class="card-img-top" 
                             alt="${postTitle}" 
                             style="height: 200px; object-fit: cover;"
                             onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%25%22 height=%22200%22%3E%3Crect width=%22100%25%22 height=%22200%22 fill=%22%23ddd%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2224%22 fill=%22%23999%22%3ENo Image%3C/text%3E%3C/svg%3E'">
                        <input type="checkbox" class="form-check-input position-absolute top-0 end-0 m-2 post-checkbox" 
                               style="z-index: 10; width: 24px; height: 24px; cursor: pointer;">
                    </div>
                    <div class="card-body">
                        <h6 class="card-title text-truncate" title="${postTitle}">${postTitle}</h6>
                        <p class="card-text">
                            <small class="text-muted">
                                <i class="bi bi-person"></i> ${artistName}<br>
                                <i class="bi bi-calendar"></i> ${published}<br>
                                <span class="badge bg-primary">${service}</span>
                            </small>
                        </p>
                        <div class="d-grid gap-2">
                            <button class="btn btn-sm btn-primary download-post-btn" 
                                    data-url="${this.escapeHtml(postUrl)}"
                                    data-title="${postTitle}">
                                <i class="bi bi-download"></i> Download Post
                            </button>
                            <a href="${this.escapeHtml(postUrl)}" 
                               target="_blank" 
                               class="btn btn-sm btn-outline-secondary">
                                <i class="bi bi-box-arrow-up-right"></i> View Post
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    attachArtistDownloadHandlers() {
        // Select posts button
        document.querySelectorAll('.select-posts-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const service = e.currentTarget.getAttribute('data-service');
                const userId = e.currentTarget.getAttribute('data-user-id');
                const name = e.currentTarget.getAttribute('data-name');
                this.showPostSelector(service, userId, name);
            });
        });
        
        // Download all button
        document.querySelectorAll('.download-artist-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const url = e.currentTarget.getAttribute('data-url');
                const name = e.currentTarget.getAttribute('data-name');
                this.downloadArtist(url, name);
            });
        });
    }

    attachPostDownloadHandlers() {
        document.querySelectorAll('.download-post-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const url = e.currentTarget.getAttribute('data-url');
                const title = e.currentTarget.getAttribute('data-title');
                this.downloadPost(url, title);
            });
        });
    }

    async showPostSelector(service, userId, artistName) {
        try {
            // Show loading modal
            this.showPostSelectorModal(artistName, [], true);
            
            // Fetch artist posts
            const response = await Ajax.get(`/search/artist/${service}/${userId}`);
            
            if (response.success && response.results) {
                this.showPostSelectorModal(artistName, response.results, false, service, userId);
            } else {
                Toast.error('Postlarni yuklashda xatolik');
                this.closePostSelectorModal();
            }
        } catch (error) {
            console.error('Error loading posts:', error);
            Toast.error('Serverga ulanishda xatolik');
            this.closePostSelectorModal();
        }
    }

    showPostSelectorModal(artistName, posts, loading = false, service = '', userId = '') {
        // Create or get modal
        let modal = document.getElementById('postSelectorModal');
        if (!modal) {
            modal = this.createPostSelectorModal();
            document.body.appendChild(modal);
            // Create Bootstrap modal instance once
            this.postSelectorModalInstance = new bootstrap.Modal(modal);
        }

        const modalTitle = modal.querySelector('.modal-title');
        const modalBody = modal.querySelector('.modal-body');
        const downloadBtn = modal.querySelector('#downloadSelectedPosts');

        modalTitle.innerHTML = `<i class="bi bi-check2-square"></i> Select Posts - ${this.escapeHtml(artistName)}`;

        if (loading) {
            modalBody.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-3 text-muted">Loading posts...</p>
                </div>
            `;
            downloadBtn.disabled = true;
        } else {
            modalBody.innerHTML = this.renderPostsList(posts);
            downloadBtn.disabled = false;
            
            // Store service and userId for download
            downloadBtn.setAttribute('data-service', service);
            downloadBtn.setAttribute('data-user-id', userId);
            downloadBtn.setAttribute('data-artist-name', artistName);
            
            // Attach checkbox handlers
            this.attachPostCheckboxHandlers();
        }

        // Show modal using stored instance
        if (this.postSelectorModalInstance) {
            this.postSelectorModalInstance.show();
        }
    }

    createPostSelectorModal() {
        const modalHtml = `
            <div class="modal fade" id="postSelectorModal" tabindex="-1">
                <div class="modal-dialog modal-xl modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Select Posts</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" style="max-height: 60vh;">
                            <!-- Posts will be loaded here -->
                        </div>
                        <div class="modal-footer">
                            <div class="me-auto">
                                <button type="button" class="btn btn-sm btn-outline-primary" id="selectAllPosts">
                                    <i class="bi bi-check-all"></i> Select All
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-secondary" id="deselectAllPosts">
                                    <i class="bi bi-x-square"></i> Deselect All
                                </button>
                            </div>
                            <span class="text-muted me-3">
                                Selected: <strong id="selectedPostCount">0</strong>
                            </span>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="downloadSelectedPosts">
                                <i class="bi bi-download"></i> Download Selected
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const div = document.createElement('div');
        div.innerHTML = modalHtml;
        return div.firstElementChild;
    }

    renderPostsList(posts) {
        if (!posts || posts.length === 0) {
            return `
                <div class="alert alert-info text-center">
                    <i class="bi bi-info-circle"></i> No posts found
                </div>
            `;
        }

        let html = '<div class="row g-3">';
        
        posts.forEach(post => {
            const postTitle = this.escapeHtml(post.title || 'Untitled');
            const postId = post.id || '';
            const published = post.published ? new Date(post.published).toLocaleDateString() : 'Unknown';
            const attachmentCount = (post.attachments || []).length + (post.file ? 1 : 0);
            
            // Get thumbnail
            let thumbnailUrl = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%25%22 height=%22150%22%3E%3Crect width=%22100%25%22 height=%22150%22 fill=%22%23ddd%22/%3E%3C/svg%3E';
            if (post.file && post.file.path) {
                thumbnailUrl = `https://kemono.cr/data${post.file.path}`;
            } else if (post.attachments && post.attachments.length > 0 && post.attachments[0].path) {
                thumbnailUrl = `https://kemono.cr/data${post.attachments[0].path}`;
            }

            html += `
                <div class="col-md-4 col-lg-3">
                    <div class="card h-100 post-select-card">
                        <div class="position-relative">
                            <img src="${thumbnailUrl}" 
                                 class="card-img-top" 
                                 alt="${postTitle}"
                                 style="height: 150px; object-fit: cover;"
                                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%25%22 height=%22150%22%3E%3Crect width=%22100%25%22 height=%22150%22 fill=%22%23ddd%22/%3E%3C/svg%3E'">
                            <div class="position-absolute top-0 end-0 p-2">
                                <input type="checkbox" class="form-check-input post-checkbox" 
                                       data-post-id="${postId}" 
                                       style="width: 24px; height: 24px; cursor: pointer;">
                            </div>
                        </div>
                        <div class="card-body p-2">
                            <h6 class="card-title text-truncate mb-1" style="font-size: 0.85rem;" title="${postTitle}">
                                ${postTitle}
                            </h6>
                            <small class="text-muted d-block" style="font-size: 0.75rem;">
                                <i class="bi bi-calendar"></i> ${published}
                            </small>
                            <small class="text-muted d-block" style="font-size: 0.75rem;">
                                <i class="bi bi-paperclip"></i> ${attachmentCount} files
                            </small>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    attachPostCheckboxHandlers() {
        const modal = document.getElementById('postSelectorModal');
        if (!modal) return;

        const updateCount = () => {
            const checked = modal.querySelectorAll('.post-checkbox:checked').length;
            const countEl = modal.querySelector('#selectedPostCount');
            if (countEl) countEl.textContent = checked;
        };

        // Individual checkboxes - remove old listeners by cloning
        modal.querySelectorAll('.post-checkbox').forEach(cb => {
            // Clone to remove old event listeners
            const newCb = cb.cloneNode(true);
            cb.parentNode.replaceChild(newCb, cb);
            newCb.addEventListener('change', updateCount);
        });

        // Select all button
        const selectAllBtn = modal.querySelector('#selectAllPosts');
        if (selectAllBtn) {
            // Clone to remove old listeners
            const newBtn = selectAllBtn.cloneNode(true);
            selectAllBtn.parentNode.replaceChild(newBtn, selectAllBtn);
            newBtn.onclick = () => {
                modal.querySelectorAll('.post-checkbox').forEach(cb => cb.checked = true);
                updateCount();
            };
        }

        // Deselect all button
        const deselectAllBtn = modal.querySelector('#deselectAllPosts');
        if (deselectAllBtn) {
            // Clone to remove old listeners
            const newBtn = deselectAllBtn.cloneNode(true);
            deselectAllBtn.parentNode.replaceChild(newBtn, deselectAllBtn);
            newBtn.onclick = () => {
                modal.querySelectorAll('.post-checkbox').forEach(cb => cb.checked = false);
                updateCount();
            };
        }

        // Download selected button
        const downloadBtn = modal.querySelector('#downloadSelectedPosts');
        if (downloadBtn) {
            // Clone to remove old listeners
            const newBtn = downloadBtn.cloneNode(true);
            downloadBtn.parentNode.replaceChild(newBtn, downloadBtn);
            newBtn.onclick = () => {
                const service = newBtn.getAttribute('data-service');
                const userId = newBtn.getAttribute('data-user-id');
                const artistName = newBtn.getAttribute('data-artist-name');
                
                const selectedPosts = Array.from(modal.querySelectorAll('.post-checkbox:checked'))
                    .map(cb => cb.getAttribute('data-post-id'));
                
                if (selectedPosts.length === 0) {
                    Toast.warning('Iltimos, kamida bitta post tanlang');
                    return;
                }
                
                this.downloadArtistSelectedPosts(service, userId, selectedPosts, artistName);
            };
        }
    }

    async downloadArtistSelectedPosts(service, userId, postIds, artistName) {
        if (!postIds || postIds.length === 0) {
            Toast.error('Postlar tanlanmagan');
            return;
        }

        // Close modal
        if (this.postSelectorModalInstance) {
            this.postSelectorModalInstance.hide();
        }

        try {
            // Build URLs for all selected posts
            const urls = postIds.map(postId => 
                `https://kemono.cr/${service}/user/${userId}/post/${postId}`
            );
            
            // Get default file type filters
            const savedFilters = localStorage.getItem('fileTypeFilters');
            let fileTypes = ['all'];
            
            if (savedFilters) {
                try {
                    const parsed = JSON.parse(savedFilters);
                    if (parsed && parsed.length > 0) {
                        fileTypes = parsed;
                    }
                } catch (e) {
                    console.error('Error parsing file type filters:', e);
                }
            }

            // Start multi-download
            Toast.info(`${postIds.length} ta post yuklab olinmoqda...`);
            
            const response = await Ajax.post('/download/start-multi', {
                urls: urls,
                filters: fileTypes
            });

            if (response.success) {
                Toast.success(`${artistName} uchun ${response.count} ta yuklab olish boshlandi`);
                
                // Redirect to download page
                setTimeout(() => {
                    window.location.href = '/download';
                }, 1500);
            } else {
                Toast.error(response.error || 'Yuklab olishda xatolik');
            }
            
        } catch (error) {
            console.error('Download selected posts error:', error);
            Toast.error('Yuklab olishda xatolik');
        }
    }

    closePostSelectorModal() {
        if (this.postSelectorModalInstance) {
            this.postSelectorModalInstance.hide();
        }
    }

    async downloadArtist(url, name) {
        if (!url || url === '#') {
            Toast.error('URL mavjud emas');
            return;
        }

        if (!Utils.isValidKemonoUrl(url)) {
            Toast.error('Noto\'g\'ri Kemono URL');
            return;
        }

        // Confirm download
        if (!confirm(`${name} artistining barcha fayllarini yuklab olmoqchimisiz?`)) {
            return;
        }

        try {
            // Get default file type filters from localStorage or use all types
            const savedFilters = localStorage.getItem('fileTypeFilters');
            let fileTypes = ['image', 'video', 'archive', 'document'];
            
            if (savedFilters) {
                try {
                    fileTypes = JSON.parse(savedFilters);
                } catch (e) {
                    console.error('Error parsing file type filters:', e);
                }
            }

            const response = await Ajax.post('/download/start', {
                url: url,
                filters: fileTypes
            });

            if (response.success) {
                Toast.success(`${name} uchun yuklab olish boshlandi`);
                
                // Redirect to download page after a short delay
                setTimeout(() => {
                    window.location.href = '/download';
                }, 1500);
            } else {
                Toast.error(response.error || 'Yuklab olishni boshlashda xatolik');
            }
        } catch (error) {
            console.error('Download artist error:', error);
            Toast.error('Serverga ulanishda xatolik');
        }
    }

    async downloadPost(url, title) {
        if (!url || url === '#') {
            Toast.error('URL mavjud emas');
            return;
        }

        if (!Utils.isValidKemonoUrl(url)) {
            Toast.error('Noto\'g\'ri Kemono URL');
            return;
        }

        // Confirm download
        if (!confirm(`"${title}" postini yuklab olmoqchimisiz?`)) {
            return;
        }

        try {
            // Get default file type filters from localStorage or use all types
            const savedFilters = localStorage.getItem('fileTypeFilters');
            let fileTypes = ['image', 'video', 'archive', 'document'];
            
            if (savedFilters) {
                try {
                    fileTypes = JSON.parse(savedFilters);
                } catch (e) {
                    console.error('Error parsing file type filters:', e);
                }
            }

            const response = await Ajax.post('/download/start', {
                url: url,
                filters: fileTypes
            });

            if (response.success) {
                Toast.success(`"${title}" uchun yuklab olish boshlandi`);
                
                // Redirect to download page after a short delay
                setTimeout(() => {
                    window.location.href = '/download';
                }, 1500);
            } else {
                Toast.error(response.error || 'Yuklab olishni boshlashda xatolik');
            }
        } catch (error) {
            console.error('Download post error:', error);
            Toast.error('Serverga ulanishda xatolik');
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
    
    // ===== Multi-Select Functionality =====
    
    setupMultiSelect() {
        // Select All button
        const selectAllBtn = document.getElementById('selectAllBtn');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAllPosts());
        }
        
        // Deselect All button
        const deselectAllBtn = document.getElementById('deselectAllBtn');
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAllPosts());
        }
        
        // Download Selected button
        const downloadSelectedBtn = document.getElementById('downloadSelectedBtn');
        if (downloadSelectedBtn) {
            downloadSelectedBtn.addEventListener('click', () => this.downloadSelectedPosts());
        }
    }
    
    updateMultiSelectUI() {
        const toolbar = document.getElementById('multiSelectToolbar');
        const countBadge = document.getElementById('selectedCount');
        
        if (toolbar && countBadge) {
            const count = this.selectedPosts.size;
            countBadge.textContent = count;
            toolbar.style.display = count > 0 ? 'block' : 'none';
        }
    }
    
    selectAllPosts() {
        const checkboxes = document.querySelectorAll('.post-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            const url = checkbox.closest('[data-post-url]').dataset.postUrl;
            if (url) this.selectedPosts.add(url);
        });
        this.updateMultiSelectUI();
    }
    
    deselectAllPosts() {
        const checkboxes = document.querySelectorAll('.post-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.selectedPosts.clear();
        this.updateMultiSelectUI();
    }
    
    attachCheckboxHandlers() {
        const checkboxes = document.querySelectorAll('.post-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const card = e.target.closest('[data-post-url]');
                const url = card ? card.dataset.postUrl : null;
                
                if (url) {
                    if (e.target.checked) {
                        this.selectedPosts.add(url);
                    } else {
                        this.selectedPosts.delete(url);
                    }
                    this.updateMultiSelectUI();
                }
            });
        });
    }
    
    async downloadSelectedPosts() {
        if (this.selectedPosts.size === 0) {
            Toast.warning('Iltimos, kamida bitta post tanlang');
            return;
        }
        
        const urls = Array.from(this.selectedPosts);
        const downloadBtn = document.getElementById('downloadSelectedBtn');
        
        Utils.showLoading(downloadBtn);
        
        try {
            const response = await Ajax.post('/download/start-multi', {
                urls: urls,
                filters: ['all']
            });
            
            if (response.success) {
                Toast.success(`${response.count} ta yuklab olish boshlandi`);
                this.deselectAllPosts();
                
                // Redirect to download page
                setTimeout(() => {
                    window.location.href = '/download';
                }, 1500);
            } else {
                Toast.error(response.error || 'Yuklab olishni boshlashda xatolik');
            }
        } catch (error) {
            console.error('Download selected error:', error);
            Toast.error('Serverga ulanishda xatolik');
        } finally {
            Utils.hideLoading(downloadBtn);
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('artistSearchForm') || document.getElementById('postSearchForm')) {
        window.searchManager = new SearchManager();
    }
});
