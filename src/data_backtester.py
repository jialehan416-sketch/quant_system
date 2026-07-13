import pandas as pd
import numpy as np
from src.logger import logger

def run_backtest(df: pd.DataFrame, initial_capital: float = 100000.0, 
                 commission: float = 0.0003, slippage: float = 0.0005) -> pd.DataFrame:
    """
    深度学习自适应回测引擎 (终极工业版)
    引入严格的交易摩擦（双边佣金 + 市场滑点），并采用底层 NumPy 数组加速
    """
    if df.empty:
        return df

    df_bt = df.copy()
    
    closes = df_bt['close'].values
    signals = df_bt['signal'].values
    n = len(df_bt)
    
    cash_arr = np.zeros(n)
    shares_arr = np.zeros(n)
    total_value_arr = np.zeros(n)
    
    cash = initial_capital
    shares = 0.0
    
    for idx in range(n):
        current_price = closes[idx]
        signal = signals[idx]
        
        # 执行买入信号 (全仓)
        if signal == 1.0 and cash > 0:  
            execution_price = current_price * (1.0 + slippage)  
            available_cash = cash * (1.0 - commission)          
            shares = available_cash / execution_price
            cash = 0.0
            
        # 执行卖出信号 (全仓)
        elif signal == -1.0 and shares > 0:  
            execution_price = current_price * (1.0 - slippage)  
            gross_cash = shares * execution_price
            cash = gross_cash * (1.0 - commission)              
            shares = 0.0
            
        cash_arr[idx] = cash
        shares_arr[idx] = shares
        total_value_arr[idx] = cash + (shares * current_price)
        
    df_bt['cash'] = cash_arr
    df_bt['shares'] = shares_arr
    df_bt['total_value'] = total_value_arr
    
    # 动态持仓状态
    df_bt['position'] = np.where(df_bt['shares'] > 0, 1.0, 0.0)
    
    # 收益率与累计收益率
    df_bt['strategy_return'] = df_bt['total_value'].pct_change().fillna(0.0)
    df_bt['market_return'] = df_bt['close'].pct_change().fillna(0.0)
    df_bt['cum_strategy_return'] = (df_bt['total_value'] / initial_capital) - 1.0
    df_bt['cum_market_return'] = (df_bt['close'] / closes[0]) - 1.0
    
    return df_bt


def print_performance_summary(df: pd.DataFrame, slippage: float = 0.0005):
    """
    华尔街标准量化绩效看板：完美兼容长线持有与高频择时模型
    """
    if df.empty or 'total_value' not in df.columns:
        logger.warning("[回测看板] 数据为空或未经回测计算，无法生成报告。")
        return

    # 1. 时间因子与收益资产
    total_days = len(df)
    years = total_days / 252.0  
    initial_val = df['total_value'].iloc[0]
    final_val = df['total_value'].iloc[-1]
    
    total_return = (final_val / initial_val) - 1.0
    cagr = ((final_val / initial_val) ** (1.0 / years) - 1.0) if years > 0 and final_val > 0 else 0.0
    
    market_initial = df['close'].iloc[0]
    market_final = df['close'].iloc[-1]
    market_total_return = (market_final / market_initial) - 1.0
    market_cagr = ((market_final / market_initial) ** (1.0 / years) - 1.0) if years > 0 else 0.0
    
    # 2. 风险指标
    strat_daily_std = df['strategy_return'].std()
    annual_vol = strat_daily_std * np.sqrt(252)  
    sharpe = ((df['strategy_return'].mean() - (0.02 / 252)) / strat_daily_std * np.sqrt(252)) if strat_daily_std > 0 else 0.0
    
    rolling_max = df['total_value'].cummax()
    max_drawdown = ((df['total_value'] - rolling_max) / rolling_max).min()
    
    # 3. PyTorch 大脑择时 Hit Rate
    if 'position' in df.columns:
        valid_predictions = df.iloc[10:-1].copy()  
        if len(valid_predictions) > 0:
            actual_move = np.where(valid_predictions['market_return'].shift(-1) > 0, 1.0, 0.0)
            ai_pred = valid_predictions['position'].values
            ai_accuracy = np.mean(ai_pred == actual_move)
        else:
            ai_accuracy = 0.0
    else:
        ai_accuracy = 0.0

    # 4. 实体交易细节统计 (含未平仓长线交易的期末虚拟结算)
    positions = df['position'].values
    close_prices = df['close'].values
    signals = df['signal'].values if 'signal' in df.columns else np.zeros(total_days)
    
    raw_signal_buys = np.sum(signals == 1.0) # AI发出买入指令的总次数
    
    trade_returns = []
    entry_price = 0.0
    in_position = False
    
    for i in range(1, len(df)):
        if positions[i] == 1.0 and positions[i-1] == 0.0:    
            entry_price = close_prices[i]
            in_position = True
        elif positions[i] == 0.0 and positions[i-1] == 1.0 and entry_price > 0:  
            trade_returns.append((close_prices[i] / entry_price) - 1.0)
            entry_price = 0.0
            in_position = False
            
    # 【核心保护：处理长线买入持有不卖出的边界情况】
    if in_position and entry_price > 0:
        # 强制在回测最后一天以收盘价做虚拟平仓，以计算这单长线交易的胜率
        trade_returns.append((close_prices[-1] / entry_price) - 1.0)

    closed_trades = len(trade_returns)
    
    if closed_trades > 0:
        win_rate = np.sum(np.array(trade_returns) > 0) / closed_trades
        profit_list = [r for r in trade_returns if r > 0]
        loss_list = [r for r in trade_returns if r <= 0]
        profit_factor = (sum(profit_list) / abs(sum(loss_list))) if len(loss_list) > 0 and sum(loss_list) != 0 else float('inf')
    else:
        win_rate = 0.0
        profit_factor = 0.0

    # 5. 🖨️ 记录专业的量化绩效报告
    logger.info("\n" + "=" * 60)
    logger.info("PyTorch 深度学习自适应策略回测绩效看板")
    logger.info("=" * 60)
    logger.info(f"回测周期: {total_days} 个交易日 (约 {years:.2f} 年)")
    logger.info(f"初始资金: ${initial_val:,.2f}  |  最终资产: ${final_val:,.2f}")
    logger.info("-" * 60)
    logger.info(f"策略总收益率: {total_return * 100:.2f}%   |   基准(买入持有)总收益: {market_total_return * 100:.2f}%")
    logger.info(f"策略年化收益 (CAGR): {cagr * 100:.2f}%  |   基准年化收益: {market_cagr * 100:.2f}%")
    logger.info(f"年化波动率: {annual_vol * 100:.2f}%   |   夏普比率 (Sharpe): {sharpe:.2f}")
    logger.info(f"最大回撤 (Max Drawdown): {max_drawdown * 100:.2f}%")
    logger.info("-" * 60)
    logger.info(f"PyTorch 每日方向预测准确率 (Hit Rate): {ai_accuracy * 100:.2f}%")
    logger.info(f"AI发出买入信号: {raw_signal_buys} 次      |   滑点约束设置: 单边 {slippage * 10000:.1f} BP")
    logger.info(f"已结算独立交易: {closed_trades} 次        |   交易胜率 (Win Rate): {win_rate * 100:.2f}%")
    logger.info(f"核心盈亏比 (Profit Factor): {profit_factor:.2f}")
    logger.info("=" * 60 + "\n")