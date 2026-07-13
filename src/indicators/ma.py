from .base import BaseIndicator
import pandas as pd
import numpy as np

class MA(BaseIndicator):
    def __init__(self, short=5, long=10, trend=60):
        self.short = short
        self.long = long
        self.trend = trend
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df['ma_short'] = df['close'].rolling(window=self.short).mean()
        df['ma_long'] = df['close'].rolling(window=self.long).mean()
        df['feat_ma_ratio'] = df['ma_short'] / (df['ma_long'] + 1e-6)
        df['feat_ma_trend'] = np.where(df['ma_short'] > df['ma_long'], 1.0, 0.0)
        
        trend_line = df['close'].rolling(window=self.trend).mean()
        df['feat_trend_ratio'] = df['close'] / (trend_line + 1e-6)
        return df