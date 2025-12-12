#!/usr/bin/env python3
"""
Сравнение тестовых и реальных данных
"""

import requests
import json

def compare_data():
    """Сравнение данных"""
    print("🔍 Сравниваем тестовые и реальные данные...")
    
    # Тестовые данные (точно как в test_chart_creation.html)
    test_data = [
        { 'time': 1640995200, 'open': 100, 'high': 105, 'low': 95, 'close': 102 },
        { 'time': 1640995260, 'open': 102, 'high': 108, 'low': 100, 'close': 106 },
        { 'time': 1640995320, 'open': 106, 'high': 110, 'low': 104, 'close': 108 },
    ]
    
    print("📋 Тестовые данные:")
    for i, item in enumerate(test_data):
        print(f"   {i+1}. {item}")
    
    try:
        # Получаем реальные данные
        response = requests.get('http://localhost:5000/api/klines/BTCUSDT?interval=15&limit=3')
        
        if response.status_code == 200:
            real_data = response.json()
            
            print(f"\n📋 Реальные данные (получено {len(real_data)} записей):")
            for i, item in enumerate(real_data):
                print(f"   {i+1}. {item}")
            
            # Сравниваем структуру
            print(f"\n🔍 Сравнение структуры:")
            if len(real_data) > 0:
                test_keys = set(test_data[0].keys())
                real_keys = set(real_data[0].keys())
                
                print(f"   Тестовые ключи: {test_keys}")
                print(f"   Реальные ключи: {real_keys}")
                
                if test_keys == real_keys:
                    print("   ✅ Структура данных совпадает")
                else:
                    print("   ❌ Структура данных различается")
                    missing_in_real = test_keys - real_keys
                    extra_in_real = real_keys - test_keys
                    if missing_in_real:
                        print(f"      Отсутствует в реальных данных: {missing_in_real}")
                    if extra_in_real:
                        print(f"      Лишние в реальных данных: {extra_in_real}")
            
            # Сравниваем типы
            print(f"\n🔍 Сравнение типов:")
            if len(real_data) > 0:
                for i, (test_item, real_item) in enumerate(zip(test_data, real_data)):
                    print(f"\n   Запись {i+1}:")
                    for key in ['time', 'open', 'high', 'low', 'close']:
                        if key in test_item and key in real_item:
                            test_type = type(test_item[key]).__name__
                            real_type = type(real_item[key]).__name__
                            test_value = test_item[key]
                            real_value = real_item[key]
                            
                            if test_type == real_type:
                                print(f"      ✅ {key}: {test_type} == {real_type} ({test_value} vs {real_value})")
                            else:
                                print(f"      ❌ {key}: {test_type} != {real_type} ({test_value} vs {real_value})")
                        else:
                            print(f"      ⚠️ {key}: отсутствует в одном из наборов данных")
            
            return True
        else:
            print(f"❌ API вернул статус {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении данных: {e}")
        return False

def test_chart_creation():
    """Тест создания графика с разными данными"""
    print("\n🧪 Тест создания графика...")
    
    print("📋 Инструкции:")
    print("   1. Откройте test_chart_creation.html в браузере")
    print("   2. Нажмите 'Создать график'")
    print("   3. Проверьте, отображаются ли свечи")
    print("   4. Если да - график работает с тестовыми данными")
    print("   5. Если нет - проблема в библиотеке или контейнере")
    
    print("\n📋 Тест в основном приложении:")
    print("   1. Откройте http://localhost:5000")
    print("   2. Перейдите на вкладку 'Графики'")
    print("   3. Нажмите кнопку 'Тестовые данные'")
    print("   4. Проверьте, отображаются ли свечи")
    print("   5. Если да - проблема в реальных данных")
    print("   6. Если нет - проблема в основном приложении")

def main():
    print("🧪 Сравнение тестовых и реальных данных")
    print("=" * 50)
    
    # Сравнение данных
    comparison_ok = compare_data()
    
    # Инструкции по тестированию
    test_chart_creation()
    
    print("\n" + "=" * 50)
    print("📊 Результаты:")
    print(f"   Сравнение данных: {'✅ Успешно' if comparison_ok else '❌ Ошибка'}")
    
    if comparison_ok:
        print("\n💡 Следующие шаги:")
        print("   1. Проверьте test_chart_creation.html")
        print("   2. Проверьте кнопку 'Тестовые данные' в основном приложении")
        print("   3. Сравните результаты")
    else:
        print("\n⚠️ Проблемы с получением данных")

if __name__ == "__main__":
    main() 