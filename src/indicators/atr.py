from .base import BaseIndicator
import pandas as pd

class ATR(BaseIndicator):
    def __init__(self, window=14):
        self.window = window
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        high = df['high']
        low = df['low']
        prev_close = df['close'].shift(1)
        tr = pd.concat([high-low, (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
        df['feat_atr_ratio'] = tr.rolling(window=self.window).mean() / (df['close'] + 1e-6)
        return df