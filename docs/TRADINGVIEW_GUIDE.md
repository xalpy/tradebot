# 📈 Руководство по интеграции TradingView

## Обзор

Вместо создания собственных графиков, вы можете использовать профессиональные графики TradingView. Это дает вам:

- ✅ Все индикаторы и инструменты TradingView
- ✅ Профессиональный интерфейс
- ✅ Инструменты рисования и анализа
- ✅ Новости и календарь событий
- ✅ Множество таймфреймов
- ✅ Мобильная адаптация

## 🚀 Варианты интеграции

### 1. Полнофункциональный виджет (рекомендуется)

**URL:** `/tradingview`

**Особенности:**
- Полный TradingView виджет с API
- Интерактивные элементы управления
- Возможность добавления индикаторов
- Инструменты рисования
- Новости и анализ

**Использование:**
```javascript
// Создание виджета
new TradingView.widget({
    "symbol": "BINANCE:BTCUSDT",
    "interval": "15",
    "theme": "dark",
    "studies": [
        "MASimple@tv-basicstudies",
        "RSI@tv-basicstudies",
        "MACD@tv-basicstudies"
    ]
});
```

### 2. Простой iframe (самый простой)

**URL:** `/tradingview-simple`

**Особенности:**
- Простое встраивание через iframe
- Минимальная настройка
- Быстрая загрузка
- Все функции TradingView

**Использование:**
```html
<iframe 
    src="https://www.tradingview.com/symbols/BINANCE-BTCUSDT/?interval=15&theme=dark"
    width="100%" 
    height="600px">
</iframe>
```

### 3. Интеграция в основное приложение

**Функция:** Переключение между обычным графиком и TradingView

**Особенности:**
- Кнопка переключения в интерфейсе
- Сохранение настроек
- Автоматическое обновление при смене символа

## 🛠️ Настройка

### Поддерживаемые символы

Все символы Binance доступны в формате:
- `BINANCE:BTCUSDT`
- `BINANCE:ETHUSDT`
- `BINANCE:SOLUSDT`
- И другие...

### Интервалы времени

- `1` - 1 минута
- `5` - 5 минут
- `15` - 15 минут
- `30` - 30 минут
- `60` - 1 час
- `240` - 4 часа
- `1D` - 1 день

### Темы оформления

- `dark` - Темная тема
- `light` - Светлая тема

## 📊 Индикаторы

### Базовые индикаторы

```javascript
"studies": [
    "MASimple@tv-basicstudies",    // Простая скользящая средняя
    "RSI@tv-basicstudies",         // RSI
    "MACD@tv-basicstudies",        // MACD
    "BB@tv-basicstudies",          // Bollinger Bands
    "Stochastic@tv-basicstudies"   // Stochastic
]
```

### Пользовательские индикаторы

Вы можете добавить любые индикаторы из библиотеки TradingView:

```javascript
"studies": [
    "MASimple@tv-basicstudies",
    "RSI@tv-basicstudies",
    "MACD@tv-basicstudies",
    "Volume@tv-basicstudies",
    "EMA@tv-basicstudies",
    "SMA@tv-basicstudies"
]
```

## 🔧 API функции

### Изменение символа

```javascript
widget.setSymbol("BINANCE:ETHUSDT", "15");
```

### Изменение интервала

```javascript
widget.setSymbol(currentSymbol, "60");
```

### Изменение типа графика

```javascript
widget.setChartType(1); // 1-свечи, 2-бары, 3-линия, 4-площадь
```

### Полноэкранный режим

```javascript
widget.fullscreen();
```

## 🎨 Кастомизация

### Настройка внешнего вида

```javascript
new TradingView.widget({
    "width": "100%",
    "height": "600px",
    "symbol": "BINANCE:BTCUSDT",
    "interval": "15",
    "timezone": "Europe/Moscow",
    "theme": "dark",
    "style": "1",
    "locale": "ru",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "container_id": "tradingview-widget"
});
```

### Добавление новостей

```javascript
"news": [
    "headlines"  // Показывать заголовки новостей
]
```

### Добавление календаря

```javascript
"calendar": true  // Показывать календарь событий
```

## 🔗 Полезные ссылки

- [TradingView Widget API](https://www.tradingview.com/widget/)
- [Документация TradingView](https://www.tradingview.com/HTML5-stock-forex-bitcoin-charting-library/)
- [Примеры использования](https://www.tradingview.com/widget/advanced-chart/)

## 💡 Советы

1. **Производительность:** Используйте iframe для простых случаев
2. **Функциональность:** Используйте виджет для полного контроля
3. **Мобильность:** TradingView автоматически адаптируется под мобильные устройства
4. **Кэширование:** Виджет кэширует данные для быстрой загрузки
5. **Безопасность:** Все данные загружаются напрямую с TradingView

## 🚨 Ограничения

- Требуется интернет-соединение
- Зависимость от доступности TradingView
- Ограничения на количество запросов (для API)
- Некоторые функции могут быть платными

## 📱 Мобильная версия

TradingView автоматически адаптируется под мобильные устройства. Для лучшего опыта:

```javascript
// Проверка мобильного устройства
if (window.innerWidth < 768) {
    // Настройки для мобильных
    widget = new TradingView.widget({
        "width": "100%",
        "height": "400px",
        "hide_side_toolbar": true,  // Скрываем боковую панель
        "studies": []  // Минимум индикаторов
    });
}
```

## 🔄 Обновления

Для автоматического обновления данных:

```javascript
// Обновление каждые 5 секунд
setInterval(() => {
    if (widget) {
        widget.setSymbol(currentSymbol, currentInterval);
    }
}, 5000);
```

---

**Примечание:** TradingView предоставляет бесплатные виджеты для некоммерческого использования. Для коммерческих проектов может потребоваться лицензия. 