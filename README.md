QUANT_SYSTEM (基于自适应深度强化学习的解耦量化交易系统)本项目是一个基于 PyTorch 深度强化学习（DQN）的工业级自适应量化策略演练系统。系统核心采用“数据接力与状态留痕”的解耦架构设计，不仅提供统一的中央控制流水线，且支持各个子模块脱离主控制链进行完全原子化的独立运行与调试。系统架构与数据接力流系统各个核心模块通过硬盘中间文件的读写实现接力式衔接。流水线运转的核心数据流向如下：数据拉取阶段 (data_fetcher.py)：从雅虎财经获取历史数据，输出 {symbol}_raw.json 原始数据快照。数据清洗与特征生成阶段 (data_processor.py)：清洗并强转原始数据格式，输出 {symbol}_cleaned.csv；随后通过指标工厂挂载技术指标，输出 {symbol}_indicators.csv。策略决策阶段 (data_strategy.py)：激活 DQN 神经网络进行环境推理，输出带仓位信号的 {symbol}_signals.csv。摩擦力回测阶段 (data_backtester.py)：注入双边摩擦成本进行资产结算，输出 {symbol}_backtest_ledger.csv 账本与 {symbol}_performance_summary.json 绩效快照。图表可视化阶段 (data_visualizer.py)：读取最终回测账本，渲染多子图全景净值曲线图 {symbol}_equity_curve.png。目录结构quant_system/
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
├── requirements.txt          # 项目依赖依赖包清单
└── main.py                   # 系统中央总线控制器与流水线调度中心
依赖环境与安装配置1. 安装基础依赖克隆项目至本地后，请确保 Python 环境满足要求，并在根目录下执行依赖安装：pip install -r requirements.txt
主要依赖项包括：torch, pandas, numpy, scikit-learn, yfinance, matplotlib, python-dotenv。2. 配置环境变量在项目根目录下创建 .env 文件，用于安全读取或声明相关的密钥环境：DATA_API_KEY=your_optional_api_key_here
如果未检测到密钥，数据引擎将自动切入无密钥的公共高速接入模式，不会引发系统崩溃。核心控制总线使用说明 (main.py)统一调度中心支持两种控制模式：传统交互面板模式与自动化命令行阶段分拆模式。模式 A：全局终端交互模式直接运行主脚本，系统将依次弹出交互面板，引导您手动选择标的池、微调特征指标窗口以及切换强化学习特征开关：python main.py
模式 B：命令行独立阶段分拆模式通过传入 --mode 参数，直接调用全局配置中心的默认参数非交互式运行。支持快速指定运行某一个特定的流水线环节：# 仅拉取最新行情数据并落盘原始 JSON 快照
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
模块级原子化独立运行指南除了通过 main.py 调度外，系统内的五个核心业务组件均已内置标准的独立执行入口。您可以彻底绕过主控制流，在项目根目录下通过直调子模块脚本的方式实现秒级局部 Debug：1. 独立下载行情python src/data_fetcher.py
该操作将只请求网络，下载全局配置中指定资产的 5 年历史日线数据，并刷新 data/{symbol}_raw.json 文件。2. 独立执行清洗与特征工程python src/data_processor.py
该操作读取现有的 _raw.json 文件，强转价格类型为 float64 并将成交量强转为 Int64，完成 NaN 清理后自动调用工厂生成指标矩阵，刷新 _cleaned.csv 与 _indicators.csv。3. 独立训练/演练交易信号python src/data_strategy.py
该操作读取现有的 _indicators.csv，直接启动包含 64 和 32 个神经元的全连接双层 QNetwork 进行 40 轮强化试错进化，结合单日吃跌惩罚与摩擦成本控制函数刷新择时信号 _signals.csv。4. 独立微调回测表现python src/data_backtester.py
该操作读取现有的 _signals.csv，使用 NumPy 底层数组全仓模拟买卖行为，扣除双边佣金与滑点，在控制台输出 Sharpe 比率、年化收益率、最大回撤、预测准确率等华尔街标准绩效报告，并刷新 _backtest_ledger.csv 账本。5. 独立修改样式并渲染图表python src/data_visualizer.py
该操作读取现有的 _backtest_ledger.csv，利用 seaborn-v0_8-darkgrid 风格套件独立绘制出包含自适应策略收益、基准对比收益以及神经网络上涨预测概率的多子图全景全中文审计图，直接更新 reports/{symbol}_equity_curve.png。核心算法与风控机制细节DQN 记忆存盘与传承：智能体在决策阶段会自动尝试从硬盘读取 quant_brain_dqn_v3_pure.pth 的历史权重矩阵，实现跨资产经验的清爽传承或增量进化。精准消除未来函数：智能体的动作输出被严格执行了 .shift(1) 顺延一日处理，确保第 $t$ 天计算的收盘决策被精准地在第 $t+1$ 天执行，完全杜绝回测中的时滞作弊现象。定向狙击暴跌奖励函数：在强化学习奖励设置中加入了严苛的死刑项机制（单日跌幅乘以权重 45.0 的超额负分铁拳），强迫大脑在市场出现崩盘前夕产生空仓过夜的本能风控灵魂。双轨制数据审计：系统在落盘时不仅提供包含了每日现金、持股明细、策略综合净值的全量 CSV 对账单，同时原子化地提炼出高价值的轻量级绩效 snapshot JSON 快照供前端或者上层应用直接读取解析。
