// static/js/feed.js
// Логика бесконечной прокрутки ленты новостей
document.addEventListener('DOMContentLoaded', () => {
    // Считываем настройки (переводы, параметры) из блока конфигурации на странице
    const configElement = document.getElementById('js-feed-config');
    if (!configElement) return;

    const config = JSON.parse(configElement.textContent);
    const T = config.translations;

    // Начальные параметры пагинации
    let page = 1;
    let isLoading = false;

    // Ссылки на элементы DOM
    const feedContainer = document.getElementById('feed-container');
    const sentinel = document.getElementById('loading-sentinel');

    // Наблюдатель IntersectionObserver: срабатывает, когда "маркер" (sentinel) виден на экране
    const observer = new IntersectionObserver((entries) => {
        // Если маркер в зоне видимости и загрузка еще не идет
        if (entries[0].isIntersecting && !isLoading) {
            isLoading = true;
            sentinel.innerHTML = `<p>${T.loading}</p>`;

            // Извлекаем текущие фильтры из URL (чтобы подгружать нужную категорию)
            const urlParams = new URLSearchParams(window.location.search);
            const activeFilter = urlParams.get('filter') || 'all';
            const currentQuery = urlParams.get('q') || '';

            // Формируем адрес запроса для следующей страницы
            const fetchUrl = `/?page=${page + 1}&filter=${activeFilter}&q=${encodeURIComponent(currentQuery)}`;

            // Отправляем асинхронный запрос на сервер
            fetch(fetchUrl, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                if (html.trim() === '') {
                    // Если данных больше нет — отключаем наблюдение
                    observer.disconnect();
                    sentinel.innerHTML = `<p>${T.noMoreContent}</p>`;
                } else {
                    // Добавляем полученные карточки в ленту
                    feedContainer.insertAdjacentHTML('beforeend', html);
                    page += 1;
                    isLoading = false;
                    sentinel.innerHTML = '';
                }
            }).catch(err => {
                console.error("Error loading more items:", err);
                isLoading = false;
                sentinel.innerHTML = '';
            });
        }
    }, { threshold: 0.1 });

    // Запускаем процесс наблюдения за маркером внизу ленты
    if (sentinel) {
        observer.observe(sentinel);
    }
});