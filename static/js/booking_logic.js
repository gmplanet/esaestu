// 1. Извлекаем конфигурацию из тега, который подготовил Django
const configElement = document.getElementById('js-config');
const config = JSON.parse(configElement.textContent);

// 2. Удобные константы для использования в коде
const API_SLOTS_URL = config.apiSlotsUrl;
const API_CONFIRM_URL = config.apiConfirmUrl;
const CSRF_TOKEN = config.csrfToken;
const T = config.translations; // Все переводы теперь здесь

// Пример того, как теперь использовать ссылки и токены в fetch:
async function confirmBooking(bookingData) {
    try {
        const response = await fetch(API_CONFIRM_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN // Токен берется из конфига, а не из куки!
            },
            body: JSON.stringify(bookingData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert(result.message);
            location.reload();
        } else {
            // Используем перевод из конфига
            alert(T.errorProcessing + (result.message ? ': ' + result.message : ''));
        }
    } catch (error) {
        console.error('Booking error:', error);
        alert(T.errorProcessing);
    }
}