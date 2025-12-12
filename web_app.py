from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from bybit_api import BybitAPI
from strategy import GhostTangentStrategy
from backtester import Backtester
import threading
import time
import json
from config import TEST_API_KEY, TEST_API_SECRET, REAL_API_KEY, REAL_API_SECRET
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Глобальные переменные
api = None
strategy = None
trading_thread = None
is_trading = False
current_symbols = []
trading_config = {
    'buy_leverage': 10,
    'sell_leverage': 10,
    'trade_balance_pct': 0.03,
    'stop_loss_pct': 0.2,
    'take_profit_pct': None,  # Тейк-профит по умолчанию отключен
    'trade_interval_sec': 60,
    'mode': 'real',  # Используем реальный режим по умолчанию
    'min_order_value': 5.0  # Минимальная стоимость ордера в USDT
}

# ====== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ЛОГИРОВАНИЯ ТОРГОВ ======
def append_trade_log(entry: dict):
    """Записывает только фактически исполненные сделки/события в trades_log.jsonl (по одной строке JSON)."""
    try:
        entry_copy = dict(entry)
        # Добавляем ISO-время для удобства чтения
        entry_copy.setdefault('time_iso', datetime.utcnow().isoformat())
        with open('trades_log.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry_copy, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"⚠️ Не удалось записать в trades_log.jsonl: {e}")

def read_trades(limit: int = 200):
    """Читает последние N строк из trades_log.jsonl (если есть)."""
    import os
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

def compute_trades_stats(trades):
    """Считает простую статистику по операциям Open/Closed/Reversed.
    PnL считается по парам open->close по символу и направлению.
    """
    from collections import defaultdict, deque
    open_stack = defaultdict(deque)  # key: (symbol, side) -> deque of opens
    stats = {
        'total_trades': 0,
        'total_closed': 0,
        'total_pnl_usd': 0.0,
        'per_symbol': {}
    }
    per_symbol = defaultdict(lambda: {
        'opened': 0,
        'closed': 0,
        'reversed': 0,
        'pnl_usd': 0.0
    })

    for t in trades:
        event = t.get('event')
        symbol = t.get('symbol')
        side = t.get('side')
        qty = float(t.get('qty', 0) or 0)
        price = float(t.get('price', 0) or 0)
        key = (symbol, side)
        if event == 'opened':
            stats['total_trades'] += 1
            per_symbol[symbol]['opened'] += 1
            open_stack[key].append({'qty': qty, 'price': price})
        elif event == 'reversed':
            stats['total_trades'] += 1
            per_symbol[symbol]['reversed'] += 1
            # Реверс трактуем как закрытие предыдущей позиции и открытие новой по направлению side
            # Для простоты: только как открытие новой (PnL уже учтен в отдельном 'closed' событии выше при закрытии)
            open_stack[key].append({'qty': qty, 'price': price})
        elif event == 'closed':
            per_symbol[symbol]['closed'] += 1
            stats['total_closed'] += 1
            # Пытаемся сопоставить к ближайшему открытию по противоположному направлению
            opp_side = 'Buy' if side == 'Sell' else 'Sell'
            opp_key = (symbol, opp_side)
            if open_stack[opp_key]:
                opened = open_stack[opp_key].popleft()
                open_price = opened['price']
                # PnL: для Buy -> Close(Sell): (close_price - open_price) * qty
                # для Sell -> Close(Buy): (open_price - close_price) * qty
                if opp_side == 'Buy':
                    pnl = (price - open_price) * opened['qty']
                else:
                    pnl = (open_price - price) * opened['qty']
                stats['total_pnl_usd'] += pnl
                per_symbol[symbol]['pnl_usd'] += pnl
    stats['per_symbol'] = per_symbol
    return stats

# Минимальные шаги qty для популярных пар (все округляем до 0.01)
QTY_PRECISION = {
    'BTCUSDT': 2,
    'ETHUSDT': 2,
    'SOLUSDT': 2,
    'LINKUSDT': 2,
}

# Минимальное количество для позиции
MIN_QTY = {
    'BTCUSDT': 0.001,
    'ETHUSDT': 0.01,
    'SOLUSDT': 0.1,
    'LINKUSDT': 0.1,
}

# Максимальное количество для позиции (защита от слишком больших позиций)
MAX_QTY = {
    'BTCUSDT': 1000,
    'ETHUSDT': 10000,
    'SOLUSDT': 100000,
    'LINKUSDT': 100000,
}


# Реестр стратегий и назначение стратегий по символам
strategy_registry = {
    'ghost': lambda: GhostTangentStrategy(),
}
try:
    from ott_strategy import OTTStrategy
    strategy_registry['ott'] = lambda: OTTStrategy()
except Exception:
    pass
try:
    from combined_strategy import CombinedStrategy
    strategy_registry['combined'] = lambda: CombinedStrategy()
except Exception:
    pass

symbol_strategies = {}

def load_symbol_strategies():
    import os
    path = 'symbol_strategies.json'
    print(f"Пытаемся загрузить стратегии из {path}")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Проверяем, есть ли вложенная структура с ключом "strategies"
                    if "strategies" in data and isinstance(data["strategies"], dict):
                        symbol_strategies.update(data["strategies"])
                        print(f"✅ Загружены стратегии из вложенной структуры: {symbol_strategies}")
                    else:
                        # Прямая структура стратегий
                        symbol_strategies.update(data)
                        print(f"✅ Загружены стратегии напрямую: {symbol_strategies}")
                else:
                    print(f"⚠️ Файл содержит неверный формат данных: {type(data)}")
        except Exception as e:
            print(f"❌ Не удалось загрузить symbol_strategies: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"📄 Файл {path} не существует, создаем пустой словарь стратегий")

def save_symbol_strategies():
    try:
        print(f"Сохраняем стратегии в файл: {symbol_strategies}")
        # Сохраняем только стратегии, а не весь объект экспорта
        with open('symbol_strategies.json', 'w', encoding='utf-8') as f:
            json.dump({"strategies": symbol_strategies}, f, ensure_ascii=False, indent=2)
        print(f"✅ Стратегии успешно сохранены в symbol_strategies.json")
    except Exception as e:
        print(f"❌ Не удалось сохранить symbol_strategies: {e}")
        import traceback
        traceback.print_exc()

def get_strategy_for_symbol(symbol: str):
    strategy_data = symbol_strategies.get(symbol, 'ghost')
    
    # Если стратегия - это строка (старый формат)
    if isinstance(strategy_data, str):
        key = strategy_data
    # Если стратегия - это объект (новый формат)
    elif isinstance(strategy_data, dict):
        key = strategy_data.get('type', 'ghost')
    else:
        key = 'ghost'
    
    factory = strategy_registry.get(key)
    if not factory:
        factory = strategy_registry['ghost']
    return factory()



def initialize_api():
    global api
    try:
        print("🔧 Инициализация API...")
        # Всегда используем реальные ключи для получения данных
        api_key = REAL_API_KEY
        api_secret = REAL_API_SECRET
        
        print(f"🔑 API ключ: {api_key[:8]}...")
        print(f"🔑 API секрет: {api_secret[:8]}...")
        
        # Для торговли используем режим из конфигурации
        trade_mode = trading_config['mode']
        print(f"🎯 Режим торговли: {trade_mode}")
        
        api = BybitAPI(api_key=api_key, api_secret=api_secret, trade_mode=trade_mode)
        print("✅ API инициализирован успешно")
    except Exception as e:
        print(f"❌ Ошибка инициализации API: {e}")
        raise e

# Загружаем назначенные стратегии при старте
load_symbol_strategies()

def trading_loop():
    global is_trading, current_symbols, api, strategy
    last_signal_time = {symbol: None for symbol in current_symbols}
    current_positions = {symbol: None for symbol in current_symbols}  # Отслеживаем текущие позиции
    # Пер-символьное состояние активного сигнала и уровня повторного входа
    active_signal = {symbol: None for symbol in current_symbols}  # {'type': 'buy'|'sell', 'time': datetime, 'expiry': datetime, 'last_entry_price': float}
    
    while is_trading:
        try:
            for symbol in current_symbols:
                if not is_trading:
                    break
                    
                # Пер-символьная стратегия и параметры
                local_strategy = get_strategy_for_symbol(symbol)
                strategy_data = symbol_strategies.get(symbol)
                symbol_balance_pct = None
                symbol_stop_loss_pct = None
                symbol_take_profit_pct = None
                symbol_interval = '15'
                if isinstance(strategy_data, dict):
                    # balance_pct ожидается в процентах (например 5)
                    if isinstance(strategy_data.get('balance_pct'), (int, float)):
                        symbol_balance_pct = float(strategy_data['balance_pct'])
                    if isinstance(strategy_data.get('stop_loss'), (int, float)):
                        symbol_stop_loss_pct = float(strategy_data['stop_loss'])
                    if isinstance(strategy_data.get('take_profit'), (int, float)):
                        symbol_take_profit_pct = float(strategy_data['take_profit'])
                    if isinstance(strategy_data.get('timeframe'), (str, int)):
                        symbol_interval = str(strategy_data['timeframe'])

                klines = api.get_klines(symbol, symbol_interval, limit=100)
                if not klines:
                    print(f"Нет данных для {symbol}, пропускаем")
                    continue
                import pandas as pd
                df = pd.DataFrame(klines, columns=['timestamp','open','high','low','close','volume','turnover'])
                if df.empty:
                    print(f"DataFrame пустой для {symbol}, пропускаем")
                    continue
                df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
                df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                
                signals = local_strategy.generate_signals(df)
                
                if signals:
                    last_signal = signals[-1]
                    # Преобразуем время сигнала
                    try:
                        signal_dt = pd.to_datetime(last_signal['time'])
                    except Exception:
                        signal_dt = None

                    # Обновляем активный сигнал, если он новый (по времени) или тип сменился
                    prev_active = active_signal.get(symbol)
                    is_new_signal_event = False
                    if signal_dt is not None:
                        if prev_active is None:
                            is_new_signal_event = True
                        else:
                            # Новый, если время больше предыдущего или сменился тип
                            if (last_signal['type'] != prev_active['type']) or (signal_dt > prev_active['time']):
                                is_new_signal_event = True
                    
                    if is_new_signal_event:
                        # Сохраняем прошлую цену входа, если тип сигнала тот же (чтобы не открывать заново ниже прошлого входа)
                        preserved_entry_price = None
                        if prev_active and prev_active.get('type') == last_signal['type']:
                            preserved_entry_price = prev_active.get('last_entry_price')

                        active_signal[symbol] = {
                            'type': last_signal['type'],
                            'time': signal_dt,
                            'expiry': (signal_dt + timedelta(days=2)) if signal_dt else None,
                            'last_entry_price': preserved_entry_price
                        }

                    # Сохраняем маркер обработки последнего сигнала (для предотвращения повторной реакции на тот же тик)
                    if str(last_signal['time']) != str(last_signal_time[symbol]):
                        open_positions = api.get_open_positions(symbol)
                        has_position = any(float(pos.get('size', 0)) > 0 for pos in open_positions)
                        # Получаем реальный тип позиции из API вместо использования кэшированного значения
                        current_position_type = get_current_position_type(symbol)
                        
                        if not has_position:
                            # Нет позиции - проверяем окно валидности сигнала (2 дня) и правило повторного входа
                            sig = active_signal.get(symbol)
                            now_dt = df['time'].iloc[-1].to_pydatetime()
                            within_window = True
                            if sig and sig.get('expiry'):
                                within_window = now_dt <= sig['expiry']
                            if not within_window:
                                # Сигнал протух - ждём новый разворот
                                print(f"{symbol}: Сигнал просрочен, ждем новый")
                                last_signal_time[symbol] = str(last_signal['time'])
                                continue

                            # Если сигнал активен и ранее уже открывалась сделка по этому сигналу, 
                            # не открываем новую, пока цена не достигнет прошлой цены входа или выше
                            price = float(df['close'].iloc[-1])
                            if sig and sig.get('last_entry_price') is not None:
                                if price < sig['last_entry_price']:
                                    print(f"{symbol}: Цена {price} ниже последнего входа {sig['last_entry_price']}, ждем повторного уровня для ре-эн트ри")
                                    last_signal_time[symbol] = str(last_signal['time'])
                                    continue

                            # Дополнительная проверка цены относительно последней сделки
                            signal_timestamp = signal_dt.timestamp() if signal_dt else None
                            can_open, reason = should_open_position(symbol, last_signal['type'], price, signal_timestamp)
                            
                            if not can_open:
                                print(f"{symbol}: {reason}")
                                last_signal_time[symbol] = str(last_signal['time'])
                                continue

                            # Нет позиции - открываем новую
                            balance = api.get_balance("USDT")
                            # Выбор процента баланса: приоритет у symbol_strategies
                            trade_pct = symbol_balance_pct if symbol_balance_pct is not None else (trading_config['trade_balance_pct'])
                            # trade_pct хранится в процентах (например 3), поэтому делим на 100
                            position_value = balance * (float(trade_pct) / 100.0)
                            
                            # Учитываем плечо при расчете количества монет
                            leverage = trading_config['buy_leverage'] if last_signal['type'] == 'buy' else trading_config['sell_leverage']
                            if isinstance(strategy_data, dict) and 'leverage' in strategy_data:
                                leverage = int(strategy_data['leverage'])
                                print(f"📊 {symbol}: расчет qty с плечом {leverage}x")
                            
                            # С плечом мы можем торговать на сумму position_value * leverage
                            leveraged_position_value = position_value * leverage
                            precision = int(QTY_PRECISION.get(symbol, 2))
                            # Сначала делим, потом округляем до нужной точности
                            qty = round(leveraged_position_value / price, precision)
                            # Дополнительно округляем до 2 знаков после запятой для всех символов
                            qty = round(qty, 2)
                            
                            # Проверяем минимальный размер позиции для биржи
                            min_qty = float(MIN_QTY.get(symbol, 0.01))
                            if qty < min_qty:
                                qty = min_qty
                                print(f"⚠️ {symbol}: qty меньше минимального, устанавливаем {min_qty}")
                            
                            # Ограничиваем максимальное количество (защита от слишком больших позиций)
                            max_qty = float(MAX_QTY.get(symbol, 1000000))
                            if qty > max_qty:
                                qty = max_qty
                                print(f"⚠️ {symbol}: qty больше максимального, ограничиваем {max_qty}")
                            
                            # Проверяем минимальную стоимость ордера и увеличиваем qty если нужно
                            min_order_value = trading_config.get('min_order_value', 5.0)
                            actual_order_value = qty * price
                            
                            # Увеличиваем qty до достижения минимальной стоимости
                            while actual_order_value < min_order_value and qty > 0:
                                qty = round(qty * 1.1, precision)  # Увеличиваем на 10%
                                qty = round(qty, 2)  # Дополнительно округляем до 2 знаков
                                actual_order_value = qty * price
                                if qty <= 0:
                                    break
                            
                            if actual_order_value < min_order_value:
                                # Если всё ещё не достигли минимума, устанавливаем точное значение
                                qty = round(min_order_value / price, precision)
                                qty = round(qty, 2)  # Дополнительно округляем до 2 знаков
                                actual_order_value = qty * price
                            
                            print(f"{symbol}: рассчитано qty={qty}, стоимость ордера=${actual_order_value:.2f}")
                            
                            if qty > 0:
                                side = 'Buy' if last_signal['type'] == 'buy' else 'Sell'
                                # Используем per-symbol плечо из symbol_strategies, если есть
                                leverage = trading_config['buy_leverage'] if side == 'Buy' else trading_config['sell_leverage']
                                if isinstance(strategy_data, dict) and 'leverage' in strategy_data:
                                    leverage = int(strategy_data['leverage'])
                                    print(f"📊 {symbol}: используем плечо из symbol_strategies: {leverage}x")
                                # Параметры риска с приоритетом per-symbol. stop_loss/take_profit в symbol_strategies в процентах.
                                stop_loss_param = trading_config['stop_loss_pct']
                                if symbol_stop_loss_pct is not None:
                                    stop_loss_param = float(symbol_stop_loss_pct) / 100.0
                                take_profit_param = trading_config.get('take_profit_pct')
                                if symbol_take_profit_pct is not None and float(symbol_take_profit_pct) > 0:
                                    take_profit_param = float(symbol_take_profit_pct) / 100.0
                                
                                print(f"{symbol}: попытка открыть {side} qty={qty} price={price} SL={stop_loss_param} TP={take_profit_param}")
                                print(f"📊 {symbol}: детали расчета - баланс: ${balance:.2f}, trade_pct: {trade_pct}%, leverage: {leverage}x, position_value: ${position_value:.2f}, leveraged_value: ${leveraged_position_value:.2f}")
                                try:
                                    result = api.place_order(
                                        symbol, 
                                        side=side, 
                                        qty=qty, 
                                        price=price, 
                                        stop_loss=stop_loss_param,
                                        take_profit=take_profit_param,
                                        leverage=leverage
                                    )
                                except Exception as order_error:
                                    print(f"❌ Ошибка размещения ордера {symbol}: {order_error}")
                                    result = None
                                
                                if result:
                                    current_positions[symbol] = last_signal['type']
                                    # Фиксируем цену входа для правила повторного входа, пока сигнал действителен
                                    if active_signal.get(symbol):
                                        active_signal[symbol]['last_entry_price'] = price
                                    append_trade_log({
                                        'event': 'opened',
                                        'symbol': symbol,
                                        'side': side,
                                        'qty': qty,
                                        'price': price,
                                        'timestamp': time.time()
                                    })
                                    socketio.emit('trade_executed', {
                                        'symbol': symbol,
                                        'side': side,
                                        'qty': qty,
                                        'price': price,
                                        'timestamp': time.time(),
                                        'action': 'opened'
                                    })
                                else:
                                    print(f"⚠️ Не удалось разместить ордер для {symbol}")
                                
                                last_signal_time[symbol] = str(last_signal['time'])
                        else:
                            # Есть позиция - проверяем на противоположный сигнал
                            if current_position_type is not None and ((current_position_type == 'buy' and last_signal['type'] == 'sell') or 
                                (current_position_type == 'sell' and last_signal['type'] == 'buy')):
                                
                                # Закрываем текущую позицию
                                close_side = 'Sell' if current_position_type == 'buy' else 'Buy'
                                position_size = 0
                                for pos in open_positions:
                                    if float(pos.get('size', 0)) > 0:
                                        position_size = float(pos.get('size', 0))
                                        break
                                
                                if position_size > 0:
                                    print(f"🔄 {symbol}: начинаем реверс позиции - закрываем {current_position_type} позицию размером {position_size}")
                                    # Закрываем позицию
                                    close_result = api.place_order(
                                        symbol,
                                        side=close_side,
                                        qty=position_size,
                                        price=float(df['close'].iloc[-1]),
                                        reduce_only=True
                                    )
                                    
                                    if close_result:
                                        print(f"✅ {symbol}: позиция успешно закрыта")
                                        append_trade_log({
                                            'event': 'closed',
                                            'symbol': symbol,
                                            'side': close_side,
                                            'qty': position_size,
                                            'price': float(df['close'].iloc[-1]),
                                            'timestamp': time.time()
                                        })
                                        socketio.emit('trade_executed', {
                                            'symbol': symbol,
                                            'side': close_side,
                                            'qty': position_size,
                                            'price': float(df['close'].iloc[-1]),
                                            'timestamp': time.time(),
                                            'action': 'closed'
                                        })
                                        
                                        # Открываем новую позицию в противоположном направлении
                                        print(f"🔄 {symbol}: открываем новую позицию в направлении {last_signal['type']}")
                                        balance = api.get_balance("USDT")
                                        price = float(df['close'].iloc[-1])
                                        # trade_balance_pct в процентах, поэтому делим на 100
                                        trade_pct = symbol_balance_pct if symbol_balance_pct is not None else (trading_config['trade_balance_pct'])
                                        position_value = balance * (float(trade_pct) / 100.0)
                                        
                                        # Учитываем плечо при расчете количества монет для реверса
                                        leverage = trading_config['buy_leverage'] if last_signal['type'] == 'buy' else trading_config['sell_leverage']
                                        if isinstance(strategy_data, dict) and 'leverage' in strategy_data:
                                            leverage = int(strategy_data['leverage'])
                                            print(f"📊 {symbol}: реверс - расчет qty с плечом {leverage}x")
                                        
                                        # С плечом мы можем торговать на сумму position_value * leverage
                                        leveraged_position_value = position_value * leverage
                                        precision = int(QTY_PRECISION.get(symbol, 2))
                                        # Сначала делим, потом округляем до нужной точности
                                        qty = round(leveraged_position_value / price, precision)
                                        # Дополнительно округляем до 2 знаков после запятой для всех символов
                                        qty = round(qty, 2)
                                        
                                        # Проверяем минимальный размер позиции для биржи
                                        min_qty = float(MIN_QTY.get(symbol, 0.01))
                                        if qty < min_qty:
                                            qty = min_qty
                                            print(f"⚠️ {symbol}: реверс - qty меньше минимального, устанавливаем {min_qty}")
                                        
                                        # Ограничиваем максимальное количество (защита от слишком больших позиций)
                                        max_qty = float(MAX_QTY.get(symbol, 1000000))
                                        if qty > max_qty:
                                            qty = max_qty
                                            print(f"⚠️ {symbol}: реверс - qty больше максимального, ограничиваем {max_qty}")
                                        
                                        # Проверяем минимальную стоимость ордера
                                        min_order_value = trading_config.get('min_order_value', 5.0)
                                        actual_order_value = qty * price
                                        
                                        if actual_order_value < min_order_value:
                                            # Увеличиваем количество до минимальной стоимости
                                            qty = round(min_order_value / price, precision)
                                            qty = round(qty, 2)  # Дополнительно округляем до 2 знаков
                                            print(f"⚠️ Увеличиваем qty для {symbol} до минимальной стоимости: {qty} (стоимость: ${qty * price:.2f})")
                                        
                                        if qty > 0:
                                            new_side = 'Buy' if last_signal['type'] == 'buy' else 'Sell'
                                            # Используем per-symbol плечо из symbol_strategies, если есть
                                            leverage = trading_config['buy_leverage'] if new_side == 'Buy' else trading_config['sell_leverage']
                                            if isinstance(strategy_data, dict) and 'leverage' in strategy_data:
                                                leverage = int(strategy_data['leverage'])
                                                print(f"📊 {symbol}: реверс - используем плечо из symbol_strategies: {leverage}x")
                                            stop_loss_param = trading_config['stop_loss_pct']
                                            if symbol_stop_loss_pct is not None:
                                                stop_loss_param = float(symbol_stop_loss_pct) / 100.0
                                            take_profit_param = trading_config.get('take_profit_pct')
                                            if symbol_take_profit_pct is not None and float(symbol_take_profit_pct) > 0:
                                                take_profit_param = float(symbol_take_profit_pct) / 100.0
                                            print(f"{symbol}: попытка реверса {new_side} qty={qty} price={price} SL={stop_loss_param} TP={take_profit_param}")
                                            
                                            # Пытаемся открыть новую позицию с повторными попытками
                                            max_retries = 3
                                            new_result = None
                                            
                                            for attempt in range(max_retries):
                                                try:
                                                    new_result = api.place_order(
                                                        symbol,
                                                        side=new_side,
                                                        qty=qty,
                                                        price=price,
                                                        stop_loss=stop_loss_param,
                                                        take_profit=take_profit_param,
                                                        leverage=leverage
                                                    )
                                                    if new_result:
                                                        break
                                                except Exception as order_error:
                                                    print(f"❌ Попытка {attempt + 1}/{max_retries} - ошибка размещения ордера реверса {symbol}: {order_error}")
                                                    if attempt < max_retries - 1:
                                                        time.sleep(1)  # Пауза перед повторной попыткой
                                            
                                            if new_result:
                                                print(f"✅ {symbol}: реверс успешно завершен - новая позиция открыта")
                                                current_positions[symbol] = last_signal['type']
                                                # Новый активный сигнал: фиксируем цену входа
                                                active_signal[symbol] = {
                                                    'type': last_signal['type'],
                                                    'time': signal_dt,
                                                    'expiry': (signal_dt + timedelta(days=2)) if signal_dt else None,
                                                    'last_entry_price': price
                                                }
                                                append_trade_log({
                                                    'event': 'reversed',
                                                    'symbol': symbol,
                                                    'side': new_side,
                                                    'qty': qty,
                                                    'price': price,
                                                    'timestamp': time.time()
                                                })
                                                socketio.emit('trade_executed', {
                                                    'symbol': symbol,
                                                    'side': new_side,
                                                    'qty': qty,
                                                    'price': price,
                                                    'timestamp': time.time(),
                                                    'action': 'reversed'
                                                })
                                            else:
                                                print(f"❌ {symbol}: не удалось открыть новую позицию после {max_retries} попыток")
                                                # Сбрасываем состояние позиции, так как старая закрыта, а новая не открылась
                                                current_positions[symbol] = None
                                        else:
                                            print(f"❌ {symbol}: рассчитанное qty <= 0, реверс не выполнен")
                                    
                                    else:
                                        print(f"❌ {symbol}: не удалось закрыть позицию для реверса")
                                        
                                last_signal_time[symbol] = str(last_signal['time'])
                            else:
                                if current_position_type is not None:
                                    print(f"{symbol}: Сигнал того же типа ({last_signal['type']}), позиция остается открытой (текущая позиция: {current_position_type})")
                                else:
                                    print(f"{symbol}: Сигнал того же типа ({last_signal['type']}), позиция остается открытой")
                else:
                    print(f"{symbol}: Нет новых сигналов.")
                
                # Отправляем обновления данных
                socketio.emit('price_update', {
                    'symbol': symbol,
                    'price': float(df['close'].iloc[-1]),
                    'timestamp': time.time()
                })
                
        except Exception as e:
            print(f"Ошибка в торговом цикле: {e}")
            raise e
            socketio.emit('error', {'message': str(e)})
        
        time.sleep(trading_config['trade_interval_sec'])

@app.route('/')
def index():
    print("🏠 Запрос главной страницы")
    return render_template('index.html')

@app.route('/test_backtest')
def test_backtest():
    return send_file('test_backtest_simple.html')

@app.route('/test_js')
def test_js():
    return send_file('test_js_simple.html')

@app.route('/test_button')
def test_button():
    return send_file('test_button_check.html')

@app.route('/api/health')
def health_check():
    """Проверка здоровья API"""
    try:
        print("🏥 Проверка здоровья API...")
        if not api:
            initialize_api()
        
        # Простая проверка - получаем информацию о BTCUSDT
        symbol_info = api.get_symbol_info("BTCUSDT")
        if symbol_info:
            return jsonify({
                'status': 'healthy',
                'message': 'API работает',
                'btc_price': symbol_info.get('lastPrice', 'N/A')
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Не удалось получить информацию о BTCUSDT'
            }), 500
    except Exception as e:
        print(f"❌ Ошибка проверки здоровья: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500



@app.route('/tradingview')
def tradingview_chart():
    return render_template('tradingview_chart.html')

@app.route('/tradingview-simple')
def tradingview_simple():
    return render_template('tradingview_simple.html')

@app.route('/tradingview-fixed')
def tradingview_fixed():
    return render_template('tradingview_fixed.html')

@app.route('/tradingview-iframe')
def tradingview_iframe():
    return render_template('tradingview_iframe.html')

@app.route('/tradingview-test')
def tradingview_test():
    return render_template('tradingview_test.html')

@app.route('/debug-chart')
def debug_chart():
    return render_template('debug_chart.html')

@app.route('/trades')
def trades_page():
    return render_template('trades.html')

@app.route('/api/trades/bybit')
def get_trades_bybit():
    """API для получения истории сделок из Bybit"""
    try:
        if not api:
            initialize_api()
        
        # Получаем историю сделок
        trades = api.get_trade_history(limit=100)
        
        # Сортируем по символу
        trades.sort(key=lambda x: x['symbol'])
        
        return jsonify({
            'success': True,
            'trades': trades,
            'total_symbols': len(trades)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/balance')
def get_balance():
    try:
        print("💰 Запрос баланса...")
        if not api:
            print("🔧 API не инициализирован, инициализируем...")
            initialize_api()
        print("📊 Получаем баланс USDT...")
        balance = api.get_balance("USDT")
        print(f"💰 Баланс получен: {balance}")
        return jsonify({'balance': balance})
    except Exception as e:
        print(f"❌ Ошибка получения баланса: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/balances')
def get_all_balances():
    try:
        if not api:
            initialize_api()
        balances = api.get_all_balances()
        return jsonify(balances)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions')
def get_positions():
    try:
        if not api:
            initialize_api()
        # Получаем все позиции, а не только по текущим символам
        pos = api.get_open_positions()
        return jsonify(pos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500




@app.route('/api/trading_pairs')
def get_trading_pairs():
    """Получает все доступные торговые пары"""
    try:
        print("📊 Запрос торговых пар...")
        if not api:
            print("🔧 API не инициализирован, инициализируем...")
            initialize_api()
        
        # Проверяем кэш
        cache_key = 'trading_pairs_cache'
        if hasattr(get_trading_pairs, cache_key):
            cached_data = getattr(get_trading_pairs, cache_key)
            if cached_data and (time.time() - cached_data['timestamp']) < 300:  # 5 минут кэш
                print("📊 Возвращаем кэшированные торговые пары")
                return jsonify(cached_data['data'])
        
        print("📊 Получаем популярные пары...")
        # Получаем популярные пары
        popular_pairs = api.get_popular_pairs()
        print(f"📊 Получено {len(popular_pairs)} популярных пар")
        
        print("📊 Получаем все пары...")
        # Получаем все пары (ограничиваем до топ-100 по объему)
        all_pairs = api.get_all_trading_pairs()[:100]
        print(f"📊 Получено {len(all_pairs)} всех пар")
        
        # Объединяем данные
        result = {
            'popular': popular_pairs,
            'all': all_pairs,
            'total_count': len(all_pairs)
        }
        
        # Кэшируем результат
        setattr(get_trading_pairs, cache_key, {
            'data': result,
            'timestamp': time.time()
        })
        
        print(f"📊 Возвращаем {len(all_pairs)} торговых пар")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Ошибка получения торговых пар: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading_pairs/search')
def search_trading_pairs():
    """Поиск торговых пар по символу"""
    try:
        if not api:
            initialize_api()
        
        query = request.args.get('q', '').upper()
        if not query:
            return jsonify([])
        
        # Получаем все пары
        all_pairs = api.get_all_trading_pairs()
        
        # Фильтруем по запросу
        filtered_pairs = []
        for pair in all_pairs:
            if query in pair['symbol']:
                filtered_pairs.append(pair)
        
        # Ограничиваем результат
        result = filtered_pairs[:20]
        
        print(f"Поиск '{query}': найдено {len(result)} пар")
        return jsonify(result)
        
    except Exception as e:
        print(f"Ошибка поиска торговых пар: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies', methods=['GET', 'POST'])
def strategies_mapping():
    """Получить/установить соответствие стратегий символам"""
    global symbol_strategies
    if request.method == 'GET':
        return jsonify(symbol_strategies)
    try:
        data = request.json or {}
        print(f"Получены данные стратегий: {data}")
        
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(k, str):
                    # Поддерживаем как строковые значения, так и объекты
                    if isinstance(v, str):
                        symbol_strategies[k.upper()] = v
                        print(f"Сохранена строка стратегия для {k}: {v}")
                    elif isinstance(v, dict):
                        symbol_strategies[k.upper()] = v
                        print(f"Сохранена объект стратегия для {k}: {v}")
                    else:
                        print(f"Пропускаем неверный тип данных для {k}: {type(v)}")
                else:
                    print(f"Пропускаем неверный ключ: {k} (тип: {type(k)})")
            
            save_symbol_strategies()
            print(f"Сохранено {len(symbol_strategies)} стратегий: {symbol_strategies}")
            return jsonify({'status': 'ok', 'strategies': symbol_strategies, 'count': len(symbol_strategies)})
        else:
            print(f"Неверный тип данных: {type(data)}")
            return jsonify({'error': 'invalid payload'}), 400
    except Exception as e:
        print(f"Ошибка сохранения стратегий: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ====== API: Trades and Stats ======
@app.route('/api/trades')
def api_get_trades():
    try:
        limit = int(request.args.get('limit', 200))
        return jsonify(read_trades(limit))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/stats')
def api_get_trades_stats():
    try:
        trades = read_trades(5000)
        stats = compute_trades_stats(trades)
        # Приводим defaultdict к обычным dict для JSON
        stats['per_symbol'] = {k: dict(v) for k, v in stats.get('per_symbol', {}).items()}
        stats['total_pnl_usd'] = round(stats['total_pnl_usd'], 2)
        for v in stats['per_symbol'].values():
            v['pnl_usd'] = round(v.get('pnl_usd', 0.0), 2)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    try:
        data = request.json
        symbol = data.get('symbol', 'BTCUSDT')
        interval = data.get('interval', '15')
        days_back = data.get('days_back', 30)
        leverage = data.get('leverage', 10)
        stop_loss_pct = data.get('stop_loss_pct', 2.0)
        take_profit_pct = data.get('take_profit_pct')  # Может быть None
        initial_balance = data.get('initial_balance', 1000.0)
        trade_size_pct = data.get('trade_size_pct', 3.0)
        
        # Конвертируем в правильные типы
        try:
            stop_loss_pct = float(stop_loss_pct) if stop_loss_pct is not None else 2.0
            take_profit_pct = float(take_profit_pct) if take_profit_pct is not None and take_profit_pct != '' else None
            leverage = int(leverage) if leverage is not None else 10
            initial_balance = float(initial_balance) if initial_balance is not None else 1000.0
            trade_size_pct = float(trade_size_pct) if trade_size_pct is not None else 3.0
        except (ValueError, TypeError) as e:
            print(f"Ошибка конвертации параметров: {e}")
            # Используем значения по умолчанию
            stop_loss_pct = 2.0
            take_profit_pct = None
            leverage = 10
            initial_balance = 1000.0
            trade_size_pct = 3.0
        
        print(f"Запускаем бэктест для {symbol}, интервал '{interval}' (тип: {type(interval)}), период {days_back} дней")
        print(f"Параметры: плечо {leverage}x, стоп-лосс {stop_loss_pct}%, тейк-профит {take_profit_pct}%, баланс ${initial_balance}, размер позиции {trade_size_pct}%")
        
        # Получаем исторические данные
        if not api:
            initialize_api()
        
        # Получаем данные по частям
        all_klines = []
        limit_per_request = 1000
        
        # Рассчитываем количество запросов
        if interval == '1':
            requests_needed = min(days_back * 24 * 60 // limit_per_request, 5)
        elif interval == '5':
            requests_needed = min(days_back * 24 * 12 // limit_per_request, 5)
        elif interval == '15':
            requests_needed = min(days_back * 24 * 4 // limit_per_request, 5)
        elif interval == '30':
            requests_needed = min(days_back * 24 * 2 // limit_per_request, 5)
        elif interval == '60':
            requests_needed = min(days_back * 24 // limit_per_request, 5)
        else:
            requests_needed = 1
        
        for i in range(requests_needed):
            print(f"Запрос {i+1}/{requests_needed}: получаем данные для {symbol} с интервалом '{interval}'")
            klines = api.get_klines(symbol, interval, limit=limit_per_request)
            if klines:
                all_klines.extend(klines)
                print(f"Получено {len(klines)} записей в запросе {i+1}")
            else:
                print(f"Нет данных в запросе {i+1}")
                break
        
        if not all_klines:
            return jsonify({'error': 'Не удалось получить исторические данные'}), 500
        
        # Убираем дубликаты и сортируем
        unique_klines = []
        seen_timestamps = set()
        
        for kline in all_klines:
            timestamp = kline[0]
            if timestamp not in seen_timestamps:
                seen_timestamps.add(timestamp)
                unique_klines.append(kline)
        
        unique_klines.sort(key=lambda x: int(x[0]))
        
        # Создаем DataFrame
        import pandas as pd
        df = pd.DataFrame(unique_klines, columns=['timestamp','open','high','low','close','volume','turnover'])
        df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
        df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        
        print(f"Получено {len(df)} исторических записей для бэктеста")
        print(f"Период: с {df['time'].iloc[0]} по {df['time'].iloc[-1]}")
        print(f"Примеры времен в DataFrame:")
        for i in range(min(5, len(df))):
            print(f"  Запись {i+1}: {df['time'].iloc[i]} - цена: {df['close'].iloc[i]}")
        
        # Запускаем бэктест
        strategy_type = data.get('strategy_type', 'ghost')
        
        if strategy_type == 'combined':
            from combined_strategy import CombinedStrategy
            strategy = CombinedStrategy()
            backtester = Backtester(strategy)
            signals = backtester.run_combined_strategy(df, leverage, stop_loss_pct, take_profit_pct, initial_balance, trade_size_pct)
        elif strategy_type == 'ott':
            from ott_strategy import OTTStrategy
            strategy = OTTStrategy()
            backtester = Backtester(strategy)
            signals = backtester.run_with_params(df, leverage, stop_loss_pct, take_profit_pct, initial_balance, trade_size_pct)
        else:
            strategy = GhostTangentStrategy()
            backtester = Backtester(strategy)
            signals = backtester.run_with_params(df, leverage, stop_loss_pct, take_profit_pct, initial_balance, trade_size_pct)
        
        # Рассчитываем статистику
        total_trades = len(signals)
        profitable_trades = 0
        total_profit_pct = 0
        total_profit_usd = 0
        max_profit = 0
        max_loss = 0
        avg_duration = 0
        
        # Инициализируем переменные
        stop_loss_trades = 0
        take_profit_trades = 0
        signal_trades = 0
        open_positions = 0
        
        if signals:
            profitable_trades = sum(1 for trade in signals if trade['profit_pct'] > 0)
            total_profit_pct = sum(trade['profit_pct'] for trade in signals)
            total_profit_usd = sum(trade['profit_usd'] for trade in signals)
            max_profit = max(trade['profit_pct'] for trade in signals) if signals else 0
            max_loss = min(trade['profit_pct'] for trade in signals) if signals else 0
            avg_duration = sum(trade['duration_hours'] for trade in signals) / len(signals) if signals else 0
            
            # Отладочная информация о причинах выхода
            exit_reasons = [trade.get('exit_reason', 'unknown') for trade in signals]
            print(f"🔍 Причины выхода из сделок: {exit_reasons[:10]}...")  # Показываем первые 10
            
            stop_loss_trades = sum(1 for trade in signals if trade.get('exit_reason') == 'stop_loss')
            take_profit_trades = sum(1 for trade in signals if trade.get('exit_reason') == 'take_profit')
            signal_trades = sum(1 for trade in signals if trade.get('exit_reason') == 'signal')
            open_positions = sum(1 for trade in signals if trade.get('exit_reason') == 'period_end')
        
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        result = {
            'trades': signals,
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': round(win_rate, 2),
            'total_profit_pct': round(total_profit_pct, 2),
            'total_profit_usd': round(total_profit_usd, 2),
            'max_profit': round(max_profit, 2),
            'max_loss': round(max_loss, 2),
            'avg_duration': round(avg_duration, 1),
            'period_start': df['time'].iloc[0].isoformat(),
            'period_end': df['time'].iloc[-1].isoformat(),
            'data_points': len(df),
            'symbol': symbol,
            'interval': interval,
            'leverage': leverage,
            'stop_loss_pct': stop_loss_pct,
            'take_profit_pct': take_profit_pct,
            'initial_balance': initial_balance,
            'trade_size_pct': trade_size_pct,
            'stop_loss_trades': stop_loss_trades,
            'take_profit_trades': take_profit_trades,
            'signal_trades': signal_trades,
            'open_positions': open_positions
        }
        
        print(f"Бэктест завершен: {total_trades} сделок, {win_rate}% прибыльных")
        print(f"Детализация выходов:")
        print(f"  - По стоп-лоссу: {stop_loss_trades}")
        print(f"  - По тейк-профиту: {take_profit_trades}")
        print(f"  - По сигналу: {signal_trades}")
        print(f"  - Открытые позиции: {open_positions}")
        
        print(f"📤 Отправляем результат клиенту: {len(result)} полей")
        print(f"📊 Результат содержит trades: {'trades' in result}")
        print(f"📊 Количество сделок в результате: {len(result.get('trades', []))}")
        
        return jsonify(result)
    except Exception as e:
        print(f"Ошибка бэктеста: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/start', methods=['POST'])
def start_trading():
    global is_trading, trading_thread, current_symbols, strategy, symbol_strategies
    
    try:
        data = request.json
        current_symbols = data.get('symbols', ['BTCUSDT'])
        config = data.get('config', {})
        
        # Пер-символьные стратегии (формат: { "BTCUSDT": "ott", "ETHUSDT": "ghost" } или объекты)
        strategies_map = data.get('strategies', {})
        if isinstance(strategies_map, dict):
            # Поддерживаем как строки, так и объекты стратегий
            for k, v in strategies_map.items():
                if isinstance(v, str) or isinstance(v, dict):
                    symbol_strategies[k.upper()] = v
            save_symbol_strategies()
            print(f"📊 Загружены стратегии: {symbol_strategies}")
        
        # Обрабатываем тейк-профит
        if 'take_profit_pct' in config:
            take_profit = config['take_profit_pct']
            if take_profit is not None and take_profit > 0:
                config['take_profit_pct'] = take_profit / 100  # Конвертируем в десятичную дробь
            else:
                config['take_profit_pct'] = None
        
        trading_config.update(config)
        print(f"⚙️ Конфигурация торговли: {trading_config}")
        print(f"📈 Символы для торговли: {current_symbols}")
        
        if not api:
            initialize_api()
        
        if not strategy:
            strategy = GhostTangentStrategy()
        
        # Устанавливаем плечо для всех символов
        for symbol in current_symbols:
            try:
                # Используем per-symbol плечо из symbol_strategies, если есть
                symbol_leverage = None
                strategy_data = symbol_strategies.get(symbol)
                if isinstance(strategy_data, dict) and 'leverage' in strategy_data:
                    symbol_leverage = int(strategy_data['leverage'])
                    print(f"📊 {symbol}: используем плечо из symbol_strategies: {symbol_leverage}x")
                else:
                    # Fallback на глобальные настройки
                    symbol_leverage = trading_config['buy_leverage']
                    print(f"📊 {symbol}: используем глобальное плечо: {symbol_leverage}x")
                
                api.set_leverage(
                    symbol, 
                    buy_leverage=symbol_leverage, 
                    sell_leverage=symbol_leverage
                )
                print(f"✅ Плечо установлено для {symbol}: {symbol_leverage}x")
            except Exception as e:
                print(f"⚠️ Не удалось установить плечо для {symbol}: {e}")
        
        if not is_trading:
            is_trading = True
            trading_thread = threading.Thread(target=trading_loop)
            trading_thread.daemon = True
            trading_thread.start()
            print("🚀 Торговый поток запущен")
        
        return jsonify({
            'status': 'success', 
            'message': 'Торговля запущена',
            'symbols': current_symbols,
            'strategies': symbol_strategies,
            'config': trading_config
        })
    except Exception as e:
        print(f"❌ Ошибка запуска торговли: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    global is_trading
    
    try:
        is_trading = False
        return jsonify({'status': 'success', 'message': 'Торговля остановлена'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/status')
def get_trading_status():
    try:
        # Получаем количество открытых позиций
        open_positions_count = 0
        if api:
            try:
                positions = api.get_open_positions()
                open_positions_count = len(positions)
            except Exception as e:
                print(f"Ошибка получения позиций: {e}")
        
        return jsonify({
            'is_trading': is_trading,
            'symbols': current_symbols,
            'config': trading_config,
            'strategies': symbol_strategies,
            'open_positions_count': open_positions_count,
            'active_pairs_count': len(current_symbols)
        })
    except Exception as e:
        print(f"Ошибка получения статуса торговли: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/place_order', methods=['POST'])
def place_manual_order():
    try:
        if not api:
            initialize_api()
        
        data = request.json
        symbol = data['symbol']
        side = data['side']
        qty = float(data['qty'])
        price = float(data.get('price', 0))
        order_type = data.get('order_type', 'Market')
        stop_loss = float(data.get('stop_loss', 0))
        take_profit = float(data.get('take_profit', 0))
        
        result = api.place_order(
            symbol=symbol,
            side=side,
            qty=qty,
            price=price if order_type == 'Limit' else None,
            stop_loss=stop_loss if stop_loss > 0 else None,
            take_profit=take_profit if take_profit > 0 else None,
            order_type=order_type
        )
        
        if result:
            return jsonify({'status': 'success', 'order': result})
        else:
            return jsonify({'error': 'Не удалось разместить ордер'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/api/test-timestamp-sync', methods=['GET'])
def test_timestamp_sync():
    """Тестирует синхронизацию времени с сервером Bybit"""
    try:
        if not api:
            return jsonify({'error': 'API не инициализирован'}), 400
        
        # Получаем информацию о синхронизации времени
        server_time = api.get_server_time()
        sync_timestamp = api.get_synchronized_timestamp()
        local_timestamp = int(time.time() * 1000)
        
        result = {
            'success': True,
            'time_offset_ms': api.time_offset,
            'server_time': server_time,
            'local_time': local_timestamp,
            'sync_time': sync_timestamp,
            'time_diff': sync_timestamp - local_timestamp
        }
        
        # Тестируем простой API запрос
        try:
            klines = api.get_klines("BTCUSDT", "1", limit=1)
            result['api_test_success'] = len(klines) > 0
            result['api_test_message'] = f"Получено {len(klines)} свечей" if klines else "Нет данных"
        except Exception as e:
            result['api_test_success'] = False
            result['api_test_message'] = str(e)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resync-time', methods=['POST'])
def resync_time():
    """Повторно синхронизирует время с сервером"""
    try:
        if not api:
            return jsonify({'error': 'API не инициализирован'}), 400
        
        # Выполняем повторную синхронизацию
        api.resync_time()
        
        return jsonify({
            'success': True,
            'message': 'Время успешно синхронизировано',
            'new_offset_ms': api.time_offset
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test-timestamp')
def test_timestamp_page():
    """Страница для тестирования синхронизации времени"""
    return render_template('test_timestamp.html')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 