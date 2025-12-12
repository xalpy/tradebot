import numpy as np
import pandas as pd
from datetime import datetime

class GhostTangentStrategy:
    def __init__(self, pivot_period=25, max_zig=10):
        self.pivot_period = pivot_period
        self.max_zig = max_zig

    def pivothigh(self, series, back, forward):
        ph = (series.shift(forward) > series.shift(forward + 1)) & \
             (series.shift(forward) > series.shift(forward - 1))
        for i in range(1, back+1):
            ph &= (series.shift(forward) > series.shift(forward + i))
        for i in range(1, forward+1):
            ph &= (series.shift(forward) > series.shift(forward - i))
        return ph

    def pivotlow(self, series, back, forward):
        pl = (series.shift(forward) < series.shift(forward + 1)) & \
             (series.shift(forward) < series.shift(forward - 1))
        for i in range(1, back+1):
            pl &= (series.shift(forward) < series.shift(forward + i))
        for i in range(1, forward+1):
            pl &= (series.shift(forward) < series.shift(forward - i))
        return pl

    def generate_signals(self, df):
        # df — DataFrame с колонками ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        signals = []
        back = self.pivot_period
        forward = self.pivot_period
        high_ph = self.pivothigh(df['high'], back, forward)
        low_pl = self.pivotlow(df['low'], back, forward)
        # Условие по объёму: текущий объём > предыдущего на 30%
        # vol_cond = df['volume'] > df['volume'].shift(1) * 1
        for idx in range(len(df)):
            # Используем время из DataFrame, которое уже обработано pandas
            if 'time' in df.columns:
                dt = df['time'].iloc[idx].strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Fallback для старого формата
                ts = df['timestamp'].iloc[idx]
                if isinstance(ts, str):
                    try:
                        ts = int(ts)
                    except Exception:
                        continue
                dt = datetime.utcfromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M:%S')
            # Сигнал на покупку (pivotlow + объём)
            if low_pl.iloc[idx]: # and vol_cond.iloc[idx]:
                signal = {
                    'type': 'buy',
                    'index': idx,
                    'price': df['close'].iloc[idx],
                    'volume': df['volume'].iloc[idx],
                    'time': dt
                }
                signals.append(signal)
                print(f"📈 Buy сигнал: {dt} - цена: {df['close'].iloc[idx]}")
            # Сигнал на продажу (pivothigh + объём)
            if high_ph.iloc[idx]: # and vol_cond.iloc[idx]:
                signal = {
                    'type': 'sell',
                    'index': idx,
                    'price': df['close'].iloc[idx],
                    'volume': df['volume'].iloc[idx],
                    'time': dt
                }
                signals.append(signal)
                print(f"📉 Sell сигнал: {dt} - цена: {df['close'].iloc[idx]}")
        return signals 