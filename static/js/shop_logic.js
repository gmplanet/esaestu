/* Слушатель события 'DOMContentLoaded'.
   Он говорит браузеру: "Не запускай этот код, пока весь HTML-документ не будет полностью загружен и прочитан".
   Это нужно, чтобы скрипт не пытался найти элементы (кнопки, тексты), которых еще нет на экране.
   Стрелочная функция () => { ... } — это современный и короткий способ записи функции.
*/
document.addEventListener('DOMContentLoaded', () => {

    /* --- БЛОК 1: НАСТРОЙКИ ОТ СЕРВЕРА --- */
    
    // Ищем на странице скрытый тег <script id="js-config">, который мы передали из Django.
    // Там лежат безопасные настройки (токены, ссылки, переводы текста).
    const configElement = document.getElementById('js-config');
    
    // Если такого элемента нет (например, мы не на странице магазина), скрипт просто прекратит работу (return),
    // чтобы не выдавать ошибок в консоль.
    if (!configElement) return;

    // Берем текстовое содержимое тега и превращаем его из формата JSON в рабочий объект JavaScript.
    const config = JSON.parse(configElement.textContent);
    
    // Раскладываем настройки по удобным переменным для быстрого доступа.
    const T = config.translations; // Тексты для уведомлений
    const csrfToken = config.csrfToken; // Токен безопасности Django для защиты от подделки запросов
    const updateCartUrlBase = config.updateCartUrlBase; // Базовая часть ссылки для обновления корзины

    /* --- БЛОК 2: АСИНХРОННОЕ ОБНОВЛЕНИЕ КОРЗИНЫ (AJAX) --- */
    
    // Создаем функцию updateQuantity и вешаем ее на объект window, чтобы она стала глобальной.
    // Это нужно, чтобы атрибуты onclick="..." в HTML могли её увидеть и запустить.
    // Слово async означает, что функция будет выполнять задачи, требующие времени (например, запрос к серверу),
    // и не будет "замораживать" вкладку браузера во время ожидания.
    window.updateQuantity = async function(itemId, newQty) {
        // Конструкция try...catch нужна для перехвата любых непредвиденных ошибок (например, пропал интернет).
        try {
            // Функция fetch отправляет запрос на сервер. 
            // Слово await говорит скрипту: "подожди, пока сервер не пришлет ответ, и только потом иди дальше".
            // Мы склеиваем базовую ссылку и ID товара, чтобы получить точный адрес, например: /cart/update/15/
            const response = await fetch(`${updateCartUrlBase}${itemId}/`, {
                method: 'POST', // Метод отправки данных
                headers: {
                    'Content-Type': 'application/json', // Говорим серверу, что отправляем данные в формате JSON
                    'X-CSRFToken': csrfToken, // Прикрепляем ключ безопасности, иначе Django отклонит запрос
                    'X-Requested-With': 'XMLHttpRequest' // Подсказываем Django, что это фоновый запрос (AJAX)
                },
                // Превращаем объект с новым количеством товара в текстовую строку JSON и кладем в тело запроса
                body: JSON.stringify({ quantity: newQty })
            });

            // Когда ответ получен, просим браузер расшифровать его из JSON обратно в объект JavaScript.
            // Это тоже занимает доли секунды, поэтому снова используем await.
            const data = await response.json();

            // Проверяем статус, который нам вернул наш python-код (views.py)
            if (data.status === 'success') {
                
                // Если всё хорошо, находим элементы на странице по их ID и меняем их внутренний текст (innerText).
                // Обрати внимание на обратные кавычки ` ` — они позволяют удобно вставлять переменные через ${...}.
                document.getElementById(`qty-${itemId}`).innerText = newQty;
                document.getElementById(`price-${itemId}`).innerText = `$${data.item_total}`;
                document.getElementById('cart-total-display').innerText = `$${data.cart_total}`;
                
                // Находим кнопки "+" и "-", чтобы обновить их функции.
                // querySelectorAll ищет все элементы с классом .qty-btn внутри конкретной строки корзины.
                const buttons = document.querySelectorAll(`#cart-item-${itemId} .qty-btn`);
                
                // Если мы нашли обе кнопки, меняем их атрибут onclick.
                // Теперь, если нажать на них в следующий раз, они отправят уже обновленное количество.
                if (buttons.length >= 2) {
                    buttons[0].setAttribute('onclick', `updateQuantity(${itemId}, ${newQty - 1})`);
                    buttons[1].setAttribute('onclick', `updateQuantity(${itemId}, ${newQty + 1})`);
                }
                
            } else if (data.status === 'deleted') {
                // Если сервер ответил, что товар удален (количество упало до 0), 
                // мы просто принудительно перезагружаем страницу, чтобы Django отрисовал корзину заново.
                location.reload();
                
            } else if (data.status === 'error') {
                // Если сервер вернул ошибку (например, превышен лимит), мы показываем красивое уведомление.
                
                // 1. Ищем, нет ли уже на экране старого сообщения об ошибке. Если есть — удаляем его.
                const oldMsg = document.getElementById('ajax-error-msg');
                if (oldMsg) oldMsg.remove();

                // 2. Создаем новый пустой тег <div> (блок).
                const msgDiv = document.createElement('div');
                msgDiv.id = 'ajax-error-msg'; // Даем ему ID, чтобы потом легко находить
                
                // 3. Добавляем блоку CSS-стили напрямую через JavaScript, чтобы он выглядел в нашем дизайне.
                msgDiv.style.cssText = 'border: 2px solid var(--pixel-blue, #0055ff); padding: 10px; margin-bottom: 20px; font-family: "VT323", monospace; font-size: 1.2rem; background: var(--pixel-white, #ffffff); color: var(--pixel-black, #000000);';
                
                // 4. Вставляем внутрь блока текст ошибки, который прислал сервер.
                msgDiv.innerText = data.message;

                // 5. Ищем главный контейнер на странице.
                const contentCenter = document.querySelector('.content-center');
                
                if (contentCenter) {
                    // Если контейнер найден, вставляем наше сообщение самым первым элементом (перед остальным содержимым).
                    contentCenter.insertBefore(msgDiv, contentCenter.firstChild);
                    // Плавно или резко прокручиваем страницу в самый верх, чтобы пользователь точно увидел ошибку.
                    window.scrollTo(0, 0); 
                } else {
                    // Резервный вариант: если структура HTML сломалась, покажем хотя бы стандартное окно браузера.
                    alert(data.message); 
                }
            }
        } catch (error) {
            // Сюда скрипт попадет, если произошел сбой сети или сервер вообще не ответил (упал).
            // Выводим технические детали в консоль разработчика (F12) для себя.
            console.error('Fetch error:', error);
            // А пользователю показываем понятный переведенный текст из настроек.
            alert(T.errorUpdating);
        }
    };


    /* --- БЛОК 3: УПРАВЛЕНИЕ ВСПЛЫВАЮЩИМ ОКНОМ (POPUP) --- */
    
    // Находим элементы всплывающего окна один раз при загрузке страницы, чтобы не искать их каждый раз при клике.
    const popup = document.getElementById('imagePopup');
    const popupImg = document.getElementById('popupImage');

    // Функция открытия. Принимает ссылку на картинку.
    window.openImagePopup = function(imageUrl) {
        // Проверяем, существуют ли элементы (чтобы не было ошибок на страницах, где нет галереи).
        if (popupImg && popup) {
            popupImg.src = imageUrl; // Подменяем источник картинки в попапе на нужный
            popup.style.display = 'flex'; // Меняем стиль display с 'none' на 'flex', делая окно видимым
        }
    };

    // Функция закрытия. Срабатывает при клике на затемненный фон вокруг картинки.
    window.closeImagePopup = function() {
        if (popup) {
            popup.style.display = 'none'; // Прячем окно
        }
    };


    /* --- БЛОК 4: СОХРАНЕНИЕ ПОЗИЦИИ ПРОКРУТКИ --- */
    
    // Слушаем событие 'beforeunload' — оно срабатывает за миллисекунду до того, как страница начнет перезагружаться.
    window.addEventListener('beforeunload', () => {
        // Сохраняем текущую позицию прокрутки (в пикселях сверху) во временное хранилище браузера (sessionStorage).
        // Это хранилище живет, пока открыта вкладка.
        sessionStorage.setItem('shopScrollPos', window.scrollY);
    });

    // Этот код выполняется сразу при загрузке страницы. 
    // Мы проверяем, есть ли в памяти сохраненная позиция прокрутки.
    const savedScroll = sessionStorage.getItem('shopScrollPos');
    if (savedScroll) {
        // Если есть, заставляем браузер мгновенно прокрутить страницу до этой точки (по оси Y).
        // parseInt превращает строку в число.
        window.scrollTo(0, parseInt(savedScroll, 10));
        // Удаляем запись из памяти, чтобы она не сработала при следующем переходе на совершенно другую страницу.
        sessionStorage.removeItem('shopScrollPos');
    }
});