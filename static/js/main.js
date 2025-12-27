document.addEventListener('DOMContentLoaded', function() {
    const burger = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar-left');

    // --- 1. ЛОГИКА БУРГЕРА (МОБИЛЬНАЯ) ---
    if (burger && sidebar) {
        burger.addEventListener('click', () => sidebar.classList.toggle('mobile-open'));

        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('mobile-open') && 
                !sidebar.contains(e.target) && !burger.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        });
    }

    // --- 2. ЛОГИКА РАСКРЫТИЯ МЕНЮ (С ПАМЯТЬЮ) ---
    // ВОССТАНОВЛЕНИЕ: Проверяем localStorage при загрузке
    const openMenuIds = JSON.parse(localStorage.getItem('openMenus')) || [];
    openMenuIds.forEach(id => {
        const activeItem = document.getElementById(id);
        if (activeItem) activeItem.classList.add('open');
    });

    const toggles = document.querySelectorAll('.js-menu-toggle');
    toggles.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const parent = this.closest('.has-children');
            parent.classList.toggle('open');

            // СОХРАНЕНИЕ: Записываем ID всех открытых меню
            const currentlyOpen = Array.from(document.querySelectorAll('.has-children.open'))
                .map(li => li.id);
            localStorage.setItem('openMenus', JSON.stringify(currentlyOpen));
        });
    });

    // --- 3. ФИКС ДЛЯ ВЫПАДАЮЩЕГО СПИСКА ЯЗЫКОВ ---
    // Сбрасываем кэш формы при загрузке, чтобы селект всегда был актуальным
    const langForm = document.getElementById('lang-form');
    if (langForm) {
        langForm.reset();
    }
});




