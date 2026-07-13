import numpy as np
import pandas as pd

class QuantumTradingEnv:
    """
    华尔街工业级自适应强化学习量化交易环境
    专门解决 DQN 智能体“死扛不卖”、“频繁高频交易”或“动作躺平”等核心内鬼问题
    """
    def __init__(self, df: pd.DataFrame, initial_balance: float = 100000.0, 
                 commission: float = 0.0003, slippage: float = 0.0005):
        self.df = df.reset_index(drop=True)
        self.n_steps = len(self.df)
        self.initial_balance = initial_balance
        self.commission = commission
        self.slippage = slippage
        
        # 特征矩阵 (假设你的 DataFrame 已经算好了技术指标)
        # 排除掉无法作为状态的列
        exclude_cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'signal', 'position']
        self.features = [c for c in df.columns if c not in exclude_cols]
        
        self.reset()

    def reset(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares = 0.0
        self.last_total_value = self.initial_balance
        self.position = 0.0  # 0.0 代表空仓，1.0 代表满仓
        
        return self._get_observation()

    def _get_observation(self):
        # 提取当前步的技术指标特征，并拼接上当前的“持仓状态”让大脑知道自己是否有货
        feat_vector = self.df.loc[self.current_step, self.features].values.astype(np.float32)
        obs = np.append(feat_vector, [self.position])  # 状态空间追加 1 维持仓记忆
        return obs

    def step(self, action):
        """
        核心动作映射逻辑：
        动作 action: 0 = 保持空仓/卖出平仓, 1 = 保持持仓/全仓买入
        """
        current_price = self.df.loc[self.current_step, 'close']
        executed_trade = False
        trade_penalty = 0.0
        
        # 1.状态机转换与摩擦力计算
        if action == 1 and self.position == 0.0:  # 空仓 -> 买入
            execution_price = current_price * (1.0 + self.slippage)
            available_cash = self.balance * (1.0 - self.commission)
            self.shares = available_cash / execution_price
            self.balance = 0.0
            self.position = 1.0
            executed_trade = True
            trade_penalty = self.initial_balance * (self.commission + self.slippage)
            
        elif action == 0 and self.position == 1.0: # 持仓 -> 卖出平仓
            execution_price = current_price * (1.0 - self.slippage)
            gross_cash = self.shares * execution_price
            self.balance = gross_cash * (1.0 - self.commission)
            self.shares = 0.0
            self.position = 0.0
            executed_trade = True
            trade_penalty = self.initial_balance * (self.commission + self.slippage)

        # 2.步进到下一个交易日
        self.current_step += 1
        done = (self.current_step >= self.n_steps - 1)
        
        # 3.计算资产结算
        next_price = self.df.loc[self.current_step, 'close']
        current_total_value = self.balance + (self.shares * next_price)
        
        # 4.终极自适应奖励函数 (Reward Shaping) - 逼迫大脑学会择时的关键
        # 计算今日资产的增量变化
        step_return = (current_total_value - self.last_total_value) / self.last_total_value
        
        # 基准大盘今日的变动
        market_return = (next_price - current_price) / current_price
        
        if self.position == 1.0:
            # 持仓时：鼓励超越大盘的超额收益，如果跌了，相比于大盘跌得少也是相对奖励
            reward = step_return - market_return
        else:
            # 空仓时：如果大盘在暴跌，AI成功空仓避险，应该给予【高额正向奖励】！！
            if market_return < 0:
                reward = abs(market_return) * 1.2  # 成功避险奖励
            else:
                reward = -market_return * 0.8     # 踏空踏损惩罚
                
        # 适度平滑单步交易产生的巨额手续费冲击，防止 AI 恐惧交易
        if executed_trade:
            reward -= (trade_penalty / self.initial_balance) * 0.2 
            
        # 5. 更新记忆缓存
        self.last_total_value = current_total_value
        obs = self._get_observation() if not done else np.zeros_like(self._get_observation())
        
        # 把最终环境动作映射回标准的 -1, 0, 1 供你的 backtester 使用
        # 这样回测就能完全捕捉到卖出信号了！
        backtest_signal = 0.0
        if executed_trade:
            backtest_signal = 1.0 if action == 1 else -1.0
            
        info = {'total_value': current_total_value, 'backtest_signal': backtest_signal}
        
        return obs, reward, done, info