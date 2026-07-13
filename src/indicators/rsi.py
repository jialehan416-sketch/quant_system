from .base import BaseIndicator
import pandas as pd

class RSI(BaseIndicator):
    def __init__(self, period=14):
        self.period = period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / (loss + 1e-6)
        df['feat_rsi'] = (100 - (100 / (1 + rs))) / 100.0
        return df