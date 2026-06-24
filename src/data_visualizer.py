import os
import matplotlib.pyplot as plt
import pandas as pd
def plot_equity_curve(df: pd.DataFrame, symbol: str, output_dir: str = "reports") -> None:
    """
    绘制双子图工业级量化看板：
    1. 上图: 账户绝对资产净值曲线(Portfolio Value)
    2. 下图：策略累计收益率 vs 大盘基准累计收益率(%)
    """
    if df is None or df.empty:
        print(f"⚠️ [可视化] {symbol} 数据为空，取消图表绘制。")
        return
        
    # 自动创建报告输出文件夹
    os.makedirs(output_dir, exist_ok=True)
    
    # 强制确保行索引为日期格式，防止绘图时横轴错乱
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    # 设置经典的量化美化风格
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'STHeiti', 'Arial', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False # 解决负号显示为方块的问题

    # 创建双子图画布 (sharex=True 保证上下两个图的时间轴完全对齐)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True, gridspec_kw={'height_ratios': [1.2, 1]})
    
    # ==========================================================
    # 📈 顶部子图：绝对资产曲线 (Portfolio Value)
    # ==========================================================
    initial_capital = 100000.0 # 初始资金基准线
    ax1.plot(df.index, df['portfolio_value'], color='#1e3d59', linewidth=2.5, label='策略净值 (Portfolio Value)')
    
    # 动态阴影染色：高于初始资金染成深蓝，低于初始资金染成橙红
    ax1.fill_between(df.index, df['portfolio_value'], initial_capital, 
                     where=(df['portfolio_value'] >= initial_capital), color='#1e3d59', alpha=0.06)
    ax1.fill_between(df.index, df['portfolio_value'], initial_capital, 
                     where=(df['portfolio_value'] < initial_capital), color='#ff6e40', alpha=0.06)
                     
    ax1.set_title(f"📊 {symbol.upper()} 量化回测全景资产看板", fontsize=14, fontweight='bold', pad=15, color='#1e3d59')
    ax1.set_ylabel("账户总资产 ($)", fontsize=11, fontweight='bold', color='#1e3d59')
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper left', frameon=True, facecolor='#ffffff')
    ax1.tick_params(colors='#1e3d59')

    # ==========================================================
    # 📉 底部子图：收益率相对表现 (Strategy vs Market)
    # ==========================================================
    # 转换为百分比进行直观对比
    strategy_pct = df['cum_strategy_return'] * 100
    market_pct = df['cum_market_return'] * 100
    
    ax2.plot(df.index, strategy_pct, color='#17b890', linewidth=2, label='本策略累计收益率 (%)')
    ax2.plot(df.index, market_pct, color='#ff6e40', linewidth=1.5, linestyle='--', label='大盘基准累计收益率 (%)')
    
    ax2.set_ylabel("累计收益率 (%)", fontsize=11, fontweight='bold', color='#1e3d59')
    ax2.set_xlabel("交易时间轴", fontsize=11, fontweight='bold', color='#1e3d59')
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='upper left', frameon=True, facecolor='#ffffff')
    ax2.tick_params(colors='#1e3d59')
    
    # 优化横轴日期标签的倾斜度和紧凑度
    plt.xticks(rotation=15)
    plt.tight_layout()
    
    # 保存高清图表
    file_path = os.path.join(output_dir, f"{symbol.upper()}_equity_curve.png")
    plt.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📈 [可视化] 终极资金曲线图已安全生成至: {file_path}")