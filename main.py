from bybit_api import BybitAPI
from strategy import GhostTangentStrategy
from backtester import Backtester
import pandas as pd
import time
import json
import os
from config import TEST_API_KEY, TEST_API_SECRET, REAL_API_KEY, REAL_API_SECRET

# Можно вынести в config.py
BUY_LEVERAGE = 10
SELL_LEVERAGE = 10
TRADE_BALANCE_PCT = 0.03  # 3% от баланса
STOP_LOSS_PCT = 0.2       # 20% стоп-лосс
TRADE_INTERVAL_SEC = 60   # Проверять раз в минуту

# Минимальные шаги qty для популярных пар
QTY_PRECISION = {
    'BTCUSDT': 3,
    'ETHUSDT': 3,
    'SOLUSDT': 2,
}

def read_trades(limit: int = 200):
    """Читает последние N строк из trades_log.jsonl (если есть)."""
    path = 'trades_log.jsonl'
    if not os.path.exists(path):
        return []
    trades = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    trades.append(json.loads(line))
                except Exception:
                    continue
        return trades[-limit:]
    except Exception as e:
        print(f"⚠️ Не удалось прочитать trades_log.jsonl: {e}")
        return []

def get_last_trade_info(symbol, signal_time=None):
    """Получает информацию о последней сделке для символа.
    
    Args:
        symbol: Торговая пара (например, 'LINKUSDT')
        signal_time: Время сигнала (timestamp) - если указано, ищет сделки только до этого времени
    
    Returns:
        dict: {'price': float, 'side': str} или None, если сделок не найдено
    """
    trades = read_trades(limit=50)  # Читаем последние 50 сделок
    
    # Ищем последнюю сделку для данного символа (любого направления)
    for trade in reversed(trades):  # Идем от новых к старым
        if (trade.get('event') == 'opened' and 
            trade.get('symbol') == symbol):
            
            # Если указано время сигнала, проверяем что сделка была до сигнала
            if signal_time is not None:
                trade_time = trade.get('timestamp', 0)
                if trade_time >= signal_time:
                    continue  # Пропускаем сделки после времени сигнала
            
            return {
                'price': float(trade.get('price', 0)),
                'side': trade.get('side', '')
            }
    
    return None

def get_current_position_type(symbol):
    """Определяет тип текущей позиции по символу из API.
    
    Args:
        symbol: Торговая пара
    
    Returns:
        str: 'buy', 'sell' или None если позиции нет
    """
    try:
        open_positions = api.get_open_positions(symbol)
        for pos in open_positions:
            size = float(pos.get('size', 0))
            if size > 0:
                side = pos.get('side', '')
                if side == 'Buy':
                    return 'buy'
                elif side == 'Sell':
                    return 'sell'
        return None
    except Exception as e:
        print(f"⚠️ Ошибка получения типа позиции для {symbol}: {e}")
        return None

def should_open_position(symbol, signal_type, current_price, signal_time=None):
    """Проверяет, можно ли открывать позицию с учетом цены последней сделки.
    
    Args:
        symbol: Торговая пара
        signal_type: Тип сигнала ('buy' или 'sell')
        current_price: Текущая цена
        signal_time: Время сигнала (timestamp) - если указано, ищет сделки только до этого времени
    
    Returns:
        tuple: (can_open: bool, reason: str)
    """
    last_trade = get_last_trade_info(symbol, signal_time)
    
    if last_trade is None:
        return True, "Нет предыдущих сделок по этому символу"
    
    last_price = last_trade['price']
    last_side = last_trade['side']
    
    # Логика сравнения:
    # Если последняя сделка была SHORT и сигнал SHORT: ждем цену ВЫШЕ последней сделки
    # Если последняя сделка была LONG и сигнал LONG: ждем цену НИЖЕ последней сделки
    # Если направления разные: можно открывать (разворот позиции)
    
    if signal_type == 'buy':  # Сигнал LONG
        if last_side == 'Buy':  # Последняя сделка тоже LONG
            if current_price < last_price:
                return True, f"Цена {current_price:.4f} ниже последней LONG сделки {last_price:.4f} - можно открывать лонг"
            else:
                return False, f"Цена {current_price:.4f} выше или равна последней LONG сделке {last_price:.4f} - ждем лучшего входа для лонга"
        else:  # Последняя сделка была SHORT - разворот позиции
            return True, f"Разворот с SHORT на LONG - можно открывать лонг"
    else:  # Сигнал SHORT
        if last_side == 'Sell':  # Последняя сделка тоже SHORT
            if current_price > last_price:
                return True, f"Цена {current_price:.4f} выше последней SHORT сделки {last_price:.4f} - можно открывать шорт"
            else:
                return False, f"Цена {current_price:.4f} ниже или равна последней SHORT сделке {last_price:.4f} - ждем лучшего входа для шорта"
        else:  # Последняя сделка была LONG - разворот позиции
            return True, f"Разворот с LONG на SHORT - можно открывать шорт"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['trade', 'backtest'], default='backtest')
    parser.add_argument('--symbol', default='BTCUSDT')
    parser.add_argument('--symbols', default='', help='Список пар через запятую, например: BTCUSDT,ETHUSDT')
    parser.add_argument('--interval', default='15')
    parser.add_argument('--trademode', choices=['test', 'real'], default='test', help='test — демо-счёт, real — реальный счёт')
    parser.add_argument('--balance', action='store_true', help='Показать все балансы и выйти')
    args = parser.parse_args()

    # Всегда используем реальные ключи для получения данных
    api_key = REAL_API_KEY
    api_secret = REAL_API_SECRET
    
    # Режим торговли определяется аргументом
    trade_mode = args.trademode

    api = BybitAPI(api_key=api_key, api_secret=api_secret, trade_mode=trade_mode)

    if args.balance:
        balances = api.get_all_balances()
        print("Балансы всех монет:")
        for coin, amount in balances.items():
            print(f"{coin}: {amount}")
        exit(0)

    strategy = GhostTangentStrategy()

    if args.mode == 'backtest':
        print("Загружаю исторические данные...")
        klines = api.get_klines(args.symbol, args.interval, limit=500)
        df = pd.DataFrame(klines, columns=['timestamp','open','high','low','close','volume','turnover'])
        df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
        # Добавляем колонку time для графика
        df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        backtester = Backtester(strategy)
        trades = backtester.run(df)
        print(f"Backtest завершён. Найдено {len(trades)} сделок")
        
        if trades:
            profitable_trades = sum(1 for trade in trades if trade['profit_pct'] > 0)
            total_profit_pct = sum(trade['profit_pct'] for trade in trades)
            total_profit_usd = sum(trade['profit_usd'] for trade in trades)
            win_rate = (profitable_trades / len(trades)) * 100
            
            print(f"Статистика:")
            print(f"  Всего сделок: {len(trades)}")
            print(f"  Прибыльных: {profitable_trades}")
            print(f"  Винрейт: {win_rate:.2f}%")
            print(f"  Общая прибыль: {total_profit_pct:.2f}%")
            print(f"  Общая прибыль USD: ${total_profit_usd:.2f}")
            
            print(f"\nПоследние 5 сделок (от новых к старым):")
            # Показываем сделки от новых к старым
            for i, trade in enumerate(reversed(trades[-5:]), 1):
                status = "✅" if trade['profit_pct'] > 0 else "❌"
                print(f"{i}. {trade['entry_type'].upper()} | Вход: ${trade['entry_price']:.2f} | Выход: ${trade['exit_price']:.2f} | "
                      f"Прибыль: {trade['profit_pct']:.2f}% (${trade['profit_usd']:.2f}) | "
                      f"Длительность: {trade['duration_hours']}ч {status}")
            
            if len(trades) > 5:
                print(f"... и еще {len(trades) - 5} сделок")
        else:
            print("Сделок не найдено")
    elif args.mode == 'trade':
        # Определяем список пар
        if args.symbols:
            symbols = [s.strip().upper() for s in args.symbols.split(',') if s.strip()]
        else:
            symbols = [args.symbol.strip().upper()]
        print(f"Устанавливаю плечо: buy={BUY_LEVERAGE}, sell={SELL_LEVERAGE}")
        for symbol in symbols:
            try:
                api.set_leverage(symbol, buy_leverage=BUY_LEVERAGE, sell_leverage=SELL_LEVERAGE)
            except Exception as e:
                print(f"Не удалось установить плечо для {symbol}: {e}")
        print(f"Режим торговли: live trading по {', '.join(symbols)}... (режим: {args.trademode})")
        last_signal_time = {symbol: None for symbol in symbols}
        current_positions = {symbol: None for symbol in symbols}  # Отслеживаем текущие позиции
        
        while True:
            try:
                for symbol in symbols:
                    klines = api.get_klines(symbol, args.interval, limit=100)
                    df = pd.DataFrame(klines, columns=['timestamp','open','high','low','close','volume','turnover'])
                    df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
                    df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                    signals = strategy.generate_signals(df)
                    
                    if signals:
                        last_signal = signals[-1]
                        if str(last_signal['time']) != str(last_signal_time[symbol]):
                            open_positions = api.get_open_positions(symbol)
                            has_position = any(float(pos.get('size', 0)) > 0 for pos in open_positions)
                            # Получаем реальный тип позиции из API вместо использования кэшированного значения
                            current_position_type = get_current_position_type(symbol)
                            
                            if not has_position:
                                # Нет позиции - проверяем цену и открываем новую
                                balance = api.get_balance("USDT")
                                price = float(df['close'].iloc[-1])
                                
                                # Проверяем цену относительно последней сделки
                                can_open, reason = should_open_position(symbol, last_signal['type'], price)
                                
                                if not can_open:
                                    print(f"{symbol}: {reason}")
                                    last_signal_time[symbol] = str(last_signal['time'])
                                    continue
                                # TRADE_BALANCE_PCT в процентах, поэтому делим на 100
                                position_value = balance * (TRADE_BALANCE_PCT / 100.0)
                                precision = int(QTY_PRECISION.get(symbol, 2))
                                qty = round(position_value / price, precision)
                                
                                if qty <= 0:
                                    print(f"{symbol}: Недостаточно баланса для открытия позиции (qty={qty}). Пополните баланс или увеличьте TRADE_BALANCE_PCT.")
                                    continue
                                
                                side = 'Buy' if last_signal['type'] == 'buy' else 'Sell'
                                leverage = BUY_LEVERAGE if side == 'Buy' else SELL_LEVERAGE
                                print(f"{symbol}: Открываю сделку: {side}, qty={qty}, price={price}, stop_loss={STOP_LOSS_PCT}%, плечо={leverage}x")
                                result = api.place_order(symbol, side=side, qty=qty, price=price, stop_loss=STOP_LOSS_PCT, leverage=leverage)
                                
                                if result:
                                    current_positions[symbol] = last_signal['type']
                                    print(f"{symbol}: Позиция открыта успешно")
                                
                                last_signal_time[symbol] = str(last_signal['time'])
                            else:
                                # Есть позиция - проверяем на противоположный сигнал
                                if current_position_type is not None and ((current_position_type == 'buy' and last_signal['type'] == 'sell') or 
                                    (current_position_type == 'sell' and last_signal['type'] == 'buy')):
                                    
                                    print(f"{symbol}: Противоположный сигнал - закрываю позицию и открываю новую")
                                    
                                    # Закрываем текущую позицию
                                    close_side = 'Sell' if current_position_type == 'buy' else 'Buy'
                                    position_size = 0
                                    for pos in open_positions:
                                        if float(pos.get('size', 0)) > 0:
                                            position_size = float(pos.get('size', 0))
                                            break
                                    
                                    if position_size > 0:
                                        # Закрываем позицию
                                        print(f"{symbol}: Закрываю позицию {close_side} {position_size}")
                                        close_result = api.place_order(
                                            symbol,
                                            side=close_side,
                                            qty=position_size,
                                            price=float(df['close'].iloc[-1]),
                                            reduce_only=True
                                        )
                                        
                                        if close_result:
                                            print(f"{symbol}: Позиция закрыта успешно")
                                            
                                            # Открываем новую позицию
                                            balance = api.get_balance("USDT")
                                            price = float(df['close'].iloc[-1])
                                            
                                            # Проверяем цену относительно последней сделки
                                            can_open, reason = should_open_position(symbol, last_signal['type'], price)
                                            
                                            if not can_open:
                                                print(f"{symbol}: {reason}")
                                                last_signal_time[symbol] = str(last_signal['time'])
                                                continue
                                            
                                            # TRADE_BALANCE_PCT в процентах, поэтому делим на 100
                                            position_value = balance * (TRADE_BALANCE_PCT / 100.0)
                                            precision = int(QTY_PRECISION.get(symbol, 2))
                                            qty = round(position_value / price, precision)
                                            
                                            if qty > 0:
                                                new_side = 'Buy' if last_signal['type'] == 'buy' else 'Sell'
                                                print(f"{symbol}: Открываю новую позицию: {new_side}, qty={qty}, price={price}")
                                                leverage = BUY_LEVERAGE if new_side == 'Buy' else SELL_LEVERAGE
                                                new_result = api.place_order(
                                                    symbol,
                                                    side=new_side,
                                                    qty=qty,
                                                    price=price,
                                                    stop_loss=STOP_LOSS_PCT,
                                                    leverage=leverage
                                                )
                                                
                                                if new_result:
                                                    current_positions[symbol] = last_signal['type']
                                                    print(f"{symbol}: Новая позиция открыта успешно")
                                    
                                    last_signal_time[symbol] = str(last_signal['time'])
                                else:
                                    if current_position_type is not None:
                                        print(f"{symbol}: Сигнал того же типа ({last_signal['type']}), позиция остается открытой (текущая позиция: {current_position_type})")
                                    else:
                                        print(f"{symbol}: Сигнал того же типа ({last_signal['type']}), позиция остается открытой")
                        else:
                            print(f"{symbol}: Сигнал уже обработан")
                    else:
                        print(f"{symbol}: Нет новых сигналов")
            except Exception as e:
                print(f"Ошибка в торговом цикле: {e}")
                raise e 
            time.sleep(TRADE_INTERVAL_SEC)
    else:
        print("Режим торговли пока не реализован.") 