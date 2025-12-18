import os
import sys
import statistics
import platform
import time
import math

# 尝试导入 matplotlib，如果失败则只打印文本提示
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("[提示] 未检测到 matplotlib，将跳过图表生成。建议安装: pip install matplotlib")

sys.path.append(os.path.dirname(__file__))
from code.hamming_mceliece.hamming_code import HammingMcEliece  # noqa: E402
from code.bch_mceliece.bch_code import BCHMcEliece  # noqa: E402

def log2_comb(n: int, k: int) -> float:
    """辅助函数：计算 log2(C(n, k))，即组合数的比特数"""
    if k < 0 or k > n:
        return 0.0
    return math.log2(math.comb(n, k))

def estimate_security(n: int, k: int, t: int) -> dict:
    """
    估算不同攻击假设下的安全性（比特）
    """
    if t <= 0:
        return {"Enum": 0.0, "ISD_Prange": 0.0}
    
    # --- 假设 1: 暴力枚举 (Enumeration) ---
    sec_enum = log2_comb(n, t)
    
    # --- 假设 2: 信息集译码 (ISD - Prange算法) ---
    if n - k >= t:
        term_denom = log2_comb(n - k, t)
        sec_isd = max(0.0, sec_enum - term_denom)
    else:
        sec_isd = 0.0

    return {
        "Enum": round(sec_enum, 1),       # 暴力枚举安全性
        "ISD_Prange": round(sec_isd, 1)   # Prange攻击安全性 (推荐参考值)
    }

def env_info() -> str:
    cpu = platform.processor() or "unknown CPU"
    py = platform.python_version()
    cores = os.cpu_count() or 1
    mem = "unknown"
    try:
        import psutil
        mem = f"{round(psutil.virtual_memory().total / (1024**3), 1)} GB"
    except Exception:
        pass
    return f"CPU: {cpu}, cores: {cores}, RAM: {mem}, Python: {py}, OS: {platform.platform()}"

def plot_results(results):
    """
    绘制基准测试结果图表
    """
    if not HAS_MATPLOTLIB:
        return

    # 简化名称用于图表显示
    names = [r["name"].replace(" 分块 McEliece", "").replace(" 分块", "") for r in results]
    
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('McEliece Variants Benchmark Results', fontsize=16)
    
    # 子图1: 运行时间 (ms)
    ax = axs[0, 0]
    x = range(len(names))
    width = 0.25
    
    # 提取时间数据
    keys = [r["key_avg_ms"] for r in results]
    encs = [r["enc_avg_ms"] for r in results]
    decs = [r["dec_avg_ms"] for r in results]
    
    # 提取标准差用于误差棒
    key_err = [r["key_std_ms"] for r in results]
    enc_err = [r["enc_std_ms"] for r in results]
    dec_err = [r["dec_std_ms"] for r in results]

    ax.bar([i - width for i in x], keys, width, label='KeyGen', yerr=key_err, capsize=5)
    ax.bar([i for i in x], encs, width, label='Encrypt', yerr=enc_err, capsize=5)
    ax.bar([i + width for i in x], decs, width, label='Decrypt', yerr=dec_err, capsize=5)
    
    ax.set_ylabel('Time (ms)')
    ax.set_title('Operation Latency (Mean & Std Dev)')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 子图2: 密钥尺寸 (Bytes)
    ax = axs[0, 1]
    ax.bar([i - 0.2 for i in x], [r["pk_size"] for r in results], 0.4, label='Public Key', color='#1f77b4')
    ax.bar([i + 0.2 for i in x], [r["sk_size"] for r in results], 0.4, label='Private Key', color='#ff7f0e')
    ax.set_ylabel('Size (Bytes)')
    ax.set_title('Key Sizes')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15)
    ax.legend()
    
    # 子图3: 安全性估算 (Bits)
    ax = axs[1, 0]
    ax.bar([i - 0.2 for i in x], [r["security"]["ISD_Prange"] for r in results], 0.4, label='ISD (Prange)', color='#d62728')
    ax.bar([i + 0.2 for i in x], [r["security"]["Enum"] for r in results], 0.4, label='Enumeration', color='#7f7f7f', alpha=0.6)
    ax.set_ylabel('Security Level (Bits)')
    ax.set_title('Security Estimation')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 子图4: 密文扩展率 & 成功率
    ax = axs[1, 1]
    ax2 = ax.twinx() # 双Y轴
    
    l1 = ax.bar(x, [r["expansion"] for r in results], 0.4, label='Expansion Rate', color='#9467bd')
    l2 = ax2.plot(x, [r["success_rate"]*100 for r in results], 'r-o', label='Success Rate (%)', linewidth=2)
    
    ax.set_ylabel('Expansion Ratio (Cipher/Msg)')
    ax2.set_ylabel('Success Rate (%)')
    ax2.set_ylim(0, 110)
    ax.set_title('Expansion & Reliability')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15)
    
    # 合并图例
    lines = [l1] + l2
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc='upper center')
    
    plt.tight_layout()
    plt.savefig('benchmark_results.png')
    print(f"\n[Info] 图表已保存至: {os.path.abspath('benchmark_results.png')}")

def measure(name, scheme_ctor, trials: int, message_bits: int):
    scheme = scheme_ctor()
    pub, priv = scheme.keygen()
    enc_times = []
    dec_times = []
    key_times = []
    success = 0
    
    # 获取用于估算的参数
    n = pub.n
    k = pub.k
    t = pub.errors_per_block * pub.L

    for _ in range(trials):
        t0 = time.perf_counter()
        # 注意：这里需要重新生成实例来测试 KeyGen 时间
        pub_i, priv_i = scheme_ctor().keygen()
        key_times.append(time.perf_counter() - t0)
        
        m = [int(os.urandom(1)[0] & 1) for _ in range(message_bits)]
        
        t1 = time.perf_counter()
        c = scheme.encrypt(m, pub)
        t2 = time.perf_counter()
        
        m2, ok = scheme.decrypt(c, pub, priv)
        t3 = time.perf_counter()
        
        enc_times.append(t2 - t1)
        dec_times.append(t3 - t2)
        if ok and m2 == m:
            success += 1

    pk_size = pub.serialize_size()
    sk_size = priv.serialize_size()
    expansion = len(c) / len(m) if len(m) > 0 else 0
    
    # 调用安全性估算
    sec = estimate_security(n, k, t)
    
    def stat(xs):
        return (statistics.mean(xs), statistics.pstdev(xs))

    key_avg, key_std = stat(key_times)
    enc_avg, enc_std = stat(enc_times)
    dec_avg, dec_std = stat(dec_times)

    print(f"\n=== {name} ===")
    print(f"参数: n={pub.n}, k={pub.k}, L={pub.L}, 每块注入错误={pub.errors_per_block}")
    print(f"公钥尺寸: {pk_size} 字节, 私钥尺寸: {sk_size} 字节")
    print(f"密文扩张率: {expansion:.2f}")
    print(f"密钥生成: 均值 {key_avg*1000:.2f} ms, 标准差 {key_std*1000:.2f} ms")
    print(f"加密: 均值 {enc_avg*1000:.2f} ms, 标准差 {enc_std*1000:.2f} ms")
    print(f"解密: 均值 {dec_avg*1000:.2f} ms, 标准差 {dec_std*1000:.2f} ms")
    print(f"解密成功率: {success}/{trials} = {success/trials*100:.2f}%")
    print("安全性估算 (Security Estimation)")
    print(f"1. 暴力枚举错误向量 (Enumeration):  {sec['Enum']} bits")
    print(f"   (假设攻击者只知道错误数量 t，直接猜测位置)")
    print(f"2. 信息集译码攻击 (ISD - Prange): {sec['ISD_Prange']} bits")
    print(f"   (标准的 McEliece 攻击基线，利用线性代数寻找无错信息集)")

    # 返回数据字典，供绘图使用
    return {
        "name": name,
        "n": n, "k": k, "t": t,
        "pk_size": pk_size,
        "sk_size": sk_size,
        "expansion": expansion,
        "key_avg_ms": key_avg * 1000, "key_std_ms": key_std * 1000,
        "enc_avg_ms": enc_avg * 1000, "enc_std_ms": enc_std * 1000,
        "dec_avg_ms": dec_avg * 1000, "dec_std_ms": dec_std * 1000,
        "success_rate": success / trials,
        "security": sec
    }

def main():
    trials = 20  
    print("测试环境:", env_info())
    
    results = [] # 用于存储所有测试结果
    
    results.append(measure(
        "Hamming(15,11) 分块 McEliece",
        lambda: HammingMcEliece(L=10, errors_per_block=1),
        trials=trials,
        message_bits=110,
    ))
    
    results.append(measure(
        "BCH(15,7,t=2) 分块 McEliece",
        lambda: BCHMcEliece(L=10, errors_per_block=2),
        trials=trials,
        message_bits=70,
    ))
    
    # 在最后统一生成图表
    plot_results(results)

if __name__ == "__main__":
    main()