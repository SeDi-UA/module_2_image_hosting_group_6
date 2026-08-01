//images.js
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', function (event) {
        if (event.key === 'F5' || event.key === 'Escape') {
            event.preventDefault();
            window.location.href = '/upload';
        }
    });

    const fileListWrapper = document.getElementById('file-list-wrapper');
    const uploadRedirectButton = document.getElementById('upload-tab-btn');

    let currentPage = 1;

    const updateTabStyles = () => {
        const uploadTab = document.getElementById('upload-tab-btn');
        const imagesTab = document.getElementById('images-tab-btn');
        const path = window.location.pathname;

        uploadTab.classList.remove('nav__tab--active');
        imagesTab.classList.remove('nav__tab--active');

        if (path.includes('images')) {
            imagesTab.classList.add('nav__tab--active');
        } else {
            uploadTab.classList.add('nav__tab--active');
        }
    };

    const showLoader = () => {
        fileListWrapper.innerHTML = `
            <div class="dropzone-status">
                <div class="spinner"></div>
                <p class="upload__prompt">Loading images...</p>
            </div>
        `;
    };

    const displayFiles = async (page = 1) => {
        showLoader();

        try {
            const response = await fetch(`/api/images?page=${page}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch images from server`);
            }

            const result = await response.json();
            const files = result.images || [];
            const pagination = result.pagination || {};

            fileListWrapper.innerHTML = '';

            if (files.length === 0) {
                fileListWrapper.innerHTML = '<p class="upload__prompt">No images uploaded yet.</p>';
            } else {
                const container = document.createElement('div');
                container.className = 'file-list-container';
                const header = document.createElement('div');
                header.className = 'file-list-header';
                header.innerHTML = `
                    <div class="file-col file-col-name">Name</div>
                    <div class="file-col file-col-url">Url</div>
                    <div class="file-col file-col-delete">Delete</div>
                `;
                container.appendChild(header);

                const list = document.createElement('div');
                list.id = 'file-list';

                files.forEach((fileData) => {
                    const fullUrl = `${window.location.origin}${fileData.url}`;
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-list-item';
                    fileItem.innerHTML = `
                        <div class="file-col file-col-name">
                            <span class="file-icon"><img src="../static/img/icon/Group.png" alt="file icon"></span>
                            <span class="file-name" title="${fileData.filename}">${fileData.filename}</span>
                        </div>
                        <div class="file-col file-col-url">
                            <a href="${fullUrl}" target="_blank">${fullUrl}</a>
                        </div>
                        <div class="file-col file-col-delete">
                            <button class="delete-btn" data-id="${fileData.id}" data-filename="${fileData.filename}">
                                <img src="../static/img/icon/delete.png" class="delete-img" alt="delete icon">
                            </button>
                        </div>
                    `;
                    list.appendChild(fileItem);
                });

                container.appendChild(list);
                fileListWrapper.appendChild(container);

                if (pagination.total_pages > 1) {
                    renderPagination(pagination);
                }

                addDeleteListeners();
                currentPage = page;
            }
        } catch (error) {
            console.error('Error fetching images:', error);
            fileListWrapper.innerHTML = '<p class="upload__prompt-error">Error loading images from server. Database connection issue.</p>';
        }
    };

    const renderPagination = (pagination) => {
        const pagContainer = document.createElement('div');
        pagContainer.className = 'pagination';

        const prevBtn = document.createElement('button');
        prevBtn.className = `pagination__btn ${!pagination.has_prev ? 'disabled' : ''}`;
        prevBtn.textContent = '‹ Prev';
        prevBtn.disabled = !pagination.has_prev;
        prevBtn.addEventListener('click', () => {
            if (pagination.has_prev) displayFiles(pagination.current_page - 1);
        });
        pagContainer.appendChild(prevBtn);

        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = `pagination__btn ${i === pagination.current_page ? 'active' : ''}`;
            pageBtn.textContent = i;
            pageBtn.addEventListener('click', () => {
                if (i !== pagination.current_page) displayFiles(i);
            });
            pagContainer.appendChild(pageBtn);
        }

        const nextBtn = document.createElement('button');
        nextBtn.className = `pagination__btn ${!pagination.has_next ? 'disabled' : ''}`;
        nextBtn.textContent = 'Next ›';
        nextBtn.disabled = !pagination.has_next;
        nextBtn.addEventListener('click', () => {
            if (pagination.has_next) displayFiles(pagination.current_page + 1);
        });
        pagContainer.appendChild(nextBtn);

        fileListWrapper.appendChild(pagContainer);
    };

    const addDeleteListeners = () => {
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', async (event) => {
                const imageId = event.currentTarget.dataset.id;
                const filename = event.currentTarget.dataset.filename;

                if (!confirm(`Are you sure you want to delete ${filename}?`)) {
                    return;
                }

                try {
                    const response = await fetch(`/api/delete?id=${imageId}`, {method: 'DELETE'});

                    if (response.ok) {
                        displayFiles(currentPage);
                    } else {
                        const errData = await response.json();
                        alert(`Failed to delete file: ${errData.message || response.statusText}`);
                    }
                } catch (error) {
                    console.error('Delete error:', error);
                    alert('Network error. Failed to delete file.');
                }
            });
        });
    };

    if (uploadRedirectButton) {
        uploadRedirectButton.addEventListener('click', () => {
            window.location.href = '/upload';
        });
    }

    updateTabStyles();
    displayFiles(1);
});