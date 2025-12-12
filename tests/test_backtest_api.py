#!/usr/bin/env python3
import requests
import json

def test_backtest_api():
    """Тестирует API бектеста"""
    
    # Данные для теста
    test_data = {
        "symbol": "BTCUSDT",
        "interval": "15",
        "days_back": 7,  # Короткий период для быстрого теста
        "leverage": 10,
        "stop_loss_pct": 2.0,
        "take_profit_pct": None,
        "initial_balance": 1000.0,
        "trade_size_pct": 3.0,
        "strategy_type": "ghost"
    }
    
    print("🧪 Тестируем API бектеста...")
    print(f"📤 Отправляем данные: {json.dumps(test_data, indent=2)}")
    
    try:
        # Отправляем запрос
        response = requests.post(
            'http://localhost:5000/api/backtest',
            headers={'Content-Type': 'application/json'},
            json=test_data,
            timeout=60  # Увеличиваем таймаут
        )
        
        print(f"📥 Получен ответ: статус {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Успешный ответ!")
            print(f"📊 Результат содержит {len(result)} полей")
            print(f"📊 Поле 'trades' есть: {'trades' in result}")
            
            if 'trades' in result:
                trades = result['trades']
                print(f"📊 Количество сделок: {len(trades)}")
                print(f"📊 Общая статистика:")
                print(f"  - Всего сделок: {result.get('total_trades', 0)}")
                print(f"  - Винрейт: {result.get('win_rate', 0)}%")
                print(f"  - Общая прибыль: {result.get('total_profit_pct', 0)}%")
                
                if trades:
                    print(f"📊 Первая сделка: {trades[0]}")
            else:
                print("❌ Поле 'trades' отсутствует в ответе")
                print(f"📊 Доступные поля: {list(result.keys())}")
                if 'error' in result:
                    print(f"❌ Ошибка: {result['error']}")
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            print(f"📄 Текст ответа: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к серверу. Убедитесь, что сервер запущен на http://localhost:5000")
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса. Возможно, бектест выполняется слишком долго.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_backtest_api()

