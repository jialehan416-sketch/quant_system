import pandas as pd

def run_backtest(df: pd.DataFrame, initial_capital: float = 100000.0) -> pd.DataFrame:
    if df is None or df.empty or 'position' not in df.columns:
        return df
        
    df_bt = df.copy()
    
    # 计算每日股票本身的涨跌幅
    df_bt['pct_change'] = df_bt['close'].pct_change().fillna(0.0)
    
    # 策略的每日收益率 = 昨天的持仓状态 * 今天的股票涨跌幅
    df_bt['strategy_return'] = df_bt['position'].shift(1).fillna(0.0) * df_bt['pct_change']
    
    # 计算累计动态权益曲线
    df_bt['equity_curve'] = (1.0 + df_bt['strategy_return']).cumprod() * initial_capital
    df_bt['total_returns'] = (df_bt['equity_curve'] / initial_capital) - 1.0
    
    return df_bt

def print_performance_summary(df: pd.DataFrame):
    """
    在控制台打印核心战报 KPI
    """
    if df is None or df.empty or 'equity_curve' not in df.columns:
        return
        
    total_return = df['total_returns'].iloc[-1] * 100
    
    # 计算最大回撤 (Drawdown)
    equity = df['equity_curve']
    max_equity = equity.cummax()
    drawdown = (equity - max_equity) / max_equity
    max_drawdown = drawdown.min() * 100
    
    print("\n" + "🏁" + " 策略回测清算报告 " + "🏁")
    print(f"   -> 测试时间跨度: {df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"   -> 初始注入本金: ${df['equity_curve'].iloc[0]:,.2f}")
    print(f"   -> 期末资产总值: ${df['equity_curve'].iloc[-1]:,.2f}")
    print(f"   -> 策略累计收益: {total_return:+.2f}%")
    print(f"   -> 期间最大回撤: {max_drawdown:.2f}%")
    print("="*30)