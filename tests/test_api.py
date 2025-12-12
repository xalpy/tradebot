#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API стратегий
"""

import requests
import json

def test_strategies_api():
    """Тестирует API стратегий"""
    
    base_url = "http://localhost:5000"
    
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
    
    try:
        # Тест 1: Получение стратегий (GET)
        print("=== ТЕСТ 1: Получение стратегий ===")
        response = requests.get(f"{base_url}/api/strategies")
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text}")
        
        # Тест 2: Сохранение стратегий (POST)
        print("\n=== ТЕСТ 2: Сохранение стратегий ===")
        response = requests.post(
            f"{base_url}/api/strategies",
            headers={'Content-Type': 'application/json'},
            json=test_strategies
        )
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text}")
        
        # Тест 3: Проверка сохранения (GET)
        print("\n=== ТЕСТ 3: Проверка сохранения ===")
        response = requests.get(f"{base_url}/api/strategies")
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к серверу. Убедитесь, что web_app.py запущен.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_strategies_api()
