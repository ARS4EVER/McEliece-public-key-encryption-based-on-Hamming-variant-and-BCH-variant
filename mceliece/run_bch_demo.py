#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分块BCH码McEliece变体演示脚本
方案：基于多个(15,7) BCH码级联（生成多项式g(x)=x^8 + x^7 + x^6 + x^4 + 1，纠错能力t=2）
分块数L可配置，示例L=10→总码长n=150，明文长度k=70
"""

import os
import sys
import time
import numpy as np
import bitarray

# 添加模块搜索路径，确保能找到code目录下的包
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

from bch_mceliece.bch_code import BCHCode  # 自定义BCH分块编码/译码模块
from bch_mceliece.keygen_bch import generate_bch_mceliece_keys  # 自定义密钥生成模块
from bch_mceliece.encrypt_bch import encrypt  # 自定义加密模块
from bch_mceliece.decrypt_bch import decrypt  # 自定义解密模块
from utils.security_estimator import estimate_security  # 安全估算模块

# -------------------------- 配置参数（可修改）--------------------------
L = 10  # 分块数（每个分块为(15,7) BCH码）
t = 2  # 每个BCH分块的纠错能力（总错误数≤L*t=20）
import random
random_seed = random.randint(1, 1000000)  # 随机生成种子
test_plaintext = "Hello_McEliece_BCH_2025"  # 测试明文（将转为二进制）
# ----------------------------------------------------------------------

def setup_random_seed(seed):
    """固定所有随机种子（numpy、os）"""
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def str_to_bitarray(s: str) -> bitarray.bitarray:
    """字符串转二进制比特数组（适配明文输入）"""
    ba = bitarray.bitarray()
    ba.frombytes(s.encode('utf-8'))
    return ba

def bitarray_to_str(ba: bitarray.bitarray) -> str:
    """二进制比特数组转字符串（适配明文输出）"""
    try:
        return ba.tobytes().decode('utf-8')
    except:
        return "解码失败（比特数组长度不匹配）"

def pad_plaintext(ba: bitarray.bitarray, k_total: int) -> bitarray.bitarray:
    """补齐明文至总明文长度k_total（分块数L×每个分块明文长度7）"""
    pad_len = k_total - (len(ba) % k_total)
    if pad_len != k_total:
        ba.extend([0]*pad_len)
    return ba[:k_total]  # 确保不超过总长度

def main():
    # 1. 初始化配置
    setup_random_seed(random_seed)
# 计算总码长和总明文长度
    k_per_block = 7  # 每个BCH分块的明文长度
    n_per_block = 15  # 每个BCH分块的码长
    k_total = L * k_per_block  # 总明文长度（70 bits）
    n_total = L * n_per_block  # 总码长（150 bits）
    t_total = L * t  # 总错误数（20 bits）
    print("="*60)
    print(f"分块BCH码McEliece演示（L={L}，(n,k,t)=({n_total},{k_total},{t})）")
    print(f"随机种子：{random_seed}")
    print(f"测试明文：{test_plaintext}")
    print("="*60)

    # 2. 准备明文（字符串→二进制→补齐至k_total bits）
    plaintext_ba = str_to_bitarray(test_plaintext)
    print(f"原始明文比特数：{len(plaintext_ba)}")
    plaintext_ba_padded = pad_plaintext(plaintext_ba, k_total)
    print(f"补齐后明文比特数：{len(plaintext_ba_padded)}")
    print(f"补齐后明文（二进制前20位）：{plaintext_ba_padded[:20].to01()}...")
    print("-"*60)

    # 3. 密钥生成（记录时间和尺寸）
    start_keygen = time.perf_counter()
    pub_key, priv_key = generate_bch_mceliece_keys(L=L, t=t)
    keygen_time = (time.perf_counter() - start_keygen) * 1000  # 转为ms

    # 计算密钥尺寸（字节）
    pub_key_size = len(pub_key.tobytes()) if isinstance(pub_key, bitarray.bitarray) else len(np.array(pub_key).tobytes())
    priv_key_size = len(priv_key["S"].tobytes()) + len(priv_key["P"].tobytes()) + len(priv_key["bch_params"])
    print("【密钥生成结果】")
    print(f"公钥尺寸：{pub_key_size} 字节")
    print(f"私钥尺寸：{priv_key_size} 字节")
    print(f"密钥生成时间：{keygen_time:.2f} ms")
    print("-"*60)

    # 4. 加密（记录时间）
    start_encrypt = time.perf_counter()
    ciphertext_ba = encrypt(plaintext_ba_padded, pub_key, t_total=L*t)
    encrypt_time = (time.perf_counter() - start_encrypt) * 1000  # 转为ms

    print("【加密结果】")
    print(f"密文比特数：{len(ciphertext_ba)}")
    print(f"密文扩张率：{len(ciphertext_ba)/len(plaintext_ba_padded):.2f}")
    print(f"加密时间：{encrypt_time:.2f} ms")
    print(f"密文（二进制前20位）：{ciphertext_ba[:20].to01()}...")
    print("-"*60)

    # 5. 解密（记录时间）
    start_decrypt = time.perf_counter()
    decrypted_ba = decrypt(ciphertext_ba, priv_key, L=L, t=t)
    decrypt_time = (time.perf_counter() - start_decrypt) * 1000  # 转为ms

    print("【解密结果】")
    print(f"解密后明文比特数：{len(decrypted_ba)}")
    print(f"解密时间：{decrypt_time:.2f} ms")
    decrypted_str = bitarray_to_str(decrypted_ba)
    print(f"解密后明文：{decrypted_str}")

    # 验证解密正确性
    is_success = (decrypted_ba == plaintext_ba_padded)
    print(f"解密成功率：{'100%' if is_success else '0%'}")
    print("="*60)

    # 6. 安全估算（不同攻击假设）
    print("\n【安全估算（不同攻击假设）】")
    security_results = estimate_security(n_total, k_total, t_total, code_type="bch")
    
    print(f"参数：码长={n_total}, 信息位={k_total}, 纠错能力={t_total}, 码类型=BCH")
    print("\n各攻击模型安全级别（比特）：")
    for attack_type, security_level in security_results["各攻击模型安全级别"].items():
        print(f"  {attack_type}: {security_level:.1f} 比特")
    
    print("\n安全摘要：")
    for metric, value in security_results["安全摘要"].items():
        print(f"  {metric}: {value:.1f} 比特")
    
    # 7. 输出汇总报告
    print("\n【演示汇总】")
    print(f"1. 密钥尺寸：公钥{pub_key_size}B / 私钥{priv_key_size}B")
    print(f"2. 时间性能：密钥生成{keygen_time:.2f}ms / 加密{encrypt_time:.2f}ms / 解密{decrypt_time:.2f}ms")
    print(f"3. 密文扩张率：{len(ciphertext_ba)/len(plaintext_ba_padded):.2f}")
    print(f"4. 解密成功率：{'100%' if is_success else '0%'}")
    print(f"5. 典型安全级别：{security_results['安全摘要']['典型安全级别']:.1f} 比特（基于Ball-Collision ISD攻击）")

if __name__ == "__main__":
    main()