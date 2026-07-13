import pandas as pd
from .rsi import RSI
from .macd import MACD
# 以后新增指标只需在这里 import 并加入列表
def apply_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    # 这里定义所有你想用的指标对象
    indicators = [RSI(), MACD()] 
    for ind in indicators:
        df = ind.calculate(df)
    return df