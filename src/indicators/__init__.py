# src/indicators/__init__.py

import importlib
import pkgutil
import os
import pandas as pd
from src.logger import logger

indicators = []
package_path = os.path.dirname(__file__)

# 自动化扫描并注册当前目录下所有的指标插件
for _, module_name, _ in pkgutil.iter_modules([package_path]):
    if module_name == 'base': 
        continue
    try:
        module = importlib.import_module(f'.{module_name}', package=__name__)
        class_name = module_name.upper()
        
        if hasattr(module, class_name):
            indicators.append(getattr(module, class_name)())
            logger.info(f"  -> [自动化审计] 成功挂载技术指标插件: {class_name}")
    except Exception as e:
        logger.error(f"  -> [熔断警告] 插件 {module_name} 加载失败: {e}")


def apply_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    工业级防御性指标计算管线
    自动兼容 【返回新DataFrame】 与 【就地修改且漏写return】 的两栖指标插件
    """
    if df is None or df.empty:
        logger.warning("[特征拦截] 输入的清洗后数据流为空，跳过所有指标计算。")
        return pd.DataFrame()
        
    # 深拷贝一份，彻底隔离 Pandas 的 SettingWithCopyWarning 警告
    df_out = df.copy()
    
    for ind in indicators:
        try:
            # 尝试执行插件计算
            res = ind.calculate(df_out)
            
            # 【核心防御逻辑】：
            # 如果插件内部写了 `return df`，我们采用返回的新对象；
            # 如果插件内部漏写了 return（res为None），由于它已经在内存中就地修改了 df_out，我们继续沿用 df_out
            if res is not None:
                df_out = res
                
        except Exception as e:
            logger.error(f"插件 [{ind.__class__.__name__}] 运行期崩溃: {e}，已自动跳过该指标以保护主流程。")
            
    return df_out