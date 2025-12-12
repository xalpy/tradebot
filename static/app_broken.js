// Глобальные переменные

// Глобальный обработчик ошибок
window.addEventListener('error', function(event) {
    console.error('🚨 Глобальная ошибка:', event.error);
    if (event.error && event.error.message && event.error.message.includes('Value is null')) {
        console.log('🔧 Игнорируем ошибку Value is null');
        event.preventDefault();
    }
});

let socket;
let chart;
let isConnected = false;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    loadInitialData();
    setupEventListeners();
    // График будет инициализирован при переходе на вкладку
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
            }, 500); // Увеличиваем задержку
        });
    }
    
    // Инициализируем график сразу, если мы уже на вкладке графика
    const activeTab = document.querySelector('.tab-pane.active');
    if (activeTab && activeTab.id === 'chart') {
        setTimeout(() => {
            initializeChart();
        }, 1000);
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

// Загрузка популярных пар для автоматической торговли
async function loadPopularPairs() {
    try {
        console.log('Загружаем популярные пары...');
        
        const response = await fetch('/api/trading_pairs');
        const data = await response.json();
        
        if (data.popular) {
            const popularSymbols = data.popular.map(pair => pair.symbol).join(',');
            document.getElementById('tradingSymbols').value = popularSymbols;
            
            console.log(`Установлено ${data.popular.length} популярных пар`);
            showToast(`Установлено ${data.popular.length} популярных пар`, 'success');
        } else {
            console.error('Ошибка загрузки популярных пар:', data);
            showToast('Ошибка загрузки популярных пар', 'error');
        }
    } catch (error) {
        console.error('Ошибка загрузки популярных пар:', error);
        showToast('Ошибка загрузки популярных пар', 'error');
    }
}

// Обновление селекта с торговыми парами
function updateSymbolSelect(selectId, popularPairs, allPairs) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    // Сохраняем текущее значение
    const currentValue = select.value;
    
    // Очищаем селект
    select.innerHTML = '';
    
    // Добавляем опцию по умолчанию
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Выберите пару...';
    defaultOption.style.color = '#ecf0f1';
    defaultOption.style.backgroundColor = '#2c3e50';
    select.appendChild(defaultOption);
    
    // Добавляем популярные пары
    if (popularPairs.length > 0) {
        const popularGroup = document.createElement('optgroup');
        popularGroup.label = '🔥 Популярные пары';
        
        popularPairs.forEach(pair => {
            const option = document.createElement('option');
            option.value = pair.symbol;
            option.textContent = `${pair.symbol} | $${pair.price.toFixed(2)}`;
            option.style.color = '#ecf0f1';
            option.style.backgroundColor = '#2c3e50';
            popularGroup.appendChild(option);
        });
        
        select.appendChild(popularGroup);
    }
    
    // Добавляем все пары
    if (allPairs.length > 0) {
        const allGroup = document.createElement('optgroup');
        allGroup.label = `📊 Все пары (${allPairs.length})`;
        
        allPairs.forEach(pair => {
            const option = document.createElement('option');
            option.value = pair.symbol;
            const volumeM = (pair.volume24h/1000000).toFixed(1);
            option.textContent = `${pair.symbol} | $${pair.price.toFixed(2)} | $${volumeM}M`;
            option.style.color = '#ecf0f1';
            option.style.backgroundColor = '#2c3e50';
            allGroup.appendChild(option);
        });
        
        select.appendChild(allGroup);
    }
    
    // Восстанавливаем значение, если оно было
    if (currentValue) {
        select.value = currentValue;
    }
    
    // Добавляем обработчик для улучшения отображения
    select.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption) {
            selectedOption.style.backgroundColor = '#3498db';
            selectedOption.style.color = '#ffffff';
        }
    });
}

// Запуск торговли
async function startTrading() {
    try {
        const symbols = document.getElementById('tradingSymbols').value.split(',').map(s => s.trim());
        const takeProfitValue = document.getElementById('takeProfitPct').value;
        const config = {
            buy_leverage: parseInt(document.getElementById('buyLeverage').value),
            sell_leverage: parseInt(document.getElementById('sellLeverage').value),
            trade_balance_pct: parseFloat(document.getElementById('tradeBalancePct').value) / 100,
            stop_loss_pct: parseFloat(document.getElementById('stopLossPct').value) / 100,
            take_profit_pct: takeProfitValue ? parseFloat(takeProfitValue) : null,
            trade_interval_sec: parseInt(document.getElementById('tradeInterval').value),
            mode: document.getElementById('tradingMode').value
        };
        
        const response = await fetch('/api/trading/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symbols, config }),
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            showToast(result.message, 'success');
            loadTradingStatus();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('Ошибка запуска торговли', 'error');
        console.error('Ошибка:', error);
    }
}

// Остановка торговли
async function stopTrading() {
    try {
        const response = await fetch('/api/trading/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            showToast(result.message, 'success');
            loadTradingStatus();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('Ошибка остановки торговли', 'error');
        console.error('Ошибка:', error);
    }
}

// Размещение ручного ордера
async function placeManualOrder(event) {
    event.preventDefault();
    
    try {
        const takeProfitValue = document.getElementById('orderTakeProfit').value;
        const formData = {
            symbol: document.getElementById('orderSymbol').value,
            side: document.getElementById('orderSide').value,
            qty: parseFloat(document.getElementById('orderQty').value),
            order_type: document.getElementById('orderType').value,
            stop_loss: parseFloat(document.getElementById('orderStopLoss').value) / 100,
            take_profit: takeProfitValue ? parseFloat(takeProfitValue) / 100 : null
        };
        
        if (formData.order_type === 'Limit') {
            formData.price = parseFloat(document.getElementById('orderPrice').value);
        }
        
        const response = await fetch('/api/place_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            showToast('Ордер размещен успешно', 'success');
            document.getElementById('manualOrderForm').reset();
            loadPositions();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('Ошибка размещения ордера', 'error');
        console.error('Ошибка:', error);
    }
}

// Запуск бэктеста
async function runBacktest(event) {
    event.preventDefault();
    
    try {
        const takeProfitValue = document.getElementById('backtestTakeProfit').value;
        const formData = {
            symbol: document.getElementById('backtestSymbol').value,
            interval: document.getElementById('backtestInterval').value,
            days_back: parseInt(document.getElementById('backtestDays').value),
            leverage: parseInt(document.getElementById('backtestLeverage').value),
            stop_loss_pct: parseFloat(document.getElementById('backtestStopLoss').value),
            take_profit_pct: takeProfitValue ? parseFloat(takeProfitValue) : null,
            initial_balance: parseFloat(document.getElementById('backtestBalance').value),
            trade_size_pct: parseFloat(document.getElementById('backtestTradeSize').value),
            strategy_type: document.getElementById('backtestStrategy').value
        };
        
        console.log('Запускаем бэктест для:', formData);
        
        const response = await fetch('/api/backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });
        
        const result = await response.json();
        console.log('Результат бэктеста:', result);
        
        if (result.trades !== undefined) {
            displayBacktestResults(result);
            showToast(`Бэктест завершен. ${result.total_trades} сделок, винрейт ${result.win_rate}%`, 'success');
        } else {
            showToast(result.error || 'Ошибка бэктеста', 'error');
        }
    } catch (error) {
        showToast('Ошибка запуска бэктеста: ' + error.message, 'error');
        console.error('Ошибка:', error);
    }
}

// Отображение результатов бэктеста
function displayBacktestResults(result) {
    const container = document.getElementById('backtestResults');
    
    let html = `
        <div class="alert alert-info">
            <h6>Результаты бэктеста</h6>
            <div class="mb-2"><small class="text-muted">
                <strong>Причины выхода:</strong> 🔄 Сигнал | 🛑 Стоп-лосс | 💰 Тейк-профит | 📈 Открытая позиция (не закрыта до конца периода)
            </small></div>
            <div class="row">
                <div class="col-md-2">
                    <strong>Всего сделок:</strong> ${result.total_trades}
                </div>
                <div class="col-md-2">
                    <strong>Прибыльных:</strong> ${result.profitable_trades}
                </div>
                <div class="col-md-2">
                    <strong>Винрейт:</strong> ${result.win_rate}%
                </div>
                <div class="col-md-2">
                    <strong>Общая прибыль:</strong> ${result.total_profit_pct}%
                </div>
                <div class="col-md-2">
                    <strong>Макс. прибыль:</strong> ${result.max_profit}%
                </div>
                <div class="col-md-2">
                    <strong>Макс. убыток:</strong> ${result.max_loss}%
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-md-2">
                    <strong>По сигналу:</strong> ${result.signal_trades || 0}
                </div>
                <div class="col-md-2">
                    <strong>По стоп-лоссу:</strong> ${result.stop_loss_trades || 0}
                </div>
                <div class="col-md-2">
                    <strong>По тейк-профиту:</strong> ${result.take_profit_trades || 0}
                </div>
                <div class="col-md-2">
                    <strong>Открытые позиции:</strong> ${result.open_positions || 0}
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-md-3">
                    <strong>Общая прибыль USD:</strong> $${result.total_profit_usd}
                </div>
                <div class="col-md-3">
                    <strong>Средняя длительность:</strong> ${result.avg_duration}ч
                </div>
                <div class="col-md-3">
                    <strong>Период:</strong> ${new Date(result.period_start).toLocaleDateString()} - ${new Date(result.period_end).toLocaleDateString()}
                </div>
                <div class="col-md-3">
                    <strong>Точек данных:</strong> ${result.data_points}
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-md-2">
                    <strong>Стратегия:</strong> ${result.strategy_type || 'GhostTangent'}
                </div>
                <div class="col-md-2">
                    <strong>Плечо:</strong> ${result.leverage}x
                </div>
                <div class="col-md-2">
                    <strong>Стоп-лосс:</strong> ${result.stop_loss_pct}%
                </div>
                <div class="col-md-2">
                    <strong>Тейк-профит:</strong> ${result.take_profit_pct ? result.take_profit_pct + '%' : 'Отключен'}
                </div>
                <div class="col-md-2">
                    <strong>Размер позиции:</strong> ${result.trade_size_pct}%
                </div>
            </div>
        </div>
    `;
    
    if (result.trades && result.trades.length > 0) {
        // Сортируем сделки от новых к старым
        const sortedTrades = [...result.trades].reverse();
        
        html += '<div class="table-responsive">';
        html += '<div class="d-flex justify-content-between align-items-center mb-2">';
        html += `<span>Показано ${Math.min(15, sortedTrades.length)} из ${sortedTrades.length} сделок</span>`;
        if (sortedTrades.length > 15) {
            html += `<button class="btn btn-sm btn-outline-primary" onclick="toggleAllTrades()">Показать все сделки</button>`;
        }
        html += '</div>';
        
        html += '<table class="table table-sm" id="tradesTable">';
        html += '<thead><tr><th>Вход</th><th>Выход</th><th>Тип</th><th>Плечо</th><th>Уверенность</th><th>Прибыль %</th><th>Прибыль $</th><th>Длительность</th><th>Статус</th><th>Причина выхода</th></tr></thead><tbody>';
        
        // Показываем только первые 15 сделок (которые теперь самые новые)
        const visibleTrades = sortedTrades.slice(0, 15);
        
        visibleTrades.forEach((trade, index) => {
            const entryTime = new Date(trade.entry_time).toLocaleString();
            const exitTime = new Date(trade.exit_time).toLocaleString();
            const profitClass = trade.profit_pct >= 0 ? 'text-success' : 'text-danger';
            const statusClass = trade.status === 'profitable' ? 'text-success' : 'text-danger';
            const statusIcon = trade.status === 'profitable' ? '✅' : '❌';
            
            // Определяем иконку и текст для причины выхода
            let exitReasonIcon = '🔄';
            let exitReasonText = 'Сигнал';
            if (trade.exit_reason === 'stop_loss') {
                exitReasonIcon = '🛑';
                exitReasonText = 'Стоп-лосс';
            } else if (trade.exit_reason === 'take_profit') {
                exitReasonIcon = '💰';
                exitReasonText = 'Тейк-профит';
            } else if (trade.exit_reason === 'period_end') {
                exitReasonIcon = '📈';
                exitReasonText = 'Открытая позиция';
            }
            
            // Определяем цвет уверенности
            const confidence = trade.confidence || 50;
            let confidenceClass = 'text-muted';
            if (confidence >= 80) {
                confidenceClass = 'text-success';
            } else if (confidence >= 60) {
                confidenceClass = 'text-warning';
            } else if (confidence >= 40) {
                confidenceClass = 'text-info';
            }
            
            html += `
                <tr class="trade-row ${index >= 15 ? 'hidden-trade' : ''}">
                    <td>${entryTime}<br><small>$${trade.entry_price.toFixed(2)}</small></td>
                    <td>${exitTime}<br><small>$${trade.exit_price.toFixed(2)}</small></td>
                    <td>${trade.entry_type.toUpperCase()}</td>
                    <td>${trade.leverage}x</td>
                    <td class="${confidenceClass}">${confidence}%</td>
                    <td class="${profitClass}">${trade.profit_pct}%</td>
                    <td class="${profitClass}">$${trade.profit_usd}</td>
                    <td>${trade.duration_hours}ч</td>
                    <td class="${statusClass}">${statusIcon} ${trade.status}</td>
                    <td><small>${exitReasonIcon} ${exitReasonText}</small></td>
                </tr>
            `;
        });
        
        // Добавляем скрытые строки для остальных сделок
        const hiddenTrades = sortedTrades.slice(15);
        hiddenTrades.forEach(trade => {
            const entryTime = new Date(trade.entry_time).toLocaleString();
            const exitTime = new Date(trade.exit_time).toLocaleString();
            const profitClass = trade.profit_pct >= 0 ? 'text-success' : 'text-danger';
            const statusClass = trade.status === 'profitable' ? 'text-success' : 'text-danger';
            const statusIcon = trade.status === 'profitable' ? '✅' : '❌';
            
            html += `
                <tr class="trade-row hidden-trade" style="display: none;">
                    <td>${entryTime}<br><small>$${trade.entry_price.toFixed(2)}</small></td>
                    <td>${exitTime}<br><small>$${trade.exit_price.toFixed(2)}</small></td>
                    <td>${trade.entry_type.toUpperCase()}</td>
                    <td class="${profitClass}">${trade.profit_pct}%</td>
                    <td class="${profitClass}">$${trade.profit_usd}</td>
                    <td>${trade.duration_hours}ч</td>
                    <td class="${statusClass}">${statusIcon} ${trade.status}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        
        // Сохраняем данные для переключения
        window.allTradesData = sortedTrades;
    }
    
    container.innerHTML = html;
}

// Удалено - заменено на TradingView
    try {
        const symbol = document.getElementById('chartSymbol').value || 'BTCUSDT';
        const interval = document.getElementById('chartInterval').value || '15';
        const chartContainer = document.getElementById('chartContainer');
        
        console.log('🚀 Загружаем график для:', symbol);
        
        if (!symbol) {
            chartContainer.innerHTML = '<div class="text-center p-4 text-muted">Выберите символ</div>';
            return;
        }
        
        // Показываем загрузку
        chartContainer.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin fa-2x"></i><br>Загрузка через WebSocket...</div>';
        
        // Создаем Promise для получения данных через WebSocket
        const chartDataPromise = new Promise((resolve, reject) => {
            // Обработчик для получения данных
            const handleChartData = (data) => {
                console.log('📡 Получен ответ от WebSocket:', data);
                
                if (data.success) {
                    console.log('📊 Получено данных через WebSocket:', data.data.length);
                    console.log('📋 Первая запись от WebSocket:', data.data[0]);
                    console.log('📋 Тип первой записи:', typeof data.data[0]);
                    console.log('📋 Ключи первой записи:', Object.keys(data.data[0]));
                    resolve(data.data);
                } else {
                    console.error('❌ Ошибка от WebSocket:', data.error);
                    reject(new Error(data.error || 'Ошибка получения данных'));
                }
                // Удаляем обработчик после использования
                socket.off('chart_data', handleChartData);
            };
            
            // Подписываемся на событие
            socket.on('chart_data', handleChartData);
            
            // Отправляем запрос
            socket.emit('request_chart_data', {
                symbol: symbol,
                interval: interval,
                limit: 10
            });
            
            // Таймаут на случай, если данные не придут
            setTimeout(() => {
                socket.off('chart_data', handleChartData);
                reject(new Error('Таймаут получения данных'));
            }, 10000);
        });
        
        // Получаем данные
        const data = await chartDataPromise;
        
        if (!data || data.length === 0) {
            chartContainer.innerHTML = '<div class="text-center p-4 text-muted">Нет данных</div>';
            return;
        }
        
        // Удаляем старый график
        if (chart) {
            chart.remove();
            chart = null;
        }
        
        // Создаем новый контейнер для графика
        chartContainer.innerHTML = '';
        const newChartContainer = document.createElement('div');
        newChartContainer.id = 'newChartContainer';
        newChartContainer.style.width = '800px';
        newChartContainer.style.height = '400px';
        newChartContainer.style.display = 'block';
        newChartContainer.style.position = 'relative';
        newChartContainer.style.border = '1px solid #ccc';
        newChartContainer.style.backgroundColor = '#ffffff';
        
        chartContainer.appendChild(newChartContainer);
        
        // Ждем обновления DOM
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Создаем график с простыми настройками
        chart = LightweightCharts.createChart(newChartContainer, {
            width: 800,
            height: 400,
            layout: {
                background: { color: '#ffffff' },
                textColor: '#000000',
            },
            grid: {
                vertLines: { visible: false },
                horzLines: { visible: false },
            },
            timeScale: {
                visible: true,
                timeVisible: true,
                secondsVisible: false,
            },
            rightPriceScale: {
                visible: true,
            },
            crosshair: {
                visible: false,
            },
        });
        
        // Добавляем серию свечей с простыми настройками
        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#00ff88',
            downColor: '#ff4757',
            borderVisible: false,
            wickUpColor: '#00ff88',
            wickDownColor: '#ff4757',
        });
        
        // Преобразуем данные
        const chartData = data.map(item => {
            let time = Number(item.time);
            
            // Проверяем, что время не слишком большое (не в будущем)
            if (time > 2000000000) {  // Если больше 2000 года в секундах
                console.log(`⚠️ Время слишком большое: ${time}, конвертируем...`);
                time = Math.floor(time / 1000);
            }
            
            return {
                time: time,
                open: Number(item.open),
                high: Number(item.high),
                low: Number(item.low),
                close: Number(item.close)
            };
        }).filter(item => 
            !isNaN(item.time) && 
            !isNaN(item.open) && 
            !isNaN(item.high) && 
            !isNaN(item.low) && 
            !isNaN(item.close) &&
            item.time > 0 &&
            item.open > 0 &&
            item.high > 0 &&
            item.low > 0 &&
            item.close > 0
        );
        
        console.log('✅ Обработано свечей:', chartData.length);
        console.log('📋 Первая свеча:', chartData[0]);
        console.log('🕐 Время первой свечи:', new Date(chartData[0].time * 1000).toISOString());
        console.log('🕐 Текущее время:', new Date().toISOString());
        
        // Сравниваем с тестовыми данными
        const testData = [
            { time: 1640995200, open: 100, high: 105, low: 95, close: 102 },
            { time: 1640995260, open: 102, high: 108, low: 100, close: 106 },
            { time: 1640995320, open: 106, high: 110, low: 104, close: 108 }
        ];
        
        console.log('🔄 Сравнение с тестовыми данными:');
        console.log('   Тестовая свеча:', testData[0]);
        console.log('   Реальная свеча:', chartData[0]);
        console.log('   Структура совпадает:', JSON.stringify(Object.keys(testData[0])) === JSON.stringify(Object.keys(chartData[0])));
        
        if (chartData.length === 0) {
            throw new Error('Нет валидных данных для отображения');
        }
        
        // Устанавливаем данные
        candlestickSeries.setData(chartData);
        
        console.log('✅ График создан успешно!');
        showToast(`График загружен: ${symbol}`, 'success');
        
        // Дополнительный тест: попробуем создать график с тестовыми данными для сравнения
        console.log('🧪 Дополнительный тест: создаем график с тестовыми данными...');
        const testChartContainer = document.createElement('div');
        testChartContainer.id = 'testChartContainer';
        testChartContainer.style.width = '400px';
        testChartContainer.style.height = '200px';
        testChartContainer.style.border = '2px solid red';
        testChartContainer.style.marginTop = '10px';
        
        chartContainer.appendChild(testChartContainer);
        
        const testChart = LightweightCharts.createChart(testChartContainer, {
            width: 400,
            height: 200,
            layout: {
                background: { color: '#ffffff' },
                textColor: '#000000',
            },
            grid: {
                vertLines: { visible: false },
                horzLines: { visible: false },
            },
            timeScale: {
                visible: true,
                timeVisible: true,
                secondsVisible: false,
            },
            rightPriceScale: {
                visible: true,
            },
            crosshair: {
                visible: false,
            },
        });
        
        const testCandlestickSeries = testChart.addCandlestickSeries({
            upColor: '#00ff88',
            downColor: '#ff4757',
            borderVisible: false,
            wickUpColor: '#00ff88',
            wickDownColor: '#ff4757',
        });
        
        testCandlestickSeries.setData(testData);
        console.log('✅ Тестовый график создан для сравнения');
        
    } catch (error) {
        console.error('❌ Ошибка:', error);
        const chartContainer = document.getElementById('chartContainer');
        chartContainer.innerHTML = `<div class="text-center p-4 text-danger">
            <i class="fas fa-exclamation-triangle fa-2x mb-3"></i><br>
            Ошибка загрузки графика<br>
            <small>${error.message}</small>
        </div>`;
        showToast('Ошибка загрузки графика: ' + error.message, 'error');
    }
}

// Загрузка тестовых данных
async function loadTestData() {
    try {
        console.log('🧪 Загружаем тестовые данные...');
        
        const symbol = document.getElementById('chartSymbol').value || 'BTCUSDT';
        const chartContainer = document.getElementById('chartContainer');
        
        // Показываем индикатор загрузки
        chartContainer.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin fa-2x"></i><br><br>Загрузка тестовых данных...</div>';
        
        // Тестовые данные (точно как в test_chart_creation.html)
        const testData = [
            { time: 1640995200, open: 100, high: 105, low: 95, close: 102 },
            { time: 1640995260, open: 102, high: 108, low: 100, close: 106 },
            { time: 1640995320, open: 106, high: 110, low: 104, close: 108 },
            { time: 1640995380, open: 108, high: 112, low: 106, close: 110 },
            { time: 1640995440, open: 110, high: 115, low: 108, close: 113 },
            { time: 1640995500, open: 113, high: 118, low: 111, close: 116 },
            { time: 1640995560, open: 116, high: 120, low: 114, close: 118 },
            { time: 1640995620, open: 118, high: 122, low: 116, close: 120 },
            { time: 1640995680, open: 120, high: 125, low: 118, close: 123 },
            { time: 1640995740, open: 123, high: 128, low: 121, close: 126 }
        ];
        
        console.log('📊 Тестовые данные:', testData);
        
        // Восстанавливаем контейнер графика
        chartContainer.innerHTML = '';
        chartContainer.style.width = '100%';
        chartContainer.style.height = '400px';
        
        // Удаляем старый график, если он существует
        if (chart) {
            try {
                chart.remove();
                chart = null;
                console.log('🗑️ Старый график удален');
            } catch (error) {
                console.warn('⚠️ Ошибка удаления старого графика:', error);
            }
        }
        
        // Проверяем, что контейнер существует и видим
        if (!chartContainer) {
            throw new Error('Контейнер графика не найден');
        }
        
        // Принудительно устанавливаем размеры
        chartContainer.style.display = 'block';
        chartContainer.style.visibility = 'visible';
        chartContainer.style.position = 'relative';
        
        // Ждем немного, чтобы DOM обновился
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Проверяем размеры контейнера
        const containerWidth = chartContainer.clientWidth;
        const containerHeight = chartContainer.clientHeight;
        
        console.log(`📏 Размеры контейнера: ${containerWidth}x${containerHeight}`);
        
        if (containerWidth <= 0 || containerHeight <= 0) {
            throw new Error(`Неверные размеры контейнера: ${containerWidth}x${containerHeight}`);
        }
        
        // Создаем график
        chart = LightweightCharts.createChart(chartContainer, {
            width: containerWidth,
            height: containerHeight,
            layout: {
                background: { color: 'rgba(0, 0, 0, 0.2)' },
                textColor: '#fff',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.1)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.1)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.2)',
                textColor: '#fff',
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.2)',
                textColor: '#fff',
                timeVisible: true,
                secondsVisible: false,
            },
        });
        
        // Добавляем серию свечей
        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#00ff88',
            downColor: '#ff4757',
            borderVisible: false,
            wickUpColor: '#00ff88',
            wickDownColor: '#ff4757',
        });
        
        // Устанавливаем тестовые данные
        candlestickSeries.setData(testData);
        
        console.log('✅ Тестовый график создан успешно с', testData.length, 'свечами');
        showToast(`Тестовый график загружен: ${testData.length} свечей`, 'success');
        
    } catch (error) {
        console.error('❌ Ошибка загрузки тестовых данных:', error);
        const chartContainer = document.getElementById('chartContainer');
        chartContainer.innerHTML = `<div class="text-center p-4 text-danger">
            <i class="fas fa-exclamation-triangle fa-2x mb-3"></i><br>
            Ошибка загрузки тестовых данных<br>
            <small>${error.message}</small>
        </div>`;
        showToast('Ошибка загрузки тестовых данных: ' + error.message, 'error');
    }
}

// Тестирование реальных данных от API
async function loadRealDataTest() {
    try {
        console.log('🧪 Тестируем реальные данные от API...');
        
        const symbol = document.getElementById('chartSymbol').value || 'BTCUSDT';
        const interval = document.getElementById('chartInterval').value || '15';
        const chartContainer = document.getElementById('chartContainer');
        
        // Показываем индикатор загрузки
        chartContainer.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin fa-2x"></i><br><br>Тестируем реальные данные...</div>';
        
        // Получаем данные от API
        const response = await fetch(`/api/klines/${symbol}?interval=${interval}&limit=3`);
        const data = await response.json();
        
        console.log('📊 Получены реальные данные:', data);
        
        if (!Array.isArray(data) || data.length === 0) {
            throw new Error('Нет данных от API');
        }
        
        // Преобразуем в точно такой же формат как тестовые данные
        const processedData = data.map((item, index) => {
            console.log(`📋 Обрабатываем запись ${index + 1}:`, item);
            
            // Создаем точно такой же объект как в тестовых данных
            const candle = Object.assign({}, {
                time: Number(item.time),
                open: Number(item.open),
                high: Number(item.high),
                low: Number(item.low),
                close: Number(item.close)
            });
            
            console.log(`✅ Итоговая свеча ${index + 1}:`, candle);
            return candle;
        });
        
        console.log('🧪 Обработанные данные:', processedData);
        
        // Создаем график
        chartContainer.innerHTML = '';
        chartContainer.style.width = '100%';
        chartContainer.style.height = '400px';
        
        // Удаляем старый график
        if (chart) {
            chart.remove();
            chart = null;
        }
        
        // Создаем новый график
        chart = LightweightCharts.createChart(chartContainer, {
            width: chartContainer.clientWidth,
            height: chartContainer.clientHeight,
            layout: {
                background: { color: 'rgba(0, 0, 0, 0.2)' },
                textColor: '#fff',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.1)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.1)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.2)',
                textColor: '#fff',
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.2)',
                textColor: '#fff',
                timeVisible: true,
                secondsVisible: false,
            },
        });
        
        // Добавляем серию свечей
        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#00ff88',
            downColor: '#ff4757',
            borderVisible: false,
            wickUpColor: '#00ff88',
            wickDownColor: '#ff4757',
        });
        
        // Устанавливаем реальные данные
        candlestickSeries.setData(processedData);
        
        console.log('✅ График с реальными данными создан успешно!');
        showToast(`График с реальными данными: ${processedData.length} свечей`, 'success');
        
    } catch (error) {
        console.error('❌ Ошибка тестирования реальных данных:', error);
        const chartContainer = document.getElementById('chartContainer');
        chartContainer.innerHTML = `<div class="text-center p-4 text-danger">
            <i class="fas fa-exclamation-triangle fa-2x mb-3"></i><br>
            Ошибка тестирования реальных данных<br>
            <small>${error.message}</small>
        </div>`;
        showToast('Ошибка тестирования реальных данных: ' + error.message, 'error');
    }
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

// ===== TRADINGVIEW INTEGRATION =====

let tradingViewWidget = null;
let isTradingViewMode = false;

// Инициализация TradingView виджета
function initTradingViewWidget() {
    const container = document.getElementById('tradingview-widget');
    if (!container) {
        console.error('TradingView контейнер не найден');
        return;
    }
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    // Получаем текущий символ
    const symbolSelect = document.getElementById('chartSymbol');
    const intervalSelect = document.getElementById('chartInterval');
    const symbol = symbolSelect.value || 'BTCUSDT';
    const interval = intervalSelect.value || '15';
    
    // Создаем виджет
    tradingViewWidget = new TradingView.widget({
        "width": "100%",
        "height": "100%",
        "symbol": `BINANCE:${symbol}`,
        "interval": interval,
        "timezone": "Europe/Moscow",
        "theme": "dark",
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
    
    console.log('TradingView виджет инициализирован');
}

// Переключение между обычным графиком и TradingView
function switchToTradingView() {
    const chartContainer = document.getElementById('chartContainer');
    const tradingViewContainer = document.getElementById('tradingviewContainer');
    const switchButton = document.getElementById('switchToTradingView');
    
    if (!isTradingViewMode) {
        // Переключаемся на TradingView
        chartContainer.style.display = 'none';
        tradingViewContainer.style.display = 'block';
        switchButton.innerHTML = '<i class="fas fa-chart-bar me-1"></i>Обычный график';
        switchButton.className = 'btn btn-outline-primary';
        
        // Загружаем TradingView скрипт если еще не загружен
        if (typeof TradingView === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://s3.tradingview.com/tv.js';
            script.onload = function() {
                console.log('TradingView скрипт загружен');
                initTradingViewWidget();
            };
            script.onerror = function() {
                console.error('Ошибка загрузки TradingView скрипта');
                showToast('Ошибка загрузки TradingView', 'error');
            };
            document.head.appendChild(script);
        } else {
            initTradingViewWidget();
        }
        
        isTradingViewMode = true;
    } else {
        // Переключаемся обратно на обычный график
        chartContainer.style.display = 'block';
        tradingViewContainer.style.display = 'none';
        switchButton.innerHTML = '<i class="fas fa-chart-line me-1"></i>TradingView';
        switchButton.className = 'btn btn-success';
        
        isTradingViewMode = false;
    }
}

// Обновление TradingView виджета при изменении символа или интервала
function updateTradingViewWidget() {
    if (tradingViewWidget && isTradingViewMode) {
        const symbolSelect = document.getElementById('chartSymbol');
        const intervalSelect = document.getElementById('chartInterval');
        const symbol = symbolSelect.value || 'BTCUSDT';
        const interval = intervalSelect.value || '15';
        
        tradingViewWidget.setSymbol(`BINANCE:${symbol}`, interval);
    }
} 