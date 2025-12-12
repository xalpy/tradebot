#!/usr/bin/env python3
"""
Тест для проверки функциональности получения торговых пар с Bybit
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bybit_api import BybitAPI
from config import REAL_API_KEY, REAL_API_SECRET

def test_get_all_trading_pairs():
    """Тест получения всех торговых пар"""
    print("🔍 Тестируем получение всех торговых пар...")
    
    try:
        # Инициализируем API
        api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='test')
        
        # Получаем все пары
        all_pairs = api.get_all_trading_pairs()
        
        if all_pairs:
            print(f"✅ Получено {len(all_pairs)} торговых пар")
            
            # Показываем топ-10 по объему
            print("\n📊 Топ-10 пар по объему торгов:")
            for i, pair in enumerate(all_pairs[:10], 1):
                volume_m = pair['volume24h'] / 1000000
                print(f"   {i:2d}. {pair['symbol']:<10} | ${pair['price']:>8.2f} | ${volume_m:>6.1f}M")
            
            # Статистика
            total_volume = sum(pair['volume24h'] for pair in all_pairs)
            avg_price = sum(pair['price'] for pair in all_pairs) / len(all_pairs)
            
            print(f"\n📈 Статистика:")
            print(f"   Общий объем торгов: ${total_volume/1000000:.1f}M")
            print(f"   Средняя цена: ${avg_price:.2f}")
            print(f"   Диапазон цен: ${min(pair['price'] for pair in all_pairs):.2f} - ${max(pair['price'] for pair in all_pairs):.2f}")
            
            return True
        else:
            print("❌ Не удалось получить торговые пары")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении торговых пар: {e}")
        return False

def test_get_popular_pairs():
    """Тест получения популярных торговых пар"""
    print("\n🔥 Тестируем получение популярных торговых пар...")
    
    try:
        # Инициализируем API
        api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='test')
        
        # Получаем популярные пары
        popular_pairs = api.get_popular_pairs()
        
        if popular_pairs:
            print(f"✅ Получено {len(popular_pairs)} популярных пар")
            
            print("\n🔥 Популярные торговые пары:")
            for i, pair in enumerate(popular_pairs, 1):
                volume_m = pair['volume24h'] / 1000000
                print(f"   {i:2d}. {pair['symbol']:<10} | ${pair['price']:>8.2f} | ${volume_m:>6.1f}M")
            
            return True
        else:
            print("❌ Не удалось получить популярные пары")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении популярных пар: {e}")
        return False

def test_symbol_info():
    """Тест получения информации о конкретном символе"""
    print("\nℹ️  Тестируем получение информации о символе...")
    
    try:
        # Инициализируем API
        api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='test')
        
        # Тестируем несколько популярных символов
        test_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        
        for symbol in test_symbols:
            info = api.get_symbol_info(symbol)
            if info:
                print(f"✅ {symbol}:")
                print(f"   Статус: {info.get('status', 'N/A')}")
                print(f"   Базовая валюта: {info.get('baseCoin', 'N/A')}")
                print(f"   Котируемая валюта: {info.get('quoteCoin', 'N/A')}")
                print(f"   Последняя цена: ${float(info.get('lastPrice', 0)):.2f}")
                print(f"   Объем 24ч: ${float(info.get('volume24h', 0))/1000000:.1f}M")
            else:
                print(f"❌ Не удалось получить информацию о {symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при получении информации о символе: {e}")
        return False

def test_api_endpoints():
    """Тест API endpoints для торговых пар"""
    print("\n🌐 Тестируем API endpoints...")
    
    try:
        import requests
        
        # Тестируем endpoint получения всех пар
        response = requests.get('http://localhost:5000/api/trading_pairs')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ /api/trading_pairs: {data.get('total_count', 0)} пар")
            
            if data.get('popular'):
                print(f"   Популярных пар: {len(data['popular'])}")
            if data.get('all'):
                print(f"   Всего пар: {len(data['all'])}")
        else:
            print(f"❌ /api/trading_pairs: {response.status_code}")
        
        # Тестируем поиск
        response = requests.get('http://localhost:5000/api/trading_pairs/search?q=BTC')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ /api/trading_pairs/search: найдено {len(data)} пар с 'BTC'")
        else:
            print(f"❌ /api/trading_pairs/search: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании API endpoints: {e}")
        print("   Убедитесь, что веб-приложение запущено на localhost:5000")
        return False

def main():
    print("🧪 Тестируем функциональность торговых пар...")
    print("=" * 60)
    
    # Тест 1: Получение всех пар
    all_pairs_ok = test_get_all_trading_pairs()
    
    # Тест 2: Получение популярных пар
    popular_pairs_ok = test_get_popular_pairs()
    
    # Тест 3: Информация о символах
    symbol_info_ok = test_symbol_info()
    
    # Тест 4: API endpoints
    api_endpoints_ok = test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("📊 Результаты тестирования:")
    print(f"   Все торговые пары: {'✅ Работает' if all_pairs_ok else '❌ Ошибка'}")
    print(f"   Популярные пары: {'✅ Работает' if popular_pairs_ok else '❌ Ошибка'}")
    print(f"   Информация о символах: {'✅ Работает' if symbol_info_ok else '❌ Ошибка'}")
    print(f"   API endpoints: {'✅ Работает' if api_endpoints_ok else '❌ Ошибка'}")
    
    if all_pairs_ok and popular_pairs_ok and symbol_info_ok:
        print("\n🎉 Функциональность торговых пар работает корректно!")
        return True
    else:
        print("\n⚠️  Некоторые функции требуют доработки")
        return False

if __name__ == "__main__":
    main() 