# McEliece 变体项目使用指南 (README)

本项目实现了基于 Hamming 码和 BCH 码的 McEliece 密码系统变体，并提供了基准测试脚本以评估其性能。

## 1. 环境依赖 (Dependencies)

在运行代码之前，请确保安装以下 Python 库：

- **Python 版本**: 3.8+ (建议)
- **必需库**:
  - `matplotlib >= 3.5.0` (用于绘制基准测试图表)
  - `psutil >= 5.9.0` (用于获取系统内存信息)

**安装命令**:

Bash

```
pip install -r infomation/requirements.txt
```

或者手动安装：

Bash

```
pip install matplotlib psutil
```

## 2. 如何复现实验 (Reproduction)

本项目包含三个主要的可执行脚本，分别用于演示和性能基准测试。请在项目根目录下运行以下命令（确保 `infomation` 文件夹在您的 Python 路径中，或者直接在父目录运行）。

### 2.1 运行基准测试 (Benchmark)

此脚本会对比 Hamming 和 BCH 变体的密钥生成、加解密耗时、密钥大小及密文扩张率，并生成可视化图表 `benchmark_results.png`。

**示例命令**:

Bash

```
python infomation/run_benchmark.py
```

- **输出**: 控制台将打印详细的性能数据（毫秒级耗时、安全性估算位），并在当前目录生成对比图表。

### 2.2 运行功能演示 (Demo)

验证加密和解密流程的正确性。

- **Hamming 变体演示**:

  Bash

  ```
  python infomation/run_hamming_demo.py
  ```

  输出示例: `Hamming demo -> 成功: True 消息一致: True`

- **BCH 变体演示**:

  Bash

  ```
  python infomation/run_bch_demo.py
  ```

  输出示例: `BCH demo -> 成功: True 消息一致: True`

## 3. 参数说明 (Key Parameters)

系统支持通过修改脚本中的参数来调整安全级别和性能。

### 通用参数 (在 `run_benchmark.py` 或 Demo 中修改)

- **`L` (Blocks)**: 分块数量。
  - 作用：决定了总的码长 $N$ 和信息位 $K$。总码长 = 单块长度 $\times L$。
  - 示例：在 `run_benchmark.py` 中设置 `L=10`。
- **`trials`**: 测试循环次数。增加此数值可获得更稳定的平均耗时。

### 变体特定参数

1. **HammingMcEliece**
   - **基底**: (15, 11) Hamming 码。
   - **`errors_per_block`**: 每块纠错能力。默认为 **1** (Hamming 码的理论上限)。
   - **`n` (总码长)**: $15 \times L$
   - **`k` (信息位)**: $11 \times L$
2. **BCHMcEliece**
   - **基底**: (15, 7) BCH 码。
   - **`errors_per_block`**: 每块纠错能力。默认为 **2** (BCH(15,7) 的设计能力)。
   - **`n` (总码长)**: $15 \times L$
   - **`k` (信息位)**: $7 \times L$

## 4. 随机种子固定 (Reproducibility)

为了确保实验结果（生成的密钥、错误向量等）可重复，代码支持传入指定的随机数生成器实例或设置全局种子。

### 设置全局种子

在运行脚本 (`run_benchmark.py` 等) 的最开始添加以下代码：

Python

```
import random
random.seed(42)  
```

由于 `HammingMcEliece` 和 `BCHMcEliece` 的构造函数默认参数为 `rng=random`，设置全局种子即可生效。
