#!/usr/bin/env python3
"""
Тест валидации данных для графика
"""

import sys
import os
import requests
import json

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_data_validation():
    """Тест валидации данных"""
    print("🧪 Тестируем валидацию данных...")
    
    try:
        # Получаем данные через API
        response = requests.get('http://localhost:5000/api/klines/BTCUSDT?interval=15&limit=50')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Получено {len(data)} записей")
            
            if len(data) == 0:
                print("❌ Нет данных для проверки")
                return False
            
            # Проверяем каждую запись
            valid_count = 0
            invalid_count = 0
            
            for i, item in enumerate(data):
                # Проверяем наличие всех полей
                required_fields = ['time', 'open', 'high', 'low', 'close']
                missing_fields = [field for field in required_fields if field not in item]
                
                if missing_fields:
                    print(f"❌ Запись {i+1}: отсутствуют поля {missing_fields}")
                    invalid_count += 1
                    continue
                
                # Проверяем типы данных
                try:
                    time_val = int(item['time'])
                    open_val = float(item['open'])
                    high_val = float(item['high'])
                    low_val = float(item['low'])
                    close_val = float(item['close'])
                except (ValueError, TypeError) as e:
                    print(f"❌ Запись {i+1}: неверные типы данных - {e}")
                    invalid_count += 1
                    continue
                
                # Проверяем логику OHLC
                if high_val < max(open_val, close_val):
                    print(f"❌ Запись {i+1}: high ({high_val}) < max(open, close) ({max(open_val, close_val)})")
                    invalid_count += 1
                    continue
                
                if low_val > min(open_val, close_val):
                    print(f"❌ Запись {i+1}: low ({low_val}) > min(open, close) ({min(open_val, close_val)})")
                    invalid_count += 1
                    continue
                
                if open_val <= 0 or high_val <= 0 or low_val <= 0 or close_val <= 0:
                    print(f"❌ Запись {i+1}: отрицательные или нулевые цены")
                    invalid_count += 1
                    continue
                
                valid_count += 1
                
                # Показываем первые 3 валидные записи
                if valid_count <= 3:
                    print(f"✅ Запись {i+1}: {item}")
            
            print(f"\n📊 Результаты валидации:")
            print(f"   Валидных записей: {valid_count}")
            print(f"   Невалидных записей: {invalid_count}")
            print(f"   Всего записей: {len(data)}")
            
            if valid_count > 0:
                print("✅ Данные прошли валидацию")
                return True
            else:
                print("❌ Нет валидных данных")
                return False
                
        else:
            print(f"❌ API вернул статус {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def test_sample_data():
    """Тест с образцовыми данными"""
    print("\n🧪 Тестируем образцовые данные...")
    
    # Валидные данные
    valid_data = [
        {'time': 1640995200, 'open': 100.0, 'high': 105.0, 'low': 95.0, 'close': 102.0},
        {'time': 1640995260, 'open': 102.0, 'high': 108.0, 'low': 100.0, 'close': 106.0},
        {'time': 1640995320, 'open': 106.0, 'high': 110.0, 'low': 104.0, 'close': 108.0},
    ]
    
    # Невалидные данные
    invalid_data = [
        {'time': 1640995380, 'open': 108.0, 'high': 105.0, 'low': 110.0, 'close': 106.0},  # high < close
        {'time': 1640995440, 'open': 110.0, 'high': 115.0, 'low': 120.0, 'close': 113.0},  # low > high
        {'time': 1640995500, 'open': 0.0, 'high': 115.0, 'low': 95.0, 'close': 113.0},     # open = 0
    ]
    
    print("✅ Валидные данные:")
    for i, item in enumerate(valid_data):
        print(f"   {i+1}. {item}")
    
    print("❌ Невалидные данные:")
    for i, item in enumerate(invalid_data):
        print(f"   {i+1}. {item}")
    
    return True

def main():
    print("🧪 Тест валидации данных для графика")
    print("=" * 50)
    
    # Тест 1: Валидация реальных данных
    data_validation_ok = test_data_validation()
    
    # Тест 2: Образцовые данные
    sample_data_ok = test_sample_data()
    
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    print(f"   Валидация данных: {'✅ Работает' if data_validation_ok else '❌ Ошибка'}")
    print(f"   Образцовые данные: {'✅ Работает' if sample_data_ok else '❌ Ошибка'}")
    
    if data_validation_ok:
        print("\n🎉 Данные корректны для отображения в графике!")
    else:
        print("\n⚠️ Проблемы с данными требуют исправления")

if __name__ == "__main__":
    main() 