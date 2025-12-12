import numpy as np
from .utils import BinaryField, generate_permutation_matrix, generate_random_invertible_matrix
from .hamming_code import BlockHammingCode

class HammingMcElieceKeyGenerator:
    """分块汉明码McEliece密钥生成器"""
    
    def __init__(self, L=10, random_seed=None):
        """
        初始化密钥生成器
        
        参数:
            L: 分块数量
            random_seed: 随机种子
        """
        self.L = L
        self.random_seed = random_seed
        self.code = BlockHammingCode(L=L)
        
        if random_seed:
            np.random.seed(random_seed)
    
    def generate_keys(self):
        """生成公钥和私钥"""
        # 原始生成矩阵
        G = self.code.get_generator_matrix()
        k, n = G.shape
        
        # 生成随机可逆矩阵S
        S, S_inv = generate_random_invertible_matrix(k, self.random_seed)
        
        # 生成置换矩阵P
        P = generate_permutation_matrix(n, self.random_seed)
        
        # 计算公钥 G' = S * G * P
        G_prime = BinaryField.matrix_multiply(
            BinaryField.matrix_multiply(S, G), P
        ) % 2
        
        # 公钥: (G_prime, t)
        public_key = {
            'G_prime': G_prime,
            't': self.code.t,
            'n': n,
            'k': k
        }
        
        # 私钥: (S, S_inv, G, P, code_params)
        private_key = {
            'S': S,
            'S_inv': S_inv,
            'G': G,
            'P': P,
            'P_inv': P.T,  # 置换矩阵的逆是其转置
            'code': self.code,
            'n': n,
            'k': k,
            't': self.code.t
        }
        
        return public_key, private_key
    
    def get_key_sizes(self, public_key, private_key):
        """计算密钥大小（字节）"""
        # 公钥大小
        G_prime_size = public_key['G_prime'].nbytes
        public_key_size = G_prime_size + 24  # 加上t, n, k的存储
        
        # 私钥大小
        S_inv_size = private_key['S_inv'].nbytes
        G_size = private_key['G'].nbytes
        P_size = private_key['P'].nbytes
        private_key_size = S_inv_size + G_size + P_size + 100  # 加上其他参数
        
        return public_key_size, private_key_size

# 提供便捷的函数接口，与run_hamming_demo.py兼容
def generate_hamming_key(L=10, random_seed=None):
    """
    生成汉明码McEliece密钥对
    
    参数:
        L: 分块数量
        random_seed: 随机种子
        
    返回:
        public_key: 公钥字典
        private_key: 私钥字典
    """
    # 创建密钥生成器实例
    keygen = HammingMcElieceKeyGenerator(L=L, random_seed=random_seed)
    
    # 生成密钥对
    public_key, private_key = keygen.generate_keys()
    
    return public_key, private_key

def save_keys(public_key, private_key, prefix="hamming"):
    """
    保存密钥对到文件
    
    参数:
        public_key: 公钥字典
        private_key: 私钥字典
        prefix: 文件名前缀
    """
    np.save(f"{prefix}_public_key.npy", public_key)
    np.savez(f"{prefix}_private_key.npz", **private_key)

def load_public_key(prefix="hamming"):
    """
    从文件加载公钥
    
    参数:
        prefix: 文件名前缀
        
    返回:
        public_key: 公钥字典
    """
    return np.load(f"{prefix}_public_key.npy", allow_pickle=True).item()

def load_private_key(prefix="hamming"):
    """
    从文件加载私钥
    
    参数:
        prefix: 文件名前缀
        
    返回:
        private_key: 私钥字典
    """
    with np.load(f"{prefix}_private_key.npz") as data:
        return dict(data)