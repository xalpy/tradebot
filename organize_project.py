#!/usr/bin/env python3
"""
Скрипт для организации файлов проекта
Перемещает файлы по соответствующим папкам
"""

import os
import shutil
import glob
from pathlib import Path

def create_directory_if_not_exists(directory):
    """Создает директорию, если она не существует"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"📁 Создана директория: {directory}")
    else:
        print(f"📁 Директория уже существует: {directory}")

def move_file(source, destination):
    """Перемещает файл с проверкой на существование"""
    if os.path.exists(source):
        if os.path.exists(destination):
            print(f"⚠️ Файл уже существует: {destination}")
            return False
        
        try:
            shutil.move(source, destination)
            print(f"✅ Перемещен: {source} → {destination}")
            return True
        except Exception as e:
            print(f"❌ Ошибка перемещения {source}: {e}")
            return False
    else:
        print(f"⚠️ Файл не найден: {source}")
        return False

def organize_project():
    """Основная функция организации проекта"""
    print("🧹 Организация файлов проекта")
    print("=" * 50)
    
    # Создаем необходимые директории
    directories = [
        'tests/chart_tests',
        'tests/data_tests', 
        'tests/strategy_tests',
        'tests/api_tests',
        'tests/ui_tests',
        'debug',
        'temp',
        'logs'
    ]
    
    for directory in directories:
        create_directory_if_not_exists(directory)
    
    print("\n📋 Перемещение файлов:")
    print("-" * 30)
    
    # Тесты для графиков
    chart_tests = [
        'test_chart_creation.html',
        'test_chart.html',
        'test_chart_data.py',
        'test_library.html',
        'test_styles.html'
    ]
    
    for file in chart_tests:
        if os.path.exists(file):
            move_file(file, f'tests/chart_tests/{file}')
    
    # Тесты данных
    data_tests = [
        'test_data_types.py',
        'test_data_validation.py',
        'test_real_data.py',
        'compare_data.py'
    ]
    
    for file in data_tests:
        if os.path.exists(file):
            move_file(file, f'tests/data_tests/{file}')
    
    # Тесты стратегий
    strategy_tests = [
        'test_combined_strategy.py',
        'test_advanced_backtest.py',
        'test_new_backtest.py',
        'test_double_signals.py',
        'test_take_profit.py'
    ]
    
    for file in strategy_tests:
        if os.path.exists(file):
            move_file(file, f'tests/strategy_tests/{file}')
    
    # Тесты API
    api_tests = [
        'test_api.py',
        'test_real_api.py',
        'test_historical.py'
    ]
    
    for file in api_tests:
        if os.path.exists(file):
            move_file(file, f'tests/api_tests/{file}')
    
    # UI тесты
    ui_tests = [
        'test_trading_pairs.py',
        'test_fixes.py'
    ]
    
    for file in ui_tests:
        if os.path.exists(file):
            move_file(file, f'tests/ui_tests/{file}')
    
    # Отладочные файлы
    debug_files = [
        'debug_chart.py',
        'quick_test.py'
    ]
    
    for file in debug_files:
        if os.path.exists(file):
            move_file(file, f'debug/{file}')
    
    # Перемещаем существующие тесты из папки tests
    existing_tests = [
        'tests/test_chart.py'
    ]
    
    for file in existing_tests:
        if os.path.exists(file):
            move_file(file, f'tests/chart_tests/test_chart.py')
    
    print("\n🧹 Очистка временных файлов:")
    print("-" * 30)
    
    # Удаляем __pycache__ директории
    pycache_dirs = glob.glob('**/__pycache__', recursive=True)
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            print(f"🗑️ Удален: {pycache_dir}")
        except Exception as e:
            print(f"⚠️ Не удалось удалить {pycache_dir}: {e}")
    
    # Удаляем .pyc файлы
    pyc_files = glob.glob('**/*.pyc', recursive=True)
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            print(f"🗑️ Удален: {pyc_file}")
        except Exception as e:
            print(f"⚠️ Не удалось удалить {pyc_file}: {e}")
    
    print("\n📊 Создание отчета:")
    print("-" * 30)
    
    # Создаем отчет о структуре
    report = []
    report.append("# Структура проекта после организации")
    report.append("")
    
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '.git' in root:
            continue
        
        level = root.replace('.', '').count(os.sep)
        indent = '  ' * level
        report.append(f"{indent}{os.path.basename(root)}/")
        
        subindent = '  ' * (level + 1)
        for file in sorted(files):
            if not file.startswith('.'):
                report.append(f"{subindent}{file}")
    
    # Сохраняем отчет
    with open('PROJECT_STRUCTURE.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print("✅ Отчет сохранен в PROJECT_STRUCTURE.md")
    
    print("\n🎯 Рекомендации:")
    print("-" * 30)
    print("1. Проверьте, что все файлы перемещены корректно")
    print("2. Обновите импорты в тестах, если необходимо")
    print("3. Добавьте новые папки в .gitignore, если нужно")
    print("4. Проверьте, что все тесты работают после перемещения")

def create_gitignore_updates():
    """Создает обновления для .gitignore"""
    print("\n📝 Обновление .gitignore:")
    print("-" * 30)
    
    gitignore_additions = [
        "",
        "# Временные файлы",
        "temp/",
        "logs/",
        "",
        "# Отладочные файлы", 
        "debug/",
        "",
        "# Отчеты",
        "PROJECT_STRUCTURE.md"
    ]
    
    with open('.gitignore', 'a', encoding='utf-8') as f:
        f.write('\n'.join(gitignore_additions))
    
    print("✅ Добавлены новые правила в .gitignore")

def main():
    """Главная функция"""
    try:
        organize_project()
        create_gitignore_updates()
        
        print("\n" + "=" * 50)
        print("✅ Организация проекта завершена!")
        print("📁 Файлы распределены по папкам")
        print("🗑️ Временные файлы удалены")
        print("📋 Отчет создан")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 