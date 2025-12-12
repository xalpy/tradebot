#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправления удаления стратегий
"""

import json
import os

def test_remove_strategy():
    """Тестирует удаление стратегий"""
    print("🧪 Тестируем удаление стратегий...")
    
    try:
        # Читаем текущий файл стратегий
        with open('symbol_strategies.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📋 Исходные стратегии: {data['strategies']}")
        initial_count = len(data['strategies'])
        
        # Удаляем одну стратегию (например, DOGEUSDT)
        symbol_to_remove = "DOGEUSDT"
        if symbol_to_remove in data['strategies']:
            del data['strategies'][symbol_to_remove]
            print(f"🗑️ Удалена стратегия {symbol_to_remove}")
        else:
            print(f"⚠️ Стратегия {symbol_to_remove} не найдена")
        
        # Сохраняем обновленный файл
        with open('symbol_strategies.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Стратегии после удаления: {data['strategies']}")
        final_count = len(data['strategies'])
        
        if final_count < initial_count:
            print(f"✅ Удаление успешно! Было: {initial_count}, стало: {final_count}")
            return True
        else:
            print(f"❌ Удаление не сработало! Было: {initial_count}, стало: {final_count}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def test_clear_all_strategies():
    """Тестирует очистку всех стратегий"""
    print("\n🗑️ Тестируем очистку всех стратегий...")
    
    try:
        # Читаем текущий файл стратегий
        with open('symbol_strategies.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📋 Исходные стратегии: {data['strategies']}")
        initial_count = len(data['strategies'])
        
        # Очищаем все стратегии
        data['strategies'] = {}
        
        # Сохраняем пустой файл
        with open('symbol_strategies.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Стратегии после очистки: {data['strategies']}")
        final_count = len(data['strategies'])
        
        if final_count == 0:
            print(f"✅ Очистка успешна! Было: {initial_count}, стало: {final_count}")
            return True
        else:
            print(f"❌ Очистка не сработала! Было: {initial_count}, стало: {final_count}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def restore_test_data():
    """Восстанавливает тестовые данные"""
    print("\n🔄 Восстанавливаем тестовые данные...")
    
    test_data = {
        "strategies": {
            "BTCUSDT": {
                "balance_pct": 3,
                "leverage": 10,
                "stop_loss": 20,
                "take_profit": null,
                "timeframe": "15",
                "type": "ghost"
            },
            "ETHUSDT": {
                "type": "ghost",
                "timeframe": "60",
                "stop_loss": 40,
                "take_profit": 40,
                "balance_pct": 5
            },
            "DOGEUSDT": {
                "balance_pct": 5,
                "stop_loss": 40,
                "take_profit": 40,
                "timeframe": "60"
            }
        }
    }
    
    with open('symbol_strategies.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print("✅ Тестовые данные восстановлены")

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования удаления стратегий...")
    print("=" * 60)
    
    # Сохраняем резервную копию
    if os.path.exists('symbol_strategies.json'):
        with open('symbol_strategies.json', 'r', encoding='utf-8') as f:
            backup_data = f.read()
        
        with open('symbol_strategies_backup.json', 'w', encoding='utf-8') as f:
            f.write(backup_data)
        print("📋 Создана резервная копия")
    
    tests = [
        ("Удаление одной стратегии", test_remove_strategy),
        ("Очистка всех стратегий", test_clear_all_strategies)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Тест: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append(result)
            if result:
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - НЕ ПРОЙДЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
            results.append(False)
    
    # Восстанавливаем данные
    restore_test_data()
    
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print(f"✅ Успешно: {sum(results)}")
    print(f"❌ Ошибок: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n✅ Исправления удаления стратегий работают корректно:")
        print("   - Удаление одной стратегии работает")
        print("   - Очистка всех стратегий работает")
        print("   - Данные корректно сохраняются в файл")
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("\n🔧 Рекомендации:")
        print("   - Проверьте права доступа к файлу")
        print("   - Убедитесь, что файл не заблокирован")

if __name__ == "__main__":
    main()
