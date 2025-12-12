#!/usr/bin/env python3
"""
性能测试和测量工具
"""

import platform
import os
import sys
import numpy as np

def calculate_security_level(n, k, t):
    """
    计算McEliece密码系统的安全性等级（基于信息集解码攻击）
    
    参数:
        n: 码长
        k: 信息位长度
        t: 纠错能力
        
    返回:
        security: 安全等级（比特数）
    """
    # 信息集解码攻击的计算复杂度近似为 C(n, t) * 2^(k - sqrt(ktn))
    # 这里使用近似公式计算安全等级
    
    # 计算组合数 C(n, t) 的对数
    if t == 0:
        log_c = 0
    else:
        # 使用斯特林公式近似阶乘
        log_n_fact = n * np.log2(n) - n
        log_t_fact = t * np.log2(t) - t
        log_nt_fact = (n-t) * np.log2(n-t) - (n-t)
        log_c = log_n_fact - log_t_fact - log_nt_fact
    
    # 计算指数部分
    exponent = k - np.sqrt(k * t * n)
    if exponent < 0:
        exponent = 0
    
    # 总复杂度
    total_complexity = log_c + exponent
    
    return max(0, total_complexity)

def get_system_info():
    """
    获取系统信息
    
    返回:
        system_info: 包含系统信息的字典
    """
    system_info = {
        "操作系统": platform.system(),
        "操作系统版本": platform.version(),
        "CPU架构": platform.machine(),
        "CPU型号": platform.processor(),
        "Python版本": platform.python_version(),
        "内存信息": f"{os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024 ** 3):.2f} GB" if hasattr(os, 'sysconf') else "未知",
        "当前工作目录": os.getcwd(),
        "Python执行路径": sys.executable
    }
    
    return system_info