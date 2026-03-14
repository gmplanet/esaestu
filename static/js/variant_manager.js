document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('variants-container');
    const addButton = document.getElementById('add-variant-btn');

    // Если на странице нет кнопки добавления, значит у пользователя нет прав, выходим
    if (!addButton || !container) return;

    // Функция для создания новой строки ввода
    window.addVariantRow = function() {
        const row = document.createElement('div');
        row.className = 'variant-input-row';
        
        // Внутренняя структура строки: название (Size) и значения (S, M, L)
        row.innerHTML = `
            <div style="flex: 1;">
                <input type="text" name="option_names" placeholder="Название (напр. Размер)" required>
            </div>
            <div style="flex: 2;">
                <input type="text" name="option_values" placeholder="Значения через запятую (напр. S, M, L)" required>
            </div>
            <button type="button" class="btn-main pixel-btn-action pixel-btn-red" onclick="this.parentElement.remove()" style="height: 40px; padding: 0 10px;">X</button>
        `;
        
        container.appendChild(row);
    };

    addButton.addEventListener('click', addVariantRow);
});