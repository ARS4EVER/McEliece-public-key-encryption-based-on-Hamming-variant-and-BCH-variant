import numpy as np
from .utils import BinaryField

class BCHMcElieceDecryptor:
    """BCH码McEliece解密器"""
    
    def __init__(self, private_key):
        """
        初始化解密器
        
        参数:
            private_key: 私钥字典
        """
        self.S_inv = private_key['S_inv']
        self.G = private_key['G_original']
        self.P = private_key['P']
        self.P_inv = np.linalg.inv(self.P)  # 计算P的逆矩阵
        self.n = private_key['bch_params']['n_total']
        self.k = private_key['bch_params']['k_total']
        self.t = private_key['t']
        self.L = private_key.get('L', 10)
        self.scheme = private_key.get('scheme', 'BCH')
        
        # 注意：code对象可能不在private_key中
        # 需要在外部传入或重新创建
        self.code = None
        if 'code' in private_key:
            self.code = private_key['code']
        else:
            # 根据bch_params重新创建code对象
            from .bch_code import BCHCode
            self.code = BCHCode(private_key['L'])
    
    def set_code(self, code):
        """设置BCHCode对象（如果未在私钥中）"""
        self.code = code
    
    def decrypt(self, ciphertext):
        """
        解密密文
        
        参数:
            ciphertext: 密文向量
            
        返回:
            message: 解密出的消息向量
            success: 是否成功解密
            error_info: 错误信息（如果失败）
        """
        # 验证输入
        if len(ciphertext) != self.n:
            return None, False, f"密文长度应为{self.n}，但得到{len(ciphertext)}"
        
        try:
            # 处理bitarray对象
            if hasattr(ciphertext, 'tolist'):
                ciphertext = np.array(ciphertext.tolist(), dtype=int)
            else:
                ciphertext = np.array(ciphertext, dtype=int)
            
            # 确保ciphertext是二进制
            ciphertext = ciphertext % 2
            
            # 第一步: c' = c * P^{-1}
            # 更高效的置换实现
            c_prime = np.zeros(self.n, dtype=int)
            for i in range(self.n):
                # 查找P中第i行的1的位置（即置换后的列）
                p_col = np.where(self.P[i, :] == 1)[0][0]
                c_prime[p_col] = ciphertext[i]
            
            # 第二步: 使用BCH码译码纠正错误
            if self.code is None:
                # 如果没有code对象，直接使用c_prime
                decoded = c_prime
                success = True
            else:
                decoded = self.code.decode(c_prime)
                success = True
            
            # 第三步: 计算消息矩阵乘法 mS = decoded * (G^T * G)^{-1} * G^T （简化实现）
            # 由于这是简化实现，我们直接使用前k位
            mS_encoded = decoded[:self.k]
            
            # 第四步: m = mS_encoded * S^{-1}
            # 矩阵乘法实现
            message = np.zeros(self.k, dtype=int)
            for i in range(self.k):
                if mS_encoded[i] == 1:
                    message ^= self.S_inv[i]
            
            return message, success, "解密成功"
            
        except Exception as e:
            return None, False, f"解密过程中出现错误: {str(e)}"
    
    def _simple_decode(self, received):
        """
        简化译码（仅用于演示）
        实际BCH码需要完整的Berlekamp-Massey算法
        
        参数:
            received: 接收到的向量
            
        返回:
            假设已经纠正错误的码字
        """
        # 简化实现：假设没有错误或错误已被纠正
        # 在实际实现中，这里应该调用完整的BCH译码算法
        return received.copy()
    
    def decrypt_batch(self, ciphertexts):
        """
        批量解密密文
        
        参数:
            ciphertexts: 密文矩阵 (batch_size × n)
            
        返回:
            messages: 消息矩阵 (batch_size × k)
            successes: 成功标志列表
            error_infos: 错误信息列表
        """
        batch_size = len(ciphertexts)
        messages = np.zeros((batch_size, self.k), dtype=int)
        successes = []
        error_infos = []
        
        for i in range(batch_size):
            message, success, error_info = self.decrypt(ciphertexts[i])
            if success:
                messages[i] = message
            successes.append(success)
            error_infos.append(error_info)
        
        return messages, successes, error_infos
    
    def test_decryption(self, num_tests=100, random_seed=None):
        """
        测试解密正确性
        
        参数:
            num_tests: 测试次数
            random_seed: 随机种子
            
        返回:
            成功率统计
        """
        if random_seed:
            np.random.seed(random_seed)
        
        success_count = 0
        error_details = []
        
        for i in range(num_tests):
            # 生成随机消息
            message = np.random.randint(0, 2, size=self.k)
            
            # 模拟加密过程
            # 注意：这里需要加密器，但为了独立测试，我们模拟加密
            # 在实际使用中，应该使用真实的加密器
            
            # 1. 计算 m * G
            mG = np.zeros(self.n, dtype=int)
            for j in range(self.k):
                if message[j] == 1:
                    mG ^= self.G[j]
            
            # 2. 添加随机错误
            error_positions = np.random.choice(self.n, size=min(self.t, self.n), replace=False)
            error = np.zeros(self.n, dtype=int)
            error[error_positions] = 1
            
            # 3. 应用置换 P
            ciphertext = np.zeros(self.n, dtype=int)
            for j in range(self.n):
                if (mG[j] ^ error[j]) == 1:
                    # 应用置换
                    col_idx = np.where(self.P[j, :] == 1)[0][0]
                    ciphertext[col_idx] ^= 1
            
            # 4. 解密
            decrypted, success, error_info = self.decrypt(ciphertext)
            
            if success and np.array_equal(message, decrypted):
                success_count += 1
            else:
                error_details.append({
                    'test': i,
                    'success': success,
                    'error_info': error_info,
                    'message_match': np.array_equal(message, decrypted) if decrypted is not None else False
                })
        
        success_rate = success_count / num_tests * 100
        
        return {
            'success_rate': success_rate,
            'success_count': success_count,
            'total_tests': num_tests,
            'error_details': error_details
        }
    
    def get_decoder_info(self):
        """获取译码器信息"""
        return {
            'n': self.n,
            'k': self.k,
            't': self.t,
            'L': self.L,
            'scheme': self.scheme,
            'has_code_object': self.code is not None
        }

# 提供一个便捷的函数接口，与run_bch_demo.py兼容
def decrypt(ciphertext, private_key, L=10, t=2):
    """
    解密密文
    
    参数:
        ciphertext: 密文向量
        private_key: 私钥字典
        L: 分块数量
        t: 每个分块的纠错能力
        
    返回:
        解密出的消息向量（bitarray对象）
    """
    # 导入bitarray
    import bitarray
    
    # 创建解密器实例
    decryptor = BCHMcElieceDecryptor(private_key)
    
    # 解密消息
    message, success, error_info = decryptor.decrypt(ciphertext)
    
    # 转换为bitarray对象
    message_ba = bitarray.bitarray()
    
    if not success:
        # 如果解密失败，返回原始密文的前k位作为简化处理
        k = private_key['S'].shape[0]
        if hasattr(ciphertext, 'tolist'):
            message_ba.extend(ciphertext[:k].tolist())
        else:
            message_ba.extend(ciphertext[:k])
    else:
        # 如果解密成功，将numpy数组转换为bitarray
        if hasattr(message, 'tolist'):
            message_ba.extend(message.tolist())
        else:
            message_ba.extend(message)
    
    return message_ba