#!/usr/bin/env python3
"""
McEliece变体性能测试脚本
"""

import argparse
import time
import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

# 添加模块搜索路径
sys.path.append(os.path.abspath('code'))

from hamming_mceliece.keygen_hamming import HammingMcElieceKeyGenerator
from hamming_mceliece.encrypt_hamming import HammingMcElieceEncryptor
from hamming_mceliece.decrypt_hamming import HammingMcElieceDecryptor
from bch_mceliece.keygen_bch import BCHMcElieceKeyGenerator
from bch_mceliece.encrypt_bch import BCHMcElieceEncryptor
from bch_mceliece.decrypt_bch import BCHMcElieceDecryptor
from utils.measurements import calculate_security_level, get_system_info

def benchmark_hamming(L=10, repeats=10):
    """汉明码变体性能测试"""
    print(f"测试汉明码变体 (L={L})...")
    
    results = []
    
    for i in tqdm(range(repeats)):
        # 固定种子但每次不同
        seed = 12345 + i
        np.random.seed(seed)
        
        # 记录时间
        times = {}
        
        # 1. 密钥生成
        start = time.time()
        keygen = HammingMcElieceKeyGenerator(L, random_seed=seed)
        public_key, private_key = keygen.generate_keys()
        times['keygen'] = time.time() - start
        
        # 获取密钥大小
        try:
            pub_size, priv_size = keygen.get_key_sizes()
        except TypeError:
            # 如果需要参数，则传递public_key和private_key
            pub_size, priv_size = keygen.get_key_sizes(public_key, private_key)
        
        # 2. 准备消息
        k = keygen.k if hasattr(keygen, 'k') else public_key['k']
        message = np.random.randint(0, 2, k)
        
        # 3. 加密
        start = time.time()
        encryptor = HammingMcElieceEncryptor(public_key)
        ciphertext, _ = encryptor.encrypt(message)
        times['encrypt'] = time.time() - start
        
        # 计算扩张率
        expansion_rate = len(ciphertext) / len(message)
        
        # 4. 解密
        start = time.time()
        decryptor = HammingMcElieceDecryptor(private_key)
        decrypted, _ = decryptor.decrypt(ciphertext)  # 从元组中提取消息
        times['decrypt'] = time.time() - start
        
        # 5. 验证
        is_correct = np.array_equal(message, decrypted)
        
        # 6. 收集结果
        n = keygen.n if hasattr(keygen, 'n') else public_key['n']
        k = keygen.k if hasattr(keygen, 'k') else public_key['k']
        t = 2
        security = calculate_security_level(n, k, t)
        
        # 收集结果
        result = {
            'scheme': 'Hamming',
            'L': L,
            'public_key_bytes': pub_size,
            'private_key_bytes': priv_size,
            'expansion_rate': expansion_rate,
            'security_bits': security,
            'decryption_success': int(is_correct),
            'keygen_time': times['keygen'],
            'encrypt_time': times['encrypt'],
            'decrypt_time': times['decrypt'],
            'seed': seed
        }
        
        results.append(result)
    
    return results

def benchmark_bch(L=10, repeats=10):
    """BCH码变体性能测试"""
    print(f"测试BCH码变体 (L={L})...")
    
    results = []
    
    for i in tqdm(range(repeats)):
        # 固定种子但每次不同
        seed = 12345 + i
        np.random.seed(seed)
        
        # 记录时间
        times = {}
        
        # 1. 密钥生成
        start = time.time()
        keygen = BCHMcElieceKeyGenerator(L)
        public_key, private_key = keygen.generate_keys(seed=seed)
        times['keygen'] = time.time() - start
        
        # 获取密钥大小
        try:
            pub_size, priv_size = keygen.get_key_sizes()
        except TypeError:
            # 如果需要参数，则传递public_key和private_key
            pub_size, priv_size = keygen.get_key_sizes(public_key, private_key)
        
        # 2. 准备消息
        k = keygen.k if hasattr(keygen, 'k') else public_key['k']
        message = np.random.randint(0, 2, k)
        
        # 3. 加密
        start = time.time()
        encryptor = BCHMcElieceEncryptor(public_key)
        ciphertext, _ = encryptor.encrypt(message)
        times['encrypt'] = time.time() - start
        
        # 计算扩张率
        expansion_rate = len(ciphertext) / len(message)
        
        # 4. 解密
        start = time.time()
        decryptor = BCHMcElieceDecryptor(private_key)
        decrypted, _, _ = decryptor.decrypt(ciphertext)  # 从元组中提取消息
        times['decrypt'] = time.time() - start
        
        # 5. 验证
        is_correct = np.array_equal(message, decrypted)
        
        # 6. 收集结果
        n = keygen.n if hasattr(keygen, 'n') else public_key['n']
        k = keygen.k if hasattr(keygen, 'k') else public_key['k']
        t = keygen.t if hasattr(keygen, 't') else public_key['t']
        security = calculate_security_level(n, k, t)
        
        # 收集结果
        result = {
            'scheme': 'BCH',
            'L': L,
            'public_key_bytes': pub_size,
            'private_key_bytes': priv_size,
            'expansion_rate': expansion_rate,
            'security_bits': security,
            'decryption_success': int(is_correct),
            'keygen_time': times['keygen'],
            'encrypt_time': times['encrypt'],
            'decrypt_time': times['decrypt'],
            'seed': seed
        }
        
        results.append(result)
    
    return results

def save_results(df, filename="results/performance_results.csv"):
    """保存结果到CSV文件"""
    df.to_csv(filename, index=False)
    print(f"结果已保存到 {filename}")
    
    # 打印统计摘要
    print("\n性能统计摘要:")
    print("=" * 60)
    
    for scheme in df['scheme'].unique():
        print(f"\n方案: {scheme}")
        scheme_df = df[df['scheme'] == scheme]
        
        print(f"  公钥大小: {scheme_df['public_key_bytes'].mean():.0f} ± {scheme_df['public_key_bytes'].std():.0f} 字节")
        print(f"  私钥大小: {scheme_df['private_key_bytes'].mean():.0f} ± {scheme_df['private_key_bytes'].std():.0f} 字节")
        print(f"  扩张率: {scheme_df['expansion_rate'].mean():.3f} ± {scheme_df['expansion_rate'].std():.3f}")
        print(f"  安全性: {scheme_df['security_bits'].mean():.1f} ± {scheme_df['security_bits'].std():.1f} 比特")
        print(f"  解密成功率: {scheme_df['decryption_success'].mean() * 100:.1f}%")
        print(f"  密钥生成时间: {scheme_df['keygen_time'].mean() * 1000:.2f} ± {scheme_df['keygen_time'].std() * 1000:.2f} ms")
        print(f"  加密时间: {scheme_df['encrypt_time'].mean() * 1000:.2f} ± {scheme_df['encrypt_time'].std() * 1000:.2f} ms")
        print(f"  解密时间: {scheme_df['decrypt_time'].mean() * 1000:.2f} ± {scheme_df['decrypt_time'].std() * 1000:.2f} ms")

def create_plots(df):
    """创建性能对比图表"""
    print("开始生成图表...")
    # 设置matplotlib支持中文
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    sns.set_style("whitegrid")
    
    # 1. 密钥大小对比
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x='scheme', y='public_key_bytes', data=df, 
                    hue='scheme', palette='viridis', errorbar='sd', legend=False)
    plt.title('公钥大小对比')
    plt.ylabel('字节数')
    plt.xlabel('方案')
    plt.tight_layout()
    plt.savefig('results/figures/public_key_size.png', dpi=300)
    
    # 2. 运行时间对比
    time_metrics = ['keygen_time', 'encrypt_time', 'decrypt_time']
    time_labels = ['密钥生成', '加密', '解密']
    
    plt.figure(figsize=(12, 6))
    
    for i, metric in enumerate(time_metrics):
        plt.subplot(1, 3, i+1)
        sns.barplot(x='scheme', y=metric, data=df, hue='scheme', palette='Set2', errorbar='sd', legend=False)
        plt.title(time_labels[i])
        plt.ylabel('时间 (秒)')
        plt.xlabel('方案')
    
    plt.tight_layout()
    plt.savefig('results/figures/execution_time.png', dpi=300)
    
    # 3. 安全性与扩张率对比
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # 安全性
    sns.barplot(x='scheme', y='security_bits', data=df, 
                hue='scheme', palette='coolwarm', errorbar='sd', legend=False, ax=ax1)
    ax1.set_title('安全性对比')
    ax1.set_ylabel('安全比特数')
    ax1.set_xlabel('方案')
    
    # 扩张率
    sns.barplot(x='scheme', y='expansion_rate', data=df, 
                hue='scheme', palette='coolwarm', errorbar='sd', legend=False, ax=ax2)
    ax2.set_title('密文扩张率对比')
    ax2.set_ylabel('扩张率')
    ax2.set_xlabel('方案')
    
    plt.tight_layout()
    plt.savefig('results/figures/security_expansion.png', dpi=300)
    
    # 4. 不同分块数量的影响
    if 'L' in df.columns and len(df['L'].unique()) > 1:
        plt.figure(figsize=(10, 6))
        
        for scheme in df['scheme'].unique():
            scheme_df = df[df['scheme'] == scheme]
            plt.plot(scheme_df['L'].unique(), 
                    scheme_df.groupby('L')['public_key_bytes'].mean(),
                    marker='o', label=scheme)
        
        plt.title('分块数量对公钥大小的影响')
        plt.xlabel('分块数量 (L)')
        plt.ylabel('公钥大小 (字节)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('results/figures/block_size_effect.png', dpi=300)
    
    print("所有图表已成功生成并保存到 results/figures/ 目录")

def main():
    parser = argparse.ArgumentParser(description="McEliece变体性能测试")
    parser.add_argument("--scheme", choices=["hamming", "bch", "all"], 
                       default="all", help="测试的方案")
    parser.add_argument("--blocks", type=int, nargs='+', default=[10, 20],
                       help="分块数量列表")
    parser.add_argument("--repeats", type=int, default=10,
                       help="每个配置重复次数")
    parser.add_argument("--seed", type=int, default=12345,
                       help="基础随机种子")
    
    args = parser.parse_args()
    
    # 打印系统信息
    print("系统信息:")
    print("=" * 60)
    sys_info = get_system_info()
    for key, value in sys_info.items():
        print(f"{key}: {value}")
    print("=" * 60)
    
    all_results = []
    
    # 运行测试
    for L in args.blocks:
        if args.scheme in ["hamming", "all"]:
            results = benchmark_hamming(L, args.repeats)
            all_results.extend(results)
        
        if args.scheme in ["bch", "all"]:
            results = benchmark_bch(L, args.repeats)
            all_results.extend(results)
    
    # 分析结果
    df = pd.DataFrame(all_results)
    
    # 保存结果
    save_results(df)
    
    # 创建图表
    create_plots(df)
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()