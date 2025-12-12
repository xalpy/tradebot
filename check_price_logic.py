#!/usr/bin/env python3
"""
Проверка логики цены с реальными данными из лога
"""

import json
from main import get_last_trade_price, should_open_position

def check_price_logic():
    """Проверяет логику с реальными данными из лога"""
    
    print("=== Проверка логики цены с реальными данными ===\n")
    
    # Читаем текущий лог сделок
    with open('trades_log.jsonl', 'r', encoding='utf-8') as f:
        trades = []
        for line in f:
            line = line.strip()
            if line:
                trades.append(json.loads(line))
    
    print("📊 Все сделки в логе:")
    for i, trade in enumerate(trades, 1):
        print(f"  {i}. {trade['symbol']} {trade['side']} по цене {trade['price']} ({trade.get('time_iso', 'N/A')})")
    
    print(f"\n🔍 Анализ для каждой пары:")
    
    # Группируем сделки по символам
    symbols = set(trade['symbol'] for trade in trades)
    
    for symbol in symbols:
        print(f"\n📈 {symbol}:")
        
        # Получаем все сделки для этого символа
        symbol_trades = [t for t in trades if t['symbol'] == symbol]
        
        # Группируем по направлениям
        buy_trades = [t for t in symbol_trades if t['side'] == 'Buy']
        sell_trades = [t for t in symbol_trades if t['side'] == 'Sell']
        
        print(f"  Сделки на покупку: {len(buy_trades)}")
        for trade in buy_trades:
            print(f"    - {trade['price']} ({trade.get('time_iso', 'N/A')})")
        
        print(f"  Сделки на продажу: {len(sell_trades)}")
        for trade in sell_trades:
            print(f"    - {trade['price']} ({trade.get('time_iso', 'N/A')})")
        
        # Проверяем логику для последних сделок
        if buy_trades:
            last_buy = max(buy_trades, key=lambda x: x['timestamp'])
            last_buy_price = get_last_trade_price(symbol, 'Buy')
            print(f"  Последняя покупка: {last_buy_price} (из функции: {last_buy_price})")
        
        if sell_trades:
            last_sell = max(sell_trades, key=lambda x: x['timestamp'])
            last_sell_price = get_last_trade_price(symbol, 'Sell')
            print(f"  Последняя продажа: {last_sell_price} (из функции: {last_sell_price})")
        
        # Тестируем логику с текущими ценами (примерные)
        test_prices = {
            'LINKUSDT': 23.500,  # Примерная текущая цена
            'DOGEUSDT': 0.21500,  # Примерная текущая цена
        }
        
        if symbol in test_prices:
            current_price = test_prices[symbol]
            print(f"  Тестирование при цене {current_price}:")
            
            # Тест для шорта
            can_open_sell, reason_sell = should_open_position(symbol, "sell", current_price)
            print(f"    Шорт: {'✅' if can_open_sell else '❌'} {reason_sell}")
            
            # Тест для лонга
            can_open_buy, reason_buy = should_open_position(symbol, "buy", current_price)
            print(f"    Лонг: {'✅' if can_open_buy else '❌'} {reason_buy}")

if __name__ == "__main__":
    check_price_logic()

