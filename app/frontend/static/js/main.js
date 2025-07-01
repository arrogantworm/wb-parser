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

// Select Category

const categories = document.querySelectorAll('.category-card ul li p:not(.toggle)');

function requestCategoryStatus(category_id) {
    fetch(`/api/parse/?category_id=${category_id}`)
        .then(async response => {
            const data = await response.json();

            if (!response.ok) {
                throw data;
            }

            switch (data.status) {
                case 'ok':
                case 'parsing':
                    window.location.href = `products/?category_id=${category_id}`;
                    break;
            }
        })
        .catch(error => {
            if (error.hasOwnProperty('error')) {
                console.error(error.error); // Вывести ошибку через messages
            } else {
                console.error('Ошибка запроса:', error);
            }
        });
}


categories.forEach((category) => {
    category.addEventListener('click', () => {
        let category_id = category.dataset.id;

        requestCategoryStatus(category_id);
    })
})