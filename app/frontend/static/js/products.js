// Пагинация
const paginationNav = document.querySelector('.pagination');
const paginationUl = paginationNav.querySelector('ul');
const prevBtn = paginationNav.querySelector('.prev');
const nextBtn = paginationNav.querySelector('.next');
let scrollStep = 60;

// Таблица с товарами
const tableWrapper = document.querySelector('.table-wrapper');

// get параметры
const params = new URLSearchParams(window.location.search);
const categoryId = params.get('category_id');
let page = params.get('page');
if (!page) {
    page = 1;
    params.set('page', page);
    window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`);
}

// Навигация
const mainNav = document.querySelector('nav.categories');

// Получение пути к категории
async function requestCategoryPath() {
    try {
        const response = await fetch(`/api/category-path/?category_id=${categoryId}`);
        const data = await response.json();

        if (!response.ok) {
            throw data;
        }

        switch (data.status) {
            case 'ok':
            case 'parsing':
                return data;
            default:
                return 'unknown';
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
}

// Функция отрисовки пути категории
function renderCategoryPath(path) {
    if (!Array.isArray(path)) {
        console.warn('path не массив:', path);
        return;
    }

    const ul = document.createElement('ul');
    path.forEach(([id, name]) => {
        const li = document.createElement('li');
        li.dataset.id = id;
        li.textContent = name;
        ul.appendChild(li);
    });

    // Очищаем и вставляем
    mainNav.innerHTML = '';
    mainNav.appendChild(ul);
}

async function initCategoryNav() {
    let categoryNavData = await requestCategoryPath();

    switch (categoryNavData.status) {
        case 'ok':
            renderCategoryPath(categoryNavData['category_path']);
            break;
        case 'parsing':
            setTimeout(initCategoryNav, 500);
            break;
    }
}

// Проверка готовности данных
async function requestCategoryStatus() {
    try {
        const response = await fetch(`/api/parse/?category_id=${categoryId}`);
        const data = await response.json();

        if (!response.ok) {
            throw data;
        }

        console.log(data);

        switch (data['status']) {
            case 'ok':
                return 'ready';
            case 'parsing':
                return 'parsing';
            default:
                return 'unknown';
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
}

// Запрос данных товаров
async function requestProducts(page) {
    params.set('page', page);
    const url = `/api/products/?${params.toString()}`;
    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
        throw new Error('Ошибка сети: ' + response.status);
    }

    if (data.hasOwnProperty('results')) {
        return data;
    }

    return null;
}


// Пагинация

function renderPagination(count, pageSize, currentPage) {
    const totalPages = Math.ceil(count / pageSize);

    paginationUl.innerHTML = '';

    for (let i = 1; i <= totalPages; i++) {
        const li = document.createElement('li');
        li.textContent = i;

        if (i === currentPage) {
            li.classList.add('active');
        }

        li.addEventListener('click', async () => {
            if (i === currentPage) return;

            params.set('page', i);
            history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);

            let data = await requestProducts(i);
            renderProductsTable(data['results']);
            renderPagination(data['count'], 20, i);
        });

        paginationUl.appendChild(li);
    }

    // prev / next обработчики
    prevBtn.classList.toggle('disabled', currentPage === 1);
    nextBtn.classList.toggle('disabled', currentPage === totalPages);

    prevBtn.onclick = async () => {
        if (currentPage > 1) {
            params.set('page', currentPage - 1);
            history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
            let data = await requestProducts(currentPage - 1);
            renderProductsTable(data['results']);
            renderPagination(data['count'], 20, currentPage - 1);
        }
    };

    nextBtn.onclick = async () => {
        if (currentPage < totalPages) {
            params.set('page', currentPage + 1);
            history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
            let data = await requestProducts(currentPage + 1);
            renderProductsTable(data['results']);
            renderPagination(data['count'], 20, currentPage + 1);
        }
    };
}

// Сортировка
function initSorting() {
    const currentSort = params.get('sort');
    document.querySelectorAll('.sort-btn').forEach(btn => {
        const baseSort = btn.dataset.sort.replace('-', '');

        btn.classList.remove('ascending', 'descending');
        btn.dataset.sort = baseSort;

        // Теперь если эта кнопка совпадает с текущим sort из URL
        if (currentSort === baseSort) {
            btn.classList.add('ascending');
            btn.dataset.sort = baseSort;
        }
        if (currentSort === '-' + baseSort) {
            btn.classList.add('descending');
            btn.dataset.sort = '-' + baseSort;
        }

        // Обработка нажатия
        btn.addEventListener('click', async () => {
            let newSort;
            if (btn.dataset.sort.startsWith('-')) {
                newSort = btn.dataset.sort.substring(1);
                btn.classList.remove('descending');
                btn.classList.add('ascending');
            } else {
                newSort = '-' + btn.dataset.sort;
                btn.classList.remove('ascending');
                btn.classList.add('descending');
            }
            btn.dataset.sort = newSort;

            // Снимаем со всех остальных кнопок
            document.querySelectorAll('.sort-btn').forEach(otherBtn => {
                if (otherBtn !== btn) {
                    otherBtn.classList.remove('ascending', 'descending');
                    otherBtn.dataset.sort = otherBtn.dataset.sort.replace('-', '');
                }
            });

            // Обновляем URL и грузим
            params.set('sort', newSort);
            params.set('page', 1);
            history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);

            let data = await requestProducts(1);
            if (data) {
                renderProductsTable(data['results']);
                renderPagination(data['count'], 20, 1);
            }
        });
    });
}


// Первоначальное отображение данных товаров
function initProductsTable(products) {
    // Создаём элементы
    const table = document.createElement('table');
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');

    // Заполняем заголовок таблицы
    thead.innerHTML = `
        <tr>
            <th>
                <div class="th-wrapper">
                    <p>Название</p>
                    <div class="sort-btn" data-sort="name">
                        <div class="bar"></div><div class="bar"></div><div class="bar"></div>
                    </div>
                </div>
            </th>
            <th>
                <div class="th-wrapper">
                    <p>Цена</p>
                    <div class="sort-btn" data-sort="price">
                        <div class="bar"></div><div class="bar"></div><div class="bar"></div>
                    </div>
                </div>
            </th>
            <th>
                <div class="th-wrapper">
                    <p>Цена со скидкой</p>
                    <div class="sort-btn" data-sort="discounted_price">
                        <div class="bar"></div><div class="bar"></div><div class="bar"></div>
                    </div>
                </div>
            </th>
            <th>
                <div class="th-wrapper">
                    <p>Рейтинг</p>
                    <div class="sort-btn" data-sort="rating">
                        <div class="bar"></div><div class="bar"></div><div class="bar"></div>
                    </div>
                </div>
            </th>
            <th>
                <div class="th-wrapper">
                    <p>Отзывы</p>
                    <div class="sort-btn" data-sort="feedbacks">
                        <div class="bar"></div><div class="bar"></div><div class="bar"></div>
                    </div>
                </div>
            </th>
        </tr>
    `;

    // Заполняем тело таблицы
    products.forEach(product => {
        const size = product.sizes[0] || { price: '-', discounted_price: '-' };
        const wbLink = `https://wildberries.ru/catalog/${product.wb_id}/detail.aspx`;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><a href="${wbLink}" target="_blank" rel="noopener noreferrer">${product.name}</a></td>
            <td>${size.price}</td>
            <td>${size.discounted_price}</td>
            <td>${product.review_rating}</td>
            <td>${product.feedbacks}</td>
        `;

        tbody.appendChild(tr);
    });

    // Собираем таблицу
    table.appendChild(thead);
    table.appendChild(tbody);

    // Заменяем старую таблицу
    tableWrapper.innerHTML = '';
    tableWrapper.appendChild(table);
}

// Рендер таблицы с товарами
function renderProductsTable(products) {
    let tableBody = document.querySelector('tbody');
    tableBody.innerHTML = '';

    // Заполняем тело таблицы
    products.forEach(product => {
        const size = product.sizes[0] || { price: '-', discounted_price: '-' };
        const wbLink = `https://wildberries.ru/catalog/${product.wb_id}/detail.aspx`;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><a href="${wbLink}" target="_blank" rel="noopener noreferrer">${product.name}</a></td>
            <td>${size.price}</td>
            <td>${size.discounted_price}</td>
            <td>${product.review_rating}</td>
            <td>${product.feedbacks}</td>
        `;

        tableBody.appendChild(tr);
    });
}

async function initProductsInfo() {
    const parsingStatus = await requestCategoryStatus(categoryId);
    console.log('Статус:', parsingStatus);

    switch (parsingStatus) {
        case 'ready':
            let data = await requestProducts(page);
            if (!data) {
                console.error('Не удалось загрузить товары');
                return;
            };
            initProductsTable(data['results']);
            // Пагинация
            renderPagination(data['count'], 20, parseInt(page));
            paginationNav.classList.remove('hidden');

            initSorting();
            break;
        case 'parsing':
            console.log('Жду 5 секунд')
            setTimeout(initProductsInfo, 5000);
            break;
        default:
            console.error('Что-то пошло не так со сбором товаров');
            break;
    }

}

async function init() {
    // Поиск по категории
    if (categoryId !== null) {

        // Получаем путь к категории
        initCategoryNav();

        // Запуск парсинга и отображение товаров
        initProductsInfo();
    }
}

init();
