document.addEventListener('DOMContentLoaded', () => {
    const dataContainer = document.getElementById('booking-data');
    if (!dataContainer) return;

    const apiSlotsUrl = dataContainer.getAttribute('data-slots-url');
    const apiConfirmUrl = dataContainer.getAttribute('data-confirm-url');
    const csrfToken = dataContainer.getAttribute('data-csrf');

    const serviceSelect = document.getElementById('service-select');
    const providerSelect = document.getElementById('provider-select');
    const dateInput = document.getElementById('booking-date');
    const slotsContainer = document.getElementById('slots-container');
    
    const slotsModeContainer = document.getElementById('slots-mode-container');
    const timeSlotsDiv = document.getElementById('time-slots');
    
    const exactTimeModeContainer = document.getElementById('exact-time-mode-container');
    const freeBlocksList = document.getElementById('free-blocks-list');
    const exactTimeStart = document.getElementById('exact-time-start');
    const exactTimeEnd = document.getElementById('exact-time-end');

    const summaryBlock = document.getElementById('booking-summary');
    const summaryCountRow = document.getElementById('summary-slots-row');
    const summaryCount = document.getElementById('summary-count');
    const summaryExactRow = document.getElementById('summary-exact-row');
    const summaryExactTime = document.getElementById('summary-exact-time');
    const summaryPriceContainer = document.getElementById('summary-price-container');
    const confirmBtn = document.getElementById('confirm-booking-btn');

    let selectedSlots = [];
    let currentServicePrice = 0;
    let currentBookingType = 'slots';
    
    // Сохраняем исходную валюту при загрузке страницы
    let sellerCurrency = '';
    const currencyEl = document.getElementById('summary-currency');
    if (currencyEl) {
        sellerCurrency = currencyEl.innerText;
    }

    function updateImagePreview(selectElement, containerId, imageId) {
        const selectedOption = selectElement.options[selectElement.selectedIndex];
        const imageUrl = selectedOption.getAttribute('data-image');
        const container = document.getElementById(containerId);
        const image = document.getElementById(imageId);

        if (imageUrl && imageUrl.trim() !== '') {
            image.src = imageUrl;
            container.classList.remove('hidden');
        } else {
            container.classList.add('hidden');
        }
    }

    // --- ЛОГИКА ФИЛЬТРАЦИИ ИСПОЛНИТЕЛЕЙ ---
    serviceSelect.addEventListener('change', () => {
        updateImagePreview(serviceSelect, 'service-image-container', 'service-image');
        
        const selectedOption = serviceSelect.options[serviceSelect.selectedIndex];
        const allowedProvidersStr = selectedOption.getAttribute('data-providers');
        const allowedProviders = allowedProvidersStr ? allowedProvidersStr.split(',') : [];

        // Перебираем всех мастеров и скрываем тех, кто не привязан к услуге
        Array.from(providerSelect.options).forEach(option => {
            if (option.value === "") {
                option.style.display = 'block'; // Всегда показываем опцию "Любой свободный"
            } else if (allowedProviders.includes(option.value)) {
                option.style.display = 'block';
            } else {
                option.style.display = 'none';
            }
        });

        // Если выбранный мастер был скрыт, сбрасываем выбор
        if (providerSelect.value !== "" && !allowedProviders.includes(providerSelect.value)) {
            providerSelect.value = "";
            updateImagePreview(providerSelect, 'provider-image-container', 'provider-image');
        }
        
        fetchAvailability();
    });

    providerSelect.addEventListener('change', () => {
        updateImagePreview(providerSelect, 'provider-image-container', 'provider-image');
        fetchAvailability();
    });
    
    dateInput.addEventListener('change', fetchAvailability);

    async function fetchAvailability() {
        const serviceId = serviceSelect.value;
        const providerId = providerSelect.value;
        const dateVal = dateInput.value;

        selectedSlots = [];
        exactTimeStart.value = '';
        exactTimeEnd.innerHTML = '<option value="">-- : --</option>';
        exactTimeEnd.disabled = true;
        updateSummary();

        if (!serviceId || !dateVal) {
            slotsContainer.classList.add('hidden');
            return;
        }

        const selectedOption = serviceSelect.options[serviceSelect.selectedIndex];
        currentServicePrice = parseFloat(selectedOption.getAttribute('data-price')) || 0;

        try {
            slotsContainer.classList.remove('hidden');
            timeSlotsDiv.innerHTML = '<p>Loading...</p>';
            freeBlocksList.innerHTML = '<p>Loading...</p>';
            
            const response = await fetch(`${apiSlotsUrl}?service_id=${serviceId}&provider_id=${providerId}&date=${dateVal}`);
            const data = await response.json();

            if (data.error) {
                timeSlotsDiv.innerHTML = `<p style="color: red;">${data.error}</p>`;
                return;
            }

            currentBookingType = data.booking_type;

            if (currentBookingType === 'slots') {
                slotsModeContainer.classList.remove('hidden');
                exactTimeModeContainer.classList.add('hidden');
                renderSlots(data.slots);
            } else if (currentBookingType === 'exact_time') {
                slotsModeContainer.classList.add('hidden');
                exactTimeModeContainer.classList.remove('hidden');
                renderFreeBlocks(data.free_blocks);
            }

        } catch (error) {
            console.error('Error fetching availability:', error);
        }
    }

    function renderSlots(slots) {
        timeSlotsDiv.innerHTML = '';
        if (!slots || slots.length === 0) {
            timeSlotsDiv.innerHTML = '<p>No available slots on this date.</p>';
            return;
        }

        slots.forEach(slot => {
            const btn = document.createElement('button');
            btn.className = 'slot-btn';
            btn.innerText = slot.time;
            btn.dataset.datetime = slot.datetime;
            
            if (slot.is_booked) {
                btn.classList.add('booked');
                btn.disabled = true;
            } else {
                btn.addEventListener('click', () => toggleSlot(btn, slot.datetime));
            }
            timeSlotsDiv.appendChild(btn);
        });
    }

    function toggleSlot(btn, datetime) {
        const index = selectedSlots.indexOf(datetime);
        if (index > -1) {
            selectedSlots.splice(index, 1);
            btn.classList.remove('selected');
        } else {
            selectedSlots.push(datetime);
            btn.classList.add('selected');
        }
        selectedSlots.sort();
        updateSummary();
    }

    // --- ЛОГИКА ГЕНЕРАЦИИ СЕТКИ 15 МИНУТ ДЛЯ ТОЧНОГО ВРЕМЕНИ ---
    function renderFreeBlocks(blocks) {
        freeBlocksList.innerHTML = '';
        exactTimeStart.innerHTML = '<option value="">-- : --</option>';
        exactTimeEnd.innerHTML = '<option value="">-- : --</option>';
        exactTimeEnd.disabled = true;

        if (!blocks || blocks.length === 0) {
            freeBlocksList.innerHTML = '<li>No free time available on this date.</li>';
            exactTimeStart.disabled = true;
            return;
        }

        exactTimeStart.disabled = false;
        blocks.forEach(block => {
            const li = document.createElement('li');
            li.innerText = `${block.start_time} - ${block.end_time}`;
            freeBlocksList.appendChild(li);

            // Заполняем список возможного времени начала с шагом 15 минут
            let current = new Date(block.start_datetime);
            const end = new Date(block.end_datetime);

            while (current < end) {
                const option = document.createElement('option');
                option.value = current.toISOString();
                
                let hours = current.getHours().toString().padStart(2, '0');
                let mins = current.getMinutes().toString().padStart(2, '0');
                option.text = `${hours}:${mins}`;
                
                option.dataset.blockEnd = block.end_datetime;
                exactTimeStart.appendChild(option);

                current.setMinutes(current.getMinutes() + 15);
            }
        });
    }

    // Обработка выбора времени начала (заполняем список времени окончания)
    exactTimeStart.addEventListener('change', function() {
        exactTimeEnd.innerHTML = '<option value="">-- : --</option>';
        
        if (!this.value) {
            exactTimeEnd.disabled = true;
            updateSummary();
            return;
        }

        exactTimeEnd.disabled = false;
        const selectedOption = this.options[this.selectedIndex];
        
        let current = new Date(this.value);
        current.setMinutes(current.getMinutes() + 15); // Окончание минимум через 15 минут
        const maxEnd = new Date(selectedOption.dataset.blockEnd);

        // Генерируем опции до конца доступного свободного блока
        while (current <= maxEnd) {
            const option = document.createElement('option');
            option.value = current.toISOString();
            
            let hours = current.getHours().toString().padStart(2, '0');
            let mins = current.getMinutes().toString().padStart(2, '0');
            option.text = `${hours}:${mins}`;
            
            exactTimeEnd.appendChild(option);
            current.setMinutes(current.getMinutes() + 15);
        }
        updateSummary();
    });

    exactTimeEnd.addEventListener('change', updateSummary);

    // --- ОБНОВЛЕНИЕ БЛОКА ИТОГОВ И ПРОВЕРКА ЦЕНЫ ---
    function updateSummary() {
        let isReadyToBook = false;

        if (currentBookingType === 'slots') {
            if (selectedSlots.length > 0) {
                isReadyToBook = true;
                summaryCountRow.classList.remove('hidden');
                summaryExactRow.classList.add('hidden');
                summaryCount.innerText = selectedSlots.length;
                
                if (currentServicePrice > 0) {
                    summaryPriceContainer.innerHTML = `<span id="summary-currency">${sellerCurrency}</span> <span id="summary-price">${(selectedSlots.length * currentServicePrice).toFixed(2)}</span>`;
                } else {
                    summaryPriceContainer.innerText = "Price not specified, payment upon service completion";
                }
            }
        } else if (currentBookingType === 'exact_time') {
            const startVal = exactTimeStart.value;
            const endVal = exactTimeEnd.value;
            
            if (startVal && endVal) {
                isReadyToBook = true;
                summaryCountRow.classList.add('hidden');
                summaryExactRow.classList.remove('hidden');
                
                const startObj = new Date(startVal);
                const endObj = new Date(endVal);
                
                const startStr = `${startObj.getHours().toString().padStart(2, '0')}:${startObj.getMinutes().toString().padStart(2, '0')}`;
                const endStr = `${endObj.getHours().toString().padStart(2, '0')}:${endObj.getMinutes().toString().padStart(2, '0')}`;
                
                summaryExactTime.innerText = `${startStr} - ${endStr}`;
                
                // Считаем количество 15-минутных отрезков для расчета цены
                const diffMs = endObj - startObj;
                const diffMins = Math.round(diffMs / 60000);
                const blocksCount = diffMins / 15;
                
                if (currentServicePrice > 0) {
                    summaryPriceContainer.innerHTML = `<span id="summary-currency">${sellerCurrency}</span> <span id="summary-price">${(blocksCount * currentServicePrice).toFixed(2)}</span>`;
                } else {
                    summaryPriceContainer.innerText = "Price not specified, payment upon service completion";
                }
            }
        }

        if (isReadyToBook) {
            summaryBlock.classList.remove('hidden');
        } else {
            summaryBlock.classList.add('hidden');
        }
    }

    confirmBtn.addEventListener('click', async () => {
        confirmBtn.disabled = true;
        confirmBtn.innerText = 'PROCESSING...';

        const serviceId = serviceSelect.value;
        const providerId = providerSelect.value;
        const comment = document.getElementById('customer-comment').value;

        const payload = {
            service_id: serviceId,
            provider_id: providerId,
            comment: comment
        };

        if (currentBookingType === 'slots') {
            payload.slots = selectedSlots;
        } else if (currentBookingType === 'exact_time') {
            // Передаем на сервер точное время начала и окончания
            payload.exact_start = exactTimeStart.value;
            payload.exact_end = exactTimeEnd.value;
        }

        try {
            const response = await fetch(apiConfirmUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.status === 'success') {
                alert(data.message);
                window.location.reload();
            } else {
                alert(data.message);
                confirmBtn.disabled = false;
                confirmBtn.innerText = 'CONFIRM BOOKING';
            }
        } catch (error) {
            alert('Error processing booking.');
            console.error(error);
            confirmBtn.disabled = false;
            confirmBtn.innerText = 'CONFIRM BOOKING';
        }
    });
});