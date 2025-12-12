#!/usr/bin/env python3
"""
Тест реальных данных для графика
"""

import requests
import json

def test_real_data():
    """Тестируем реальные данные"""
    print("🧪 Тестируем реальные данные...")
    
    try:
        # Получаем данные
        response = requests.get('http://localhost:5000/api/klines/BTCUSDT?interval=15&limit=3')
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Получено {len(data)} записей")
            
            # Проверяем структуру
            if len(data) > 0:
                first_item = data[0]
                print(f"📋 Первая запись: {first_item}")
                
                # Проверяем поля
                required_fields = ['time', 'open', 'high', 'low', 'close']
                extra_fields = [k for k in first_item.keys() if k not in required_fields]
                
                if extra_fields:
                    print(f"⚠️ Лишние поля: {extra_fields}")
                else:
                    print("✅ Структура данных корректна")
                
                # Проверяем типы
                print(f"🔍 Типы данных:")
                for field in required_fields:
                    if field in first_item:
                        value = first_item[field]
                        print(f"   {field}: {type(value).__name__} = {value}")
                    else:
                        print(f"   {field}: ОТСУТСТВУЕТ")
                
                # Проверяем логику OHLC
                print(f"🔍 Проверка OHLC логики:")
                high = first_item['high']
                low = first_item['low']
                open_val = first_item['open']
                close_val = first_item['close']
                
                print(f"   high >= max(open, close): {high} >= {max(open_val, close_val)} = {high >= max(open_val, close_val)}")
                print(f"   low <= min(open, close): {low} <= {min(open_val, close_val)} = {low <= min(open_val, close_val)}")
                
                if high >= max(open_val, close_val) and low <= min(open_val, close_val):
                    print("   ✅ OHLC логика корректна")
                else:
                    print("   ❌ OHLC логика нарушена")
                
                return True
            else:
                print("❌ Нет данных")
                return False
        else:
            print(f"❌ API вернул статус {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    print("🧪 Тест реальных данных")
    print("=" * 40)
    
    success = test_real_data()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Тест пройден успешно")
        print("💡 Теперь попробуйте загрузить график в браузере")
    else:
        print("❌ Тест не пройден")
        print("💡 Проверьте, запущен ли сервер (python web_app.py)")

if __name__ == "__main__":
    main() 