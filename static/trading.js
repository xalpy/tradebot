// Trading Management System
class TradingManager {
    constructor() {
        this.socket = null;
        this.tradingStatus = false;
        this.selectedSymbols = new Set();
        this.strategies = {};
        this.tradingConfig = {
            buy_leverage: 10,
            sell_leverage: 10,
            trade_balance_pct: 3,
            stop_loss_pct: 20,
            take_profit_pct: null,
            trade_interval_sec: 60,
            mode: 'real',
            timeframe: '15'
        };
        this.init();
    }

    init() {
        this.initSocket();
        this.bindEvents();
        this.loadSavedConfig(); // Загружаем сохраненные настройки
        this.loadStrategies(); // Сначала загружаем стратегии
        this.loadTradingPairs(); // Потом торговые пары
        this.loadTradingStatus(); // Загружаем статус торговли
        this.updateStatus();
    }

    initSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('🔗 Подключен к серверу');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('❌ Отключен от сервера');
            this.updateConnectionStatus(false);
        });

        this.socket.on('trade_executed', (data) => {
            this.addTradeLog(`✅ Сделка: ${data.symbol} ${data.side} ${data.qty} @ $${data.price} (${data.action})`);
            this.updateLastTradeTime();
        });

        this.socket.on('price_update', (data) => {
            // Обновляем цены в реальном времени
        });

        this.socket.on('error', (data) => {
            this.addTradeLog(`❌ Ошибка: ${data.message}`, 'error');
        });
    }

    bindEvents() {
        // Кнопки управления торговлей
        document.getElementById('startTradingBtn')?.addEventListener('click', () => this.startTrading());
        document.getElementById('stopTradingBtn')?.addEventListener('click', () => this.stopTrading());

        // Поиск символов
        document.getElementById('symbolSearch')?.addEventListener('input', (e) => this.filterSymbols(e.target.value));
        document.getElementById('refreshSymbolsBtn')?.addEventListener('click', () => this.loadTradingPairs());

        // Автосохранение настроек
        document.getElementById('generalTradingForm')?.addEventListener('change', () => {
            this.saveGeneralConfig();
            this.addTradeLog('⚙️ Настройки автоматически сохранены');
        });
    }

    async loadTradingPairs() {
        try {
            const response = await fetch('/api/trading_pairs');
            const data = await response.json();
            
            if (data.popular && data.all) {
                this.renderPopularPairs(data.popular);
                this.renderAllPairs(data.all);
            }
        } catch (error) {
            console.error('Ошибка загрузки торговых пар:', error);
            this.addTradeLog('❌ Ошибка загрузки торговых пар', 'error');
        }
    }

    renderPopularPairs(pairs) {
        const container = document.getElementById('popularPairsContainer');
        if (!container) return;

        container.innerHTML = pairs.map(pair => `
            <div class="form-check form-check-inline">
                <input class="form-check-input" type="checkbox" id="pop_${pair.symbol}" value="${pair.symbol}" 
                       ${this.selectedSymbols.has(pair.symbol) ? 'checked' : ''}>
                <label class="form-check-label" for="pop_${pair.symbol}">
                    ${pair.symbol} <small class="text-muted">($${pair.price})</small>
                </label>
            </div>
        `).join('');

        // Добавляем обработчики событий
        container.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedSymbols.add(e.target.value);
                } else {
                    this.selectedSymbols.delete(e.target.value);
                }
                this.updateActivePairsCount();
                this.renderStrategiesTable(); // Обновляем таблицу стратегий
            });
        });
    }

    renderAllPairs(pairs) {
        const container = document.getElementById('allPairsContainer');
        if (!container) return;

        container.innerHTML = pairs.map(pair => `
            <div class="form-check form-check-inline">
                <input class="form-check-input" type="checkbox" id="all_${pair.symbol}" value="${pair.symbol}"
                       ${this.selectedSymbols.has(pair.symbol) ? 'checked' : ''}>
                <label class="form-check-label" for="all_${pair.symbol}">
                    ${pair.symbol} <small class="text-muted">($${pair.price})</small>
                </label>
            </div>
        `).join('');

        // Добавляем обработчики событий
        container.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedSymbols.add(e.target.value);
                } else {
                    this.selectedSymbols.delete(e.target.value);
                }
                this.updateActivePairsCount();
                this.renderStrategiesTable(); // Обновляем таблицу стратегий
            });
        });
    }

    filterSymbols(query) {
        const checkboxes = document.querySelectorAll('#popularPairsContainer input[type="checkbox"], #allPairsContainer input[type="checkbox"]');
        
        checkboxes.forEach(checkbox => {
            const label = checkbox.nextElementSibling;
            const symbol = checkbox.value;
            
            if (symbol.toLowerCase().includes(query.toLowerCase())) {
                checkbox.parentElement.style.display = 'inline-block';
            } else {
                checkbox.parentElement.style.display = 'none';
            }
        });
    }

    async loadStrategies() {
        try {
            console.log('🔄 Загружаем стратегии...');
            const response = await fetch('/api/strategies');
            console.log('📡 Ответ сервера:', response.status, response.statusText);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const loadedStrategies = await response.json();
            console.log('📋 Загруженные стратегии с сервера:', loadedStrategies);
            
            // Обновляем только если это не перезагрузка после удаления
            if (Object.keys(loadedStrategies).length > 0) {
                this.strategies = loadedStrategies;
                console.log('📋 Обновлены локальные стратегии:', this.strategies);
                
                // Добавляем символы из загруженных стратегий в выбранные
                if (this.strategies && typeof this.strategies === 'object') {
                    // Функция для проверки, является ли символ торговой парой
                    const isValidTradingPair = (symbol) => {
                        return /^[A-Z]{2,10}USDT$/.test(symbol) || /^[A-Z]{2,10}BTC$/.test(symbol);
                    };
                    
                    Object.keys(this.strategies).forEach(symbol => {
                        if (isValidTradingPair(symbol)) {
                            this.selectedSymbols.add(symbol);
                        } else {
                            console.log(`⚠️ Пропускаем невалидную торговую пару при загрузке: ${symbol}`);
                        }
                    });
                }
            } else {
                console.log('📋 Сервер вернул пустые стратегии, оставляем локальные данные');
            }
            
            this.renderStrategiesTable();
            this.updateActivePairsCount();
            this.addTradeLog(`📋 Загружены ${Object.keys(this.strategies).length} сохраненных стратегий`);
        } catch (error) {
            console.error('❌ Ошибка загрузки стратегий:', error);
            this.addTradeLog(`❌ Ошибка загрузки стратегий: ${error.message}`, 'error');
        }
    }

    renderStrategiesTable() {
        const tbody = document.getElementById('strategiesTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';
        console.log('🔄 Рендерим таблицу стратегий...');
        console.log('📋 Локальные стратегии:', this.strategies);
        console.log('📋 Выбранные символы:', Array.from(this.selectedSymbols));

        // Функция для проверки, является ли символ торговой парой
        const isValidTradingPair = (symbol) => {
            // Проверяем, что символ выглядит как торговая пара (например, BTCUSDT, ETHUSDT)
            return /^[A-Z]{2,10}USDT$/.test(symbol) || /^[A-Z]{2,10}BTC$/.test(symbol);
        };

        let renderedCount = 0;

        // Добавляем строки только для реальных торговых пар из стратегий
        Object.keys(this.strategies).forEach(symbol => {
            if (isValidTradingPair(symbol)) {
                const strategy = this.strategies[symbol] || 'ghost';
                const row = this.createStrategyRow(symbol, strategy);
                tbody.appendChild(row);
                renderedCount++;
                console.log(`✅ Добавлена строка для стратегии: ${symbol}`);
            } else {
                console.log(`⚠️ Пропускаем невалидную торговую пару: ${symbol}`);
            }
        });
        
        // Также добавляем строки для выбранных символов, которых нет в стратегиях
        this.selectedSymbols.forEach(symbol => {
            if (isValidTradingPair(symbol) && !this.strategies[symbol]) {
                const row = this.createStrategyRow(symbol, 'ghost');
                tbody.appendChild(row);
                renderedCount++;
                console.log(`✅ Добавлена строка для выбранного символа: ${symbol}`);
            }
        });

        console.log(`📊 Всего отрендерено строк: ${renderedCount}`);
    }

    createStrategyRow(symbol, strategy = 'ghost') {
        // Получаем сохраненные настройки для символа
        const savedStrategy = this.strategies[symbol];
        const strategyType = typeof savedStrategy === 'string' ? savedStrategy : (savedStrategy?.type || strategy);
        const timeframe = savedStrategy?.timeframe || '15';
        const leverage = savedStrategy?.leverage || 10;
        const stopLoss = savedStrategy?.stop_loss || 20;
        const takeProfit = savedStrategy?.take_profit || '';
        const balancePct = savedStrategy?.balance_pct || 3;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <strong>${symbol}</strong>
                <br><small class="text-muted">${this.getSymbolPrice(symbol)}</small>
            </td>
            <td>
                <select class="form-select form-select-sm strategy-select" data-symbol="${symbol}">
                    <option value="ghost" ${strategyType === 'ghost' ? 'selected' : ''}>Ghost Strategy</option>
                    <option value="ott" ${strategyType === 'ott' ? 'selected' : ''}>OTT Strategy</option>
                    <option value="combined" ${strategyType === 'combined' ? 'selected' : ''}>Combined Strategy</option>
                </select>
            </td>
            <td>
                <select class="form-select form-select-sm timeframe-select" data-symbol="${symbol}">
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
                <input type="number" class="form-control form-control-sm leverage-input" 
                       data-symbol="${symbol}" value="${leverage}" min="1" max="100">
            </td>
            <td>
                <input type="number" class="form-control form-control-sm stoploss-input" 
                       data-symbol="${symbol}" value="${stopLoss}" step="0.1" min="0.1" max="100">
            </td>
            <td>
                <input type="number" class="form-control form-control-sm takeprofit-input" 
                       data-symbol="${symbol}" value="${takeProfit}" step="0.1" min="0.1" max="100" placeholder="Отключен">
            </td>
            <td>
                <input type="number" class="form-control form-control-sm balance-input" 
                       data-symbol="${symbol}" value="${balancePct}" step="0.1" min="0.1" max="100">
            </td>
            <td>
                <span class="badge bg-secondary">Неактивна</span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="tradingManager.removeStrategy('${symbol}')">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;

        // Добавляем обработчики событий
        row.querySelector('.strategy-select').addEventListener('change', (e) => {
            this.strategies[e.target.dataset.symbol] = e.target.value;
            this.saveAllStrategies(); // Автоматически сохраняем при изменении
        });

        // Добавляем обработчики для других полей стратегии
        row.querySelector('.timeframe-select')?.addEventListener('change', (e) => {
            if (!this.strategies[e.target.dataset.symbol]) {
                this.strategies[e.target.dataset.symbol] = {};
            }
            if (typeof this.strategies[e.target.dataset.symbol] === 'string') {
                this.strategies[e.target.dataset.symbol] = { type: this.strategies[e.target.dataset.symbol] };
            }
            this.strategies[e.target.dataset.symbol].timeframe = e.target.value;
            this.saveAllStrategies();
        });

        row.querySelector('.leverage-input')?.addEventListener('change', (e) => {
            if (!this.strategies[e.target.dataset.symbol]) {
                this.strategies[e.target.dataset.symbol] = {};
            }
            if (typeof this.strategies[e.target.dataset.symbol] === 'string') {
                this.strategies[e.target.dataset.symbol] = { type: this.strategies[e.target.dataset.symbol] };
            }
            this.strategies[e.target.dataset.symbol].leverage = parseInt(e.target.value);
            this.saveAllStrategies();
        });

        row.querySelector('.stoploss-input')?.addEventListener('change', (e) => {
            if (!this.strategies[e.target.dataset.symbol]) {
                this.strategies[e.target.dataset.symbol] = {};
            }
            if (typeof this.strategies[e.target.dataset.symbol] === 'string') {
                this.strategies[e.target.dataset.symbol] = { type: this.strategies[e.target.dataset.symbol] };
            }
            this.strategies[e.target.dataset.symbol].stop_loss = parseFloat(e.target.value);
            this.saveAllStrategies();
        });

        row.querySelector('.takeprofit-input')?.addEventListener('change', (e) => {
            if (!this.strategies[e.target.dataset.symbol]) {
                this.strategies[e.target.dataset.symbol] = {};
            }
            if (typeof this.strategies[e.target.dataset.symbol] === 'string') {
                this.strategies[e.target.dataset.symbol] = { type: this.strategies[e.target.dataset.symbol] };
            }
            this.strategies[e.target.dataset.symbol].take_profit = e.target.value ? parseFloat(e.target.value) : null;
            this.saveAllStrategies();
        });

        row.querySelector('.balance-input')?.addEventListener('change', (e) => {
            if (!this.strategies[e.target.dataset.symbol]) {
                this.strategies[e.target.dataset.symbol] = {};
            }
            if (typeof this.strategies[e.target.dataset.symbol] === 'string') {
                this.strategies[e.target.dataset.symbol] = { type: this.strategies[e.target.dataset.symbol] };
            }
            this.strategies[e.target.dataset.symbol].balance_pct = parseFloat(e.target.value);
            this.saveAllStrategies();
        });

        return row;
    }

    getSymbolPrice(symbol) {
        // Здесь можно добавить получение актуальной цены
        return '$0.00';
    }

    addStrategyRow() {
        const symbol = prompt('Введите торговую пару (например, BTCUSDT):');
        if (symbol && symbol.trim()) {
            const upperSymbol = symbol.trim().toUpperCase();
            this.selectedSymbols.add(upperSymbol);
            this.renderStrategiesTable();
            this.updateActivePairsCount();
        }
    }

    async removeStrategy(symbol) {
        console.log(`🗑️ Удаляем стратегию для ${symbol}`);
        console.log(`📋 Стратегии до удаления:`, this.strategies);
        
        // Удаляем из локальных данных
        this.selectedSymbols.delete(symbol);
        delete this.strategies[symbol];
        
        console.log(`📋 Стратегии после удаления:`, this.strategies);
        
        // Обновляем UI
        this.renderStrategiesTable();
        this.updateActivePairsCount();
        
        // Сохраняем изменения на сервере
        try {
            await this.saveAllStrategies();
            this.addTradeLog(`🗑️ Удалена стратегия для ${symbol}`);
            this.showToast(`Стратегия ${symbol} удалена`, 'success');
        } catch (error) {
            console.error(`❌ Ошибка при удалении стратегии ${symbol}:`, error);
            this.addTradeLog(`❌ Ошибка удаления стратегии ${symbol}: ${error.message}`, 'error');
            this.showToast(`Ошибка удаления стратегии ${symbol}`, 'error');
        }
    }

    async saveAllStrategies() {
        try {
            // Фильтруем только торговые пары перед сохранением
            const isValidTradingPair = (symbol) => {
                return /^[A-Z]{2,10}USDT$/.test(symbol) || /^[A-Z]{2,10}BTC$/.test(symbol);
            };
            
            const filteredStrategies = {};
            Object.keys(this.strategies).forEach(symbol => {
                if (isValidTradingPair(symbol)) {
                    filteredStrategies[symbol] = this.strategies[symbol];
                } else {
                    console.log(`⚠️ Пропускаем невалидную торговую пару при сохранении: ${symbol}`);
                }
            });
            
            console.log('🔄 Сохраняем отфильтрованные стратегии:', filteredStrategies);
            console.log('📊 Количество отфильтрованных стратегий:', Object.keys(filteredStrategies).length);
            console.log('📊 Количество локальных стратегий:', Object.keys(this.strategies).length);
            const response = await fetch('/api/strategies', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(filteredStrategies)
            });

            console.log('📡 Ответ сервера:', response.status, response.statusText);

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Результат сохранения:', result);
                
                // НЕ обновляем локальные данные из ответа сервера
                // чтобы избежать перезаписи удаленных стратегий
                console.log('📋 Локальные стратегии остаются:', this.strategies);
                
                // Используем количество из ответа сервера или локальный подсчет
                const savedCount = result.count || Object.keys(filteredStrategies).length;
                this.addTradeLog(`✅ Сохранено ${savedCount} стратегий`);
                this.showToast(`Сохранено ${savedCount} стратегий`, 'success');
                return result;
            } else {
                const errorText = await response.text();
                console.error('❌ Ошибка ответа сервера:', errorText);
                throw new Error(`Ошибка сохранения: ${response.status} ${response.statusText}`);
            }
        } catch (error) {
            console.error('❌ Ошибка сохранения стратегий:', error);
            this.addTradeLog(`❌ Ошибка сохранения стратегий: ${error.message}`, 'error');
            this.showToast(`Ошибка сохранения стратегий: ${error.message}`, 'error');
        }
    }

    async startTrading() {
        if (this.selectedSymbols.size === 0) {
            this.showToast('Выберите хотя бы одну торговую пару', 'warning');
            return;
        }

        const config = this.getGeneralConfig();
        const symbols = Array.from(this.selectedSymbols);

        try {
            const response = await fetch('/api/trading/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    symbols: symbols,
                    config: config,
                    strategies: this.strategies
                })
            });

            if (response.ok) {
                this.tradingStatus = true;
                this.updateStatus();
                this.addTradeLog('🚀 Торговля запущена');
                this.showToast('Торговля успешно запущена', 'success');
            } else {
                throw new Error('Ошибка запуска торговли');
            }
        } catch (error) {
            console.error('Ошибка запуска торговли:', error);
            this.addTradeLog('❌ Ошибка запуска торговли', 'error');
            this.showToast('Ошибка запуска торговли', 'error');
        }
    }

    async stopTrading() {
        try {
            const response = await fetch('/api/trading/stop', {
                method: 'POST'
            });

            if (response.ok) {
                this.tradingStatus = false;
                this.updateStatus();
                this.addTradeLog('⏹️ Торговля остановлена');
                this.showToast('Торговля остановлена', 'info');
            } else {
                throw new Error('Ошибка остановки торговли');
            }
        } catch (error) {
            console.error('Ошибка остановки торговли:', error);
            this.addTradeLog('❌ Ошибка остановки торговли', 'error');
            this.showToast('Ошибка остановки торговли', 'error');
        }
    }

    getGeneralConfig() {
        return {
            buy_leverage: parseInt(document.getElementById('buyLeverage')?.value || 10),
            sell_leverage: parseInt(document.getElementById('sellLeverage')?.value || 10),
            trade_balance_pct: parseFloat(document.getElementById('tradeBalancePct')?.value || 3),
            stop_loss_pct: parseFloat(document.getElementById('stopLossPct')?.value || 20),
            take_profit_pct: document.getElementById('takeProfitPct')?.value ? 
                parseFloat(document.getElementById('takeProfitPct').value) : null,
            trade_interval_sec: parseInt(document.getElementById('tradeInterval')?.value || 60),
            mode: document.getElementById('tradingMode')?.value || 'real',
            timeframe: document.getElementById('tradingTimeframe')?.value || '15'
        };
    }

    saveGeneralConfig() {
        this.tradingConfig = this.getGeneralConfig();
        localStorage.setItem('tradingConfig', JSON.stringify(this.tradingConfig));
    }

    loadSavedConfig() {
        try {
            const savedConfig = localStorage.getItem('tradingConfig');
            if (savedConfig) {
                this.tradingConfig = JSON.parse(savedConfig);
                this.applySavedConfig();
                this.addTradeLog('⚙️ Загружены сохраненные настройки');
            }
        } catch (error) {
            console.error('Ошибка загрузки сохраненных настроек:', error);
        }
    }

    applySavedConfig() {
        // Применяем сохраненные настройки к полям формы
        if (this.tradingConfig.buy_leverage) {
            const element = document.getElementById('buyLeverage');
            if (element) element.value = this.tradingConfig.buy_leverage;
        }
        if (this.tradingConfig.sell_leverage) {
            const element = document.getElementById('sellLeverage');
            if (element) element.value = this.tradingConfig.sell_leverage;
        }
        if (this.tradingConfig.trade_balance_pct) {
            const element = document.getElementById('tradeBalancePct');
            if (element) element.value = this.tradingConfig.trade_balance_pct;
        }
        if (this.tradingConfig.stop_loss_pct) {
            const element = document.getElementById('stopLossPct');
            if (element) element.value = this.tradingConfig.stop_loss_pct;
        }
        if (this.tradingConfig.take_profit_pct) {
            const element = document.getElementById('takeProfitPct');
            if (element) element.value = this.tradingConfig.take_profit_pct;
        }
        if (this.tradingConfig.trade_interval_sec) {
            const element = document.getElementById('tradeInterval');
            if (element) element.value = this.tradingConfig.trade_interval_sec;
        }
        if (this.tradingConfig.mode) {
            const element = document.getElementById('tradingMode');
            if (element) element.value = this.tradingConfig.mode;
        }
        if (this.tradingConfig.timeframe) {
            const element = document.getElementById('tradingTimeframe');
            if (element) element.value = this.tradingConfig.timeframe;
        }
    }

    async loadTradingStatus() {
        try {
            const response = await fetch('/api/trading/status');
            if (response.ok) {
                const status = await response.json();
                this.tradingStatus = status.is_trading;
                
                // Обновляем выбранные символы из статуса
                if (status.symbols) {
                    status.symbols.forEach(symbol => {
                        this.selectedSymbols.add(symbol);
                    });
                }
                
                // Обновляем стратегии из статуса
                if (status.strategies) {
                    this.strategies = { ...this.strategies, ...status.strategies };
                }
                
                this.updateStatus();
                this.updateActivePairsCount();
                this.addTradeLog('📊 Статус торговли загружен');
            }
        } catch (error) {
            console.error('Ошибка загрузки статуса торговли:', error);
        }
    }

    updateStatus() {
        const badge = document.getElementById('tradingStatusBadge');
        const startBtn = document.getElementById('startTradingBtn');
        const stopBtn = document.getElementById('stopTradingBtn');

        if (this.tradingStatus) {
            badge.textContent = 'Активна';
            badge.className = 'badge bg-success me-2';
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            badge.textContent = 'Остановлена';
            badge.className = 'badge bg-secondary me-2';
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    }

    updateActivePairsCount() {
        const countElement = document.getElementById('activePairsCount');
        if (countElement) {
            countElement.textContent = this.selectedSymbols.size;
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        const textElement = document.getElementById('connectionText');
        
        if (statusElement) {
            statusElement.className = `status-indicator ${connected ? 'status-active' : 'status-inactive'}`;
        }
        
        if (textElement) {
            textElement.textContent = connected ? 'Подключено' : 'Отключено';
        }
    }

    addTradeLog(message, type = 'info') {
        const logContainer = document.getElementById('tradeLog');
        if (!logContainer) return;

        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `<span class="text-muted">[${timestamp}]</span> ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;

        // Ограничиваем количество записей
        while (logContainer.children.length > 100) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    clearTradeLog() {
        const logContainer = document.getElementById('tradeLog');
        if (logContainer) {
            logContainer.innerHTML = '<div class="text-muted">Лог торговли очищен...</div>';
        }
    }

    exportTradeLog() {
        const logContainer = document.getElementById('tradeLog');
        if (!logContainer) return;

        const logText = Array.from(logContainer.children)
            .map(entry => entry.textContent)
            .join('\n');

        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trade_log_${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    exportStrategies() {
        // Получаем актуальные настройки из формы
        const currentConfig = this.getGeneralConfig();
        
        // Фильтруем только торговые пары для экспорта
        const isValidTradingPair = (symbol) => {
            return /^[A-Z]{2,10}USDT$/.test(symbol) || /^[A-Z]{2,10}BTC$/.test(symbol);
        };
        
        const filteredStrategies = {};
        Object.keys(this.strategies).forEach(symbol => {
            if (isValidTradingPair(symbol)) {
                filteredStrategies[symbol] = this.strategies[symbol];
            }
        });
        
        const filteredSelectedSymbols = Array.from(this.selectedSymbols).filter(symbol => isValidTradingPair(symbol));
        
        // Создаем подробный объект экспорта
        const exportData = {
            metadata: {
                exportDate: new Date().toISOString(),
                version: '1.1',
                description: 'Экспорт торговых стратегий и настроек TradeBot',
                author: 'TradeBot System',
                totalStrategies: Object.keys(filteredStrategies).length,
                totalSymbols: filteredSelectedSymbols.length
            },
            tradingConfig: {
                general: {
                    buy_leverage: currentConfig.buy_leverage,
                    sell_leverage: currentConfig.sell_leverage,
                    trade_balance_pct: currentConfig.trade_balance_pct,
                    stop_loss_pct: currentConfig.stop_loss_pct,
                    take_profit_pct: currentConfig.take_profit_pct,
                    trade_interval_sec: currentConfig.trade_interval_sec,
                    mode: currentConfig.mode,
                    timeframe: currentConfig.timeframe
                },
                description: {
                    buy_leverage: 'Плечо для покупок (1-100)',
                    sell_leverage: 'Плечо для продаж (1-100)',
                    trade_balance_pct: 'Процент баланса на сделку (0.1-100)',
                    stop_loss_pct: 'Стоп-лосс в процентах (0.1-100)',
                    take_profit_pct: 'Тейк-профит в процентах (0.1-100, null = отключен)',
                    trade_interval_sec: 'Интервал проверки сигналов в секундах',
                    mode: 'Режим торговли (real/simulation)',
                    timeframe: 'Таймфрейм для анализа (1,5,15,30,60,240,1D)'
                }
            },
            strategies: filteredStrategies,
            selectedSymbols: filteredSelectedSymbols,
            strategyTypes: {
                ghost: 'Ghost Strategy - основана на pivot points и трендовых линиях',
                ott: 'OTT Strategy - One-Time Trigger с адаптивными уровнями',
                combined: 'Combined Strategy - комбинация Ghost и OTT стратегий'
            },
            notes: {
                strategyFormat: 'Каждая стратегия может быть строкой (тип) или объектом с параметрами',
                parameters: {
                    type: 'Тип стратегии (ghost/ott/combined)',
                    timeframe: 'Таймфрейм для стратегии',
                    leverage: 'Плечо для данной пары',
                    stop_loss: 'Стоп-лосс в процентах',
                    take_profit: 'Тейк-профит в процентах (null = отключен)',
                    balance_pct: 'Процент баланса для данной пары'
                }
            }
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tradebot_config_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.addTradeLog(`📤 Экспортирован конфиг: ${Object.keys(this.strategies).length} стратегий, ${this.selectedSymbols.size} символов`);
        this.showToast('Конфигурация экспортирована', 'success');
    }

    importStrategies(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                console.log('📥 Импортируемые данные:', data);
                
                // Поддержка старого и нового формата
                let strategies, config, selectedSymbols;
                
                if (data.strategies) {
                    // Новый формат
                    strategies = data.strategies;
                    config = data.tradingConfig?.general || data.config;
                    selectedSymbols = data.selectedSymbols || [];
                    
                    // Применяем общие настройки
                    if (config) {
                        this.tradingConfig = { ...this.tradingConfig, ...config };
                        this.applySavedConfig();
                        this.saveGeneralConfig();
                    }
                    
                    // Добавляем выбранные символы
                    selectedSymbols.forEach(symbol => {
                        this.selectedSymbols.add(symbol);
                    });
                    
                    this.addTradeLog(`📥 Импортирован конфиг версии ${data.metadata?.version || '1.0'}`);
                    if (data.metadata) {
                        this.addTradeLog(`📊 Стратегий: ${data.metadata.totalStrategies}, Символов: ${data.metadata.totalSymbols}`);
                    }
                } else {
                    throw new Error('Неверный формат файла: отсутствуют стратегии');
                }
                
                // Применяем стратегии
                this.strategies = strategies;
                this.renderStrategiesTable();
                this.updateActivePairsCount();
                this.saveAllStrategies();
                
                this.addTradeLog(`✅ Импортировано ${Object.keys(strategies).length} стратегий`);
                this.showToast('Конфигурация импортирована', 'success');
                
            } catch (error) {
                console.error('Ошибка импорта конфига:', error);
                this.addTradeLog(`❌ Ошибка импорта: ${error.message}`, 'error');
                this.showToast('Ошибка импорта конфига', 'error');
            }
        };
        reader.readAsText(file);
    }

    updateLastTradeTime() {
        const timeElement = document.getElementById('lastTradeTime');
        if (timeElement) {
            timeElement.textContent = new Date().toLocaleTimeString();
        }
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastBody = document.getElementById('toastBody');
        
        if (toast && toastBody) {
            toastBody.textContent = message;
            toast.className = `toast show bg-${type}`;
            
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }
    }
}

// Глобальные функции для кнопок
function selectPopularPairs() {
    const checkboxes = document.querySelectorAll('#popularPairsContainer input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
        tradingManager.selectedSymbols.add(checkbox.value);
    });
    tradingManager.updateActivePairsCount();
    tradingManager.renderStrategiesTable();
}

function selectAllPairs() {
    const checkboxes = document.querySelectorAll('#allPairsContainer input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
        tradingManager.selectedSymbols.add(checkbox.value);
    });
    tradingManager.updateActivePairsCount();
    tradingManager.renderStrategiesTable();
}

function addStrategyRow() {
    tradingManager.addStrategyRow();
}

function saveAllStrategies() {
    tradingManager.saveAllStrategies();
}

function loadStrategies() {
    tradingManager.loadStrategies();
    tradingManager.showToast('Стратегии загружены', 'success');
}

async function clearAllStrategies() {
    if (confirm('Вы уверены, что хотите очистить все стратегии?')) {
        console.log('🗑️ Очищаем ВСЕ стратегии...');
        console.log('📋 Стратегии до очистки:', tradingManager.strategies);
        
        // Очищаем ВСЕ стратегии
        tradingManager.strategies = {};
        tradingManager.selectedSymbols.clear();
        
        console.log('📋 Стратегии после очистки:', tradingManager.strategies);
        
        // Обновляем UI
        tradingManager.renderStrategiesTable();
        tradingManager.updateActivePairsCount();
        
        // Сохраняем изменения на сервере
        try {
            await tradingManager.saveAllStrategies();
            tradingManager.addTradeLog('🗑️ ВСЕ стратегии очищены');
            tradingManager.showToast('Все стратегии очищены', 'success');
        } catch (error) {
            console.error('❌ Ошибка при очистке стратегий:', error);
            tradingManager.addTradeLog(`❌ Ошибка очистки стратегий: ${error.message}`, 'error');
            tradingManager.showToast('Ошибка очистки стратегий', 'error');
        }
    }
}

async function forceClearAllStrategies() {
    if (confirm('ВНИМАНИЕ! Это удалит ВСЕ стратегии без исключения. Продолжить?')) {
        console.log('🗑️ Принудительно очищаем ВСЕ стратегии...');
        console.log('📋 Стратегии до очистки:', tradingManager.strategies);
        
        // Очищаем ВСЕ стратегии
        tradingManager.strategies = {};
        tradingManager.selectedSymbols.clear();
        
        console.log('📋 Стратегии после очистки:', tradingManager.strategies);
        
        // Обновляем UI
        tradingManager.renderStrategiesTable();
        tradingManager.updateActivePairsCount();
        
        // Сохраняем изменения на сервере
        try {
            await tradingManager.saveAllStrategies();
            tradingManager.addTradeLog('🗑️ ВСЕ стратегии принудительно очищены');
            tradingManager.showToast('Все стратегии принудительно очищены', 'success');
        } catch (error) {
            console.error('❌ Ошибка при принудительной очистке стратегий:', error);
            tradingManager.addTradeLog(`❌ Ошибка принудительной очистки стратегий: ${error.message}`, 'error');
            tradingManager.showToast('Ошибка принудительной очистки стратегий', 'error');
        }
    }
}

function clearTradeLog() {
    tradingManager.clearTradeLog();
}

function exportTradeLog() {
    tradingManager.exportTradeLog();
}

function exportStrategies() {
    tradingManager.exportStrategies();
}

function importStrategies() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
        if (e.target.files.length > 0) {
            tradingManager.importStrategies(e.target.files[0]);
        }
    };
    input.click();
}

// Инициализация при загрузке страницы
let tradingManager;
document.addEventListener('DOMContentLoaded', () => {
    tradingManager = new TradingManager();
});

