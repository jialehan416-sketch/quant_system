import logging
import os
import sys

def setup_logger(name="QUANT_SYSTEM", log_file="logs/system.log"):
    """
    初始化标准化分级日志系统
    """
    # 确保 logs 目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 捕获所有等级
    
    # 定义日志输出格式
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    )
    
    # 1. 控制台处理器：只显示 INFO 及以上信息，防止信息过载
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 2. 文件处理器：记录所有 DEBUG 及以上信息，用于事后审计
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 避免重复添加处理器
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger

# 创建全局 logger 实例
logger = setup_logger()