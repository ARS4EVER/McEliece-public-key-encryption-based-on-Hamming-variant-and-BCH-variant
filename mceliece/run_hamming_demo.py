#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分块汉明码McEliece变体演示脚本
方案：基于多个(7,4)汉明码级联
分块数L可配置，示例L=20→总码长n=140，明文长度k=80
"""

import os
import sys
import time
import random
import numpy as np
import bitarray

# 添加code目录到模块搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

from hamming_mceliece.keygen_hamming import generate_hamming_key, save_keys, load_public_key, load_private_key
from hamming_mceliece.encrypt_hamming import hamming_encrypt
from hamming_mceliece.decrypt_hamming import hamming_decrypt

# -------------------------- 配置参数（可修改）--------------------------
L = 20  # 分块数（每个分块为(15,11,3)汉明码）
t = 1  # 每个汉明分块的纠错能力（总错误数≤L*t=20）
random_seed = random.randint(1, 1000000)  # 随机生成种子
# 使用固定的测试明文
# 原始明文：Hello_McEliece_Hamming_2025（重复足够次数以达到220位）
# 当L=20时，每个分块11位，总信息位长度是11*20=220位
# 我们生成一个220位的二进制向量（随机生成，但使用固定种子确保可重复性）
# ----------------------------------------------------------------------

def setup_random_seed(seed):
    """固定所有随机种子（numpy、random）"""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def main():
    # 1. 初始化配置
    setup_random_seed(random_seed)
    
    # 计算总码长和总明文长度
    # 注意：(15,11,3)汉明码，每个分块11位信息位，15位码长
    k_per_block = 11  # 每个汉明分块的明文长度
    n_per_block = 15  # 每个汉明分块的码长
    k_total = L * k_per_block  # 总明文长度
    n_total = L * n_per_block  # 总码长
    
    print("="*60)
    print(f"分块汉明码McEliece演示（L={L}，(n,k,t)=({n_total},{k_total},{t})）")
    print(f"随机种子：{random_seed}")
    print("="*60)

    # 2. 准备明文（生成220位随机明文）
    plaintext = np.random.randint(0, 2, size=k_total, dtype=int)
    print(f"明文比特数：{len(plaintext)}")
    print(f"明文（二进制前20位）：{''.join(map(str, plaintext[:20]))}...")
    print("-"*60)

    # 3. 密钥生成（记录时间和尺寸）
    print("【密钥生成结果】")
    start_keygen = time.time()
    public_key, private_key = generate_hamming_key(L=L)
    save_keys(public_key, private_key, prefix="hamming")
    keygen_time = (time.time() - start_keygen) * 1000  # 转为ms

    # 计算密钥尺寸（字节）
    pub_key_size = public_key["G_prime"].nbytes
    priv_key_size = private_key["S"].nbytes + private_key["P"].nbytes
    print(f"公钥尺寸：{pub_key_size} 字节")
    print(f"私钥尺寸：{priv_key_size} 字节")
    print(f"密钥生成时间：{keygen_time:.2f} ms")
    print("-"*60)

    # 4. 加密（记录时间）
    print("【加密结果】")
    start_encrypt = time.time()
    ciphertext = hamming_encrypt(plaintext, public_key)
    encrypt_time = (time.time() - start_encrypt) * 1000  # 转为ms

    print(f"密文比特数：{len(ciphertext)}")
    print(f"密文扩张率：{len(ciphertext)/len(plaintext):.2f}")
    print(f"加密时间：{encrypt_time:.2f} ms")
    print(f"密文（二进制前20位）：{''.join(map(str, ciphertext[:20]))}...")
    print("-"*60)

    # 5. 解密（记录时间）
    print("【解密结果】")
    start_decrypt = time.time()
    decrypted_plaintext = hamming_decrypt(ciphertext, private_key)
    decrypt_time = (time.time() - start_decrypt) * 1000  # 转为ms

    print(f"解密后明文比特数：{len(decrypted_plaintext)}")
    print(f"解密时间：{decrypt_time:.2f} ms")
    
    # 验证解密正确性
    is_success = np.array_equal(decrypted_plaintext, plaintext)
    print(f"解密成功率：{'100%' if is_success else '0%'}")
    print("="*60)

    # 6. 输出汇总报告
    print("\n【演示汇总】")
    print(f"1. 密钥尺寸：公钥{pub_key_size}B / 私钥{priv_key_size}B")
    print(f"2. 时间性能：密钥生成{keygen_time:.2f}ms / 加密{encrypt_time:.2f}ms / 解密{decrypt_time:.2f}ms")
    print(f"3. 密文扩张率：{len(ciphertext)/len(plaintext):.2f}")
    print(f"4. 解密成功率：{'100%' if is_success else '0%'}")
    # 估算安全性
    security_estimate = 2 * t * np.log2(n_total)
    print(f"5. 安全性估算：{security_estimate:.1f} 比特（基于错误数×码长对数模型）")

if __name__ == "__main__":
    main()