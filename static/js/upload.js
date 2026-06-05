document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' || event.key === 'F5') {
            event.preventDefault();
            sessionStorage.removeItem('pageWasVisited');
            window.location.href = '/';
        }
    });

    const fileUpload = document.getElementById('file-upload');
    const imagesButton = document.getElementById('images-tab-btn');
    const dropzone = document.querySelector('.upload__dropzone');
    const currentUploadInput = document.querySelector('.upload__input');
    const copyButton = document.querySelector('.upload__copy')
    const statusEl = document.getElementById('status-message');
    const MAX_FILE_COUNT = 10;

    const showStatus = (text, type = 'success') => {
        statusEl.textContent = text;
        statusEl.className = 'status-message visible'
        statusEl.classList.add(`status-message--${type}`);

        setTimeout(() => {
            statusEl.classList.remove(`visible`);
        }, 7000);
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
            showStatus(`You cannot upload more than ${MAX_FILE_COUNT} files at once!`, "error");
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
            showStatus(`No valid files to upload. Skipped: ${skippedFiles.join(', ')}`, "error");
            return;
        }

        try {
            const result = await uploadFilesToServer(validFiles);
            const storedFiles = JSON.parse(localStorage.getItem('uploadedImages')) || [];
            let lastUploadedUrl = '';

            result.files.forEach(fileData => {
                storedFiles.push({
                    name: fileData.original_name, // Зберігаємо оригінальну назву
                    url: fileData.url
                });
                lastUploadedUrl = fileData.url;
            });

            localStorage.setItem('uploadedImages', JSON.stringify(storedFiles));

            if (currentUploadInput && lastUploadedUrl) {
                currentUploadInput.value = `${window.location.origin}${lastUploadedUrl}`;
            }

            // Формуємо красивий статус для користувача
            if (skippedFiles.length > 0) {
                showStatus(`Successfully uploaded ${validFiles.length} file(s). Skipped ${skippedFiles.length} invalid file(s).`, "success");
            } else {
                showStatus("All files uploaded successfully!", "success");
            }

        } catch (error) {
            console.error('Upload failed:', error);
            showStatus(`Upload failed: ${error.message}`, "error");
        }
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

    if (copyButton && currentUploadInput) {
        copyButton.addEventListener('click', () => {
            const textToCopy = currentUploadInput.value;

            if (textToCopy && textToCopy !== 'https://') {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    copyButton.textContent = 'COPIED!';
                    setTimeout(() => {
                        copyButton.textContent = 'COPY';
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                });
            }
        });
    }

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