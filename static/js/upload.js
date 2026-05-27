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
        const storedFiles = JSON.parse(localStorage.getItem('uploadedImages')) || [];
        const isImagesPage = window.location.pathname.includes('images');

        uploadTab.classList.remove('nav__tab--active');
        imagesTab.classList.remove('nav__tab--active');

        if (isImagesPage) {
            imagesTab.classList.add('nav__tab--active');
        } else {
            uploadTab.classList.add('nav__tab--active');
        }
    };

    const handleAndStoreFiles = (files) => {
        if (!files || files.length === 0) {
            return;
        }
        const storedFiles = JSON.parse(localStorage.getItem('uploadedImages')) || [];
        const allowedTypes = ['image/jpg','image/jpeg', 'image/png', 'image/gif'];
        const MAX_SIZE_BYTES = 3 * 1024 * 1024;
        let filesAdded = false;
        let lastFileName = '';

        for (const file of files) {
            if (!allowedTypes.includes(file.type)) {
                showStatus("Invalid file type!", "error");
                continue;
            }
            if (file.size > MAX_SIZE_BYTES) {
                showStatus("Invalid file size too large!", "error");
                continue;
            }

            const reader = new FileReader();
            reader.onload = (event) => {
                const fileData = {
                    //  Додати генерацію унікального імені
                    name: file.name,
                    //  Додати генерацію унікального імені

                    url: event.target.result
                };
                storedFiles.push(fileData);
                localStorage.setItem('uploadedImages', JSON.stringify(storedFiles));
                updateTabStyles();
            };
            reader.readAsDataURL(file);
            filesAdded = true;
            lastFileName = file.name;
        }

        if (filesAdded) {
            if (currentUploadInput) {
                currentUploadInput.value = `https://sharefile.xyz/${lastFileName}`;
            }
            showStatus("Files selected successfully! Go to the 'Images' tab to view them.");
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