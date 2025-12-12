import pandas as pd
import numpy as np

class OTTStrategy:
    """
    Optimized Trend Tracker (OTT) Strategy
    Основана на Pine Script индикаторе OTT
    """
    
    def __init__(self, length=2, percent=1.4, ma_type="VAR"):
        self.length = length
        self.percent = percent
        self.ma_type = ma_type
        
    def var_func(self, src):
        """VAR (Variable Moving Average) функция"""
        valpha = 2 / (self.length + 1)
        vud1 = np.where(src > np.roll(src, 1), src - np.roll(src, 1), 0)
        vdd1 = np.where(src < np.roll(src, 1), np.roll(src, 1) - src, 0)
        
        # Сумма за 9 периодов
        vud = pd.Series(vud1).rolling(9).sum().fillna(0)
        vdd = pd.Series(vdd1).rolling(9).sum().fillna(0)
        
        vcmo = (vud - vdd) / (vud + vdd)
        vcmo = vcmo.fillna(0)
        
        var = np.zeros_like(src)
        for i in range(1, len(src)):
            var[i] = valpha * abs(vcmo.iloc[i]) * src[i] + (1 - valpha * abs(vcmo.iloc[i])) * var[i-1]
        
        return var
    
    def wwma_func(self, src):
        """WWMA (Welles Wilder Moving Average) функция"""
        wwalpha = 1 / self.length
        wwma = np.zeros_like(src)
        wwma[0] = src[0]
        
        for i in range(1, len(src)):
            wwma[i] = wwalpha * src[i] + (1 - wwalpha) * wwma[i-1]
        
        return wwma
    
    def zlema_func(self, src):
        """ZLEMA (Zero Lag Exponential Moving Average) функция"""
        zxlag = int(self.length / 2) if self.length % 2 == 0 else int((self.length - 1) / 2)
        zxemadata = src + (src - np.roll(src, zxlag))
        zxemadata[0:zxlag] = src[0:zxlag]  # Исправляем NaN в начале
        
        # Простая EMA
        alpha = 2 / (self.length + 1)
        zlema = np.zeros_like(src)
        zlema[0] = zxemadata[0]
        
        for i in range(1, len(src)):
            zlema[i] = alpha * zxemadata[i] + (1 - alpha) * zlema[i-1]
        
        return zlema
    
    def tsf_func(self, src):
        """TSF (Time Series Forecast) функция"""
        tsf = np.zeros_like(src)
        
        for i in range(self.length, len(src)):
            # Линейная регрессия
            x = np.arange(self.length)
            y = src[i-self.length+1:i+1]
            
            # Коэффициенты линейной регрессии
            n = len(x)
            sum_x = np.sum(x)
            sum_y = np.sum(y)
            sum_xy = np.sum(x * y)
            sum_x2 = np.sum(x * x)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
            
            # Прогноз
            tsf[i] = slope * (self.length - 1) + intercept + slope
        
        return tsf
    
    def get_ma(self, src):
        """Получение скользящей средней выбранного типа"""
        if self.ma_type == "SMA":
            return pd.Series(src).rolling(self.length).mean().fillna(method='bfill')
        elif self.ma_type == "EMA":
            return pd.Series(src).ewm(span=self.length).mean()
        elif self.ma_type == "WMA":
            weights = np.arange(1, self.length + 1)
            return pd.Series(src).rolling(self.length).apply(
                lambda x: np.dot(x, weights) / weights.sum(), raw=True
            ).fillna(method='bfill')
        elif self.ma_type == "TMA":
            half_length = int(np.ceil(self.length / 2))
            sma1 = pd.Series(src).rolling(half_length).mean()
            return sma1.rolling(int(np.floor(self.length / 2)) + 1).mean().fillna(method='bfill')
        elif self.ma_type == "VAR":
            return pd.Series(self.var_func(src))
        elif self.ma_type == "WWMA":
            return pd.Series(self.wwma_func(src))
        elif self.ma_type == "ZLEMA":
            return pd.Series(self.zlema_func(src))
        elif self.ma_type == "TSF":
            return pd.Series(self.tsf_func(src))
        else:
            return pd.Series(src).rolling(self.length).mean().fillna(method='bfill')
    
    def calculate_ott(self, df):
        """Расчет OTT индикатора"""
        src = df['close'].values
        mavg = self.get_ma(src).values
        
        fark = mavg * self.percent * 0.01
        
        # Long Stop
        long_stop = mavg - fark
        long_stop_prev = np.roll(long_stop, 1)
        long_stop_prev[0] = long_stop[0]
        
        for i in range(1, len(long_stop)):
            if mavg[i] > long_stop_prev[i]:
                long_stop[i] = max(long_stop[i], long_stop_prev[i])
            else:
                long_stop[i] = long_stop[i]
        
        # Short Stop
        short_stop = mavg + fark
        short_stop_prev = np.roll(short_stop, 1)
        short_stop_prev[0] = short_stop[0]
        
        for i in range(1, len(short_stop)):
            if mavg[i] < short_stop_prev[i]:
                short_stop[i] = min(short_stop[i], short_stop_prev[i])
            else:
                short_stop[i] = short_stop[i]
        
        # Direction
        dir_array = np.ones(len(src))
        for i in range(1, len(dir_array)):
            if dir_array[i-1] == -1 and mavg[i] > short_stop_prev[i]:
                dir_array[i] = 1
            elif dir_array[i-1] == 1 and mavg[i] < long_stop_prev[i]:
                dir_array[i] = -1
            else:
                dir_array[i] = dir_array[i-1]
        
        # MT (Moving Trend)
        mt = np.where(dir_array == 1, long_stop, short_stop)
        
        # OTT
        ott = np.where(mavg > mt, mt * (200 + self.percent) / 200, mt * (200 - self.percent) / 200)
        
        return pd.Series(ott, index=df.index)
    
    def generate_signals(self, df):
        """Генерация сигналов на основе OTT"""
        if len(df) < self.length + 10:
            return []
        
        # Добавляем OTT к DataFrame
        df = df.copy()
        df['ott'] = self.calculate_ott(df)
        df['ott_prev'] = df['ott'].shift(1)
        df['ott_prev2'] = df['ott'].shift(2)
        df['ott_prev3'] = df['ott'].shift(3)
        
        signals = []
        
        for i in range(3, len(df)):
            # Сигналы на основе пересечения OTT[2] и OTT[3]
            ott_2 = df['ott_prev2'].iloc[i]
            ott_3 = df['ott_prev3'].iloc[i]
            ott_2_prev = df['ott_prev2'].iloc[i-1]
            ott_3_prev = df['ott_prev3'].iloc[i-1]
            
            # Buy сигнал: OTT[2] пересекает OTT[3] снизу вверх
            if ott_2 > ott_3 and ott_2_prev <= ott_3_prev:
                signal = {
                    'time': df['time'].iloc[i].strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'buy',
                    'price': df['close'].iloc[i],
                    'ott_value': ott_2,
                    'signal_strength': abs(ott_2 - ott_3) / ott_3 * 100
                }
                signals.append(signal)
                print(f"📈 OTT Buy сигнал: {signal['time']} - цена: {signal['price']}")
            
            # Sell сигнал: OTT[2] пересекает OTT[3] сверху вниз
            elif ott_2 < ott_3 and ott_2_prev >= ott_3_prev:
                signal = {
                    'time': df['time'].iloc[i].strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'sell',
                    'price': df['close'].iloc[i],
                    'ott_value': ott_2,
                    'signal_strength': abs(ott_2 - ott_3) / ott_3 * 100
                }
                signals.append(signal)
                print(f"📉 OTT Sell сигнал: {signal['time']} - цена: {signal['price']}")
        
        return signals
    
    def get_ott_data(self, df):
        """Получение данных OTT для отображения на графике"""
        df = df.copy()
        df['ott'] = self.calculate_ott(df)
        df['ott_prev'] = df['ott'].shift(1)
        df['ott_prev2'] = df['ott'].shift(2)
        
        # Определение цвета OTT
        df['ott_color'] = np.where(df['ott_prev2'] > df['ott_prev2'].shift(1), 'green', 'red')
        
        return df[['ott', 'ott_color']] 