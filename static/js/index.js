const allImgBlocks = document.querySelectorAll('.hero__img');
const randomIndex = Math.floor(Math.random() * allImgBlocks.length);
const randomBlock = allImgBlocks[randomIndex];
randomBlock.classList.add('is-visible');

document.body.style.setProperty('background-color', '#151515');

document.addEventListener('DOMContentLoaded', function () {
    const showcaseButton = document.querySelector('.header__button-btn');
    if (showcaseButton) {
        showcaseButton.addEventListener('click', function () {
            window.location.href = '/upload';
        });
    }
});
