#!/usr/bin/env python3
"""
Тестовый скрипт для проверки сохранения стратегий
"""

import json
import os

def test_save_strategies():
    """Тестирует сохранение стратегий"""
    
    # Тестовые стратегии
    test_strategies = {
        "BTCUSDT": {
            "type": "combined",
            "timeframe": "15",
            "leverage": 10,
            "stop_loss": 20,
            "take_profit": 50,
            "balance_pct": 3
        },
        "ETHUSDT": {
            "type": "ott",
            "timeframe": "30",
            "leverage": 15,
            "stop_loss": 15,
            "take_profit": 30,
            "balance_pct": 2.5
        }
    }
    
    # Сохраняем стратегии
    try:
        with open('symbol_strategies.json', 'w', encoding='utf-8') as f:
            json.dump(test_strategies, f, ensure_ascii=False, indent=2)
        print("✅ Стратегии успешно сохранены")
        
        # Проверяем, что файл создался
        if os.path.exists('symbol_strategies.json'):
            print("✅ Файл symbol_strategies.json создан")
            
            # Читаем обратно
            with open('symbol_strategies.json', 'r', encoding='utf-8') as f:
                loaded_strategies = json.load(f)
            
            print(f"✅ Загружено {len(loaded_strategies)} стратегий")
            print(f"Содержимое: {json.dumps(loaded_strategies, indent=2, ensure_ascii=False)}")
        else:
            print("❌ Файл не создался")
            
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        import traceback
        traceback.print_exc()

def test_load_strategies():
    """Тестирует загрузку стратегий"""
    
    try:
        if os.path.exists('symbol_strategies.json'):
            with open('symbol_strategies.json', 'r', encoding='utf-8') as f:
                strategies = json.load(f)
            print(f"✅ Загружено {len(strategies)} стратегий")
            print(f"Содержимое: {json.dumps(strategies, indent=2, ensure_ascii=False)}")
        else:
            print("❌ Файл symbol_strategies.json не существует")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== ТЕСТ СОХРАНЕНИЯ СТРАТЕГИЙ ===")
    test_save_strategies()
    print("\n=== ТЕСТ ЗАГРУЗКИ СТРАТЕГИЙ ===")
    test_load_strategies()
