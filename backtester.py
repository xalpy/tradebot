import pandas as pd
from strategy import GhostTangentStrategy
import matplotlib.pyplot as plt

class Backtester:
    def __init__(self, strategy):
        self.strategy = strategy

    def run(self, df):
        signals = self.strategy.generate_signals(df)
        return self.process_signals_with_trades(df, signals)
    
    def run_with_params(self, df, leverage=10, stop_loss_pct=2.0, take_profit_pct=None, initial_balance=1000.0, trade_size_pct=3.0):
        """
        Запускает бэктест с учетом плеча, стоп-лосса, тейк-профита и размера позиции
        """
        signals = self.strategy.generate_signals(df)
        return self.process_signals_with_trades_advanced(df, signals, leverage, stop_loss_pct, take_profit_pct, initial_balance, trade_size_pct)
    
    def run_combined_strategy(self, df, leverage=10, stop_loss_pct=2.0, take_profit_pct=None, initial_balance=1000.0, trade_size_pct=3.0):
        """
        Запускает бэктест с комбинированной стратегией
        """
        from combined_strategy import CombinedStrategy
        
        combined_strategy = CombinedStrategy()
        signals = combined_strategy.generate_signals(df)
        
        # Добавляем информацию о стратегии к сигналам
        for signal in signals:
            signal['strategy'] = 'combined'
            signal['confidence'] = signal.get('confidence', 50)
        
        return self.process_signals_with_trades_advanced(df, signals, leverage, stop_loss_pct, take_profit_pct, initial_balance, trade_size_pct)
    
    def process_signals_with_trades(self, df, signals):
        """
        Обрабатывает сигналы с логикой двойных сигналов:
        - Если нет позиции и пришел сигнал - открываем позицию
        - Если есть позиция и пришел противоположный сигнал - закрываем и открываем новую
        """
        trades = []
        current_position = None
        current_entry = None
        
        # Сортируем сигналы по времени
        sorted_signals = sorted(signals, key=lambda x: pd.to_datetime(x['time']))
        
        for signal in sorted_signals:
            if current_position is None:
                # Нет позиции - открываем новую
                current_position = signal['type']
                current_entry = signal
            else:
                # Есть позиция - проверяем на противоположный сигнал
                if ((current_position == 'buy' and signal['type'] == 'sell') or 
                    (current_position == 'sell' and signal['type'] == 'buy')):
                    
                    # Закрываем текущую позицию
                    exit_price = signal['price']
                    entry_price = current_entry['price']
                    
                    # Рассчитываем прибыль/убыток
                    if current_position == 'buy':
                        profit_pct = (exit_price - entry_price) / entry_price * 100
                        profit_usd = exit_price - entry_price
                    else:  # sell
                        profit_pct = (entry_price - exit_price) / entry_price * 100
                        profit_usd = entry_price - exit_price
                    
                    # Создаем запись о сделке
                    trade = {
                        'entry_time': current_entry['time'],
                        'entry_type': current_position,
                        'entry_price': entry_price,
                        'exit_time': signal['time'],
                        'exit_type': signal['type'],
                        'exit_price': exit_price,
                        'profit_pct': round(profit_pct, 2),
                        'profit_usd': round(profit_usd, 2),
                        'duration_hours': self.calculate_duration(current_entry['time'], signal['time']),
                        'status': 'profitable' if profit_pct > 0 else 'loss'
                    }
                    trades.append(trade)
                    
                    # Открываем новую позицию
                    current_position = signal['type']
                    current_entry = signal
        
        # Если осталась открытая позиция в конце периода, закрываем по последней цене
        if current_position is not None and current_entry is not None:
            last_price = df['close'].iloc[-1]
            entry_price = current_entry['price']
            
            if current_position == 'buy':
                profit_pct = (last_price - entry_price) / entry_price * 100
                profit_usd = last_price - entry_price
            else:  # sell
                profit_pct = (entry_price - last_price) / entry_price * 100
                profit_usd = entry_price - last_price
            
            trade = {
                'entry_time': current_entry['time'],
                'entry_type': current_position,
                'entry_price': entry_price,
                'exit_time': df['time'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S'),
                'exit_type': 'close',
                'exit_price': last_price,
                'profit_pct': round(profit_pct, 2),
                'profit_usd': round(profit_usd, 2),
                'duration_hours': self.calculate_duration(current_entry['time'], df['time'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')),
                'status': 'profitable' if profit_pct > 0 else 'loss'
            }
            trades.append(trade)
        
        return trades
    
    def process_signals_with_trades_advanced(self, df, signals, leverage, stop_loss_pct, take_profit_pct, initial_balance, trade_size_pct):
        """
        Обрабатывает сигналы с учетом плеча, стоп-лосса, тейк-профита и размера позиции
        """
        trades = []
        current_position = None
        current_entry = None
        current_balance = initial_balance
        
        # Сортируем сигналы по времени
        sorted_signals = sorted(signals, key=lambda x: pd.to_datetime(x['time']))
        
        print(f"🔍 Всего сигналов: {len(sorted_signals)}")
        print(f"💰 Начальный баланс: ${initial_balance}")
        print(f"📊 Параметры: плечо {leverage}x, размер позиции {trade_size_pct}%, стоп-лосс {stop_loss_pct}% (тип: {type(stop_loss_pct)}), тейк-профит {take_profit_pct}% (тип: {type(take_profit_pct)})")
        for i, sig in enumerate(sorted_signals[:5]):  # Показываем первые 5 сигналов
            print(f"  Сигнал {i+1}: {sig['time']} - {sig['type']} - ${sig['price']}")
        
        for i, signal in enumerate(sorted_signals):
            if current_position is None:
                # Нет позиции - открываем новую
                current_position = signal['type']
                current_entry = signal
            else:
                # Есть позиция - проверяем на противоположный сигнал или стоп-лосс
                exit_signal = None
                exit_reason = None
                
                # Проверяем стоп-лосс
                stop_loss_hit = self.check_stop_loss(df, current_entry, signal, stop_loss_pct, current_position, leverage)
                print(f"🔍 Проверка стоп-лосса: {current_position} позиция, вход: {current_entry['price']}, стоп: {stop_loss_pct}% -> {stop_loss_hit}")
                
                if stop_loss_hit:
                    exit_signal = signal
                    exit_reason = 'stop_loss'
                    print(f"🛑 Сработал стоп-лосс: {current_position} позиция, вход: {current_entry['price']}, стоп: {stop_loss_pct}%")
                # Проверяем тейк-профит
                elif take_profit_pct:
                    take_profit_hit = self.check_take_profit(df, current_entry, signal, take_profit_pct, current_position, leverage)
                    print(f"🔍 Проверка тейк-профита: {current_position} позиция, вход: {current_entry['price']}, тейк: {take_profit_pct}% -> {take_profit_hit}")
                    
                    if take_profit_hit:
                        exit_signal = signal
                        exit_reason = 'take_profit'
                        print(f"🎯 Сработал тейк-профит: {current_position} позиция, вход: {current_entry['price']}, тейк: {take_profit_pct}%")
                # Проверяем противоположный сигнал
                elif ((current_position == 'buy' and signal['type'] == 'sell') or 
                      (current_position == 'sell' and signal['type'] == 'buy')):
                    exit_signal = signal
                    exit_reason = 'signal'
                    print(f"📊 Выход по сигналу: {current_position} -> {signal['type']}")
                
                if exit_signal:
                    # Закрываем текущую позицию
                    if exit_reason in ['stop_loss', 'take_profit']:
                        # Находим точную цену срабатывания стоп-лосса или тейк-профита
                        exit_price = self.get_exit_price(df, current_entry, exit_signal, exit_reason, stop_loss_pct, take_profit_pct, current_position, leverage)
                        print(f"💰 Цена выхода: {exit_price} (вход: {current_entry['price']})")
                    else:
                        exit_price = exit_signal['price']
                    entry_price = current_entry['price']
                    
                    # Рассчитываем прибыль/убыток с учетом плеча
                    if current_position == 'buy':
                        price_change_pct = (exit_price - entry_price) / entry_price
                        profit_pct = price_change_pct * leverage * 100
                        profit_usd = price_change_pct * leverage * (current_balance * trade_size_pct / 100)
                        print(f"📊 Buy позиция: вход ${entry_price:.2f} -> выход ${exit_price:.2f} = {profit_pct:.2f}% (${profit_usd:.2f})")
                    else:  # sell
                        price_change_pct = (entry_price - exit_price) / entry_price
                        profit_pct = price_change_pct * leverage * 100
                        profit_usd = price_change_pct * leverage * (current_balance * trade_size_pct / 100)
                        print(f"📊 Sell позиция: вход ${entry_price:.2f} -> выход ${exit_price:.2f} = {profit_pct:.2f}% (${profit_usd:.2f})")
                    
                    # Обновляем баланс
                    old_balance = current_balance
                    current_balance += profit_usd
                    print(f"💰 Баланс: ${old_balance:.2f} -> ${current_balance:.2f} (изменение: ${profit_usd:.2f})")
                    
                    # Создаем запись о сделке
                    trade = {
                        'entry_time': current_entry['time'],
                        'entry_type': current_position,
                        'entry_price': entry_price,
                        'exit_time': exit_signal['time'],
                        'exit_type': exit_signal['type'],
                        'exit_price': exit_price,
                        'profit_pct': round(profit_pct, 2),
                        'profit_usd': round(profit_usd, 2),
                        'duration_hours': self.calculate_duration(current_entry['time'], exit_signal['time']),
                        'status': 'profitable' if profit_pct > 0 else 'loss',
                        'leverage': leverage,
                        'exit_reason': exit_reason,
                        'balance_after': round(current_balance, 2)
                    }
                    trades.append(trade)
                    print(f"💼 Создана сделка: {current_entry['time']} -> {exit_signal['time']} ({exit_reason})")
                    
                    # Открываем новую позицию (если это был сигнал, а не стоп-лосс)
                    if exit_reason == 'signal':
                        current_position = signal['type']
                        current_entry = signal
                    else:
                        current_position = None
                        current_entry = None
        
        # Если осталась открытая позиция в конце периода, закрываем по последней цене
        if current_position is not None and current_entry is not None:
            last_price = df['close'].iloc[-1]
            entry_price = current_entry['price']
            
            if current_position == 'buy':
                price_change_pct = (last_price - entry_price) / entry_price
                profit_pct = price_change_pct * leverage * 100
                profit_usd = price_change_pct * leverage * (current_balance * trade_size_pct / 100)
                print(f"📊 Buy позиция (конец периода): вход ${entry_price:.2f} -> выход ${last_price:.2f} = {profit_pct:.2f}% (${profit_usd:.2f})")
            else:  # sell
                price_change_pct = (entry_price - last_price) / entry_price
                profit_pct = price_change_pct * leverage * 100
                profit_usd = price_change_pct * leverage * (current_balance * trade_size_pct / 100)
                print(f"📊 Sell позиция (конец периода): вход ${entry_price:.2f} -> выход ${last_price:.2f} = {profit_pct:.2f}% (${profit_usd:.2f})")
            
            old_balance = current_balance
            current_balance += profit_usd
            print(f"💰 Баланс (конец периода): ${old_balance:.2f} -> ${current_balance:.2f} (изменение: ${profit_usd:.2f})")
            
            trade = {
                'entry_time': current_entry['time'],
                'entry_type': current_position,
                'entry_price': entry_price,
                'exit_time': df['time'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S'),
                'exit_type': 'close',
                'exit_price': last_price,
                'profit_pct': round(profit_pct, 2),
                'profit_usd': round(profit_usd, 2),
                'duration_hours': self.calculate_duration(current_entry['time'], df['time'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')),
                'status': 'profitable' if profit_pct > 0 else 'loss',
                'leverage': leverage,
                'exit_reason': 'period_end',
                'balance_after': round(current_balance, 2)
            }
            trades.append(trade)
        
        return trades
    
    def check_stop_loss(self, df, entry_signal, current_signal, stop_loss_pct, position_type, leverage=1):
        """
        Проверяет, сработал ли стоп-лосс между входом и текущим сигналом
        Учитывает плечо: реальный стоп-лосс = stop_loss_pct / leverage
        """
        entry_price = entry_signal['price']
        entry_time = pd.to_datetime(entry_signal['time'])
        current_time = pd.to_datetime(current_signal['time'])
        
        # Учитываем плечо: реальный стоп-лосс уменьшается с плечом
        real_stop_loss_pct = stop_loss_pct / leverage
        print(f"🔍 Проверка стоп-лосса: {position_type} позиция, вход: ${entry_price:.2f}, стоп: {stop_loss_pct}% (реальный: {real_stop_loss_pct:.2f}% с плечом {leverage}x)")
        
        # Находим все свечи между входом и текущим сигналом
        mask = (df['time'] >= entry_time) & (df['time'] <= current_time)
        candles_between = df[mask]
        
        if position_type == 'buy':
            # Для длинной позиции стоп-лосс срабатывает при падении цены
            # Проверяем, была ли цена ниже стоп-лосса в любой момент
            for _, candle in candles_between.iterrows():
                # Проверяем low свечи (минимальная цена)
                loss_pct = (entry_price - candle['low']) / entry_price * 100
                if loss_pct >= real_stop_loss_pct:
                    print(f"🔍 Стоп-лосс сработал: цена упала до {candle['low']} (потеря: {loss_pct:.2f}%, реальный стоп: {real_stop_loss_pct:.2f}%)")
                    return True
        else:  # sell
            # Для короткой позиции стоп-лосс срабатывает при росте цены
            # Проверяем, была ли цена выше стоп-лосса в любой момент
            for _, candle in candles_between.iterrows():
                # Проверяем high свечи (максимальная цена)
                loss_pct = (candle['high'] - entry_price) / entry_price * 100
                if loss_pct >= real_stop_loss_pct:
                    print(f"🔍 Стоп-лосс сработал: цена выросла до {candle['high']} (потеря: {loss_pct:.2f}%, реальный стоп: {real_stop_loss_pct:.2f}%)")
                    return True
        
        return False
    
    def check_take_profit(self, df, entry_signal, current_signal, take_profit_pct, position_type, leverage=1):
        """
        Проверяет, сработал ли тейк-профит между входом и текущим сигналом
        Учитывает плечо: реальный тейк-профит = take_profit_pct / leverage
        """
        entry_price = entry_signal['price']
        entry_time = pd.to_datetime(entry_signal['time'])
        current_time = pd.to_datetime(current_signal['time'])
        
        # Учитываем плечо: реальный тейк-профит уменьшается с плечом
        real_take_profit_pct = take_profit_pct / leverage
        print(f"🔍 Проверка тейк-профита: {position_type} позиция, вход: ${entry_price:.2f}, тейк: {take_profit_pct}% (реальный: {real_take_profit_pct:.2f}% с плечом {leverage}x)")
        
        # Находим все свечи между входом и текущим сигналом
        mask = (df['time'] >= entry_time) & (df['time'] <= current_time)
        candles_between = df[mask]
        
        if position_type == 'buy':
            # Для длинной позиции тейк-профит срабатывает при росте цены
            # Проверяем, была ли цена выше тейк-профита в любой момент
            for _, candle in candles_between.iterrows():
                # Проверяем high свечи (максимальная цена)
                profit_pct = (candle['high'] - entry_price) / entry_price * 100
                if profit_pct >= real_take_profit_pct:
                    print(f"🎯 Тейк-профит сработал: цена выросла до {candle['high']} (прибыль: {profit_pct:.2f}%, реальный тейк: {real_take_profit_pct:.2f}%)")
                    return True
        else:  # sell
            # Для короткой позиции тейк-профит срабатывает при падении цены
            # Проверяем, была ли цена ниже тейк-профита в любой момент
            for _, candle in candles_between.iterrows():
                # Проверяем low свечи (минимальная цена)
                profit_pct = (entry_price - candle['low']) / entry_price * 100
                if profit_pct >= real_take_profit_pct:
                    print(f"🎯 Тейк-профит сработал: цена упала до {candle['low']} (прибыль: {profit_pct:.2f}%, реальный тейк: {real_take_profit_pct:.2f}%)")
                    return True
        
        return False
    
    def get_exit_price(self, df, entry_signal, current_signal, exit_reason, stop_loss_pct, take_profit_pct, position_type, leverage=1):
        """
        Находит реальную цену срабатывания стоп-лосса или тейк-профита
        Учитывает плечо: реальные уровни = уровни / leverage
        """
        entry_price = entry_signal['price']
        entry_time = pd.to_datetime(entry_signal['time'])
        current_time = pd.to_datetime(current_signal['time'])
        
        # Находим все свечи между входом и текущим сигналом
        mask = (df['time'] >= entry_time) & (df['time'] <= current_time)
        candles_between = df[mask]
        
        if exit_reason == 'stop_loss':
            if position_type == 'buy':
                # Для длинной позиции ищем реальную цену, по которой сработал стоп-лосс
                real_stop_loss_pct = stop_loss_pct / leverage
                target_price = entry_price * (1 - real_stop_loss_pct / 100)
                for _, candle in candles_between.iterrows():
                    if candle['low'] <= target_price:
                        # Возвращаем реальную цену low свечи (может быть ниже стоп-лосса)
                        return candle['low']
            else:  # sell
                # Для короткой позиции ищем реальную цену, по которой сработал стоп-лосс
                real_stop_loss_pct = stop_loss_pct / leverage
                target_price = entry_price * (1 + real_stop_loss_pct / 100)
                for _, candle in candles_between.iterrows():
                    if candle['high'] >= target_price:
                        # Возвращаем реальную цену high свечи (может быть выше стоп-лосса)
                        return candle['high']
        elif exit_reason == 'take_profit':
            if position_type == 'buy':
                # Для длинной позиции ищем реальную цену, по которой сработал тейк-профит
                real_take_profit_pct = take_profit_pct / leverage
                target_price = entry_price * (1 + real_take_profit_pct / 100)
                for _, candle in candles_between.iterrows():
                    if candle['high'] >= target_price:
                        # Возвращаем реальную цену high свечи (может быть выше тейк-профита)
                        return candle['high']
            else:  # sell
                # Для короткой позиции ищем реальную цену, по которой сработал тейк-профит
                real_take_profit_pct = take_profit_pct / leverage
                target_price = entry_price * (1 - real_take_profit_pct / 100)
                for _, candle in candles_between.iterrows():
                    if candle['low'] <= target_price:
                        # Возвращаем реальную цену low свечи (может быть ниже тейк-профита)
                        return candle['low']
        
        # Если не нашли точную цену, возвращаем цену текущего сигнала
        return current_signal['price']
    
    def calculate_duration(self, entry_time, exit_time):
        """Рассчитывает продолжительность сделки в часах"""
        try:
            entry_dt = pd.to_datetime(entry_time)
            exit_dt = pd.to_datetime(exit_time)
            duration = exit_dt - entry_dt
            return round(duration.total_seconds() / 3600, 1)
        except:
            return 0

    def plot_signals(self, df, signals):
        plt.figure(figsize=(15, 8))
        plt.plot(df['time'] if 'time' in df.columns else df.index, df['close'], label='Close Price', color='blue')
        
        buy_signals = [s for s in signals if s['type'] == 'buy']
        sell_signals = [s for s in signals if s['type'] == 'sell']
        
        if buy_signals:
            buy_idx = [s['index'] for s in buy_signals]
            buy_price = [s['price'] for s in buy_signals]
            plt.scatter(buy_idx, buy_price, marker='^', color='green', label='Buy', s=100, zorder=5)
        if sell_signals:
            sell_idx = [s['index'] for s in sell_signals]
            sell_price = [s['price'] for s in sell_signals]
            plt.scatter(sell_idx, sell_price, marker='v', color='red', label='Sell', s=100, zorder=5)
        
        plt.title('Backtest Signals')
        plt.xlabel('Index')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def trades_table_and_profit(self, signals, buy_leverage=1, sell_leverage=1):
        # Формируем сделки: открываем по buy, закрываем по sell (и наоборот), только если exit позже entry по времени
        trades = []
        position = None
        entry = None
        # Сортируем сигналы по времени
        for s in sorted(signals, key=lambda x: pd.to_datetime(x['time'])):
            if position is None:
                position = s['type']
                entry = s
            else:
                # Закрываем только если сигнал противоположный и время ПОЗЖЕ entry
                if ((position == 'buy' and s['type'] == 'sell') or (position == 'sell' and s['type'] == 'buy')) \
                    and pd.to_datetime(s['time']) > pd.to_datetime(entry['time']):
                    if position == 'buy':
                        profit_pct = (s['price'] - entry['price']) / entry['price'] * 100 * buy_leverage
                    else:
                        profit_pct = (entry['price'] - s['price']) / entry['price'] * 100 * sell_leverage
                    trades.append({
                        'entry_time': entry['time'],
                        'entry_type': entry['type'],
                        'entry_price': entry['price'],
                        'exit_time': s['time'],
                        'exit_type': s['type'],
                        'exit_price': s['price'],
                        'profit_%': round(profit_pct, 2)
                    })
                    position = None
                    entry = None
        # Выводим таблицу
        if trades:
            df_trades = pd.DataFrame(trades)
            print(df_trades)
            total_profit = df_trades['profit_%'].sum()
            print(f'Итоговый профит с учётом плеча: {round(total_profit, 2)}%')
        else:
            print('Сделок не найдено.') 