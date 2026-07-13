# QUANT_SYSTEM

## 基于自适应深度强化学习的解耦量化交易系统

本项目是一个基于 PyTorch 深度强化学习（DQN）的工业级自适应量化策略演练系统。系统核心采用解耦设计架构，将数据获取、特征工程、模型训练、回测结算与可视化完全隔离，支持模块化独立执行与流水线调度。

---

## 项目结构

```
quant_system/
│
├── src/
│   ├── __init__.py
│   ├── config.py             # 全局集中式配置中心，管理资产池、摩擦系数与网格参数
│   ├── logger.py             # 鲁棒型日志器，采用 UTF-8 编码规避多平台乱码
│   ├── indicators/           # 特征工程指标计算插件库
│   ├── data_fetcher.py       # 雅虎财经高速数据接口模块
│   ├── data_processor.py     # 矩阵清洗与双轨制数据落盘引擎
│   ├── data_strategy.py      # PyTorch DQN 核心架构与强化学习训练引擎
│   ├── data_backtester.py    # NumPy 加速版真实摩擦力回测结算模块
│   └── data_visualizer.py    # 多子图资产净值全景审计图渲染模块
│
├── data/                     # 存放中间接力文件（JSON, CSV）的冷数据矩阵区
├── reports/                  # 存放绩效全景图与轻量绩效快照的分析报告区
├── logs/                     # 存放系统分级归档日志的目录
│
├── .env                      # 环境变量配置文件（如存放 API 密钥）
├── requirements.txt          # 项目依赖包清单
└── main.py                   # 系统中央总线控制器与流水线调度中心
```

---

## 依赖环境与安装配置

### 1. 安装基础依赖

克隆项目至本地后，请确保 Python 环境满足要求，并在根目录下执行依赖安装：

```bash
pip install -r requirements.txt
```

主要依赖项包括：
- `torch` - 深度学习框架
- `pandas` - 数据处理
- `numpy` - 数值计算
- `scikit-learn` - 机器学习工具
- `yfinance` - 财经数据接口
- `matplotlib` - 数据可视化
- `python-dotenv` - 环境变量管理

### 2. 配置环境变量

在项目根目录下创建 `.env` 文件，用于安全读取或声明相关的 API 密钥与参数：

```env
# 示例配置
YFINANCE_TIMEOUT=30
LOG_LEVEL=INFO
```

> **注意**：如果未检测到密钥，数据引擎将自动切入无密钥的公共高速接入模式，不会引发系统崩溃。

---

## 核心控制总线使用说明 (main.py)

统一调度中心支持两种控制模式：

### 模式 A：交互式管理模式

通过标准输入交互式地选择要执行的流水线环节。

### 模式 B：命令行独立阶段分拆模式

通过传入 `--mode` 参数，直接调用全局配置中心的默认参数非交互式运行。支持快速指定运行某一个特定的流水线环节：

```bash
# 仅执行数据下载
python main.py --mode download

# 仅执行数据清洗与类型强制转换
python main.py --mode clean

# 仅重新计算技术指标特征矩阵
python main.py --mode indicators

# 仅激活强化学习智能体训练并输出交易信号
python main.py --mode signals

# 仅独立运行包含手续费与滑点的回测结算
python main.py --mode backtest

# 仅重新渲染并更新资产收益图表
python main.py --mode visualize

# 以非交互模式一键跑通 1 至 6 步全套管线
python main.py --mode all
```

---

## 模块级原子化独立运行指南

除了通过 `main.py` 调度外，系统内的五个核心业务组件均已内置标准的独立执行入口。您可以彻底绕过主控制流，在项目根目录下直接运行各模块：

### 1. 独立执行数据下载

```bash
python src/data_fetcher.py
```

该操作将只请求网络，下载全局配置中指定资产的 5 年历史日线数据，并刷新 `data/{symbol}_raw.json` 文件。

### 2. 独立执行清洗与特征工程

```bash
python src/data_processor.py
```

该操作读取现有的 `_raw.json` 文件，强转价格类型为 `float64` 并将成交量强转为 `Int64`，完成 NaN 清理后自动调用工厂生成指标矩阵，刷新 `_cleaned.csv` 与 `_indicators.csv`。

### 3. 独立执行强化学习训练

```bash
python src/data_strategy.py
```

该操作读取现有的 `_indicators.csv`，直接启动包含 64 和 32 个神经元的全连接双层 QNetwork 进行 40 轮强化试错进化，结合单日吃跌惩罚与摩擦成本控制函数，刷新 `_signals.csv`。

### 4. 独立执行回测结算

```bash
python src/data_backtester.py
```

该操作读取现有的 `_signals.csv`，使用 NumPy 底层数组全仓模拟买卖行为，扣除双边佣金与滑点，在控制台输出 Sharpe 比率、年化收益率、最大回撤、预测准确率等关键指标，并生成 `_backtest_ledger.csv`。

### 5. 独立执行可视化渲染

```bash
python src/data_visualizer.py
```

该操作读取现有的 `_backtest_ledger.csv`，利用 `seaborn-v0_8-darkgrid` 风格套件独立绘制出包含自适应策略收益、基准对比收益以及神经网络上涨预测概率的多子图，并保存至 `reports/` 目录。

---

## 快速开始

### 一键执行完整流水线

```bash
python main.py --mode all
```

### 分阶段执行

1. **获取数据**
   ```bash
   python main.py --mode download
   ```

2. **数据处理与特征提取**
   ```bash
   python main.py --mode clean
   python main.py --mode indicators
   ```

3. **模型训练**
   ```bash
   python main.py --mode signals
   ```

4. **回测与评估**
   ```bash
   python main.py --mode backtest
   ```

5. **可视化结果**
   ```bash
   python main.py --mode visualize
   ```

---

## 核心特性

- ✅ 深度强化学习（DQN）自适应交易策略
- ✅ 模块化解耦设计架构
- ✅ 完整的数据处理流水线
- ✅ 真实摩擦力成本模型
- ✅ 多指标评价体系
- ✅ 高性能数据处理（NumPy 加速）
- ✅ 灵活的配置管理系统

---

## 输出文件说明

| 文件名 | 说明 |
|-------|------|
| `{symbol}_raw.json` | 原始历史行情数据 |
| `{symbol}_cleaned.csv` | 清洗后的价格与成交量数据 |
| `{symbol}_indicators.csv` | 特征工程计算结果 |
| `{symbol}_signals.csv` | 强化学习模型输出的交易信号 |
| `{symbol}_backtest_ledger.csv` | 回测交易账本与绩效指标 |

---

## 许可证

本项目采用 MIT 许可证。

---

## 贡献

欢迎提交 Issue 和 Pull Request！
