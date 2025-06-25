// Search

searchWrapper = document.querySelector('.search-wrapper');
searchInput = document.querySelector('#search-input');

searchWrapper.addEventListener('click', () => {
    searchInput.focus();
});

searchInput.addEventListener('focus', () => {
    searchWrapper.classList.add('focus');
});

searchInput.addEventListener('focusout', () => {
    searchWrapper.classList.remove('focus');
});

// Categories

document.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', (e) => {
    const target = e.target;
    if (target.tagName === 'P' && target.nextElementSibling?.tagName === 'UL') {
        target.nextElementSibling.classList.toggle('open');
        target.classList.toggle('open');
        e.stopPropagation();
    }
    });
});