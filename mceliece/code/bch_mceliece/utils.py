import numpy as np

class BinaryField:
    """二进制域(GF(2))操作工具类"""
    
    @staticmethod
    def matrix_multiply(a, b):
        """GF(2)上的矩阵乘法
        
        参数:
            a: 第一个矩阵
            b: 第二个矩阵
            
        返回:
            乘积矩阵
        """
        if a.shape[1] != b.shape[0]:
            raise ValueError("矩阵维度不匹配")
        
        result = np.zeros((a.shape[0], b.shape[1]), dtype=int)
        
        for i in range(a.shape[0]):
            for j in range(b.shape[1]):
                # 计算点积，模2
                result[i][j] = np.sum(a[i] * b[:, j]) % 2
        
        return result

def generate_error_vector(n, t, random_state=None):
    """生成GF(2)上的随机错误向量
    
    参数:
        n: 向量长度
        t: 错误位数
        random_state: 随机状态对象或None
        
    返回:
        错误向量（长度为n的numpy数组）
    """
    if random_state is None:
        random_state = np.random
    
    error = np.zeros(n, dtype=int)
    error_positions = random_state.choice(n, size=min(t, n), replace=False)
    error[error_positions] = 1
    
    return error