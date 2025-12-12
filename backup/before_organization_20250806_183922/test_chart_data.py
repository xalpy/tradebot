#!/usr/bin/env python3
"""
Тест для проверки получения данных графика
"""

import sys
import os
import requests
import json

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bybit_api import BybitAPI
from config import REAL_API_KEY, REAL_API_SECRET

def test_api_klines():
    """Тест получения данных через API"""
    print("🌐 Тестируем получение данных через API...")
    
    try:
        # Тестируем API endpoint
        response = requests.get('http://localhost:5000/api/klines/BTCUSDT?interval=15&limit=50')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API вернул {len(data)} записей")
            
            if len(data) > 0:
                # Показываем первые 3 записи
                print("\n📊 Примеры данных:")
                for i, item in enumerate(data[:3]):
                    print(f"   {i+1}. Время: {item['time']}, Открытие: ${item['open']}, Закрытие: ${item['close']}")
                
                # Проверяем структуру данных
                first_item = data[0]
                required_fields = ['time', 'open', 'high', 'low', 'close']
                missing_fields = [field for field in required_fields if field not in first_item]
                
                if missing_fields:
                    print(f"❌ Отсутствуют поля: {missing_fields}")
                    return False
                else:
                    print("✅ Структура данных корректна")
                    return True
            else:
                print("❌ Нет данных в ответе")
                return False
        else:
            print(f"❌ API вернул статус {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании API: {e}")
        return False

def test_direct_api_call():
    """Тест прямого вызова API Bybit"""
    print("\n🔍 Тестируем прямой вызов API Bybit...")
    
    try:
        # Инициализируем API
        api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='test')
        
        # Получаем данные
        klines = api.get_klines('BTCUSDT', '15', limit=50)
        
        if klines:
            print(f"✅ Получено {len(klines)} записей от Bybit API")
            
            # Показываем первые 3 записи
            print("\n📊 Примеры данных от Bybit:")
            for i, kline in enumerate(klines[:3]):
                timestamp, open_price, high, low, close, volume, turnover = kline
                print(f"   {i+1}. Время: {timestamp}, Открытие: {open_price}, Закрытие: {close}")
            
            return True
        else:
            print("❌ Нет данных от Bybit API")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при вызове Bybit API: {e}")
        return False

def test_data_format():
    """Тест формата данных для LightweightCharts"""
    print("\n📋 Тестируем формат данных для LightweightCharts...")
    
    try:
        # Получаем данные через API
        response = requests.get('http://localhost:5000/api/klines/BTCUSDT?interval=15&limit=10')
        
        if response.status_code == 200:
            data = response.json()
            
            if len(data) > 0:
                # Проверяем типы данных
                first_item = data[0]
                
                print("📊 Проверка типов данных:")
                print(f"   time: {type(first_item['time'])} = {first_item['time']}")
                print(f"   open: {type(first_item['open'])} = {first_item['open']}")
                print(f"   high: {type(first_item['high'])} = {first_item['high']}")
                print(f"   low: {type(first_item['low'])} = {first_item['low']}")
                print(f"   close: {type(first_item['close'])} = {first_item['close']}")
                
                # Проверяем, что time - это число (timestamp)
                if isinstance(first_item['time'], int):
                    print("✅ Время в правильном формате (timestamp)")
                else:
                    print("❌ Время должно быть числом (timestamp)")
                    return False
                
                # Проверяем, что цены - это числа
                price_fields = ['open', 'high', 'low', 'close']
                for field in price_fields:
                    if not isinstance(first_item[field], (int, float)):
                        print(f"❌ Поле {field} должно быть числом")
                        return False
                
                print("✅ Все поля имеют правильные типы")
                return True
            else:
                print("❌ Нет данных для проверки")
                return False
        else:
            print(f"❌ API вернул статус {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке формата: {e}")
        return False

def test_chart_initialization():
    """Тест инициализации графика"""
    print("\n📈 Тестируем инициализацию графика...")
    
    try:
        # Проверяем, что веб-приложение запущено
        response = requests.get('http://localhost:5000/')
        
        if response.status_code == 200:
            print("✅ Веб-приложение доступно")
            
            # Проверяем, что LightweightCharts загружается
            response = requests.get('https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js')
            
            if response.status_code == 200:
                print("✅ LightweightCharts доступен")
                return True
            else:
                print("❌ LightweightCharts недоступен")
                return False
        else:
            print("❌ Веб-приложение недоступно")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке графика: {e}")
        return False

def main():
    print("🧪 Тестируем функциональность графика...")
    print("=" * 60)
    
    # Тест 1: Прямой вызов Bybit API
    direct_api_ok = test_direct_api_call()
    
    # Тест 2: API endpoint
    api_endpoint_ok = test_api_klines()
    
    # Тест 3: Формат данных
    data_format_ok = test_data_format()
    
    # Тест 4: Инициализация графика
    chart_init_ok = test_chart_initialization()
    
    print("\n" + "=" * 60)
    print("📊 Результаты тестирования:")
    print(f"   Прямой вызов Bybit API: {'✅ Работает' if direct_api_ok else '❌ Ошибка'}")
    print(f"   API endpoint: {'✅ Работает' if api_endpoint_ok else '❌ Ошибка'}")
    print(f"   Формат данных: {'✅ Работает' if data_format_ok else '❌ Ошибка'}")
    print(f"   Инициализация графика: {'✅ Работает' if chart_init_ok else '❌ Ошибка'}")
    
    if direct_api_ok and api_endpoint_ok and data_format_ok:
        print("\n🎉 Данные графика работают корректно!")
        print("\n💡 Если свечи не отображаются, проверьте:")
        print("   1. Выбран ли символ в селекте")
        print("   2. Загружена ли библиотека LightweightCharts")
        print("   3. Консоль браузера на наличие ошибок")
        return True
    else:
        print("\n⚠️  Некоторые функции требуют доработки")
        return False

if __name__ == "__main__":
    main() 