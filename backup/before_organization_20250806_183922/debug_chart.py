#!/usr/bin/env python3
"""
Быстрая диагностика проблемы с графиком
"""

import requests
import json

def test_api_data():
    """Тест данных API"""
    print("🔍 Тестируем данные API...")
    
    try:
        response = requests.get('http://localhost:5000/api/klines/BTCUSDT?interval=15&limit=5')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Получено {len(data)} записей")
            
            if len(data) > 0:
                print("📊 Первая запись:")
                first_item = data[0]
                for key, value in first_item.items():
                    print(f"   {key}: {value} (тип: {type(value).__name__})")
                
                # Проверяем на null значения
                null_fields = [key for key, value in first_item.items() if value is None]
                if null_fields:
                    print(f"❌ Найдены null поля: {null_fields}")
                else:
                    print("✅ Null значений не найдено")
                
                return True
            else:
                print("❌ Нет данных")
                return False
        else:
            print(f"❌ API вернул {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_server():
    """Тест сервера"""
    print("\n🌐 Тестируем сервер...")
    
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code == 200:
            print("✅ Сервер работает")
            return True
        else:
            print(f"❌ Сервер вернул {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Сервер недоступен: {e}")
        return False

def main():
    print("🚀 Быстрая диагностика графика")
    print("=" * 40)
    
    # Тест 1: Сервер
    server_ok = test_server()
    
    # Тест 2: Данные API
    data_ok = test_api_data()
    
    print("\n" + "=" * 40)
    print("📊 Результаты:")
    print(f"   Сервер: {'✅ Работает' if server_ok else '❌ Проблема'}")
    print(f"   Данные API: {'✅ Работают' if data_ok else '❌ Проблема'}")
    
    if server_ok and data_ok:
        print("\n✅ API работает корректно!")
        print("\n💡 Следующие шаги:")
        print("   1. Откройте test_chart_creation.html в браузере")
        print("   2. Нажмите 'Создать график'")
        print("   3. Проверьте, создается ли график без данных")
        print("   4. Если да - проблема в данных, если нет - проблема в библиотеке")
    else:
        print("\n❌ Проблемы с API")
        print("\n🔧 Решения:")
        if not server_ok:
            print("   - Запустите сервер: python web_app.py")
        if not data_ok:
            print("   - Проверьте API ключи в config.py")
            print("   - Проверьте интернет соединение")

if __name__ == "__main__":
    main() 