import os
import matplotlib.pyplot as plt
import pandas as pd
from src.logger import logger

def plot_equity_curve(df: pd.DataFrame, symbol: str, output_dir: str = "reports"):
    """
    工业级多子图可视化审计系统（去污染纯净版）
    """
    if df.empty or 'total_value' not in df.columns:
        logger.warning(f"[可视化引擎] {symbol} 数据集为空，跳过绘图。")
        return

    os.makedirs(output_dir, exist_ok=True)
    df_plot = df.copy()
    
    if 'date' in df_plot.columns:
        df_plot['date'] = pd.to_datetime(df_plot['date'])
        df_plot = df_plot.set_index('date')
    else:
        try:
            df_plot.index = pd.to_datetime(df_plot.index)
        except Exception:
            pass

    #核心修复：必须先应用样式，再紧跟注入中文字体配置，顺序错了就会失效！
    plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False  # 彻底修复负号方块

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, 
                                   gridspec_kw={'height_ratios': [2, 1]})
    
    # ------------------ 上方子图 ------------------
    ax1.plot(df_plot.index, df_plot['cum_strategy_return'] * 100, 
             label='PyTorch AI 自适应策略', color='#1f77b4', linewidth=2.5)
    ax1.plot(df_plot.index, df_plot['cum_market_return'] * 100, 
             label=f'基准(买入持有 {symbol})', color='#ff7f0e', linestyle='--', linewidth=1.5, alpha=0.8)
    
    if 'position' in df_plot.columns:
        ax1.fill_between(df_plot.index, ax1.get_ylim()[0], ax1.get_ylim()[1], 
                         where=(df_plot['position'] == 1.0), color='#2ca02c', alpha=0.08, label='AI 重仓持股期')

    # 安全去污染：移除了导致 Arial 报错的表情
    ax1.set_title(f"{symbol} 深度强化学习量化演练全景审计报告", fontsize=15, fontweight='bold', pad=15)
    ax1.set_ylabel("累计收益率 (%)", fontsize=12)
    ax1.legend(loc='upper left', fontsize=11, frameon=True, facecolor='white', framealpha=0.9)
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    # ------------------ 下方子图 ------------------
    if 'ml_prob' in df_plot.columns:
        ax2.plot(df_plot.index, df_plot['ml_prob'], color='#9467bd', linewidth=1.0, alpha=0.8, label='AI 明日上涨预测概率')
        ax2.axhline(0.57, color='#d62728', linestyle=':', linewidth=1.2, alpha=0.8, label='突破开仓线 (0.57)')
        ax2.axhline(0.43, color='#2ca02c', linestyle=':', linewidth=1.2, alpha=0.8, label='转空平仓线 (0.43)')
        ax2.axhline(0.50, color='gray', linestyle='-', linewidth=0.8, alpha=0.3)
        
        ax2.set_ylabel("神经网络多头信心度", fontsize=12)
        ax2.set_ylim(-0.05, 1.05)
        ax2.legend(loc='upper left', fontsize=10, frameon=True, facecolor='white', framealpha=0.9)
        ax2.grid(True, linestyle=':', alpha=0.5)

    ax2.set_xlabel("历史回测时间轴", fontsize=12)
    
    plt.tight_layout() # 顺序正确后，这一行再也不会喷出警告了
    output_path = os.path.join(output_dir, f"{symbol}_equity_curve.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()