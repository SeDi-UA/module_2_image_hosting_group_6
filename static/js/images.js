document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', function (event) {
        if (event.key === 'F5' || event.key === 'Escape') {
            event.preventDefault();
            window.location.href = '/upload';
        }
    });
    const fileListWrapper = document.getElementById('file-list-wrapper');
    const uploadRedirectButton = document.getElementById('upload-tab-btn');

    const updateTabStyles = () => {
        const uploadTab = document.getElementById('upload-tab-btn');
        const imagesTab = document.getElementById('images-tab-btn');
        const isImagesPage = window.location.pathname.includes('images');

        uploadTab.classList.remove('nav__tab--active');
        imagesTab.classList.remove('nav__tab--active');

        if (isImagesPage) {
            imagesTab.classList.add('nav__tab--active');
        } else {
            uploadTab.classList.add('nav__tab--active');
        }
    };

    const displayFiles = async () => {
        fileListWrapper.innerHTML = '';

        try {
            const response = await fetch('/api/images');
            if (!response.ok) {
                throw new Error('Failed to fetch images from server');
            }

            const result = await response.json();
            const files = result.images || [];

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
                            <span class="file-name" title="${fileData.name}">${fileData.name}</span>
                        </div>
                        <div class="file-col file-col-url">
                            <a href="${fullUrl}" target="_blank">${fullUrl}</a>
                        </div>
                        <div class="file-col file-col-delete">
                            <button class="delete-btn" data-filename="${fileData.name}"><img src="../static/img/icon/delete.png" alt="delete icon"></button>
                        </div>
                    `;
                    list.appendChild(fileItem);
                });

                container.appendChild(list);
                fileListWrapper.appendChild(container);
                addDeleteListeners();
            }
        } catch (error) {
            console.error(error);
            fileListWrapper.innerHTML = '<p class="upload__prompt-error">Error loading images from server.</p>';
        }
        updateTabStyles();
    };

    const addDeleteListeners = () => {
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', async (event) => {
//                const filename = event.currentTarget.dataset.filename;
//                fetch('/api/delete?file=${filename}', {method: 'DELETE'})
            });
        });
    };

    if (uploadRedirectButton) {
        uploadRedirectButton.addEventListener('click', () => {
            window.location.href = '/upload';
        });
    }

    displayFiles();
});