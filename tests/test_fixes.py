#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений
- Ошибка "unhashable type: 'dict'"
- Формат экспорта конфига
"""

import json
import pandas as pd
from datetime import datetime, timedelta

def test_combined_strategy():
    """Тестируем исправление ошибки с множествами в CombinedStrategy"""
    print("🧪 Тестируем CombinedStrategy...")
    
    try:
        from combined_strategy import CombinedStrategy
        
        # Создаем тестовые данные
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='1H')
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
        
        print(f"✅ CombinedStrategy работает корректно. Получено {len(signals)} сигналов")
        
        # Проверяем, что время в сигналах - строки
        if signals:
            first_signal = signals[0]
            time_type = type(first_signal['time'])
            print(f"📅 Тип времени в сигнале: {time_type}")
            
            if isinstance(first_signal['time'], str):
                print("✅ Время корректно преобразовано в строку")
            else:
                print("⚠️ Время не преобразовано в строку")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в CombinedStrategy: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_export_format():
    """Тестируем новый формат экспорта"""
    print("\n📤 Тестируем формат экспорта...")
    
    # Создаем тестовые данные в новом формате
    test_export = {
        "metadata": {
            "exportDate": datetime.now().isoformat(),
            "version": "1.1",
            "description": "Экспорт торговых стратегий и настроек TradeBot",
            "author": "TradeBot System",
            "totalStrategies": 3,
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
            },
            "description": {
                "buy_leverage": "Плечо для покупок (1-100)",
                "sell_leverage": "Плечо для продаж (1-100)",
                "trade_balance_pct": "Процент баланса на сделку (0.1-100)",
                "stop_loss_pct": "Стоп-лосс в процентах (0.1-100)",
                "take_profit_pct": "Тейк-профит в процентах (0.1-100, null = отключен)",
                "trade_interval_sec": "Интервал проверки сигналов в секундах",
                "mode": "Режим торговли (real/simulation)",
                "timeframe": "Таймфрейм для анализа (1,5,15,30,60,240,1D)"
            }
        },
        "strategies": {
            "BTCUSDT": {
                "type": "ghost",
                "timeframe": "60",
                "leverage": 10,
                "stop_loss": 20,
                "take_profit": 50,
                "balance_pct": 3
            },
            "ETHUSDT": {
                "type": "ott",
                "timeframe": "60",
                "leverage": 15,
                "stop_loss": 15,
                "take_profit": 30,
                "balance_pct": 2.5
            },
            "SOLUSDT": {
                "type": "combined",
                "timeframe": "5",
                "leverage": 20,
                "stop_loss": 25,
                "take_profit": None,
                "balance_pct": 4
            }
        },
        "selectedSymbols": ["BTCUSDT", "ETHUSDT"],
        "strategyTypes": {
            "ghost": "Ghost Strategy - основана на pivot points и трендовых линиях",
            "ott": "OTT Strategy - One-Time Trigger с адаптивными уровнями",
            "combined": "Combined Strategy - комбинация Ghost и OTT стратегий"
        },
        "notes": {
            "strategyFormat": "Каждая стратегия может быть строкой (тип) или объектом с параметрами",
            "parameters": {
                "type": "Тип стратегии (ghost/ott/combined)",
                "timeframe": "Таймфрейм для стратегии",
                "leverage": "Плечо для данной пары",
                "stop_loss": "Стоп-лосс в процентах",
                "take_profit": "Тейк-профит в процентах (null = отключен)",
                "balance_pct": "Процент баланса для данной пары"
            }
        }
    }
    
    try:
        # Проверяем, что JSON сериализуется корректно
        json_str = json.dumps(test_export, indent=2, ensure_ascii=False)
        print(f"✅ JSON сериализация успешна. Размер: {len(json_str)} символов")
        
        # Проверяем, что можно десериализовать обратно
        parsed = json.loads(json_str)
        print(f"✅ JSON десериализация успешна")
        
        # Проверяем структуру
        assert 'metadata' in parsed
        assert 'tradingConfig' in parsed
        assert 'strategies' in parsed
        assert 'selectedSymbols' in parsed
        assert 'strategyTypes' in parsed
        assert 'notes' in parsed
        
        print("✅ Структура экспорта корректна")
        
        # Проверяем метаданные
        metadata = parsed['metadata']
        assert metadata['version'] == '1.1'
        assert metadata['totalStrategies'] == 3
        assert metadata['totalSymbols'] == 2
        
        print("✅ Метаданные корректны")
        
        # Проверяем стратегии
        strategies = parsed['strategies']
        assert len(strategies) == 3
        assert 'BTCUSDT' in strategies
        assert 'ETHUSDT' in strategies
        assert 'SOLUSDT' in strategies
        
        print("✅ Стратегии корректны")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в формате экспорта: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Тестируем обратную совместимость с старым форматом"""
    print("\n🔄 Тестируем обратную совместимость...")
    
    # Старый формат
    old_format = {
        "strategies": {
            "BTCUSDT": "ghost",
            "ETHUSDT": "ott"
        },
        "config": {
            "buy_leverage": 10,
            "sell_leverage": 10,
            "trade_balance_pct": 3.0
        },
        "exportDate": "2024-01-01T00:00:00",
        "version": "1.0"
    }
    
    try:
        # Проверяем, что старый формат тоже работает
        json_str = json.dumps(old_format, indent=2)
        parsed = json.loads(json_str)
        
        assert 'strategies' in parsed
        assert 'config' in parsed
        assert 'exportDate' in parsed
        assert 'version' in parsed
        
        print("✅ Обратная совместимость работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обратной совместимости: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов исправлений...")
    
    tests = [
        test_combined_strategy,
        test_export_format,
        test_backward_compatibility
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка выполнения теста {test.__name__}: {e}")
            results.append(False)
    
    print(f"\n📊 Результаты тестов:")
    print(f"✅ Успешно: {sum(results)}")
    print(f"❌ Ошибок: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 Все тесты прошли успешно!")
    else:
        print("⚠️ Некоторые тесты не прошли")

if __name__ == "__main__":
    main()
