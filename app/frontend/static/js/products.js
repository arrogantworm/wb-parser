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
const searchQuery = params.get('q');
let page = params.get('page');
if (!page) {
    page = 1;
    params.set('page', page);
    window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`);
}

// Графики
let chart1Instance = null;
let chart2Instance = null;

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
async function requestParsingStatus() {
    try {
        let url;

        if (categoryId) {
            url = `/api/parse/?category_id=${categoryId}`;
        } else if (searchQuery) {
            url = `/api/parse/?q=${searchQuery}`;
        };
        const response = await fetch(url);
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

            reloadTable(i);
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
            reloadTable(currentPage - 1);
        }
    };

    nextBtn.onclick = async () => {
        if (currentPage < totalPages) {
            params.set('page', currentPage + 1);
            history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
            reloadTable(currentPage + 1);
        }
    };
}

// Сортировка
function initSorting() {
    let currentSort = params.get('sort') || 'name';

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

            reloadTable(1);
        });
    });
}


// Фильтры

function initFilters() {
    const minPriceInput = document.getElementById('low-price');
    const maxPriceInput = document.getElementById('top-price');
    const minRatingInput = document.querySelector('input[placeholder="Не ниже"]');
    const minFeedbacksInput = document.querySelector('input[placeholder="Не менее"]');

    const applyBtn = document.querySelector('.filter-btns .primary');
    const resetBtn = document.querySelector('.filter-btns .secondary');

    // После объявления minPriceInput, maxPriceInput...
    if (params.get('min_price')) minPriceInput.value = params.get('min_price');
    if (params.get('top_price')) maxPriceInput.value = params.get('top_price');
    if (params.get('min_rating')) minRatingInput.value = params.get('min_rating');
    if (params.get('min_feedbacks')) minFeedbacksInput.value = params.get('min_feedbacks');

    applyBtn.onclick = () => {
        if (minPriceInput.value) {
            params.set('min_price', minPriceInput.value);
        } else {
            params.delete('min_price');
        }

        if (maxPriceInput.value) {
            params.set('top_price', maxPriceInput.value);
        } else {
            params.delete('top_price');
        }

        if (minRatingInput.value) {
            params.set('min_rating', minRatingInput.value);
        } else {
            params.delete('min_rating');
        }

        if (minFeedbacksInput.value) {
            params.set('min_feedbacks', minFeedbacksInput.value);
        } else {
            params.delete('min_feedbacks');
        }

        params.set('page', 1);
        page = 1;

        history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
        initProductsInfo();
    };

    resetBtn.onclick = () => {
        params.delete('min_price');
        params.delete('top_price');
        params.delete('min_rating');
        params.delete('min_feedbacks');
        params.set('page', 1);

        minPriceInput.value = '';
        maxPriceInput.value = '';
        minRatingInput.value = '';
        minFeedbacksInput.value = '';

        history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
        initProductsInfo();
    };
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

async function reloadTable(page) {
    let data = await requestProducts(page);
    if (data) {
        renderProductsTable(data['results']);
        renderPagination(data['count'], 20, page);
    }
}

// Графики

async function initCharts() {
    const chartsSection = document.getElementById('charts');
    const chart1Container = document.getElementById('chart1').parentElement;
    const chart2Container = document.getElementById('chart2').parentElement;

    const chart1Ctx = document.getElementById('chart1').getContext('2d');
    const chart2Ctx = document.getElementById('chart2').getContext('2d');

    try {
        const url = `/api/charts/?${params.toString()}`;
        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw new Error('Ошибка при загрузке графиков');
        }

        // 1. Гистограмма цен
        const labels1 = data.price_histogram.map(item => item.range);
        const counts1 = data.price_histogram.map(item => item.count);

        if (chart1Instance) {
            chart1Instance.destroy();
        }
        chart1Instance = new Chart(chart1Ctx, {
            type: 'bar',
            data: {
                labels: labels1,
                datasets: [{
                    label: 'Количество товаров',
                    data: counts1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        let chart1Loading = chart1Container.querySelector('.loading');
        if (chart1Loading) {
            chart1Loading.remove();
        }

        // 2. Линейный график скидка vs рейтинг
        const labels2 = data.discount_vs_rating.map((_, idx) => idx + 1); // просто индекс
        const ratings = data.discount_vs_rating.map(item => item.rating);
        const discounts = data.discount_vs_rating.map(item => item.discount_percent);

        if (chart2Instance) {
            chart2Instance.destroy();
        }
        chart2Instance = new Chart(chart2Ctx, {
            type: 'line',
            data: {
                labels: labels2,
                datasets: [{
                    label: 'Рейтинг',
                    data: ratings,
                    yAxisID: 'y1',
                    borderWidth: 2
                }, {
                    label: 'Скидка (%)',
                    data: discounts,
                    yAxisID: 'y2',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                stacked: false,
                scales: {
                    y1: {
                        type: 'linear',
                        position: 'left',
                        beginAtZero: true,
                        suggestedMax: 5
                    },
                    y2: {
                        type: 'linear',
                        position: 'right',
                        beginAtZero: true
                    }
                }
            }
        });
        let chart2Loading = chart2Container.querySelector('.loading');
        if (chart2Loading) {
            chart2Loading.remove();
        }


    } catch (err) {
        console.error('Ошибка загрузки графиков:', err);
    }
}

async function initProductsInfo() {
    const parsingStatus = await requestParsingStatus();
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

            // Сортировка
            initSorting();

            // Фильтры
            initFilters();

            // Графики
            initCharts();
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
    if (categoryId || searchQuery ) {

        if (categoryId) {
            // Получаем путь к категории
            initCategoryNav();
        } else if (searchQuery) {
            mainNav.remove();
        };

        // Запуск парсинга и отображение товаров
        initProductsInfo();
    }
}

// Графики заглушка
const ctx = document.getElementById('chart1');

chart1Instance = new Chart(ctx, {
    type: 'bar',
    data: {
    labels: [],
    datasets: [
    {
        label: '',
        data: [],
        borderWidth: 1
    }]
    },
    options: {
    scales: {
        y: {
        beginAtZero: true
        }
    }
    }
});
const ctx2 = document.getElementById('chart2');

chart2Instance = new Chart(ctx2, {
    type: 'line',
    data: {
    labels: [],
    datasets: [{
        label: '',
        data: [],
        borderWidth: 1
    },
    {
        label: '',
        data: [],
        borderWidth: 1
    }]
    },
    options: {
    scales: {
        y: {
        beginAtZero: true
        }
    }
    }
});

// Инициализация
init();
