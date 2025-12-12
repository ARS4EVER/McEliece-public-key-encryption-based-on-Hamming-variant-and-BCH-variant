# McEliece密码系统性能指标计算逻辑

本文档详细解释了`performance_results.csv`中每个性能指标的计算方法和逻辑。

## 1. 方案名称 (scheme)
- **定义**：使用的加密方案类型
- **值**：`Hamming`（汉明码变体）或`BCH`（BCH码变体）
- **计算逻辑**：直接由测试函数指定，在`benchmark_hamming`和`benchmark_bch`函数中硬编码

## 2. 分块数量 (L)
- **定义**：用于构造McEliece密码系统的码分块数量
- **值**：测试时指定的整数（如10, 20等）
- **计算逻辑**：作为函数参数传递给测试函数，影响码的总长度和信息位长度

## 3. 公钥大小 (public_key_bytes)
- **定义**：公钥的存储空间大小（以字节为单位）

### 汉明码变体实现
```python
def get_key_sizes(self, public_key, private_key):
    G_prime_size = public_key['G_prime'].nbytes  # 使用numpy数组的nbytes属性
    public_key_size = G_prime_size + 24  # 加上t, n, k的存储
    return public_key_size, private_key_size
```

### BCH码变体实现
```python
def get_key_sizes(self):
    public_key_bytes = self.k * self.n // 8  # 计算二进制位数并转换为字节
    return public_key_bytes, private_key_bytes
```

- **差异**：汉明码使用numpy的`nbytes`属性（基于数据类型），BCH码使用二进制位数除以8的手动计算

## 4. 私钥大小 (private_key_bytes)
- **定义**：私钥的存储空间大小（以字节为单位）

### 汉明码变体实现
```python
def get_key_sizes(self, public_key, private_key):
    S_inv_size = private_key['S_inv'].nbytes
    G_size = private_key['G'].nbytes
    P_size = private_key['P'].nbytes
    private_key_size = S_inv_size + G_size + P_size + 100  # 加上其他参数
    return public_key_size, private_key_size
```

### BCH码变体实现
```python
def get_key_sizes(self):
    private_key_bytes = (self.k*self.k + self.k*self.n + self.n*self.n + self.k*self.k) // 8
    return public_key_bytes, private_key_bytes
```

- **差异**：汉明码使用numpy数组的`nbytes`属性，BCH码使用二进制位数总和除以8的手动计算

## 5. 扩张率 (expansion_rate)
- **定义**：密文长度与明文长度的比值
- **计算公式**：`expansion_rate = len(ciphertext) / len(message)`
- **实现位置**：在`benchmark_hamming`和`benchmark_bch`函数中计算

## 6. 安全级别 (security_bits)
- **定义**：基于信息集解码攻击的安全级别估算（以比特为单位）
- **计算逻辑**：使用`utils.measurements.calculate_security_level`函数

```python
def calculate_security_level(n, k, t):
    # 信息集解码攻击的计算复杂度近似为 C(n, t) * 2^(k - sqrt(ktn))
    if t == 0:
        log_c = 0
    else:
        # 使用斯特林公式近似计算组合数的对数
        log_n_fact = n * np.log2(n) - n
        log_t_fact = t * np.log2(t) - t
        log_nt_fact = (n-t) * np.log2(n-t) - (n-t)
        log_c = log_n_fact - log_t_fact - log_nt_fact
    
    # 计算指数部分
    exponent = k - np.sqrt(k * t * n)
    if exponent < 0:
        exponent = 0
    
    # 总复杂度
    total_complexity = log_c + exponent
    
    return max(0, total_complexity)
```

- **参数**：
  - `n`：码长
  - `k`：信息位长度
  - `t`：纠错能力（汉明码固定为2，BCH码由码参数决定）

## 7. 解密成功率 (decryption_success)
- **定义**：解密后消息与原始消息是否一致的标志
- **计算公式**：`is_correct = np.array_equal(message, decrypted)`
- **值**：1表示成功，0表示失败
- **实现位置**：在`benchmark_hamming`和`benchmark_bch`函数中计算

## 8. 密钥生成时间 (keygen_time)
- **定义**：生成公钥和私钥所需的时间
- **计算逻辑**：使用`time.time()`记录开始和结束时间的差值

```python
start = time.time()
keygen = HammingMcElieceKeyGenerator(L, random_seed=seed)
public_key, private_key = keygen.generate_keys()
times['keygen'] = time.time() - start
```

- **单位**：秒（在CSV中存储原始值，打印时转换为毫秒）

## 9. 加密时间 (encrypt_time)
- **定义**：加密消息所需的时间
- **计算逻辑**：使用`time.time()`记录开始和结束时间的差值

```python
start = time.time()
encryptor = HammingMcElieceEncryptor(public_key)
ciphertext, _ = encryptor.encrypt(message)
times['encrypt'] = time.time() - start
```

- **单位**：秒（在CSV中存储原始值，打印时转换为毫秒）

## 10. 解密时间 (decrypt_time)
- **定义**：解密密文所需的时间
- **计算逻辑**：使用`time.time()`记录开始和结束时间的差值

```python
start = time.time()
decryptor = HammingMcElieceDecryptor(private_key)
decrypted = decryptor.decrypt(ciphertext)
times['decrypt'] = time.time() - start
```

- **单位**：秒（在CSV中存储原始值，打印时转换为毫秒）

## 11. 随机种子 (seed)
- **定义**：测试中使用的随机种子，确保结果可复现
- **值**：从12345开始，每次测试递增1
- **计算逻辑**：`seed = 12345 + i`（i为测试迭代次数）

## 性能统计摘要生成

在`save_results`函数中，对每个方案的结果进行统计分析：

```python
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
```

- **统计方法**：
  - 均值：`mean()`
  - 标准差：`std()`
  - 单位转换：时间从秒转换为毫秒（乘以1000）
  - 百分比转换：解密成功率从0/1转换为百分比（乘以100）

## 汉明码与BCH码的主要差异

1. **密钥大小计算方法**：
   - 汉明码：使用numpy数组的`nbytes`属性，基于数据类型
   - BCH码：手动计算二进制位数并转换为字节

2. **纠错能力**：
   - 汉明码：固定为t=2
   - BCH码：由码参数决定，通常更高（如t=5）

3. **安全级别**：
   - BCH码变体在相同参数下通常提供更高的安全级别
   - 汉明码变体的密钥大小显著大于BCH码变体

4. **性能**：
   - BCH码变体通常在密钥大小和安全性方面表现更好
   - 汉明码变体实现相对简单