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

def generate_permutation_matrix(n, random_seed=None):
    """生成随机置换矩阵
    
    参数:
        n: 矩阵大小
        random_seed: 随机种子
        
    返回:
        置换矩阵 (n x n numpy数组)
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    perm = np.random.permutation(n)
    P = np.zeros((n, n), dtype=int)
    P[np.arange(n), perm] = 1
    
    return P

def generate_random_invertible_matrix(size, random_seed=None):
    """生成随机的可逆二进制矩阵及其逆矩阵
    
    参数:
        size: 矩阵大小
        random_seed: 随机种子
        
    返回:
        (S, S_inv): 可逆矩阵及其逆矩阵
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    max_attempts = 100
    for _ in range(max_attempts):
        # 生成随机矩阵
        matrix = np.random.randint(0, 2, (size, size))
        
        # 检查行列式是否为1 mod 2
        det = np.linalg.det(matrix)
        if det % 2 != 0:
            # 计算逆矩阵
            try:
                inv_matrix = np.linalg.inv(matrix)
                # 转换为二进制矩阵
                inv_matrix = (inv_matrix % 2).astype(int)
                return matrix, inv_matrix
            except np.linalg.LinAlgError:
                continue
    
    # 如果无法生成可逆矩阵，使用单位矩阵加上随机扰动
    identity = np.eye(size, dtype=int)
    random_part = np.random.randint(0, 2, (size, size))
    matrix = (identity + random_part) % 2
    
    # 计算逆矩阵
    inv_matrix = np.linalg.inv(matrix)
    inv_matrix = (inv_matrix % 2).astype(int)
    
    return matrix, inv_matrix

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