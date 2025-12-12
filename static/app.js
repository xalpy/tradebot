// Глобальные переменные
let socket;
let widget;
let isConnected = false;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    loadInitialData();
    setupEventListeners();
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
            "height": "500px",
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
    loadBalance();
    loadAllBalances();
    loadPositions();
    loadTradingStatus();
    loadTradingPairs();
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Кнопки управления торговлей
    document.getElementById('startTrading').addEventListener('click', startTrading);
    document.getElementById('stopTrading').addEventListener('click', stopTrading);
    
    // Форма ручного ордера
    document.getElementById('manualOrderForm').addEventListener('submit', placeManualOrder);
    document.getElementById('orderType').addEventListener('change', togglePriceField);
    
    // Форма бэктеста
    document.getElementById('backtestForm').addEventListener('submit', runBacktest);
    
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
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Нет открытых позиций</td></tr>';
            return;
        }
        
        let html = '';
        positions.forEach(pos => {
            const size = parseFloat(pos.size || 0);
            if (size > 0) {
                const pnl = parseFloat(pos.unrealisedPnl || 0);
                const pnlClass = pnl >= 0 ? 'text-success' : 'text-danger';
                html += `
                    <tr>
                        <td>${pos.symbol}</td>
                        <td>${pos.side}</td>
                        <td>${size}</td>
                        <td>$${parseFloat(pos.avgPrice || 0).toFixed(2)}</td>
                        <td class="${pnlClass}">$${pnl.toFixed(2)}</td>
                    </tr>
                `;
            }
        });
        
        if (html === '') {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Нет открытых позиций</td></tr>';
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
        const response = await fetch('/api/trading_pairs');
        const data = await response.json();
        
        if (data.popular) {
            updateSymbolSelect('tradingSymbol', data.popular, data.popular);
            showToast(`Загружено ${data.popular.length} популярных пар`, 'success');
        }
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
        const symbols = Array.from(document.querySelectorAll('input[name="tradingSymbol"]:checked')).map(cb => cb.value);
        // if (symbols.length === 0) {
        //     showToast('Выберите хотя бы один символ', 'error');
        //     return;
        // }
        
        const config = {
            buy_leverage: parseInt(document.getElementById('buyLeverage').value),
            sell_leverage: parseInt(document.getElementById('sellLeverage').value),
            trade_balance_pct: parseFloat(document.getElementById('tradeBalancePct').value) / 100,
            stop_loss_pct: parseFloat(document.getElementById('stopLossPct').value) / 100,
            trade_interval_sec: parseInt(document.getElementById('tradeIntervalSec').value),
            mode: document.getElementById('tradingMode').value
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
    event.preventDefault();
    
    try {
        const formData = new FormData(event.target);
        
        // Отладочная информация
        console.log('FormData содержимое:');
        for (let [key, value] of formData.entries()) {
            console.log(`${key}: ${value}`);
        }
        
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
        
        console.log('Данные для отправки:', backtestData);
        
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
        
        console.log('Результат бэктеста:', result);
        
        if (result.trades !== undefined) {
            displayBacktestResults(result);
        } else {
            showToast(`Ошибка: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Ошибка бэктеста:', error);
        showToast('Ошибка выполнения бэктеста', 'error');
    }
}

// Отображение результатов бэктеста
function displayBacktestResults(result) {
    const container = document.getElementById('backtestResults');
    
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
                    <td>${trade.entry_type || trade.side || 'N/A'}</td>
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
    
    container.innerHTML = html;
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