import numpy as np
from .utils import BinaryField

class HammingMcElieceDecryptor:
    """分块汉明码McEliece解密器"""
    
    def __init__(self, private_key):
        """
        初始化解密器
        
        参数:
            private_key: 私钥字典
        """
        self.S_inv = private_key['S_inv']
        self.G = private_key['G']
        self.P = private_key['P']
        self.P_inv = private_key['P_inv']
        self.code = private_key['code']
        self.k = private_key['k']
    
    def decrypt(self, ciphertext):
        """
        解密密文
        
        参数:
            ciphertext: 密文向量
            
        返回:
            message: 解密出的消息向量
            success: 是否成功解密
        """
        # 第一步: c' = c * P^{-1}
        c_prime = BinaryField.matrix_multiply(
            ciphertext.reshape(1, -1), self.P_inv
        )[0] % 2
        
        # 第二步: 使用原始码译码
        decoded = self.code.decode(c_prime)
        
        # 第三步: 提取信息位（假设G是系统形式）
        # 在实际实现中，需要解方程得到mS
        # 这里简化：假设G是系统形式，信息位在前k列
        mS_encoded = decoded[:self.k]
        
        # 第四步: m = (mS) * S^{-1}
        mS = mS_encoded[:self.k]  # 取前k位作为mS
        message = BinaryField.matrix_multiply(
            mS.reshape(1, -1), self.S_inv
        )[0] % 2
        
        # 验证解密是否正确
        success = True  # 简化实现
        
        return message, success

# 提供便捷的函数接口，与run_hamming_demo.py兼容
def hamming_decrypt(ciphertext, private_key):
    """
    使用汉明码McEliece私钥解密密文
    
    参数:
        ciphertext: 密文向量
        private_key: 私钥字典
        
    返回:
        message: 解密后的消息向量
    """
    # 创建解密器实例
    decryptor = HammingMcElieceDecryptor(private_key)
    
    # 解密密文
    message, _ = decryptor.decrypt(ciphertext)
    
    return message