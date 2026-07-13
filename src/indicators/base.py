from abc import ABC, abstractmethod
import pandas as pd

class BaseIndicator(ABC):
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """所有子类必须实现此方法，在 df 中增加指标列"""
        pass