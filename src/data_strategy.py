import os
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
from src.logger import logger

# ==========================================
# 1. DQN 深度 Q 网络架构
# ==========================================
class QNetwork(nn.Module):
    def __init__(self, input_dim, action_dim=2):
        super(QNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, action_dim)
        )
        
    def forward(self, x):
        return self.network(x)


# ==========================================
# 2. 经验回放缓冲区
# ==========================================
class ReplayBuffer:
    def __init__(self, capacity=5000):
        self.buffer = []
        self.capacity = capacity
        
    def push(self, state, action, reward, next_state, done):
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
        self.buffer.append((state, action, reward, next_state, done))
        
    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)
        
    def __len__(self):
        return len(self.buffer)


# ==========================================
# 3. 底层技术指标特征原材料计算模块（保持不变）
# ==========================================
from src.indicators.factory import apply_all_indicators
from src.logger import logger

def generate_signals(df, enabled_factors):
    # 彻底解耦：指标计算被完全剥离到独立模块
    try:
        df_signals = apply_all_indicators(df.copy())
        logger.info("技术指标特征工程计算成功。")
    except Exception as e:
        logger.error(f"特征计算失败: {e}")
        return df # 返回原始数据或处理错误
    
    # ... 后续 DQN 决策逻辑保持不变 ...
# ==========================================
# 4. DRL 强化学习自主信号生成引擎 (纯净重塑版)
# ==========================================
def generate_signals(df, enabled_factors, rolling_window=40, top_q=0.82, bottom_q=0.18):
    df_signals = df.copy()
    
    #核心突破：更换知识库文件名，强制 AI 摆脱旧世界的“非理性硬扛”记忆，重新做人
    MODEL_FILE = "quant_brain_dqn_v3_pure.pth"
    
    factor_map = {
        'MA': ['feat_ma_ratio', 'feat_ma_trend'],
        'TREND': ['feat_trend_ratio'],
        'RSI': ['feat_rsi'],
        'MACD': ['feat_macd'],
        'BB': ['feat_bb_pos'],
        'KDJ': ['feat_kdj'],
        'ATR': ['feat_atr_ratio']
    }
    
    feature_cols = []
    for code, is_enabled in enabled_factors.items():
        if is_enabled and code in factor_map:
            feature_cols.extend(factor_map[code])
    if not feature_cols:
        feature_cols = ['feat_ma_ratio']
        
    df_signals['next_ret'] = df_signals['close'].pct_change().shift(-1)
    df_env = df_signals.dropna(subset=feature_cols + ['next_ret']).copy()
    
    if len(df_env) < 50:
        df_signals['position'] = 0
        df_signals['signal'] = 0
        return df_signals
        
    X = df_env[feature_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    next_returns = df_env['next_ret'].values
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = QNetwork(input_dim=len(feature_cols), action_dim=2).to(device)
    
    if os.path.exists(MODEL_FILE):
        try:
            model.load_state_dict(torch.load(MODEL_FILE, map_location=device))
            logger.info(f"[清爽传承] 读取 V3 纯净择时记忆库...")
        except Exception as e:
            logger.warning(f"记忆读取失败，全新开天辟地。")
    else:
        logger.info("[白纸状态] 已强制粉碎旧记忆钢印！从零构建具备风控灵魂的新生量化大脑！")
        
    optimizer = optim.Adam(model.parameters(), lr=0.0005)
    criterion = nn.MSELoss()
    memory = ReplayBuffer(capacity=5000)
    
    #优化后的学习配置
    num_episodes = 40       # 提升到 40 轮，让从零开始的大脑学得更透彻
    batch_size = 64
    gamma = 0.95            
    epsilon = 0.4           # 加大探索率，逼迫它多去尝试“空仓”过夜
    real_friction_cost = 0.0008 # 工业级真实摩擦总和 (万三佣金 + 万五滑点)
    
    model.train()
    for episode in range(num_episodes):
        last_action = 0  
        
        for t in range(len(X_scaled) - 1):
            state = X_scaled[t]
            next_state = X_scaled[t+1]
            
            if random.random() < epsilon:
                action = random.choice([0, 1])
            else:
                with torch.no_grad():
                    state_t = torch.tensor(state, dtype=torch.float32).to(device)
                    q_values = model(state_t)
                    action = torch.argmax(q_values).item()
            
            # ---- 奖励函数重组：精确定向狙击暴跌 ----
            action_return = next_returns[t] if action == 1 else 0.0
            benchmark_return = next_returns[t]
            
            # 1. 超额阿尔法收益基础分
            alpha_reward = action_return - benchmark_return
            
            # 2. 核心死刑项：单日吃跌致命惩罚
            # 如果明天市场大跌（<0），而你作死选择持仓（action=1），直接施加极度严厉的负分铁拳！
            if next_returns[t] < 0 and action == 1:
                downside_penalty = abs(next_returns[t]) * 45.0  
            else:
                downside_penalty = 0.0
                
            # 3. 换仓摩擦成本惩罚
            friction_penalty = real_friction_cost if action != last_action else 0.0
            
            # 综合积分公式
            reward = (20.0 * alpha_reward) - downside_penalty - (4.0 * friction_penalty)
            
            memory.push(state, action, reward, next_state, False)
            last_action = action
            
            if len(memory) > batch_size:
                transitions = memory.sample(batch_size)
                b_state, b_action, b_reward, b_next_state, _ = zip(*transitions)
                
                b_state = torch.tensor(np.array(b_state), dtype=torch.float32).to(device)
                b_action = torch.tensor(b_action, dtype=torch.long).unsqueeze(1).to(device)
                b_reward = torch.tensor(b_reward, dtype=torch.float32).unsqueeze(1).to(device)
                b_next_state = torch.tensor(np.array(b_next_state), dtype=torch.float32).to(device)
                
                current_q = model(b_state).gather(1, b_action)
                with torch.no_grad():
                    max_next_q = model(b_next_state).max(1)[0].unsqueeze(1)
                    target_q = b_reward + gamma * max_next_q
                    
                loss = criterion(current_q, target_q)
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0) # 稳定神经元
                optimizer.step()
                
        epsilon = max(0.01, epsilon * 0.90)

    torch.save(model.state_dict(), MODEL_FILE)
    logger.info(f"[固化大脑] 带有严苛风控基因的全新矩阵已存盘。")

    # 4. 实战推演与核心时间对齐
    model.eval()
    all_features = df_signals[feature_cols].fillna(0.0).values
    all_features_scaled = scaler.transform(all_features)
    
    raw_actions = []
    with torch.no_grad():
        for s in all_features_scaled:
            s_t = torch.tensor(s, dtype=torch.float32).to(device)
            action = torch.argmax(model(s_t)).item()
            raw_actions.append(action)
            
    # 关键修复：使用 .shift(1) 将 AI 的动作完美的向后对齐一天！
    # 确保第 t 天算出来的精妙决策，被精准地执行在第 t+1 天的实盘交易里，消除时滞造成的全盘崩盘。
    aligned_positions = pd.Series(raw_actions, index=df_signals.index).shift(1).fillna(0).astype(int)
    
    df_signals['position'] = aligned_positions
    df_signals['signal'] = aligned_positions
    
    return df_signals