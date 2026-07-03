import os
import matplotlib.pyplot as plt
import pandas as pd

def plot_equity_curve(df: pd.DataFrame, symbol: str, output_dir: str = "reports"):
    """
    绘制资产权益曲线，并自动保存为图片
    """
    if df is None or df.empty or 'equity_curve' not in df.columns:
        return
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制策略净值曲线
    ax.plot(df.index, df['equity_curve'], label='Multi-Factor State Machine', color='#1f77b4', linewidth=2)
    
    # 基础样式美化
    ax.set_title(f"Quant Backtest Equity Curve - {symbol}", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Portfolio Value ($)", fontsize=12)
    ax.legend(loc="upper left", fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # 自动旋转日期标记防止重叠
    fig.autofmt_xdate()
    
    output_path = os.path.join(output_dir, f"{symbol}_equity_curve.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[图形渲染] 资产曲线图已绘制并保存至: {output_path}")