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

searchInput.parentElement.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = searchInput.value;
    const url = `/api/parse/?q=${query}`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw data;
        }

        console.log(data);

        if (data.hasOwnProperty('type')) {
            switch (data['type']) {
                case 'category':
                    let category_id = data['category_id'];
                    window.location.href = `products/?category_id=${category_id}`;
                    break;

                case 'search':
                    window.location.href = `products/?q=${query}`;
                    break;

                default:
                    console.log('?');
            }
        }
    } catch (error) {
        if (error.hasOwnProperty('error')) {
            console.error('Ошибка от сервера:', error.error);
            return 'error';
        } else {
            console.error('Ошибка запроса:', error);
            return 'error';
        }
    }
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