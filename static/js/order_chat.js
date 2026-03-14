document.addEventListener("DOMContentLoaded", function() {
    // Получаем ссылки на основные элементы интерфейса чата
    const chatWrapper = document.getElementById("chat-wrapper");
    const chatForm = document.getElementById("chat-form");
    const commentInput = document.getElementById("comment-input");
    const sendBtn = document.getElementById("send-btn");

    // Функция для автоматической прокрутки блока сообщений в самый низ
    function scrollChatToBottom() {
        const container = document.getElementById("chat-messages");
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    // Прокручиваем чат вниз при первой загрузке страницы
    scrollChatToBottom();

    // Функция фонового обновления (AJAX Polling)
    async function fetchChatUpdates() {
        try {
            // Запрашиваем текущую страницу целиком
            const response = await fetch(window.location.href);
            if (response.ok) {
                // Получаем HTML-код страницы в виде текста
                const htmlText = await response.text();
                
                // Превращаем текст в полноценное DOM-дерево для удобного поиска
                const parser = new DOMParser();
                const doc = parser.parseFromString(htmlText, "text/html");
                
                // Находим обновленный блок чата в загруженном HTML
                const newChatWrapper = doc.getElementById("chat-wrapper");
                
                // Если содержимое нового чата отличается от текущего, заменяем его
                if (newChatWrapper && newChatWrapper.innerHTML !== chatWrapper.innerHTML) {
                    chatWrapper.innerHTML = newChatWrapper.innerHTML;
                    scrollChatToBottom(); // Снова прокручиваем вниз к новым сообщениям
                }
            }
        } catch (error) {
            console.error("Error fetching chat updates:", error);
        }
    }

    // Запускаем функцию обновления каждые 3000 миллисекунд (3 секунды)
    setInterval(fetchChatUpdates, 3000);

    // Перехват отправки формы для работы без перезагрузки страницы
    if (chatForm) {
        chatForm.addEventListener("submit", async function(e) {
            e.preventDefault(); // Блокируем стандартное поведение формы
            
            // Собираем данные из текстового поля
            const formData = new FormData(chatForm);
            sendBtn.disabled = true; // Отключаем кнопку, чтобы избежать двойной отправки
            
            try {
                // Отправляем POST-запрос на URL, указанный в атрибуте action формы
                const response = await fetch(chatForm.action, {
                    method: "POST",
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest' // Указываем серверу, что это AJAX-запрос
                    }
                });

                if (response.ok) {
                    commentInput.value = ""; // Очищаем поле ввода при успешной отправке
                    await fetchChatUpdates(); // Сразу принудительно запрашиваем обновленный список сообщений
                }
            } catch (error) {
                console.error("Error sending message:", error);
            } finally {
                sendBtn.disabled = false; // Включаем кнопку обратно
            }
        });
    }
});