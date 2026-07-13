from .base import BaseIndicator
import pandas as pd

class MACD(BaseIndicator):
    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        ema_fast = df['close'].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal, adjust=False).mean()
        df['feat_macd'] = (macd_line - signal_line) / (df['close'] + 1e-6)
        return df