#!/usr/bin/env python3
"""
McEliece密码系统安全估算工具
支持多种攻击假设下的安全等级计算
"""

import numpy as np
from typing import Dict, Optional

class SecurityEstimator:
    """
    McEliece安全估算器，支持多种攻击模型
    """
    
    def __init__(self, n: int, k: int, t: int, code_type: str = "general"):
        """
        初始化安全估算器
        
        参数:
            n: 总码长
            k: 总信息位长度
            t: 总纠错能力
            code_type: 码类型 ("bch", "hamming", "general")
        """
        self.n = n
        self.k = k
        self.t = t
        self.code_type = code_type.lower()
    
    def estimate_isd_attack(self, variant: str = "basic") -> float:
        """
        估算信息集解码(ISD)攻击的安全级别
        
        参数:
            variant: ISD变体 ("basic", "ball-collision", "stern")
            
        返回:
            安全级别（比特数）
        """
        if self.t == 0:
            return 0
            
        # 计算组合数 C(n, t) 的对数
        log_n_fact = self.n * np.log2(self.n) - self.n
        log_t_fact = self.t * np.log2(self.t) - self.t
        log_nt_fact = (self.n - self.t) * np.log2(self.n - self.t) - (self.n - self.t)
        log_c = log_n_fact - log_t_fact - log_nt_fact
        
        if variant == "basic":
            # 基础ISD复杂度: C(n, t) * 2^(k - sqrt(ktn))
            exponent = self.k - np.sqrt(self.k * self.t * self.n)
            if exponent < 0:
                exponent = 0
            total_complexity = log_c + exponent
            
        elif variant == "ball-collision":
            # 球碰撞ISD复杂度: C(n, t) * 2^(k/2 - sqrt(ktn)/2)
            exponent = (self.k - np.sqrt(self.k * self.t * self.n)) / 2
            if exponent < 0:
                exponent = 0
            total_complexity = log_c + exponent
            
        elif variant == "stern":
            # Stern算法复杂度: C(n, t) * 2^(sqrt(ktn))
            exponent = np.sqrt(self.k * self.t * self.n) / 3
            total_complexity = log_c + exponent
            
        else:
            raise ValueError(f"未知的ISD变体: {variant}")
        
        return max(0, total_complexity)
    
    def estimate_structural_attack(self) -> float:
        """
        估算结构攻击的安全级别
        
        返回:
            安全级别（比特数）
        """
        if self.code_type == "bch":
            # BCH码结构攻击复杂度: 2^(m*t), m为GF(2^m)的阶
            # 对于(15,7) BCH码，m=4
            m = 4
            return m * self.t * np.log2(2)
            
        elif self.code_type == "hamming":
            # 汉明码结构攻击复杂度: 2^(m*L), m=log2(n+1), L为分块数
            # 对于(15,11)汉明码，m=4
            m = 4
            L = self.t  # 假设每个分块1个错误，L≈t
            return m * L * np.log2(2)
            
        else:
            # 通用结构攻击复杂度
            return self.t * np.log2(self.n)
    
    def estimate_quantum_attack(self) -> float:
        """
        估算量子攻击的安全级别
        
        返回:
            安全级别（比特数）
        """
        # 量子ISD攻击复杂度约为经典ISD的平方根
        classical_isd = self.estimate_isd_attack(variant="ball-collision")
        return max(0, classical_isd / 2)
    
    def estimate_brute_force(self) -> float:
        """
        估算暴力搜索攻击的安全级别
        
        返回:
            安全级别（比特数）
        """
        # 暴力搜索所有可能的明文
        return self.k * np.log2(2)
    
    def estimate_all_attacks(self) -> Dict[str, float]:
        """
        估算所有攻击模型的安全级别
        
        返回:
            包含所有攻击模型安全级别的字典
        """
        return {
            "ISD攻击(Basic)": self.estimate_isd_attack(variant="basic"),
            "ISD攻击(Ball-Collision)": self.estimate_isd_attack(variant="ball-collision"),
            "ISD攻击(Stern)": self.estimate_isd_attack(variant="stern"),
            "结构攻击": self.estimate_structural_attack(),
            "量子攻击": self.estimate_quantum_attack(),
            "暴力搜索": self.estimate_brute_force()
        }
    
    def get_security_summary(self) -> Dict[str, float]:
        """
        获取安全估算摘要
        
        返回:
            包含关键安全指标的字典
        """
        all_attacks = self.estimate_all_attacks()
        
        return {
            "最弱安全级别": min(all_attacks.values()),
            "最强安全级别": max(all_attacks.values()),
            "平均安全级别": np.mean(list(all_attacks.values())),
            "典型安全级别": all_attacks["ISD攻击(Ball-Collision)"]  # 最常用的ISD变体
        }


def estimate_security(n: int, k: int, t: int, code_type: str = "general") -> Dict:
    """
    便捷函数：估算McEliece密码系统的安全性
    
    参数:
        n: 码长
        k: 信息位长度
        t: 纠错能力
        code_type: 码类型 ("bch", "hamming", "general")
        
    返回:
        安全估算结果的字典
    """
    estimator = SecurityEstimator(n, k, t, code_type)
    
    return {
        "参数": {
            "码长(n)": n,
            "信息位长度(k)": k,
            "纠错能力(t)": t,
            "码类型": code_type
        },
        "各攻击模型安全级别": estimator.estimate_all_attacks(),
        "安全摘要": estimator.get_security_summary()
    }
