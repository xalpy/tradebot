#!/usr/bin/env python3
"""
Скрипт для создания README файлов в папках с тестами
"""

import os

def create_readme_for_tests():
    """Создает README файлы для папок с тестами"""
    
    test_directories = {
        'tests/chart_tests': {
            'title': 'Тесты графиков',
            'description': 'Тесты для проверки работы графиков и библиотеки LightweightCharts',
            'files': [
                'test_chart_creation.html - Изолированный тест создания графика',
                'test_chart.html - Тест графика с реальными данными',
                'test_chart_data.py - Тест получения данных для графика',
                'test_library.html - Тест загрузки библиотеки LightweightCharts',
                'test_styles.html - Тест стилей для элементов интерфейса'
            ]
        },
        'tests/data_tests': {
            'title': 'Тесты данных',
            'description': 'Тесты для проверки корректности данных и их типов',
            'files': [
                'test_data_types.py - Тест типов данных от API',
                'test_data_validation.py - Тест валидации данных',
                'test_real_data.py - Тест реальных данных от Bybit API',
                'compare_data.py - Сравнение тестовых и реальных данных'
            ]
        },
        'tests/strategy_tests': {
            'title': 'Тесты стратегий',
            'description': 'Тесты для проверки работы торговых стратегий',
            'files': [
                'test_combined_strategy.py - Тест комбинированной стратегии',
                'test_advanced_backtest.py - Тест расширенного бэктестинга',
                'test_new_backtest.py - Тест нового бэктестера',
                'test_double_signals.py - Тест двойных сигналов',
                'test_take_profit.py - Тест функции тейк-профита'
            ]
        },
        'tests/api_tests': {
            'title': 'Тесты API',
            'description': 'Тесты для проверки работы с Bybit API',
            'files': [
                'test_api.py - Базовые тесты API',
                'test_real_api.py - Тесты с реальным API',
                'test_historical.py - Тесты исторических данных'
            ]
        },
        'tests/ui_tests': {
            'title': 'Тесты интерфейса',
            'description': 'Тесты для проверки пользовательского интерфейса',
            'files': [
                'test_trading_pairs.py - Тест загрузки торговых пар',
                'test_fixes.py - Тест исправлений интерфейса'
            ]
        },
        'debug': {
            'title': 'Отладочные файлы',
            'description': 'Файлы для отладки и диагностики проблем',
            'files': [
                'debug_chart.py - Отладка проблем с графиками',
                'quick_test.py - Быстрые тесты для проверки функциональности'
            ]
        }
    }
    
    for directory, info in test_directories.items():
        if os.path.exists(directory):
            readme_content = f"""# {info['title']}

{info['description']}

## Файлы в этой папке:

"""
            for file_info in info['files']:
                readme_content += f"- {file_info}\n"
            
            readme_content += f"""
## Запуск тестов

Для запуска всех тестов в этой папке:

```bash
cd {directory}
python -m pytest *.py
```

Для запуска конкретного теста:

```bash
python test_file.py
```

## Результаты

Результаты тестов выводятся в консоль. Успешные тесты помечаются ✅, неудачные - ❌.
"""
            
            readme_path = os.path.join(directory, 'README.md')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            print(f"✅ Создан README для {directory}")

def create_main_test_readme():
    """Создает основной README для папки tests"""
    
    content = """# Тесты проекта TradeBot

Эта папка содержит все тесты для проекта торгового бота.

## Структура тестов

### 📊 tests/chart_tests/
Тесты для проверки работы графиков и библиотеки LightweightCharts
- Создание графиков
- Отображение свечей
- Загрузка библиотеки
- Стили интерфейса

### 📋 tests/data_tests/
Тесты для проверки корректности данных
- Типы данных от API
- Валидация данных
- Реальные данные от Bybit
- Сравнение данных

### 📈 tests/strategy_tests/
Тесты торговых стратегий
- Комбинированная стратегия
- Бэктестинг
- Сигналы
- Тейк-профит

### 🔌 tests/api_tests/
Тесты API Bybit
- Базовые операции
- Реальные запросы
- Исторические данные

### 🖥️ tests/ui_tests/
Тесты пользовательского интерфейса
- Загрузка торговых пар
- Исправления UI

### 🐛 debug/
Отладочные файлы
- Диагностика проблем
- Быстрые тесты

## Запуск тестов

### Все тесты
```bash
python -m pytest tests/
```

### Конкретная категория
```bash
python -m pytest tests/chart_tests/
python -m pytest tests/data_tests/
python -m pytest tests/strategy_tests/
```

### Конкретный тест
```bash
python tests/chart_tests/test_chart_creation.html
python tests/data_tests/test_real_data.py
```

## Требования

- Python 3.7+
- pytest
- requests
- pandas
- pybit

## Результаты

Тесты выводят результаты в консоль:
- ✅ Успешные тесты
- ❌ Неудачные тесты
- ⚠️ Предупреждения
- 📊 Статистика

## Добавление новых тестов

1. Создайте файл в соответствующей папке
2. Добавьте описание в README.md папки
3. Обновите этот файл при необходимости
"""
    
    with open('tests/README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Создан основной README для tests/")

def main():
    """Главная функция"""
    print("📝 Создание README файлов для тестов")
    print("=" * 40)
    
    create_readme_for_tests()
    create_main_test_readme()
    
    print("\n" + "=" * 40)
    print("✅ README файлы созданы!")
    print("📋 Документация готова для всех папок с тестами")

if __name__ == "__main__":
    main() 