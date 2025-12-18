# McEliece 分块变体实现说明

## 目录结构
- `code/gf2.py`：GF(2) 工具与矩阵运算。
- `code/hamming_mceliece/hamming_code.py`：分块 Hamming(15,11) 方案（编码/译码、密钥生成、加密/解密）。
- `code/bch_mceliece/bch_code.py`：分块 BCH(15,7,t=2) 方案（编码/译码、密钥生成、加密/解密）。
- `run_hamming_demo.py`：Hamming 方案快速演示。
- `run_bch_demo.py`：BCH 方案快速演示。
- `run_benchmark.py`：统一基准测试，统计均值与标准差。
- `requirements.txt`：依赖。

## 参数选择与匹配策略
- Hamming 分块：单块 (15,11)，纠错能力 t=1；级联 L 块得到 (15L, 11L)，保持每块注入 ≤1 比特错误以保证可纠错。
- BCH 分块：单块 (15,7)，生成多项式 g(x)=x^8+x^7+x^6+x^4+1，t=2；级联 L 块得到 (15L, 7L)，每块注入 ≤2 比特错误。
- McEliece 混淆：随机可逆矩阵 S 混淆生成矩阵，随机置换 P 混淆列；公钥为 G_pub = S·G·P，私钥包含 S⁻¹、P⁻¹ 及译码表。

## 环境
Python 3.9+（测试于 3.13.2）。依赖见 requirements.txt（仅可选 psutil 用于显示内存）。

## 快速运行
```bash
python run_hamming_demo.py
python run_bch_demo.py
python run_benchmark.py  # 默认每项 20 次，含均值/标准差
```

## 基准输出指标
- 公钥/私钥尺寸（字节）
- 密文扩张率（密文比特长度 / 明文比特长度）
- 密钥生成、加密、解密时间的均值与标准差（ms）
- 解密成功率
- 安全性估计：log2 C(n, t_total) 作为枚举错误位置的复杂度下界（粗略）

## 模块接口示例
```python
from code.hamming_mceliece.hamming_code import HammingMcEliece
scheme = HammingMcEliece(L=10, errors_per_block=1)
pub, priv = scheme.keygen()
msg = [0,1]* (pub.k//2)
cipher = scheme.encrypt(msg, pub)
plain, ok = scheme.decrypt(cipher, pub, priv)
```

## 备注
- 译码：Hamming 使用综合单比特纠错；BCH 使用预计算综合表（权重 ≤ t）并做余式判定。
- 安全性估计仅为理论枚举复杂度，未考虑结构化码的潜在弱化。实际安全强度需更大参数。***

