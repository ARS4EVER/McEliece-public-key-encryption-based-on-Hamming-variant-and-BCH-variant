import numpy as np
from .utils import generate_error_vector, BinaryField

class HammingMcElieceEncryptor:
    """分块汉明码McEliece加密器"""
    
    def __init__(self, public_key):
        """
        初始化加密器
        
        参数:
            public_key: 公钥字典
        """
        self.G_prime = public_key['G_prime']
        self.t = public_key['t']
        self.n = public_key['n']
        self.k = public_key['k']
    
    def encrypt(self, message, random_state=None):
        """
        加密消息
        
        参数:
            message: 二进制消息向量 (长度=k)
            random_state: 随机状态
            
        返回:
            ciphertext: 密文向量 (长度=n)
        """
        if len(message) != self.k:
            raise ValueError(f"消息长度应为{self.k}")
        
        # 确保消息是NumPy数组
        message = np.array(message, dtype=int)
        
        # 生成随机错误向量
        error = generate_error_vector(self.n, self.t, random_state)
        
        # 计算密文: c = m * G' + e
        mG_prime = BinaryField.matrix_multiply(
            message.reshape(1, -1), self.G_prime
        )[0] % 2
        
        ciphertext = (mG_prime + error) % 2
        
        return ciphertext, error

# 提供便捷的函数接口，与run_hamming_demo.py兼容
def hamming_encrypt(message, public_key, random_state=None):
    """
    使用汉明码McEliece公钥加密消息
    
    参数:
        message: 二进制消息向量
        public_key: 公钥字典
        random_state: 随机状态
        
    返回:
        ciphertext: 密文向量
    """
    # 创建加密器实例
    encryptor = HammingMcElieceEncryptor(public_key)
    
    # 加密消息
    ciphertext, _ = encryptor.encrypt(message, random_state)
    
    return ciphertext