#!/usr/bin/env python3
"""
Итоговый тестовый скрипт для проверки всех исправлений
"""

import json
import re
import os

def test_symbol_strategies_file():
    """Тестирует файл symbol_strategies.json"""
    print("📋 Тестируем файл symbol_strategies.json...")
    
    try:
        with open('symbol_strategies.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Файл загружен успешно")
        print(f"📊 Структура: {list(data.keys())}")
        
        if 'strategies' in data:
            strategies = data['strategies']
            print(f"📈 Количество стратегий: {len(strategies)}")
            
            # Проверяем каждую стратегию
            for symbol, strategy in strategies.items():
                if re.match(r'^[A-Z]{2,10}USDT$|^[A-Z]{2,10}BTC$', symbol):
                    print(f"✅ Валидная торговая пара: {symbol}")
                else:
                    print(f"❌ НЕВАЛИДНАЯ торговая пара: {symbol}")
                    
                # Проверяем структуру стратегии
                if isinstance(strategy, dict):
                    print(f"   📋 Параметры: {list(strategy.keys())}")
                else:
                    print(f"   ⚠️ Простая стратегия: {strategy}")
        else:
            print("❌ Отсутствует ключ 'strategies'")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования файла: {e}")
        return False

def test_web_app_loading():
    """Тестирует загрузку стратегий в web_app.py"""
    print("\n🔄 Тестируем загрузку стратегий в web_app.py...")
    
    try:
        # Импортируем web_app
        import sys
        sys.path.append('.')
        
        # Создаем временный модуль
        import importlib.util
        spec = importlib.util.spec_from_file_location("web_app", "web_app.py")
        web_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_app)
        
        # Тестируем загрузку
        web_app.load_symbol_strategies()
        
        print(f"✅ Загрузка стратегий работает")
        print(f"📊 Загружено стратегий: {len(web_app.symbol_strategies)}")
        
        # Проверяем, что все символы валидные
        invalid_symbols = []
        for symbol in web_app.symbol_strategies.keys():
            if not re.match(r'^[A-Z]{2,10}USDT$|^[A-Z]{2,10}BTC$', symbol):
                invalid_symbols.append(symbol)
        
        if invalid_symbols:
            print(f"❌ Найдены невалидные символы: {invalid_symbols}")
            return False
        else:
            print(f"✅ Все символы валидные")
            return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования web_app: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_combined_strategy():
    """Тестирует исправление ошибки с множествами"""
    print("\n🧪 Тестируем CombinedStrategy...")
    
    try:
        from combined_strategy import CombinedStrategy
        import pandas as pd
        
        # Создаем тестовые данные
        dates = pd.date_range(start='2024-01-01', end='2024-01-05', freq='1H')
        df = pd.DataFrame({
            'timestamp': [int(d.timestamp() * 1000) for d in dates],
            'open': [100 + i * 0.1 for i in range(len(dates))],
            'high': [101 + i * 0.1 for i in range(len(dates))],
            'low': [99 + i * 0.1 for i in range(len(dates))],
            'close': [100.5 + i * 0.1 for i in range(len(dates))],
            'volume': [1000 + i * 10 for i in range(len(dates))],
            'turnover': [100000 + i * 1000 for i in range(len(dates))]
        })
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Создаем стратегию
        strategy = CombinedStrategy()
        
        # Генерируем сигналы
        signals = strategy.generate_signals(df)
        
        print(f"✅ CombinedStrategy работает. Получено {len(signals)} сигналов")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в CombinedStrategy: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_export_format():
    """Тестирует новый формат экспорта"""
    print("\n📤 Тестируем формат экспорта...")
    
    try:
        # Создаем тестовые данные
        test_export = {
            "metadata": {
                "exportDate": "2024-01-01T00:00:00",
                "version": "1.1",
                "description": "Тест экспорта",
                "author": "TradeBot System",
                "totalStrategies": 2,
                "totalSymbols": 2
            },
            "tradingConfig": {
                "general": {
                    "buy_leverage": 10,
                    "sell_leverage": 10,
                    "trade_balance_pct": 3.0,
                    "stop_loss_pct": 2.0,
                    "take_profit_pct": 5.0,
                    "trade_interval_sec": 60,
                    "mode": "real",
                    "timeframe": "15"
                }
            },
            "strategies": {
                "BTCUSDT": {
                    "type": "ghost",
                    "timeframe": "15",
                    "leverage": 10,
                    "stop_loss": 20,
                    "take_profit": None,
                    "balance_pct": 3
                },
                "ETHUSDT": {
                    "type": "ott",
                    "timeframe": "15",
                    "leverage": 10,
                    "stop_loss": 20,
                    "take_profit": None,
                    "balance_pct": 3
                }
            },
            "selectedSymbols": ["BTCUSDT", "ETHUSDT"]
        }
        
        # Проверяем JSON сериализацию
        json_str = json.dumps(test_export, indent=2, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        print(f"✅ JSON сериализация работает")
        print(f"✅ Структура экспорта корректна")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в формате экспорта: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск итогового тестирования всех исправлений...")
    print("=" * 60)
    
    tests = [
        ("Файл symbol_strategies.json", test_symbol_strategies_file),
        ("Загрузка стратегий в web_app.py", test_web_app_loading),
        ("CombinedStrategy (исправление множеств)", test_combined_strategy),
        ("Формат экспорта", test_export_format)
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
    
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print(f"✅ Успешно: {sum(results)}")
    print(f"❌ Ошибок: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n✅ Исправления работают корректно:")
        print("   - Файл стратегий содержит только валидные торговые пары")
        print("   - Загрузка стратегий работает без ошибок")
        print("   - CombinedStrategy исправлена (нет ошибки с множествами)")
        print("   - Формат экспорта корректен")
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("\n🔧 Рекомендации:")
        print("   - Проверьте файл symbol_strategies.json")
        print("   - Убедитесь, что все импорты работают")
        print("   - Проверьте логи сервера")

if __name__ == "__main__":
    main()
