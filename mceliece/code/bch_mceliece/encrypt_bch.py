import numpy as np
from .utils import generate_error_vector, BinaryField

class BCHMcElieceEncryptor:
    """BCH码McEliece加密器"""
    
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
        self.L = public_key.get('L', 10)
        self.scheme = public_key.get('scheme', 'BCH')
    
    def encrypt(self, message, random_state=None):
        """
        加密消息
        
        参数:
            message: 二进制消息向量 (长度=k)
            random_state: 随机状态
            
        返回:
            ciphertext: 密文向量 (长度=n)
            error: 错误向量 (用于调试)
        """
        if len(message) != self.k:
            raise ValueError(f"消息长度应为{self.k}，但得到{len(message)}")
        
        # 确保消息是二进制
        # 处理bitarray对象的特殊情况
        if hasattr(message, 'tolist'):
            message = np.array(message.tolist(), dtype=int)
        else:
            message = np.array(message, dtype=int)
        
        # 确保所有值都是0或1
        message = message % 2
        if not np.all((message == 0) | (message == 1)):
            raise ValueError("消息必须为二进制向量")
        
        # 生成随机错误向量
        error = generate_error_vector(self.n, self.t, random_state)
        
        # 计算密文: c = m * G' + e
        # 使用优化的矩阵乘法
        mG_prime = np.zeros(self.n, dtype=int)
        
        # 逐行计算避免大矩阵乘法
        for i in range(self.k):
            if message[i] == 1:
                mG_prime ^= self.G_prime[i]
        
        ciphertext = (mG_prime + error) % 2
        
        return ciphertext, error
    
    def encrypt_batch(self, messages, random_states=None):
        """
        批量加密消息
        
        参数:
            messages: 消息矩阵 (batch_size × k)
            random_states: 随机状态列表
            
        返回:
            ciphertexts: 密文矩阵 (batch_size × n)
            errors: 错误向量矩阵
        """
        batch_size = len(messages)
        ciphertexts = np.zeros((batch_size, self.n), dtype=int)
        errors = np.zeros((batch_size, self.n), dtype=int)
        
        if random_states is None:
            random_states = [None] * batch_size
        
        for i in range(batch_size):
            ciphertexts[i], errors[i] = self.encrypt(
                messages[i], 
                random_state=random_states[i]
            )
        
        return ciphertexts, errors
    
    def get_expansion_rate(self):
        """获取密文扩张率"""
        return self.n / self.k
    
    def get_parameters(self):
        """获取加密参数"""
        return {
            'n': self.n,
            'k': self.k,
            't': self.t,
            'L': self.L,
            'scheme': self.scheme,
            'expansion_rate': self.get_expansion_rate()
        }
    
    def validate_ciphertext(self, ciphertext):
        """验证密文格式"""
        if len(ciphertext) != self.n:
            return False, f"长度应为{self.n}，但得到{len(ciphertext)}"
        
        if not np.all((ciphertext == 0) | (ciphertext == 1)):
            return False, "必须为二进制向量"
        
        return True, "有效"

# 提供一个便捷的函数接口，与run_bch_demo.py兼容
def encrypt(message, public_key, t_total, random_state=None):
    """
    加密消息
    
    参数:
        message: 消息向量
        public_key: 公钥字典或矩阵
        t_total: 总错误位数
        random_state: 随机状态
        
    返回:
        密文向量（bitarray对象）
    """
    # 处理公钥字典或矩阵的情况
    if isinstance(public_key, dict):
        public_key_dict = public_key
    else:
        # 准备公钥字典（与BCHMcElieceEncryptor构造函数兼容）
        public_key_dict = {
            'G_prime': public_key,
            't': t_total,
            'n': public_key.shape[1],
            'k': public_key.shape[0]
        }
    
    # 创建加密器实例
    encryptor = BCHMcElieceEncryptor(public_key_dict)
    
    # 加密消息
    ciphertext, _ = encryptor.encrypt(message, random_state=random_state)
    
    # 将numpy数组转换为bitarray对象，与demo脚本兼容
    import bitarray
    ciphertext_ba = bitarray.bitarray()
    ciphertext_ba.extend(ciphertext.tolist())
    
    return ciphertext_ba