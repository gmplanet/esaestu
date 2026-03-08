document.addEventListener('DOMContentLoaded', function() {
    const burger = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar-left');

    // --- 1. ЛОГИКА БУРГЕРА (МОБИЛЬНАЯ) ---
    if (burger && sidebar) {

        // БАГ ИСПРАВЛЕН: оверлей через CSS ::after нельзя поймать в JS —
        // клики по нему попадают на sidebar, поэтому sidebar.contains(e.target)
        // всегда true и меню не закрывалось по клику на затемнение.
        // Решение: создаём настоящий DOM-элемент оверлея.
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);

        function openSidebar() {
            sidebar.classList.add('mobile-open');
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden'; // блокируем скролл фона
        }

        function closeSidebar() {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
            document.body.style.overflow = ''; // возвращаем скролл
        }

        burger.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.contains('mobile-open') ? closeSidebar() : openSidebar();
        });

        // Клик по оверлею — закрыть меню
        overlay.addEventListener('click', closeSidebar);

        // Клик по ссылке внутри меню — закрыть меню (для навигации)
        sidebar.addEventListener('click', (e) => {
            if (e.target.tagName === 'A' && !e.target.closest('.js-menu-toggle')) {
                closeSidebar();
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
                .map(li => li.id)
                .filter(Boolean); // игнорируем элементы без id
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