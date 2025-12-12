// Глобальные переменные
let socket;
let widget;
let isConnected = false;

console.log('📜 app_new.js загружен');

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, начинаем инициализацию...');
    initializeSocket();
    loadInitialData();
    setupEventListeners();
    console.log('Инициализация завершена');
});

// Инициализация WebSocket соединения
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        isConnected = true;
        updateConnectionStatus(true);
        showToast('Подключено к серверу', 'success');
    });
    
    socket.on('disconnect', function() {
        isConnected = false;
        updateConnectionStatus(false);
        showToast('Отключено от сервера', 'error');
    });
    
    socket.on('trade_executed', function(data) {
        let actionText = '';
        switch(data.action) {
            case 'opened':
                actionText = `Открыта позиция: ${data.symbol} ${data.side} ${data.qty}`;
                break;
            case 'closed':
                actionText = `Закрыта позиция: ${data.symbol} ${data.side} ${data.qty}`;
                break;
            case 'reversed':
                actionText = `Разворот позиции: ${data.symbol} ${data.side} ${data.qty}`;
                break;
            default:
                actionText = `Сделка: ${data.symbol} ${data.side} ${data.qty}`;
        }
        showToast(actionText, 'success');
        updateRecentTrades(data);
        loadPositions();
    });
    
    socket.on('price_update', function(data) {
        updatePriceDisplay(data);
    });
    
    socket.on('error', function(data) {
        showToast(`Ошибка: ${data.message}`, 'error');
    });
    
    // Обработка сигналов
    socket.on('signal_generated', function(data) {
        addSignal({
            symbol: data.symbol,
            type: data.type,
            strategy: data.strategy,
            status: 'pending',
            reason: data.reason || ''
        });
    });
    
    socket.on('signal_processed', function(data) {
        addSignal({
            symbol: data.symbol,
            type: data.type,
            strategy: data.strategy,
            status: 'processed',
            reason: data.reason || ''
        });
    });
    
    socket.on('signal_rejected', function(data) {
        addSignal({
            symbol: data.symbol,
            type: data.type,
            strategy: data.strategy,
            status: 'rejected',
            reason: data.reason || ''
        });
    });
    
    socket.on('signal_error', function(data) {
        addSignal({
            symbol: data.symbol,
            type: data.type,
            strategy: data.strategy,
            status: 'error',
            reason: data.reason || ''
        });
    });
}

// Инициализация TradingView графика
function initializeChart() {
    console.log('Инициализируем TradingView график...');
    
    // Загружаем TradingView скрипт если еще не загружен
    if (typeof TradingView === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://s3.tradingview.com/tv.js';
        script.onload = function() {
            console.log('TradingView скрипт загружен');
            createTradingViewWidget();
        };
        script.onerror = function() {
            console.error('Ошибка загрузки TradingView скрипта');
            showToast('Ошибка загрузки TradingView', 'error');
        };
        document.head.appendChild(script);
    } else {
        createTradingViewWidget();
    }
}

function createTradingViewWidget() {
    const container = document.getElementById('tradingview-widget');
    if (!container) {
        console.error('TradingView контейнер не найден');
        return;
    }
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    // Получаем текущие настройки
    const symbol = document.getElementById('chartSymbol').value || 'BTCUSDT';
    const interval = document.getElementById('chartInterval').value || '15';
    const theme = document.getElementById('chartTheme').value || 'dark';
    
    try {
        widget = new TradingView.widget({
            "width": "100%",
            "height": "100%",
            "symbol": `BINANCE:${symbol}`,
            "interval": interval,
            "timezone": "Europe/Moscow",
            "theme": theme,
            "style": "1",
            "locale": "ru",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": true,
            "container_id": "tradingview-widget",
            "studies": [
                "MASimple@tv-basicstudies",
                "RSI@tv-basicstudies",
                "MACD@tv-basicstudies"
            ],
            "show_popup_button": true,
            "popup_width": "1000",
            "popup_height": "650",
            "save_image": true,
            "details": true,
            "hotlist": true,
            "calendar": true,
            "news": [
                "headlines"
            ]
        });
        
        console.log('TradingView виджет создан успешно');
        
    } catch (error) {
        console.error('Ошибка создания TradingView виджета:', error);
        showToast('Ошибка создания графика', 'error');
    }
}

// Загрузка начальных данных
function loadInitialData() {
    console.log('Загрузка начальных данных...');
    loadBalance();
    loadAllBalances();
    loadPositions();
    loadTradingStatus();
    loadTradingPairs();
    loadPopularPairs();
    
    // Проверяем сохраненные стратегии перед загрузкой
    checkSavedStrategies();
    
    loadStrategies();
    loadGlobalSettings();

    // Периодическое обновление открытых позиций на дашборде
    if (window.__positionsRefreshTimer) {
        clearInterval(window.__positionsRefreshTimer);
    }
    window.__positionsRefreshTimer = setInterval(() => {
        loadPositions();
    }, 15000); // каждые 15 секунд
}

// Загрузка глобальных настроек из localStorage
function loadGlobalSettings() {
    const saved = localStorage.getItem('globalTradingSettings');
    if (saved) {
        try {
            const settings = JSON.parse(saved);
            
            const globalTactic = document.getElementById('globalTactic');
            const tradingTimeframe = document.getElementById('tradingTimeframe');
            
            if (globalTactic && settings.globalTactic) {
                globalTactic.value = settings.globalTactic;
            }
            
            if (tradingTimeframe && settings.tradingTimeframe) {
                tradingTimeframe.value = settings.tradingTimeframe;
            }
            
            console.log('Глобальные настройки загружены:', settings);
        } catch (error) {
            console.error('Ошибка загрузки глобальных настроек:', error);
        }
    }
}

// Сохранение глобальных настроек в localStorage
function saveGlobalSettings() {
    const globalTactic = document.getElementById('globalTactic');
    const tradingTimeframe = document.getElementById('tradingTimeframe');
    
    const settings = {
        globalTactic: globalTactic ? globalTactic.value : 'ott',
        tradingTimeframe: tradingTimeframe ? tradingTimeframe.value : '15'
    };
    
    localStorage.setItem('globalTradingSettings', JSON.stringify(settings));
    console.log('Глобальные настройки сохранены:', settings);
}

// Настройка обработчиков событий
function setupEventListeners() {
    console.log('🔧 Настройка обработчиков событий...');
    
    // Кнопки управления торговлей
    const startBtn = document.getElementById('startTrading');
    const stopBtn = document.getElementById('stopTrading');
    
    console.log('Кнопка startTrading найдена:', startBtn);
    console.log('Кнопка stopTrading найдена:', stopBtn);
    
    if (startBtn) {
        startBtn.addEventListener('click', startTrading);
        console.log('Обработчик для startTrading добавлен');
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', stopTrading);
        console.log('Обработчик для stopTrading добавлен');
    }
    
    // Форма ручного ордера
    document.getElementById('manualOrderForm').addEventListener('submit', placeManualOrder);
    document.getElementById('orderType').addEventListener('change', togglePriceField);
    
    // Форма бэктеста
    const backtestForm = document.getElementById('backtestForm');
    if (backtestForm) {
        console.log('✅ Форма бэктеста найдена, добавляем обработчик');
        
        // Удаляем старые обработчики, если они есть
        backtestForm.removeEventListener('submit', runBacktest);
        
        // Добавляем новый обработчик
        backtestForm.addEventListener('submit', function(e) {
            console.log('🔄 Форма бэктеста отправлена, предотвращаем стандартную отправку');
            e.preventDefault(); // Предотвращаем стандартную отправку формы
            e.stopPropagation(); // Останавливаем всплытие события
            e.stopImmediatePropagation(); // Останавливаем все остальные обработчики
            runBacktest(e);
            return false; // Дополнительная защита
        });
        
            // Также добавляем обработчик на кнопку
    const runBacktestBtn = document.getElementById('runBacktestBtn');
    console.log('🔍 Ищем кнопку бектеста:', runBacktestBtn);
    if (runBacktestBtn) {
        console.log('✅ Кнопка бектеста найдена, добавляем обработчик');
        runBacktestBtn.addEventListener('click', function(e) {
            console.log('🔄 Кнопка бэктеста нажата');
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            // Запускаем бектест напрямую
            runBacktest();
            
            return false;
        });
        console.log('✅ Обработчик для кнопки бектеста добавлен');
    } else {
        console.error('❌ Кнопка бектеста не найдена!');
    }
    } else {
        console.warn('⚠️ Форма бэктеста не найдена');
    }
    
    // Обновление TradingView графика
    document.getElementById('updateChart').addEventListener('click', function() {
        createTradingViewWidget();
    });
    document.getElementById('chartSymbol').addEventListener('change', function() {
        const symbol = this.value;
        if (symbol && widget) {
            widget.setSymbol(`BINANCE:${symbol}`, document.getElementById('chartInterval').value);
        }
    });
    document.getElementById('chartInterval').addEventListener('change', function() {
        const symbol = document.getElementById('chartSymbol').value;
        const interval = this.value;
        if (symbol && widget) {
            widget.setSymbol(`BINANCE:${symbol}`, interval);
        }
    });
    document.getElementById('chartTheme').addEventListener('change', function() {
        createTradingViewWidget(); // Пересоздаем виджет для смены темы
    });
    
    // Кнопка полноэкранного режима
    document.getElementById('fullscreenBtn').addEventListener('click', function() {
        if (widget) {
            widget.fullscreen();
        }
    });
    
    // Кнопки обновления торговых пар
    document.getElementById('refreshSymbols').addEventListener('click', loadTradingPairs);
    document.getElementById('refreshChartSymbols').addEventListener('click', loadTradingPairs);
    document.getElementById('refreshOrderSymbols').addEventListener('click', loadTradingPairs);
    document.getElementById('refreshTradingSymbols').addEventListener('click', loadPopularPairs);
    
    // Автоматическое добавление стратегий при выборе символов
    const tradingSymbolsSelect = document.getElementById('tradingSymbols');
    if (tradingSymbolsSelect) {
        tradingSymbolsSelect.addEventListener('change', function() {
            setTimeout(() => {
                addDefaultStrategiesForSelectedSymbols();
            }, 100);
        });
    }
    
    // Сохранение глобальных настроек при изменении
    const globalTactic = document.getElementById('globalTactic');
    const tradingTimeframe = document.getElementById('tradingTimeframe');
    
    if (globalTactic) {
        globalTactic.addEventListener('change', saveGlobalSettings);
    }
    
    if (tradingTimeframe) {
        tradingTimeframe.addEventListener('change', saveGlobalSettings);
    }
    
    // Автоматическое сохранение стратегий при изменении в таблице
    const strategiesTable = document.getElementById('strategiesTable');
    if (strategiesTable) {
        strategiesTable.addEventListener('change', function(e) {
            if (e.target.matches('input, select')) {
                console.log('Изменение в таблице стратегий:', e.target.type || e.target.tagName, e.target.value);
                setTimeout(() => saveStrategies(), 100);
            }
        });
        
        strategiesTable.addEventListener('blur', function(e) {
            if (e.target.matches('input, select')) {
                console.log('Потеря фокуса в таблице стратегий:', e.target.type || e.target.tagName, e.target.value);
                setTimeout(() => saveStrategies(), 100);
            }
        }, true);
    }
    
    // Обработчик переключения вкладок
    const chartTab = document.getElementById('chart-tab');
    if (chartTab) {
        chartTab.addEventListener('click', function() {
            // Инициализируем TradingView график при переходе на вкладку
            setTimeout(() => {
                if (!widget) {
                    initializeChart();
                }
            }, 100);
        });
    }
}

// Загрузка баланса
async function loadBalance() {
    try {
        const response = await fetch('/api/balance');
        const data = await response.json();
        if (data.balance !== undefined) {
            document.getElementById('balance').textContent = `$${data.balance.toFixed(2)}`;
        }
    } catch (error) {
        console.error('Ошибка загрузки баланса:', error);
    }
}

// Загрузка всех балансов
async function loadAllBalances() {
    try {
        const response = await fetch('/api/balances');
        const balances = await response.json();
        const container = document.getElementById('allBalances');
        
        if (Object.keys(balances).length === 0) {
            container.innerHTML = '<p class="text-muted">Нет данных о балансах</p>';
            return;
        }
        
        let html = '<div class="table-responsive"><table class="table table-sm">';
        html += '<thead><tr><th>Монета</th><th>Баланс</th></tr></thead><tbody>';
        
        for (const [coin, amount] of Object.entries(balances)) {
            const numericAmount = parseFloat(amount) || 0;
            html += `<tr><td>${coin}</td><td>${numericAmount.toFixed(4)}</td></tr>`;
        }
        
        html += '</tbody></table></div>';
        container.innerHTML = html;
    } catch (error) {
        console.error('Ошибка загрузки балансов:', error);
    }
}

// Загрузка позиций
async function loadPositions() {
    try {
        const response = await fetch('/api/positions');
        const positions = await response.json();
        const tbody = document.querySelector('#positionsTable tbody');
        
        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">Нет открытых позиций</td></tr>';
            return;
        }
        
        let html = '';
        positions.forEach(pos => {
            const size = parseFloat(pos.size || 0);
            if (size > 0) {
                const pnl = parseFloat(pos.unrealisedPnl || 0);
                const pnlClass = pnl >= 0 ? 'text-success' : 'text-danger';
                const avgPrice = parseFloat(pos.avgPrice || 0) || 0;
                const markPrice = parseFloat(pos.markPrice || pos.markPrice || 0) || 0;
                const leverage = parseFloat(pos.leverage || 0) || 0;
                const side = String(pos.side || '').toUpperCase();
                const value = avgPrice * size;
                const roe = value > 0 && leverage > 0
                    ? ((pnl / (value / leverage)) * 100)
                    : 0;
                const entryTime = pos.updatedTime || pos.createdTime || pos.createdAt || null;
                const entryTimeStr = entryTime ? new Date(Number(entryTime)).toLocaleString() : '-';
                html += `
                    <tr>
                        <td>${pos.symbol}</td>
                        <td>${side}</td>
                        <td>${size}</td>
                        <td>$${avgPrice.toFixed(2)}</td>
                        <td>$${markPrice ? markPrice.toFixed(2) : '-'}</td>
                        <td class="${pnlClass}">$${pnl.toFixed(2)}</td>
                        <td class="${pnlClass}">${roe.toFixed(2)}%</td>
                        <td>${entryTimeStr}</td>
                    </tr>
                `;
            }
        });
        
        if (html === '') {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">Нет открытых позиций</td></tr>';
        } else {
            tbody.innerHTML = html;
        }
    } catch (error) {
        console.error('Ошибка загрузки позиций:', error);
    }
}

// Загрузка статуса торговли
async function loadTradingStatus() {
    try {
        const response = await fetch('/api/trading/status');
        const status = await response.json();
        
        const statusElement = document.getElementById('tradingStatus');
        if (status.is_trading) {
            statusElement.textContent = 'Активна';
            statusElement.className = 'text-success';
        } else {
            statusElement.textContent = 'Остановлена';
            statusElement.className = 'text-danger';
        }
    } catch (error) {
        console.error('Ошибка загрузки статуса:', error);
    }
}

// Загрузка торговых пар
async function loadTradingPairs() {
    try {
        console.log('Загружаем торговые пары...');
        
        const response = await fetch('/api/trading_pairs');
        const data = await response.json();
        
        if (data.popular && data.all) {
            // Обновляем селекты
            updateSymbolSelect('backtestSymbol', data.popular, data.all);
            updateSymbolSelect('chartSymbol', data.popular, data.all);
            updateSymbolSelect('orderSymbol', data.popular, data.all);
            
            console.log(`Загружено ${data.total_count} торговых пар`);
            showToast(`Загружено ${data.total_count} торговых пар`, 'success');
        } else {
            console.error('Ошибка загрузки торговых пар:', data);
            showToast('Ошибка загрузки торговых пар', 'error');
        }
    } catch (error) {
        console.error('Ошибка загрузки торговых пар:', error);
        showToast('Ошибка загрузки торговых пар', 'error');
    }
}

// Загрузка популярных пар
async function loadPopularPairs() {
    try {
        console.log('=== НАЧАЛО loadPopularPairs ===');
        const response = await fetch('/api/trading_pairs');
        const data = await response.json();
        console.log('Получены данные от API:', data);
        
        if (data.popular) {
            const symbolsSelect = document.getElementById('tradingSymbols');
            console.log('Селект tradingSymbols в loadPopularPairs:', symbolsSelect);
            
            if (symbolsSelect) {
                // Очищаем текущие опции
                symbolsSelect.innerHTML = '';
                console.log('Очистили селект');
                
                // Добавляем популярные пары
                data.popular.forEach((pair, index) => {
                    const option = document.createElement('option');
                    option.value = pair.symbol;
                    option.textContent = pair.symbol;
                    // Выбираем первые 3 пары по умолчанию
                    if (['BTCUSDT', 'ETHUSDT', 'SOLUSDT'].includes(pair.symbol)) {
                        option.selected = true;
                        console.log(`Выбрали пару: ${pair.symbol}`);
                    }
                    symbolsSelect.appendChild(option);
                    console.log(`Добавили опцию ${index + 1}: ${pair.symbol}`);
                });
                
                console.log(`Загружено ${data.popular.length} популярных пар в селект`);
                console.log('Финальное состояние селекта:', Array.from(symbolsSelect.options).map(opt => ({value: opt.value, selected: opt.selected, text: opt.textContent})));
            } else {
                console.error('Селект tradingSymbols не найден в loadPopularPairs!');
            }
            
            showToast(`Загружено ${data.popular.length} популярных пар`, 'success');
        } else {
            console.log('Нет данных о популярных парах');
        }
        console.log('=== КОНЕЦ loadPopularPairs ===');
    } catch (error) {
        console.error('Ошибка загрузки популярных пар:', error);
        showToast('Ошибка загрузки популярных пар', 'error');
    }
}

// Обновление селекта символов
function updateSymbolSelect(selectId, popularPairs, allPairs) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    select.innerHTML = '';
    
    // Добавляем популярные пары
    if (popularPairs && popularPairs.length > 0) {
        popularPairs.forEach(pair => {
            const option = document.createElement('option');
            option.value = pair.symbol;
            option.textContent = pair.symbol;
            select.appendChild(option);
        });
    }
    
    // Добавляем разделитель
    if (allPairs && allPairs.length > 0) {
        const separator = document.createElement('option');
        separator.disabled = true;
        separator.textContent = '──────────';
        select.appendChild(separator);
        
        // Добавляем все пары
        allPairs.forEach(pair => {
            const option = document.createElement('option');
            option.value = pair.symbol;
            option.textContent = pair.symbol;
            select.appendChild(option);
        });
    }
}

// Запуск торговли
async function startTrading() {
    try {
        const symbolsSelect = document.getElementById('tradingSymbols');
        console.log('Селект tradingSymbols найден:', symbolsSelect);
        
        if (!symbolsSelect) {
            console.error('Селект tradingSymbols не найден!');
            showToast('Ошибка: селект символов не найден', 'error');
            return;
        }
        
        // Получаем выбранные опции
        const selectedOptions = Array.from(symbolsSelect.selectedOptions);
        const symbols = selectedOptions.map(option => option.value);
        
        console.log('Все опции в селекте:', Array.from(symbolsSelect.options).map(opt => ({value: opt.value, selected: opt.selected, text: opt.textContent})));
        console.log('Выбранные символы:', symbols);
        console.log('Количество выбранных символов:', symbols.length);
        
        if (symbols.length === 0) {
            console.log('Не выбрано ни одного символа, показываем ошибку');
            showToast('Выберите хотя бы один символ', 'error');
            return;
        }
        
        // Получаем настройки стратегий для каждой пары
        const strategies = {};
        symbols.forEach(symbol => {
            strategies[symbol] = getStrategyForSymbol(symbol);
        });
        
        const config = {
            buy_leverage: parseInt(document.getElementById('buyLeverage').value),
            sell_leverage: parseInt(document.getElementById('sellLeverage').value),
            trade_balance_pct: parseFloat(document.getElementById('tradeBalancePct').value) / 100,
            stop_loss_pct: parseFloat(document.getElementById('stopLossPct').value) / 100,
            trade_interval_sec: parseInt(document.getElementById('tradeInterval').value),
            mode: document.getElementById('tradingMode').value,
            global_timeframe: document.getElementById('tradingTimeframe').value,
            strategies: strategies
        };
        
        // Обрабатываем тейк-профит
        const takeProfitPct = document.getElementById('takeProfitPct').value;
        if (takeProfitPct && takeProfitPct > 0) {
            config.take_profit_pct = parseFloat(takeProfitPct) / 100;
        }
        
        const response = await fetch('/api/trading/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbols: symbols,
                strategies: strategies,
                config: config
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showToast('Торговля запущена', 'success');
            loadTradingStatus();
        } else {
            showToast(`Ошибка: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Ошибка запуска торговли:', error);
        showToast('Ошибка запуска торговли', 'error');
    }
}

// Остановка торговли
async function stopTrading() {
    try {
        const response = await fetch('/api/trading/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showToast('Торговля остановлена', 'success');
            loadTradingStatus();
        } else {
            showToast(`Ошибка: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Ошибка остановки торговли:', error);
        showToast('Ошибка остановки торговли', 'error');
    }
}

// Размещение ручного ордера
async function placeManualOrder(event) {
    event.preventDefault();
    
    try {
        const formData = new FormData(event.target);
        const orderData = {
            symbol: formData.get('symbol'),
            side: formData.get('side'),
            qty: parseFloat(formData.get('qty')),
            order_type: formData.get('orderType'),
            price: formData.get('price') ? parseFloat(formData.get('price')) : 0,
            stop_loss: formData.get('stopLoss') ? parseFloat(formData.get('stopLoss')) : 0,
            take_profit: formData.get('takeProfit') ? parseFloat(formData.get('takeProfit')) : 0
        };
        
        const response = await fetch('/api/place_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showToast('Ордер размещен успешно', 'success');
            event.target.reset();
            loadPositions();
        } else {
            showToast(`Ошибка: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Ошибка размещения ордера:', error);
        showToast('Ошибка размещения ордера', 'error');
    }
}

// Запуск бэктеста
async function runBacktest(event) {
    console.log('🚀 Запуск бэктеста...');
    if (event) {
        event.preventDefault();
    }
    
    try {
        console.log('📋 Получаем данные формы...');
        const backtestForm = document.getElementById('backtestForm');
        const formData = new FormData(backtestForm);
        const backtestData = {
            symbol: formData.get('symbol'),
            interval: formData.get('interval'),
            days_back: parseInt(formData.get('daysBack')),
            leverage: parseInt(formData.get('leverage')),
            stop_loss_pct: parseFloat(formData.get('stopLossPct')),
            initial_balance: parseFloat(formData.get('initialBalance')),
            trade_size_pct: parseFloat(formData.get('tradeSizePct')),
            strategy_type: formData.get('strategyType')
        };
        
        // Обрабатываем тейк-профит
        const takeProfitPct = formData.get('takeProfitPct');
        if (takeProfitPct && takeProfitPct > 0) {
            backtestData.take_profit_pct = parseFloat(takeProfitPct);
        }
        
        const response = await fetch('/api/backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(backtestData)
        });
        
        const result = await response.json();
        
        console.log('📊 Получен результат от сервера:', result);
        
        if (result.trades !== undefined) {
            console.log('✅ Результат содержит trades, отображаем результаты');
            displayBacktestResults(result);
            showToast(`Бэктест завершен. ${result.total_trades} сделок, винрейт ${result.win_rate}%`, 'success');
        } else {
            console.log('❌ Результат не содержит trades, показываем ошибку');
            showToast(`Ошибка: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Ошибка бэктеста:', error);
        showToast('Ошибка выполнения бэктеста', 'error');
    }
}

// Отображение результатов бэктеста
function displayBacktestResults(result) {
    console.log('🎨 Начинаем отображение результатов бектеста');
    const container = document.getElementById('backtestResults');
    console.log('📦 Контейнер для результатов:', container);
    
    let html = `
        <div class="card">
            <div class="card-header">
                <h5>Результаты бэктеста</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6>Общая статистика</h6>
                        <ul class="list-unstyled">
                            <li><strong>Всего сделок:</strong> ${result.total_trades}</li>
                            <li><strong>Прибыльных:</strong> ${result.profitable_trades}</li>
                            <li><strong>Винрейт:</strong> ${result.win_rate}%</li>
                            <li><strong>Общая прибыль:</strong> ${result.total_profit_pct}% ($${result.total_profit_usd})</li>
                            <li><strong>Максимальная прибыль:</strong> ${result.max_profit}%</li>
                            <li><strong>Максимальный убыток:</strong> ${result.max_loss}%</li>
                            <li><strong>Средняя продолжительность:</strong> ${result.avg_duration}ч</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>Детализация</h6>
                        <ul class="list-unstyled">
                            <li><strong>По стоп-лоссу:</strong> ${result.stop_loss_trades}</li>
                            <li><strong>По тейк-профиту:</strong> ${result.take_profit_trades}</li>
                            <li><strong>По сигналу:</strong> ${result.signal_trades}</li>
                            <li><strong>Открытые позиции:</strong> ${result.open_positions}</li>
                        </ul>
                    </div>
                </div>
                <div class="mt-3">
                    <h6>Параметры</h6>
                    <small class="text-muted">
                        Символ: ${result.symbol} | Интервал: ${result.interval} | 
                        Плечо: ${result.leverage}x | Стоп-лосс: ${result.stop_loss_pct}% | 
                        Тейк-профит: ${result.take_profit_pct || 'Не задан'}% | 
                        Размер позиции: ${result.trade_size_pct}%
                    </small>
                </div>
            </div>
        </div>
    `;
    
    if (result.trades && result.trades.length > 0) {
        html += `
            <div class="card mt-3">
                <div class="card-header">
                    <h6>Детали сделок</h6>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Дата</th>
                                    <th>Тип</th>
                                    <th>Цена входа</th>
                                    <th>Цена выхода</th>
                                    <th>Прибыль %</th>
                                    <th>Прибыль $</th>
                                    <th>Причина выхода</th>
                                </tr>
                            </thead>
                            <tbody>
        `;
        
        result.trades.forEach(trade => {
            const profitClass = trade.profit_pct >= 0 ? 'text-success' : 'text-danger';
            html += `
                <tr>
                    <td>${new Date(trade.entry_time).toLocaleString()}</td>
                    <td>${trade.side}</td>
                    <td>$${trade.entry_price.toFixed(2)}</td>
                    <td>$${trade.exit_price.toFixed(2)}</td>
                    <td class="${profitClass}">${trade.profit_pct.toFixed(2)}%</td>
                    <td class="${profitClass}">$${trade.profit_usd.toFixed(2)}</td>
                    <td>${trade.exit_reason}</td>
                </tr>
            `;
        });
        
        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    console.log('📝 HTML для отображения:', html);
    console.log('📦 Устанавливаем innerHTML в контейнер');
    container.innerHTML = html;
    console.log('✅ HTML установлен, показываем уведомление');
    showToast('Бэктест завершен', 'success');
}

// Переключение поля цены
function togglePriceField() {
    const orderType = document.getElementById('orderType').value;
    const priceField = document.getElementById('priceField');
    const priceInput = document.getElementById('orderPrice');
    
    if (orderType === 'Limit') {
        priceField.style.display = 'block';
        priceInput.required = true;
    } else {
        priceField.style.display = 'none';
        priceInput.required = false;
    }
}

// Обновление статуса подключения
function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connectionStatus');
    const textElement = document.getElementById('connectionText');
    
    if (connected) {
        statusElement.className = 'status-indicator status-active';
        textElement.textContent = 'Подключено';
    } else {
        statusElement.className = 'status-indicator status-inactive';
        textElement.textContent = 'Отключено';
    }
}

// Обновление последних сделок
function updateRecentTrades(tradeData) {
    const container = document.getElementById('recentTrades');
    const time = new Date(tradeData.timestamp * 1000).toLocaleString();
    
    let html = `
        <div class="alert alert-success">
            <strong>${tradeData.symbol}</strong> ${tradeData.side} ${tradeData.qty}
            <br><small>${time}</small>
        </div>
    `;
    
    container.innerHTML = html + container.innerHTML;
    
    // Ограничиваем количество отображаемых сделок
    const alerts = container.querySelectorAll('.alert');
    if (alerts.length > 5) {
        alerts[alerts.length - 1].remove();
    }
}

// Обновление отображения цены
function updatePriceDisplay(data) {
    // Можно добавить обновление цены в реальном времени
    console.log('Price update:', data);
}

// Показ уведомлений
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = document.getElementById('toastBody');
    
    toastBody.textContent = message;
    
    // Устанавливаем цвет в зависимости от типа
    toast.className = `toast ${type === 'error' ? 'bg-danger' : type === 'success' ? 'bg-success' : 'bg-info'}`;
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Функция переключения отображения всех сделок
function toggleAllTrades() {
    const hiddenRows = document.querySelectorAll('.hidden-trade');
    const toggleButton = document.querySelector('button[onclick="toggleAllTrades()"]');
    const statusSpan = document.querySelector('#tradesTable').previousElementSibling.querySelector('span');
    
    if (hiddenRows.length > 0) {
        const isHidden = hiddenRows[0].style.display === 'none';
        
        hiddenRows.forEach(row => {
            row.style.display = isHidden ? 'table-row' : 'none';
        });
        
        if (toggleButton) {
            toggleButton.textContent = isHidden ? 'Скрыть старые сделки' : 'Показать все сделки';
        }
        
        if (statusSpan && window.allTradesData) {
            const totalTrades = window.allTradesData.length;
            const visibleCount = isHidden ? totalTrades : Math.min(15, totalTrades);
            statusSpan.textContent = `Показано ${visibleCount} из ${totalTrades} сделок`;
        }
    }
}

// Периодическое обновление данных
setInterval(() => {
    if (isConnected) {
        loadBalance();
        loadPositions();
        loadTradingStatus();
    }
}, 30000); // Обновляем каждые 30 секунд

// ===== СИСТЕМА СИГНАЛОВ =====

// Добавление сигнала в реальном времени
function addSignal(signal) {
    const container = document.getElementById('signalsContainer');
    const time = new Date().toLocaleTimeString();
    
    let statusClass = '';
    let statusText = '';
    let icon = '';
    
    switch(signal.status) {
        case 'pending':
            statusClass = 'warning';
            statusText = 'Ожидает';
            icon = '⏳';
            break;
        case 'processed':
            statusClass = 'success';
            statusText = 'Обработан';
            icon = '✅';
            break;
        case 'rejected':
            statusClass = 'danger';
            statusText = 'Отклонен';
            icon = '❌';
            break;
        case 'error':
            statusClass = 'danger';
            statusText = 'Ошибка';
            icon = '⚠️';
            break;
        default:
            statusClass = 'info';
            statusText = 'Новый';
            icon = '📊';
    }
    
    const signalHtml = `
        <div class="alert alert-${statusClass} alert-dismissible fade show" role="alert">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <strong>${icon} ${signal.symbol}</strong> ${signal.type.toUpperCase()}
                    <br><small class="text-muted">${signal.strategy} | ${time}</small>
                    ${signal.reason ? `<br><small class="text-muted">Причина: ${signal.reason}</small>` : ''}
                </div>
                <div class="text-end">
                    <span class="badge bg-${statusClass}">${statusText}</span>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            </div>
        </div>
    `;
    
    // Добавляем в начало
    container.insertAdjacentHTML('afterbegin', signalHtml);
    
    // Ограничиваем количество сигналов
    const alerts = container.querySelectorAll('.alert');
    if (alerts.length > 20) {
        alerts[alerts.length - 1].remove();
    }
}

// Очистка сигналов
function clearSignals() {
    const container = document.getElementById('signalsContainer');
    container.innerHTML = '<p class="text-muted">Ожидание сигналов...</p>';
}

// ===== СИСТЕМА СТРАТЕГИЙ =====

// Добавление строки стратегии
function addStrategyRow(symbol = '', tactic = 'ott', timeframe = '15', enabled = true, stopLoss = 20, takeProfit = '', leverage = 10) {
    const tbody = document.getElementById('strategiesTableBody');
    if (!tbody) {
        console.error('Таблица стратегий не найдена');
        return;
    }
    
    const rowId = 'strategy_' + Date.now();
    
    // Проверяем, не существует ли уже стратегия для этого символа
    const existingRows = tbody.querySelectorAll('tr');
    for (let row of existingRows) {
        const symbolSelect = row.querySelector('select');
        if (symbolSelect && symbolSelect.value === symbol) {
            console.log(`Стратегия для ${symbol} уже существует`);
            return;
        }
    }
    
    const row = `
        <tr id="${rowId}">
            <td>
                <select class="form-select form-select-sm" onchange="updateStrategy('${rowId}', 'symbol', this.value)">
                    <option value="">Выберите пару</option>
                    <option value="BTCUSDT" ${symbol === 'BTCUSDT' ? 'selected' : ''}>BTCUSDT</option>
                    <option value="ETHUSDT" ${symbol === 'ETHUSDT' ? 'selected' : ''}>ETHUSDT</option>
                    <option value="SOLUSDT" ${symbol === 'SOLUSDT' ? 'selected' : ''}>SOLUSDT</option>
                    <option value="ADAUSDT" ${symbol === 'ADAUSDT' ? 'selected' : ''}>ADAUSDT</option>
                    <option value="DOTUSDT" ${symbol === 'DOTUSDT' ? 'selected' : ''}>DOTUSDT</option>
                    <option value="LINKUSDT" ${symbol === 'LINKUSDT' ? 'selected' : ''}>LINKUSDT</option>
                    <option value="MATICUSDT" ${symbol === 'MATICUSDT' ? 'selected' : ''}>MATICUSDT</option>
                    <option value="AVAXUSDT" ${symbol === 'AVAXUSDT' ? 'selected' : ''}>AVAXUSDT</option>
                </select>
            </td>
            <td>
                <select class="form-select form-select-sm" onchange="updateStrategy('${rowId}', 'tactic', this.value)">
                    <option value="ghost" ${tactic === 'ghost' ? 'selected' : ''}>Ghost</option>
                    <option value="ott" ${tactic === 'ott' ? 'selected' : ''}>OTT</option>
                    <option value="combined" ${tactic === 'combined' ? 'selected' : ''}>Combined</option>
                </select>
            </td>
            <td>
                <select class="form-select form-select-sm" onchange="updateStrategy('${rowId}', 'timeframe', this.value)">
                    <option value="1" ${timeframe === '1' ? 'selected' : ''}>1m</option>
                    <option value="5" ${timeframe === '5' ? 'selected' : ''}>5m</option>
                    <option value="15" ${timeframe === '15' ? 'selected' : ''}>15m</option>
                    <option value="30" ${timeframe === '30' ? 'selected' : ''}>30m</option>
                    <option value="60" ${timeframe === '60' ? 'selected' : ''}>1h</option>
                    <option value="240" ${timeframe === '240' ? 'selected' : ''}>4h</option>
                    <option value="1D" ${timeframe === '1D' ? 'selected' : ''}>1D</option>
                </select>
            </td>
            <td>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" ${enabled ? 'checked' : ''} 
                           onchange="updateStrategy('${rowId}', 'enabled', this.checked)">
                </div>
            </td>
            <td>
                <input type="number" class="form-control form-control-sm" value="${stopLoss}" 
                       onchange="updateStrategy('${rowId}', 'stopLoss', this.value)" onblur="updateStrategy('${rowId}', 'stopLoss', this.value)">
            </td>
            <td>
                <input type="number" class="form-control form-control-sm" value="${takeProfit}" 
                       placeholder="Не задан" onchange="updateStrategy('${rowId}', 'takeProfit', this.value)" onblur="updateStrategy('${rowId}', 'takeProfit', this.value)">
            </td>
            <td>
                <input type="number" class="form-control form-control-sm" value="${leverage}" 
                       onchange="updateStrategy('${rowId}', 'leverage', this.value)" onblur="updateStrategy('${rowId}', 'leverage', this.value)">
            </td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="removeStrategy('${rowId}')">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `;
    
    tbody.insertAdjacentHTML('beforeend', row);
    console.log(`Добавлена стратегия для ${symbol}:`, { tactic, timeframe, enabled, stopLoss, takeProfit, leverage });
    
    // Добавляем обработчики событий для автоматического сохранения
    setTimeout(() => {
        addRowEventListeners(rowId);
    }, 100);
    
    saveStrategies();
}

// Добавление обработчиков событий для строки стратегии
function addRowEventListeners(rowId) {
    const row = document.getElementById(rowId);
    if (!row) return;
    
    // Добавляем обработчики для всех полей ввода
    const inputs = row.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', () => {
            console.log(`Изменение в строке ${rowId}:`, input.name || input.type, input.value);
            saveStrategies();
        });
        
        input.addEventListener('blur', () => {
            console.log(`Потеря фокуса в строке ${rowId}:`, input.name || input.type, input.value);
            saveStrategies();
        });
    });
}

// Обновление стратегии
function updateStrategy(rowId, field, value) {
    const row = document.getElementById(rowId);
    if (!row) return;
    
    console.log(`Обновление стратегии ${rowId}: ${field} = ${value}`);
    
    // Обновляем данные в строке
    row.dataset[field] = value;
    
    // Сохраняем изменения
    saveStrategies();
}

// Удаление стратегии
function removeStrategy(rowId) {
    const row = document.getElementById(rowId);
    if (row) {
        row.remove();
        saveStrategies();
    }
}

// Очистка всех стратегий
function clearAllStrategies() {
    if (confirm('Вы уверены, что хотите удалить все стратегии?')) {
        const tbody = document.getElementById('strategiesTableBody');
        if (tbody) {
            tbody.innerHTML = '';
            localStorage.removeItem('tradingStrategies');
            console.log('Все стратегии удалены');
            showToast('Все стратегии удалены', 'success');
        }
    }
}

// Принудительное сохранение стратегий
function forceSaveStrategies() {
    console.log('Принудительное сохранение стратегий...');
    saveStrategies();
    showToast('Стратегии сохранены', 'success');
}

// Проверка сохраненных стратегий
function checkSavedStrategies() {
    const saved = localStorage.getItem('tradingStrategies');
    console.log('=== ПРОВЕРКА СОХРАНЕННЫХ СТРАТЕГИЙ ===');
    console.log('localStorage данные:', saved);
    
    if (saved) {
        try {
            const strategies = JSON.parse(saved);
            console.log('Парсинг успешен:', strategies);
            console.log('Количество стратегий:', strategies.length);
        } catch (error) {
            console.error('Ошибка парсинга:', error);
        }
    } else {
        console.log('Нет сохраненных данных');
    }
    
    console.log('=== КОНЕЦ ПРОВЕРКИ ===');
}

// Сохранение стратегий в localStorage
function saveStrategies() {
    console.log('=== НАЧАЛО СОХРАНЕНИЯ СТРАТЕГИЙ ===');
    
    const strategies = [];
    const rows = document.querySelectorAll('#strategiesTableBody tr');
    console.log(`Найдено строк в таблице: ${rows.length}`);
    
    rows.forEach((row, index) => {
        const symbolSelect = row.querySelector('select');
        if (symbolSelect && symbolSelect.value) {
            const tacticSelect = row.querySelector('select:nth-child(2)');
            const timeframeSelect = row.querySelector('select:nth-child(3)');
            const enabledCheckbox = row.querySelector('input[type="checkbox"]');
            const stopLossInput = row.querySelector('input[type="number"]');
            const takeProfitInput = row.querySelector('input[type="number"]:nth-child(2)');
            const leverageInput = row.querySelector('input[type="number"]:nth-child(3)');
            
            const strategy = {
                symbol: symbolSelect.value,
                tactic: tacticSelect ? tacticSelect.value : 'ott',
                timeframe: timeframeSelect ? timeframeSelect.value : '15',
                enabled: enabledCheckbox ? enabledCheckbox.checked : true,
                stopLoss: stopLossInput ? parseFloat(stopLossInput.value) || 20 : 20,
                takeProfit: takeProfitInput ? takeProfitInput.value || '' : '',
                leverage: leverageInput ? parseInt(leverageInput.value) || 10 : 10
            };
            
            strategies.push(strategy);
            console.log(`Строка ${index + 1}:`, strategy);
        } else {
            console.log(`Строка ${index + 1}: пропущена (нет символа)`);
        }
    });
    
    try {
        localStorage.setItem('tradingStrategies', JSON.stringify(strategies));
        console.log('✅ Стратегии успешно сохранены в localStorage:', strategies);
        console.log('Количество сохраненных стратегий:', strategies.length);
    } catch (error) {
        console.error('❌ Ошибка сохранения стратегий:', error);
    }
    
    console.log('=== КОНЕЦ СОХРАНЕНИЯ СТРАТЕГИЙ ===');
}

// Загрузка стратегий из localStorage
function loadStrategies() {
    console.log('=== НАЧАЛО ЗАГРУЗКИ СТРАТЕГИЙ ===');
    
    const saved = localStorage.getItem('tradingStrategies');
    const tbody = document.getElementById('strategiesTableBody');
    if (!tbody) {
        console.error('❌ Таблица стратегий не найдена');
        return;
    }
    
    console.log('Сохраненные данные из localStorage:', saved);
    
    tbody.innerHTML = '';
    
    if (saved) {
        try {
            const strategies = JSON.parse(saved);
            console.log('✅ Загружены сохраненные стратегии:', strategies);
            console.log('Количество загруженных стратегий:', strategies.length);
            
            strategies.forEach((strategy, index) => {
                console.log(`Загружаем стратегию ${index + 1}:`, strategy);
                addStrategyRow(
                    strategy.symbol,
                    strategy.tactic,
                    strategy.timeframe || '15',
                    strategy.enabled,
                    strategy.stopLoss,
                    strategy.takeProfit,
                    strategy.leverage
                );
            });
        } catch (error) {
            console.error('❌ Ошибка загрузки стратегий:', error);
        }
    } else {
        console.log('📝 Нет сохраненных стратегий в localStorage');
    }
    
    // Добавляем стратегии для выбранных символов, если их нет
    setTimeout(() => {
        addDefaultStrategiesForSelectedSymbols();
    }, 100);
    
    console.log('=== КОНЕЦ ЗАГРУЗКИ СТРАТЕГИЙ ===');
}

// Добавление стратегий по умолчанию для выбранных символов
function addDefaultStrategiesForSelectedSymbols() {
    const symbolsSelect = document.getElementById('tradingSymbols');
    if (!symbolsSelect) return;
    
    const selectedSymbols = Array.from(symbolsSelect.selectedOptions).map(option => option.value);
    const existingStrategies = Array.from(document.querySelectorAll('#strategiesTableBody tr'))
        .map(row => row.querySelector('select')?.value)
        .filter(Boolean);
    
    selectedSymbols.forEach(symbol => {
        if (!existingStrategies.includes(symbol)) {
            console.log(`Добавляем стратегию по умолчанию для ${symbol}`);
            addStrategyRow(symbol, 'ott', '15', true, 20, '', 10);
        }
    });
}

// Получение настроек стратегии для конкретной пары
function getStrategyForSymbol(symbol) {
    const rows = document.querySelectorAll('#strategiesTableBody tr');
    
    for (let row of rows) {
        const symbolSelect = row.querySelector('select');
        if (symbolSelect && symbolSelect.value === symbol) {
            const tacticSelect = row.querySelector('select:nth-child(2)');
            const timeframeSelect = row.querySelector('select:nth-child(3)');
            const enabledCheckbox = row.querySelector('input[type="checkbox"]');
            const stopLossInput = row.querySelector('input[type="number"]');
            const takeProfitInput = row.querySelector('input[type="number"]:nth-child(2)');
            const leverageInput = row.querySelector('input[type="number"]:nth-child(3)');
            
            return {
                symbol: symbolSelect.value,
                tactic: tacticSelect ? tacticSelect.value : 'ott',
                timeframe: timeframeSelect ? timeframeSelect.value : '15',
                enabled: enabledCheckbox ? enabledCheckbox.checked : true,
                stopLoss: stopLossInput ? parseFloat(stopLossInput.value) || 20 : 20,
                takeProfit: takeProfitInput ? takeProfitInput.value || '' : '',
                leverage: leverageInput ? parseInt(leverageInput.value) || 10 : 10
            };
        }
    }
    
    // Возвращаем глобальные настройки если нет специфичных
    const globalTactic = document.getElementById('globalTactic');
    const tradingTimeframe = document.getElementById('tradingTimeframe');
    const stopLossPct = document.getElementById('stopLossPct');
    const takeProfitPct = document.getElementById('takeProfitPct');
    const buyLeverage = document.getElementById('buyLeverage');
    
    return {
        symbol: symbol,
        tactic: globalTactic ? globalTactic.value : 'ott',
        timeframe: tradingTimeframe ? tradingTimeframe.value : '15',
        enabled: true,
        stopLoss: stopLossPct ? parseFloat(stopLossPct.value) || 20 : 20,
        takeProfit: takeProfitPct ? takeProfitPct.value || '' : '',
        leverage: buyLeverage ? parseInt(buyLeverage.value) || 10 : 10
    };
}

// Тестирование сигналов (для демонстрации)
function testSignals() {
    const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'];
    const types = ['buy', 'sell'];
    const strategies = ['OTT', 'Ghost', 'Combined'];
    const statuses = ['pending', 'processed', 'rejected', 'error'];
    const reasons = [
        'Недостаточно средств',
        'Рыночные условия не подходят',
        'Сигнал слишком слабый',
        'Уже есть открытая позиция',
        'Превышен лимит позиций'
    ];
    
    // Генерируем случайный сигнал
    const symbol = symbols[Math.floor(Math.random() * symbols.length)];
    const type = types[Math.floor(Math.random() * types.length)];
    const strategy = strategies[Math.floor(Math.random() * strategies.length)];
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    const reason = Math.random() > 0.5 ? reasons[Math.floor(Math.random() * reasons.length)] : '';
    
    addSignal({
        symbol: symbol,
        type: type,
        strategy: strategy,
        status: status,
        reason: reason
    });
}

 