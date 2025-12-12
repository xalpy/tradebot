#!/usr/bin/env python3
"""
Главный скрипт для полной организации проекта TradeBot
Выполняет все операции по очистке и организации файлов
"""

import os
import sys
import subprocess

def run_script(script_name, description):
    """Запускает скрипт с описанием"""
    print(f"\n🔄 {description}")
    print("-" * 40)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"✅ {description} завершено успешно")
            return True
        else:
            print(f"❌ Ошибка в {script_name}:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Не удалось запустить {script_name}: {e}")
        return False

def check_prerequisites():
    """Проверяет необходимые условия"""
    print("🔍 Проверка условий для организации проекта")
    print("-" * 40)
    
    # Проверяем, что мы в корневой папке проекта
    required_files = ['web_app.py', 'main.py', 'requirements.txt']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют необходимые файлы: {missing_files}")
        print("💡 Убедитесь, что вы находитесь в корневой папке проекта")
        return False
    
    print("✅ Все необходимые файлы найдены")
    return True

def create_backup():
    """Создает резервную копию перед организацией"""
    print("\n💾 Создание резервной копии")
    print("-" * 40)
    
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup/before_organization_{timestamp}"
    
    try:
        # Создаем папку для резервной копии
        os.makedirs(backup_dir, exist_ok=True)
        
        # Копируем файлы, которые будут перемещены
        files_to_backup = [
            'test_chart_creation.html',
            'test_chart.html',
            'test_chart_data.py',
            'test_library.html',
            'test_styles.html',
            'test_data_types.py',
            'test_data_validation.py',
            'test_real_data.py',
            'compare_data.py',
            'test_combined_strategy.py',
            'test_advanced_backtest.py',
            'test_new_backtest.py',
            'test_double_signals.py',
            'test_take_profit.py',
            'test_api.py',
            'test_real_api.py',
            'test_historical.py',
            'test_trading_pairs.py',
            'test_fixes.py',
            'debug_chart.py',
            'quick_test.py'
        ]
        
        copied_count = 0
        for file in files_to_backup:
            if os.path.exists(file):
                shutil.copy2(file, backup_dir)
                copied_count += 1
        
        print(f"✅ Резервная копия создана: {backup_dir}")
        print(f"📁 Скопировано файлов: {copied_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
        return False

def main():
    """Главная функция"""
    print("🧹 Полная организация проекта TradeBot")
    print("=" * 50)
    
    # Проверяем условия
    if not check_prerequisites():
        print("\n❌ Условия не выполнены. Организация прервана.")
        return
    
    # Создаем резервную копию
    if not create_backup():
        print("\n⚠️ Резервная копия не создана, но продолжаем...")
    
    # Запускаем скрипты организации
    scripts = [
        ('organize_project.py', 'Организация файлов по папкам'),
        ('create_test_readmes.py', 'Создание документации для тестов')
    ]
    
    success_count = 0
    for script, description in scripts:
        if run_script(script, description):
            success_count += 1
    
    print("\n" + "=" * 50)
    print("📊 Результаты организации:")
    print(f"✅ Успешно выполнено: {success_count}/{len(scripts)}")
    
    if success_count == len(scripts):
        print("\n🎉 Организация проекта завершена успешно!")
        print("\n📋 Что было сделано:")
        print("   📁 Созданы структурированные папки для тестов")
        print("   📄 Файлы перемещены по категориям")
        print("   🗑️ Удалены временные файлы")
        print("   📝 Создана документация")
        print("   💾 Создана резервная копия")
        
        print("\n🎯 Следующие шаги:")
        print("   1. Проверьте структуру проекта")
        print("   2. Убедитесь, что все тесты работают")
        print("   3. Обновите импорты, если необходимо")
        print("   4. Проверьте .gitignore")
        
    else:
        print("\n⚠️ Организация завершена с ошибками")
        print("💡 Проверьте логи выше и исправьте проблемы")
    
    print(f"\n📁 Резервная копия: backup/before_organization_*")
    print("📋 Отчет: PROJECT_STRUCTURE.md")

if __name__ == "__main__":
    main() 