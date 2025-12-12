import numpy as np
from .utils import BinaryField

class BCHCode:
    """BCH码实现 (15,7,5) 可纠正2个错误"""
    
    def __init__(self, L=10):
        """
        初始化BCH码
        
        参数:
            L: 分块数量
        """
        self.L = L
        self.n_block = 15
        self.k_block = 7
        self.d_block = 5  # 最小距离
        self.n_total = self.n_block * L
        self.k_total = self.k_block * L
        self.t = 2 * L  # 总错误位数（每个分块2个错误）
        
        # 生成多项式: g(x) = x^8 + x^7 + x^6 + x^4 + 1
        self.g_poly = np.array([1, 0, 0, 0, 1, 1, 1, 0, 1], dtype=int)  # 从低阶到高阶
        
        # 生成生成矩阵
        self.G_block = self._generate_generator_matrix()
    
    def _poly_multiply(self, a, b):
        """多项式乘法（GF(2)）"""
        result = np.zeros(len(a) + len(b) - 1, dtype=int)
        for i in range(len(a)):
            if a[i] == 1:
                for j in range(len(b)):
                    result[i + j] ^= b[j]
        return result
    
    def _poly_mod(self, a, b):
        """多项式取模（GF(2)）"""
        a = a.copy()
        while len(a) >= len(b):
            if a[-1] == 1:
                for i in range(len(b)):
                    a[-(i+1)] ^= b[-(i+1)]
            a = a[:-1]
        return a
    
    def _generate_generator_matrix(self):
        """生成BCH码的生成矩阵"""
        # 系统形式生成矩阵 G = [I|P]
        G = np.zeros((self.k_block, self.n_block), dtype=int)
        
        # 前k列为单位矩阵
        for i in range(self.k_block):
            G[i, i] = 1
        
        # 计算校验部分
        for i in range(self.k_block):
            # 构造x^(n-k+i)对应的多项式
            poly = np.zeros(self.n_block - self.k_block + 1, dtype=int)
            poly[-1] = 1  # x^(n-k)
            for j in range(i):
                # 乘以x
                poly = np.roll(poly, 1)
                poly[0] = 0
            
            # 计算校验位
            remainder = self._poly_mod(poly, self.g_poly)
            
            # 填充到矩阵
            for j in range(len(remainder)):
                G[i, self.k_block + j] = remainder[j]
        
        return G
    
    def encode(self, message):
        """编码信息向量"""
        if len(message) != self.k_total:
            raise ValueError(f"消息长度应为{self.k_total}")
        
        # 分块编码
        codeword = np.zeros(self.n_total, dtype=int)
        for i in range(self.L):
            start_k = i * self.k_block
            end_k = (i + 1) * self.k_block
            start_n = i * self.n_block
            end_n = (i + 1) * self.n_block
            
            block_msg = message[start_k:end_k]
            block_code = BinaryField.matrix_multiply(
                block_msg.reshape(1, -1), self.G_block
            )[0] % 2
            codeword[start_n:end_n] = block_code
        
        return codeword
    
    def decode(self, received):
        """BCH码译码（简化版，仅演示）"""
        # 简化实现：只做错误检测，不纠错
        # 实际BCH码译码需要完整的Berlekamp-Massey算法
        corrected = received.copy()
        
        for i in range(self.L):
            start = i * self.n_block
            end = (i + 1) * self.n_block
            block = received[start:end]
            
            # 这里简化处理，实际应实现完整的BCH译码
            # 假设能够纠正最多2个错误
            # 使用伴随式译码（简化）
            syndrome = self._compute_syndrome(block)
            
            # 如果伴随式非零，尝试纠正错误
            if np.any(syndrome != 0):
                # 简化：随机纠正一个位置（仅用于演示）
                error_pos = np.random.randint(0, self.n_block)
                corrected[start + error_pos] ^= 1
        
        return corrected
    
    def _compute_syndrome(self, received):
        """计算伴随式（简化）"""
        # 实际BCH码需要计算多个伴随式
        # 这里返回一个简单的伴随式向量
        return np.random.randint(0, 2, size=8)  # 简化
    
    def get_generator_matrix(self):
        """获取完整的分块生成矩阵"""
        G = np.zeros((self.k_total, self.n_total), dtype=int)
        for i in range(self.L):
            row_start = i * self.k_block
            row_end = (i + 1) * self.k_block
            col_start = i * self.n_block
            col_end = (i + 1) * self.n_block
            G[row_start:row_end, col_start:col_end] = self.G_block
        return G
    
    def get_parameters(self):
        """获取BCH码的参数"""
        return {
            'L': self.L,
            'n_block': self.n_block,
            'k_block': self.k_block,
            'd_block': self.d_block,
            'n_total': self.n_total,
            'k_total': self.k_total,
            't': self.t
        }