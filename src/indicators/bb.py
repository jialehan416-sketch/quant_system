from .base import BaseIndicator
import pandas as pd

class BB(BaseIndicator):
    def __init__(self, window=20, std=2.0):
        self.window = window
        self.std = std
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        middle = df['close'].rolling(window=self.window).mean()
        std = df['close'].rolling(window=self.window).std()
        upper = middle + (self.std * std)
        lower = middle - (self.std * std)
        df['feat_bb_pos'] = (df['close'] - lower) / (upper - lower + 1e-6)
        return df