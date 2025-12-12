#!/usr/bin/env python3
"""
Быстрый тест для проверки API и данных графика
"""

import requests
import json

def test_api():
    """Быстрый тест API"""
    print("🚀 Быстрый тест API...")
    
    try:
        # Тест 1: Проверяем доступность сервера
        print("1️⃣ Проверяем сервер...")
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code == 200:
            print("✅ Сервер работает")
        else:
            print(f"❌ Сервер вернул {response.status_code}")
            return False
        
        # Тест 2: Проверяем API данных
        print("2️⃣ Проверяем API данных...")
        response = requests.get('http://localhost:5000/api/klines/BTCUSDT?interval=15&limit=10', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Получено {len(data)} записей")
            
            if len(data) > 0:
                print("📊 Пример данных:")
                print(f"   Время: {data[0]['time']}")
                print(f"   Открытие: ${data[0]['open']}")
                print(f"   Закрытие: ${data[0]['close']}")
                return True
            else:
                print("❌ Нет данных")
                return False
        else:
            print(f"❌ API вернул {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу")
        print("   Запустите: python web_app.py")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    print("🧪 Быстрый тест графика")
    print("=" * 40)
    
    if test_api():
        print("\n✅ API работает корректно!")
        print("\n💡 Теперь:")
        print("   1. Откройте браузер")
        print("   2. Перейдите на http://localhost:5000")
        print("   3. Откройте вкладку 'Графики'")
        print("   4. Выберите символ и нажмите 'Обновить'")
        print("   5. Проверьте консоль браузера (F12)")
    else:
        print("\n❌ Проблемы с API")
        print("\n🔧 Решения:")
        print("   1. Запустите сервер: python web_app.py")
        print("   2. Проверьте API ключи в config.py")
        print("   3. Проверьте интернет соединение")

if __name__ == "__main__":
    main() 