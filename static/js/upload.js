document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' || event.key === 'F5') {
            event.preventDefault();
            sessionStorage.removeItem('pageWasVisited');
            window.location.href = '/';
        }
    });

    const dropzoneDefault = document.getElementById('dropzone-default');
    const dropzoneLoading = document.getElementById('dropzone-loading');
    const dropzoneResult = document.getElementById('dropzone-result');
    const dropzoneResultText = document.getElementById('dropzone-result-text');

    const fileUpload = document.getElementById('file-upload');
    const imagesButton = document.getElementById('images-tab-btn');
    const dropzone = document.querySelector('.upload__dropzone');
    const statusEl = document.getElementById('status-message');
    const uploadedContainer = document.getElementById('uploaded-files-container');
    const linksList = document.getElementById('links-list');
    const MAX_FILE_COUNT = 10;

    const changeDropzoneState = (state, text = '', type = 'success') => {
        dropzoneDefault.style.display = 'none';
        dropzoneLoading.style.display = 'none';
        dropzoneResult.style.display = 'none';

        dropzone.style.pointerEvents = 'auto';

        if (state === 'loading') {
            dropzoneLoading.style.display = 'flex';
            dropzone.style.pointerEvents = 'none';
        }
        else if (state === 'result') {
            dropzoneResult.style.display = 'flex';
            dropzoneResultText.textContent = text;
            dropzoneResultText.className = 'upload__prompt';
            dropzoneResultText.classList.add(type === 'success' ? 'text-success' : 'text-error');

            setTimeout(() => {
                changeDropzoneState('default');
            }, 3000);
        }
        else {
            dropzoneDefault.style.display = 'block';
        }
    };

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

    const uploadFilesToServer = async (filesArray) => {
        const formData = new FormData();

        filesArray.forEach(file => {
            formData.append('images', file);
        });

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: 'Unknown server error' }));
            throw new Error(errorData.message || `Server responded with status ${response.status}`);
        }

        return await response.json();
    };

    const handleAndStoreFiles = async (files) => {
        if (!files || files.length === 0) {
            return;
        }

        if (files.length > MAX_FILE_COUNT) {
            changeDropzoneState('result', `You cannot upload more than ${MAX_FILE_COUNT} files at once!`, 'error');
            return;
        }

        const allowedTypes = ['image/jpg','image/jpeg', 'image/png', 'image/gif'];
        const MAX_SIZE_BYTES = 2 * 1024 * 1024;

        const validFiles = [];
        const skippedFiles = [];

        for (const file of files) {
            if (!allowedTypes.includes(file.type)) {
                skippedFiles.push(`${file.name} (wrong type)`);
                continue;
            }
            if (file.size > MAX_SIZE_BYTES) {
                skippedFiles.push(`${file.name} (too large)`);
                continue;
            }
            validFiles.push(file);
        }
        if (validFiles.length === 0) {
            changeDropzoneState('result', `Skipped: ${skippedFiles.join(', ')}`, 'error');
            return;
        }

        changeDropzoneState('loading');

        try {
            const result = await uploadFilesToServer(validFiles);
            const storedFiles = JSON.parse(localStorage.getItem('uploadedImages')) || [];

            result.files.forEach(fileData => {
                storedFiles.push({
                    name: fileData.original_name,
                    url: fileData.url
                });
            });

            localStorage.setItem('uploadedImages', JSON.stringify(storedFiles));
            renderUploadedLinks(result.files);

            if (skippedFiles.length > 0) {
                changeDropzoneState('result', `Uploaded ${validFiles.length} file(s). Skipped ${skippedFiles.length} invalid file(s).`, 'success');
            } else {
                changeDropzoneState('result', "All files uploaded successfully!", 'success');
            }

        } catch (error) {
            console.error('Upload failed:', error);
            changeDropzoneState('result', `Upload failed: ${error.message}`, 'error');
        }
    };

    const renderUploadedLinks = (uploadedFiles) => {
        if (!linksList || !uploadedContainer) return;

        linksList.innerHTML = '';

        if (uploadedFiles.length === 0) {
            uploadedContainer.style.display = 'none';
            return;
        }

        uploadedContainer.style.display = 'block';

        uploadedFiles.forEach((file, index) => {
            const fullUrl = `${window.location.origin}${file.url}`;
            const labelGroup = document.createElement('div');
            labelGroup.className = 'upload__link-group';

            labelGroup.innerHTML = `
                <span class="upload__filename">${file.original_name}</span>
                <div class="upload__label">
                    <input type="text" class="upload__input" value="${fullUrl}" readonly />
                    <button class="upload__copy">COPY</button>
                </div>
            `;

            const copyBtn = labelGroup.querySelector('.upload__copy');

            copyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(fullUrl).then(() => {
                    copyBtn.textContent = 'COPIED!';
                    setTimeout(() => {
                        copyBtn.textContent = 'COPY';
                    }, 2000);
                }).catch(err => console.error('Failed to copy: ', err));
            });

            linksList.appendChild(labelGroup);
        });
    };

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropzone.classList.add('upload__dropzone--dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropzone.classList.remove('upload__dropzone--dragover');
            if (eventName === 'drop') handleAndStoreFiles(event.dataTransfer.files);
        });
    });

    dropzone.addEventListener('click', () => {
        fileUpload.click();
    });

    fileUpload.addEventListener('click', (event) => {
        event.stopPropagation();
    });

    if (imagesButton) {
        imagesButton.addEventListener('click', () => {
            window.location.href = '/images';
        });
    }

    fileUpload.addEventListener('change', (event) => {
        handleAndStoreFiles(event.target.files);
        event.target.value = '';
    });

    updateTabStyles();
}); 