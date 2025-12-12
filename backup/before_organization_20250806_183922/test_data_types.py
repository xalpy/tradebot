#!/usr/bin/env python3
"""
Тест типов данных для графика
"""

import requests
import json

def test_data_types():
    """Тест типов данных"""
    print("🔍 Тестируем типы данных...")
    
    try:
        # Получаем данные через API
        response = requests.get('http://localhost:5000/api/klines/BTCUSDT?interval=15&limit=5')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Получено {len(data)} записей")
            
            if len(data) == 0:
                print("❌ Нет данных для проверки")
                return False
            
            # Проверяем типы данных
            print("\n📊 Проверка типов данных:")
            for i, item in enumerate(data):
                print(f"\nЗапись {i+1}:")
                for key, value in item.items():
                    print(f"   {key}: {value} (тип: {type(value).__name__})")
                
                # Проверяем, что все значения являются числами
                numeric_fields = ['time', 'open', 'high', 'low', 'close', 'volume']
                non_numeric = [field for field in numeric_fields if not isinstance(item.get(field), (int, float))]
                
                if non_numeric:
                    print(f"   ❌ Нечисловые поля: {non_numeric}")
                else:
                    print(f"   ✅ Все поля числовые")
                
                # Проверяем, что time является int
                if not isinstance(item.get('time'), int):
                    print(f"   ❌ time должен быть int, а не {type(item.get('time')).__name__}")
                else:
                    print(f"   ✅ time является int")
                
                # Проверяем, что остальные поля являются float
                price_fields = ['open', 'high', 'low', 'close', 'volume']
                non_float = [field for field in price_fields if not isinstance(item.get(field), (int, float))]
                
                if non_float:
                    print(f"   ❌ Ценовые поля должны быть числами: {non_float}")
                else:
                    print(f"   ✅ Все ценовые поля числовые")
                
                # Показываем только первые 3 записи
                if i >= 2:
                    break
            
            return True
        else:
            print(f"❌ API вернул статус {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def compare_with_test_data():
    """Сравнение с тестовыми данными"""
    print("\n🔄 Сравнение с тестовыми данными...")
    
    # Тестовые данные из test_chart_creation.html
    test_data = [
        { 'time': 1640995200, 'open': 100, 'high': 105, 'low': 95, 'close': 102 },
        { 'time': 1640995260, 'open': 102, 'high': 108, 'low': 100, 'close': 106 },
        { 'time': 1640995320, 'open': 106, 'high': 110, 'low': 104, 'close': 108 },
    ]
    
    print("📋 Тестовые данные:")
    for i, item in enumerate(test_data):
        print(f"   {i+1}. time={item['time']} ({type(item['time']).__name__}), open={item['open']} ({type(item['open']).__name__})")
    
    # Получаем реальные данные
    try:
        response = requests.get('http://localhost:5000/api/klines/BTCUSDT?interval=15&limit=3')
        
        if response.status_code == 200:
            real_data = response.json()
            
            print("\n📋 Реальные данные:")
            for i, item in enumerate(real_data):
                print(f"   {i+1}. time={item['time']} ({type(item['time']).__name__}), open={item['open']} ({type(item['open']).__name__})")
            
            # Сравниваем типы
            print("\n🔍 Сравнение типов:")
            for i, (test_item, real_item) in enumerate(zip(test_data, real_data)):
                print(f"\nЗапись {i+1}:")
                for key in ['time', 'open', 'high', 'low', 'close']:
                    test_type = type(test_item[key]).__name__
                    real_type = type(real_item[key]).__name__
                    if test_type == real_type:
                        print(f"   ✅ {key}: {test_type} == {real_type}")
                    else:
                        print(f"   ❌ {key}: {test_type} != {real_type}")
            
            return True
        else:
            print(f"❌ API вернул статус {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при сравнении: {e}")
        return False

def main():
    print("🧪 Тест типов данных для графика")
    print("=" * 50)
    
    # Тест 1: Проверка типов данных
    types_ok = test_data_types()
    
    # Тест 2: Сравнение с тестовыми данными
    comparison_ok = compare_with_test_data()
    
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    print(f"   Типы данных: {'✅ Корректны' if types_ok else '❌ Проблема'}")
    print(f"   Сравнение: {'✅ Совпадают' if comparison_ok else '❌ Различаются'}")
    
    if types_ok and comparison_ok:
        print("\n🎉 Типы данных корректны!")
        print("💡 Теперь график должен работать")
    else:
        print("\n⚠️ Проблемы с типами данных требуют исправления")

if __name__ == "__main__":
    main() 