# API Reference

## BybitAPI Class

Основной класс для работы с Bybit API.

### Методы

#### `__init__(api_key, api_secret, trade_mode='test')`
Инициализация API клиента.
- `api_key` - API ключ
- `api_secret` - API секрет
- `trade_mode` - Режим торговли ('test' или 'real')

#### `get_klines(symbol, interval, limit=200)`
Получение исторических данных (свечи).
- `symbol` - Торговая пара (например, 'BTCUSDT')
- `interval` - Интервал ('1', '5', '15', '30', '60')
- `limit` - Количество записей (максимум 1000)

#### `get_all_trading_pairs()`
Получение всех доступных торговых пар.
Возвращает список пар, отсортированных по объему торгов.

#### `get_popular_pairs()`
Получение популярных торговых пар.
Возвращает предопределенный список популярных пар.

#### `get_balance(coin="USDT")`
Получение баланса по валюте.
- `coin` - Код валюты

#### `get_all_balances()`
Получение всех балансов аккаунта.

#### `get_open_positions(symbol)`
Получение открытых позиций по символу.

#### `place_order(symbol, side, qty, price=None, stop_loss=None, take_profit=None, order_type="Market", reduce_only=False)`
Размещение ордера.
- `symbol` - Торговая пара
- `side` - Сторона ('Buy' или 'Sell')
- `qty` - Количество
- `price` - Цена (для лимитных ордеров)
- `stop_loss` - Процент стоп-лосса
- `take_profit` - Процент тейк-профита
- `order_type` - Тип ордера ('Market' или 'Limit')
- `reduce_only` - Только закрытие позиции

## Web API Endpoints

### GET `/api/balance`
Получение баланса USDT.

### GET `/api/balances`
Получение всех балансов.

### GET `/api/positions`
Получение открытых позиций.

### GET `/api/klines/<symbol>`
Получение исторических данных для графика.
- Параметры: `interval`, `limit`

### GET `/api/trading_pairs`
Получение всех доступных торговых пар.
Возвращает популярные и все торговые пары с информацией о ценах и объемах.

### GET `/api/trading_pairs/search`
Поиск торговых пар по символу.
- Параметры: `q` - поисковый запрос

### POST `/api/backtest`
Запуск бэктеста.
```json
{
    "symbol": "BTCUSDT",
    "interval": "15",
    "days_back": 30,
    "leverage": 10,
    "stop_loss_pct": 2.0,
    "take_profit_pct": 3.0,
    "initial_balance": 1000.0,
    "trade_size_pct": 3.0
}
```

### POST `/api/trading/start`
Запуск автоматической торговли.
```json
{
    "symbols": ["BTCUSDT"],
    "config": {
        "buy_leverage": 10,
        "sell_leverage": 10,
        "trade_balance_pct": 0.03,
        "stop_loss_pct": 0.2,
        "take_profit_pct": 0.3,
        "trade_interval_sec": 60,
        "mode": "real"
    }
}
```

### POST `/api/trading/stop`
Остановка автоматической торговли.

### GET `/api/trading/status`
Получение статуса торговли.

### POST `/api/place_order`
Размещение ручного ордера.
```json
{
    "symbol": "BTCUSDT",
    "side": "Buy",
    "qty": 0.001,
    "price": 50000,
    "order_type": "Limit",
    "stop_loss": 0.02,
    "take_profit": 0.03
}
```

## WebSocket Events

### `trade_executed`
Уведомление о выполнении сделки.
```json
{
    "symbol": "BTCUSDT",
    "side": "Buy",
    "qty": 0.001,
    "action": "opened|closed|reversed"
}
```

### `price_update`
Обновление цены в реальном времени.

### `error`
Уведомление об ошибке. 