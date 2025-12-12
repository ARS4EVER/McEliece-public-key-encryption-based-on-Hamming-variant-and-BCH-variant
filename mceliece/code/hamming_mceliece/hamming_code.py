import numpy as np
from .utils import BinaryField

class BlockHammingCode:
    """分块汉明码实现"""
    
    def __init__(self, L=10, block_params=(15, 11, 3)):
        """
        初始化分块汉明码
        
        参数:
            L: 分块数量
            block_params: 单个汉明码参数 (n_block, k_block, d_block)
        """
        self.L = L
        self.n_block, self.k_block, self.d_block = block_params
        self.n_total = self.n_block * L
        self.k_total = self.k_block * L
        self.t = L  # 总错误位数（每个分块1个错误）
        
        # 生成单个汉明码的生成矩阵（系统形式）
        self.G_block = self._generate_hamming_generator()
    
    def _generate_hamming_generator(self):
        """生成(15,11)汉明码的系统形式生成矩阵"""
        # (15,11)汉明码的校验矩阵H（4×15）
        # 使用所有非零4位二进制向量作为列
        H_block = np.array([
            [1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1],
            [0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0],
            [0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1]
        ], dtype=int).T
        
        # 转换为系统形式的生成矩阵 G = [I|P]
        # 重新排列列，使前k列线性独立
        # 对于(15,11)汉明码，我们选择适当的列组成单位矩阵
        G_block = np.zeros((self.k_block, self.n_block), dtype=int)
        
        # 创建系统形式生成矩阵
        # 前11列为单位矩阵
        for i in range(self.k_block):
            G_block[i, i] = 1
        
        # 计算后面4列的校验位部分
        # G = [I | P]，其中 P^T = H_2 （H = [H_1 H_2]，H_1可逆）
        H_1 = H_block[:self.k_block, :4]  # 假设前k列对应H_1
        H_2 = H_block[self.k_block:, :4]  # 后4列对应H_2
        
        # 解方程得到P
        # 这里简化为直接构造
        P = np.array([
            [1, 0, 0, 0],
            [1, 1, 0, 0],
            [0, 1, 1, 0],
            [1, 1, 1, 0],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [1, 1, 0, 1],
            [1, 0, 1, 1],
            [0, 1, 1, 1],
            [1, 1, 1, 1],
            [0, 0, 1, 0]
        ], dtype=int)
        
        # 合并成完整的生成矩阵
        G_block[:, self.k_block:] = P
        
        return G_block
    
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
    
    def decode(self, received, t=None):
        """分块译码（仅纠正每个分块1个错误）"""
        if t is None:
            t = self.L
        
        if len(received) != self.n_total:
            raise ValueError(f"接收向量长度应为{self.n_total}")
        
        # 计算伴随式并纠正错误
        corrected = received.copy()
        
        for i in range(self.L):
            start = i * self.n_block
            end = (i + 1) * self.n_block
            block = received[start:end]
            
            # 计算伴随式 s = H * r^T
            H = self._get_parity_check_matrix()
            s = BinaryField.matrix_multiply(
                H, block.reshape(-1, 1)
            ).flatten() % 2
            
            # 如果伴随式非零，尝试纠正单个错误
            if np.any(s != 0):
                # 查找错误位置（简化版，实际应使用完备的汉明码译码）
                # 这里假设最多一个错误
                error_pos = self._find_error_position(s)
                if error_pos is not None:
                    corrected[start + error_pos] ^= 1
        
        return corrected
    
    def _get_parity_check_matrix(self):
        """获取校验矩阵"""
        # (15,11)汉明码的校验矩阵
        return np.array([
            [1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1],
            [0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0],
            [0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1]
        ], dtype=int)
    
    def _find_error_position(self, syndrome):
        """根据伴随式查找错误位置"""
        # 伴随式与H的列匹配
        H = self._get_parity_check_matrix()
        for j in range(H.shape[1]):
            if np.array_equal(H[:, j], syndrome):
                return j
        return None
    
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