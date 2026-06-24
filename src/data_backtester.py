import pandas as pd
import numpy as np
def run_backtest(df: pd.DataFrame, initial_capital: float = 100000.0) -> pd.DataFrame:
    if df.empty or 'signal' not in df.columns or 'position' not in df.columns:
        print("[回测引擎] 缺失必要信号或持仓状态列，拒绝运行回测。")
        return df
    df_back = df.copy()
    df_back['market_return'] = df_back['close'].pct_change()
    df_back['strategy_return'] = df_back['position'].shift(1) * df_back['market_return']
    df_back['cum_market_return'] = (1 + df_back['market_return'].fillna(0)).cumprod() - 1
    df_back['cum_strategy_return'] = (1 + df_back['strategy_return'].fillna(0)).cumprod() - 1
    df_back['portfolio_value'] = initial_capital * (1 + df_back['cum_strategy_return'])
    return df_back

def print_performance_summary(df: pd.DataFrame):
    if df.empty or 'cum_strategy_return' not in df.columns:
        print("[绩效报告] 缺失回测收益数据，无法生成报告。")
        return
    
    final_strategy_ret = df['cum_strategy_return'].iloc[-1]
    final_market_ret = df['cum_market_return'].iloc[-1]
    trade_count = (df['signal'] != 0).sum()
    print("\n" + " 量化策略历史回测绩效报告 ")
    print("-" * 50)
    print(f"基准大盘（买入持有）总收益率: {final_market_ret * 100:.2f}%")
    print(f"双均线交叉策略总收益率:       {final_strategy_ret * 100:.2f}%")
    print(f"策略历史总调仓触发次数:        {trade_count} 次")
    if final_strategy_ret > final_market_ret:
        print("恭喜！该策略成功击败基准大盘，斩获超额收益！")
    else:
        print("警告：该策略未跑赢大盘，可能存在均线滞后或震荡市“反复挨打”的现象。")
    
# 本地测试沙盒（模拟运行）
if __name__ == "__main__":
    print("--- 开始运行回测引擎本地离线验证 ---")
    mock_data = {
        'close': [100, 101, 102, 104, 106, 108, 107, 105, 103, 101, 99, 98],
        'position': [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0],
        'signal': [0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0]
    }
    dates = pd.date_range(start="2026-06-01", periods=12)
    test_df = pd.DataFrame(mock_data, index=dates)
    res_df = run_backtest(test_df)
    print_performance_summary(res_df)