import numpy as np
import galois
from .bch_code import BCHCode

class BCHMcElieceKeyGenerator:
    """BCH码McEliece密钥生成器"""
    
    def __init__(self, L=10):
        """
        初始化密钥生成器
        
        参数:
            L: 分块数量
        """
        self.L = L
        self.code = BCHCode(L)
        self.GF2 = galois.GF(2)
        self.n = self.code.n_total
        self.k = self.code.k_total
        
    def generate_keys(self, seed=None):
        """
        生成公钥和私钥
        
        参数:
            seed: 随机种子
            
        返回:
            public_key: 公钥矩阵 G'
            private_key: 私钥 (S, G_original, P, S_inv, code_params)
        """
        if seed is not None:
            np.random.seed(seed)
        
        # 1. 原始生成矩阵 G
        G_original = self.code.get_generator_matrix()
        # 将G_original转换为galois.GF(2)类型，以便与S和P进行矩阵乘法
        G_original = self.GF2(G_original)
        
        # 2. 随机可逆矩阵 S (k x k)
        S = self._generate_random_invertible_matrix(self.k)
        S_inv = np.linalg.inv(S)
        
        # 3. 随机置换矩阵 P (n x n)
        P = self._generate_random_permutation_matrix(self.n)
        
        # 4. 计算公钥: G' = S * G_original * P
        G_prime = S @ G_original @ P
        
        # 转换为整数类型便于存储
        G_prime_int = np.array(G_prime, dtype=int)
        S_int = np.array(S, dtype=int)
        P_int = np.array(P, dtype=int)
        S_inv_int = np.array(S_inv, dtype=int)
        
        # 从BCH码参数中获取t
        t = self.code.get_parameters()['t']
        
        # 公钥: 字典格式，包含G_prime、t、n、k等信息
        public_key = {
            'G_prime': G_prime_int,
            't': t,
            'n': self.n,
            'k': self.k,
            'bch_params': self.code.get_parameters()
        }
        
        private_key = {
            'S': S_int,
            'G_original': np.array(G_original, dtype=int),
            'P': P_int,
            'S_inv': S_inv_int,
            'bch_params': self.code.get_parameters(),
            't': t,
            'L': self.L,
            'scheme': 'BCH'
        }
        
        return public_key, private_key
    
    def _generate_random_invertible_matrix(self, size):
        """生成随机的可逆二进制矩阵"""
        max_attempts = 100
        for _ in range(max_attempts):
            # 生成随机矩阵
            matrix = np.random.randint(0, 2, (size, size))
            matrix_gf = self.GF2(matrix)
            
            try:
                # 检查是否可逆
                det = np.linalg.det(matrix_gf)
                if det != 0:
                    return matrix_gf
            except np.linalg.LinAlgError:
                continue
        
        # 如果无法生成可逆矩阵，使用单位矩阵加上随机扰动
        identity = np.eye(size, dtype=int)
        random_part = np.random.randint(0, 2, (size, size))
        matrix = (identity + random_part) % 2
        return self.GF2(matrix)
    
    def _generate_random_permutation_matrix(self, size):
        """生成随机置换矩阵"""
        perm = np.random.permutation(size)
        P = np.zeros((size, size), dtype=int)
        P[np.arange(size), perm] = 1
        return self.GF2(P)
    
    def get_key_sizes(self):
        """计算密钥大小（字节）"""
        # 公钥大小：k x n 二进制矩阵
        public_key_bytes = self.k * self.n // 8
        
        # 私钥大小：S(kxk) + G_original(kxn) + P(nxn) + S_inv(kxk) + 参数
        private_key_bytes = (self.k*self.k + self.k*self.n + self.n*self.n + self.k*self.k) // 8
        
        return public_key_bytes, private_key_bytes
    
    def estimate_security(self):
        """估算安全性（比特）"""
        # 使用信息集译码复杂度估算
        # C ≈ min_{0 ≤ w ≤ t} binom(n, w) / binom(n-k, w)
        
        n, k = self.n, self.k
        t = self.code.t  # 使用的错误位数
        
        # 计算组合数
        from math import comb, log2
        
        # 简化估算：log2(选择错误位置的方式数)
        security = log2(comb(n, t))
        
        # 考虑矩阵操作的影响
        # 实际攻击中，攻击者会尝试信息集译码
        # 这里我们使用McEliece经典安全估算公式
        complexity = log2(comb(n, t) / comb(n-k, t))
        
        return min(security, complexity)

# 提供一个便捷的函数接口，与run_bch_demo.py兼容
def generate_bch_mceliece_keys(L=10, t=2, seed=None):
    """
    生成BCH码McEliece密钥对
    
    参数:
        L: 分块数量
        t: 每个分块的纠错能力
        seed: 随机种子
        
    返回:
        public_key: 公钥矩阵
        private_key: 私钥字典
    """
    # 创建密钥生成器实例
    keygen = BCHMcElieceKeyGenerator(L=L)
    
    # 生成密钥对
    pub_key, priv_key = keygen.generate_keys(seed=seed)
    
    # 为了与demo脚本兼容，需要确保私钥包含必要的字段
    priv_key['n'] = keygen.n
    priv_key['k'] = keygen.k
    priv_key['t'] = t * L
    priv_key['L'] = L
    priv_key['scheme'] = 'BCH'
    
    return pub_key, priv_key