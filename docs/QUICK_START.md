# 🚀 Быстрый старт

## Установка и запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка API ключей
Отредактируйте файл `config.py`:
```python
REAL_API_KEY = "ваш_реальный_ключ"
REAL_API_SECRET = "ваш_реальный_секрет"
TEST_API_KEY = "ваш_тестовый_ключ"
TEST_API_SECRET = "ваш_тестовый_секрет"
```

### 3. Запуск веб-приложения
```bash
python web_app.py
```

### 4. Открытие в браузере
Перейдите по адресу: `http://127.0.0.1:5000`

## Основные функции

### 📊 Бэктестинг
1. Перейдите на вкладку "Бэктест"
2. Выберите символ и интервал
3. Выберите стратегию:
   - **GhostTangent**: Классическая стратегия на пивотных точках
   - **OTT**: Optimized Trend Tracker
   - **Комбинированная**: Объединение обеих стратегий (рекомендуется)
4. Настройте параметры:
   - Плечо (1x-100x)
   - Стоп-лосс (0.1%-50%)
   - Тейк-профит (0.1%-100%, опционально)
   - Начальный баланс
   - Размер позиции
5. Нажмите "Запустить бэктест"

### 📈 Графики
1. Перейдите на вкладку "Графики"
2. Выберите символ и интервал
3. График загрузится автоматически

### 🤖 Автоторговля
1. Перейдите на вкладку "Торговля"
2. Настройте параметры торговли
3. Нажмите "Запустить торговлю"

## Полезные команды

### CLI режим (без веб-интерфейса)
```bash
# Бэктест
python main.py backtest BTCUSDT 15 30

# Торговля
python main.py trade BTCUSDT
```

### Тестирование
```bash
# Тест API
python tests/test_api.py

# Тест бэктеста
python tests/test_advanced_backtest.py

# Тест стратегии
python tests/test_double_signals.py

# Тест комбинированной стратегии
python tests/test_combined_strategy.py
```

## Структура файлов

```
├── main.py              # CLI приложение
├── web_app.py           # Веб-приложение
├── bybit_api.py         # API Bybit
├── strategy.py          # GhostTangent стратегия
├── ott_strategy.py      # OTT стратегия
├── combined_strategy.py # Комбинированная стратегия
├── backtester.py        # Система бэктестинга
├── config.py            # Конфигурация
├── static/              # CSS, JS файлы
├── templates/           # HTML шаблоны
├── tests/               # Тесты
└── docs/                # Документация
```

## Поддержка

- 📖 Полная документация: `docs/`
- 🧪 Тесты: `tests/`
- 📝 API Reference: `docs/API_REFERENCE.md`
- 📈 Strategy Guide: `docs/STRATEGY_GUIDE.md`
- 🔄 Combined Strategy: `docs/COMBINED_STRATEGY_GUIDE.md` 