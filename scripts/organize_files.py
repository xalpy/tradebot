import os
import shutil

def create_directories():
    """Создает структуру папок"""
    directories = [
        'tests',
        'docs',
        'scripts',
        'backup'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Создана папка: {directory}")

def organize_files():
    """Организует файлы по папкам"""
    
    # Создаем папки
    create_directories()
    
    # Перемещаем тестовые файлы
    test_files = [
        'test_advanced_backtest.py',
        'test_chart.py',
        'test_new_backtest.py',
        'test_double_signals.py',
        'test_real_api.py',
        'test_historical.py',
        'test_api.py'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            shutil.move(file, f'tests/{file}')
            print(f"📁 Перемещен: {file} → tests/")
    
    # Перемещаем скрипты
    script_files = [
        'organize_files.py'
    ]
    
    for file in script_files:
        if os.path.exists(file):
            shutil.move(file, f'scripts/{file}')
            print(f"📁 Перемещен: {file} → scripts/")
    
    # Создаем README файл
    create_readme()
    
    # Создаем .gitignore
    create_gitignore()
    
    print("\n🎉 Организация файлов завершена!")

def create_readme():
    """Создает README файл"""
    readme_content = """# Trading Bot Dashboard

Современный веб-интерфейс для торгового бота с поддержкой Bybit API.

## 🚀 Возможности

- **Реальное время**: Отслеживание цен и позиций в реальном времени
- **Бэктестинг**: Продвинутый бэктест с настройкой плеча и стоп-лосса
- **Графики**: Интерактивные свечные графики с LightweightCharts
- **Автоторговля**: Автоматическая торговля с логикой "двойных сигналов"
- **Управление рисками**: Настройка стоп-лосса и размера позиций

## 📁 Структура проекта

```
├── main.py              # Основной скрипт для CLI
├── web_app.py           # Flask веб-приложение
├── bybit_api.py         # API для работы с Bybit
├── strategy.py          # Торговая стратегия GhostTangent
├── backtester.py        # Система бэктестинга
├── config.py            # Конфигурация API ключей
├── requirements.txt     # Зависимости Python
├── static/              # Статические файлы (CSS, JS)
├── templates/           # HTML шаблоны
├── tests/               # Тестовые скрипты
├── scripts/             # Вспомогательные скрипты
└── docs/                # Документация
```

## 🛠 Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте API ключи в `config.py`

3. Запустите веб-приложение:
```bash
python web_app.py
```

## 📊 Бэктестинг

Бэктест поддерживает:
- Настройку плеча (1x-100x)
- Стоп-лосс (0.1%-50%)
- Размер позиции (1%-100%)
- Начальный баланс
- Анализ причин выхода из позиций

## 🔧 Конфигурация

Основные параметры в `config.py`:
- `REAL_API_KEY` / `REAL_API_SECRET` - API ключи для реальной торговли
- `TEST_API_KEY` / `TEST_API_SECRET` - API ключи для тестовой торговли

## 📈 Стратегия

GhostTangent Strategy основана на:
- Определении пивотных точек (pivot high/low)
- Сигналах входа и выхода
- Логике "двойных сигналов" для разворота позиций

## 🚨 Риски

- Торговля криптовалютами связана с высокими рисками
- Используйте только те средства, которые можете позволить себе потерять
- Тестируйте стратегии на демо-счетах перед реальной торговлей

## 📝 Лицензия

Этот проект предназначен для образовательных целей.
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("📝 Создан README.md")

def create_gitignore():
    """Создает .gitignore файл"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# API Keys (безопасность)
config_backup.py
.env

# Temporary files
*.tmp
*.temp
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print("📝 Создан .gitignore")

if __name__ == "__main__":
    organize_files() 