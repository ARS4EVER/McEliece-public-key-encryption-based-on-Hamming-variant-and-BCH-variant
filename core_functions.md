# 项目核心函数伪代码

## 1. 分块级联生成矩阵 (Block Generator)

### 函数签名
```
block_generator(L: int) -> Matrix
```

### 功能描述
生成分块级联McEliece密码系统的生成矩阵，将小码长的纠错码（如Hamming(15,11)、BCH(15,7)）通过分块对角生成矩阵扩展为大规模密码系统。

### 伪代码
```
function block_generator(L):
    // 获取基础码生成矩阵 G_b (k_b × n_b)
    base = base_generator()
    k_b = 基础码信息位长度
    n_b = 基础码码长
    
    // 计算总信息位长度 k 和总码长 n
    k = L × k_b
    n = L × n_b
    
    // 初始化全零的分块对角生成矩阵 G (k × n)
    G = [[0] * n for _ in [0..k-1]]
    
    // 填充分块对角矩阵
    for blk in [0..L-1]:
        for r in [0..k_b-1]:
            row_idx = blk × k_b + r  // 当前行在总矩阵中的索引
            
            // 将基础码的当前行复制到总矩阵的对应分块位置
            for c, v in enumerate(base[r]):
                col_idx = blk × n_b + c  // 当前列在总矩阵中的索引
                G[row_idx][col_idx] = v
    
    return G
```

### 数学原理
分块对角生成矩阵的构造满足：
$$G = \begin{pmatrix} G_b & 0 & \cdots & 0 \\ 0 & G_b & \cdots & 0 \\ \vdots & \vdots & \ddots & \vdots \\ 0 & 0 & \cdots & G_b \end{pmatrix}$$

其中，$G_b$ 是基础码生成矩阵，维度为 $k_b \times n_b$，L 是分块数。总生成矩阵 G 的维度为 $(Lk_b) \times (Ln_b)$。

## 2. 密钥生成 (Key Generation)

### 函数签名
```
keygen() -> Tuple[PublicKey, PrivateKey]
```

### 功能描述
生成McEliece密码系统的公钥和私钥对，包括生成混淆矩阵S、置换矩阵P以及它们的逆矩阵。

### 伪代码
```
function keygen():
    // 生成随机可逆混淆矩阵 S (k × k)
    S = random_invertible_matrix(k)
    S_inv = matrix_inverse(S)  // 计算 S 的逆矩阵
    
    // 生成随机置换矩阵 P (n × n)
    P = random_permutation(n)
    P_inv = inverse_permutation(P)  // 计算 P 的逆置换
    
    // 计算公钥生成矩阵：G_pub = S × G × P
    G_pub = apply_permutation_matrix(matrix_multiply(S, G), P)
    
    // 构建公钥和私钥对象
    public_key = PublicKey(G_pub, n, k, L, errors_per_block, P)
    private_key = PrivateKey(S_inv, P_inv, syndrome_table, L, errors_per_block)
    
    return (public_key, private_key)
```

## 3. 加密 (Encryption)

### 函数签名
```
encrypt(m_bits: BitVector, pub: PublicKey) -> BitVector
```

### 功能描述
使用公钥对明文进行加密，生成密文。

### 伪代码
```
function encrypt(m_bits, public_key):
    // 检查明文长度是否符合要求
    if len(m_bits) != public_key.k:
        raise ValueError("明文长度必须为 k")
    
    // 计算 u = m × G_pub
    u = matrix_vector_multiply(m_bits, public_key.G_pub)
    
    // 生成错误向量 e (每块 t_b 个错误)
    e_private = generate_error_vector(public_key.n, public_key.L, public_key.errors_per_block)
    
    // 使用置换矩阵 P 打乱错误向量位置
    e_public = apply_permutation(e_private, public_key.P)
    
    // 生成密文：c = u + e
    c = [u[i] XOR e_public[i] for i in [0..public_key.n-1]]
    
    return c
```

## 4. 解密 (Decryption)

### 函数签名
```
decrypt(c_bits: BitVector, pub: PublicKey, priv: PrivateKey) -> Tuple[BitVector, bool]
```

### 功能描述
使用私钥对密文进行解密，恢复明文。

### 伪代码
```
function decrypt(c_bits, public_key, private_key):
    // 检查密文长度是否符合要求
    if len(c_bits) != public_key.n:
        raise ValueError("密文长度必须为 n")
    
    // 使用逆置换矩阵 P_inv 恢复原始错误向量位置
    c_perm = apply_permutation(c_bits, private_key.P_inv)
    
    // 分块解码
    decoded = []
    success = true
    for blk in [0..public_key.L-1]:
        // 提取当前分块
        block = c_perm[blk × n_b : (blk + 1) × n_b]
        
        // 解码当前分块
        msg_block, ok = decode_block(block, private_key.syndrome_table)
        decoded.extend(msg_block)
        success = success AND ok
    
    // 使用逆混淆矩阵 S_inv 恢复原始明文
    m = matrix_vector_multiply(decoded, private_key.S_inv)
    
    return (m, success)
```

## 5. MMT 算法 (Information Set Decoding)

### 函数签名
```
isd_mmt(G_pub: Matrix, c: BitVector, t: int, max_iter: int = 100000) -> Tuple[BitVector, bool, int]
```

### 功能描述
使用MMT算法进行信息集译码攻击，尝试恢复密文中的错误向量。

### 伪代码
```
function isd_mmt(G_pub, c, t, max_iter):
    k = G_pub的行数  // 信息位长度
    n = G_pub的列数  // 码长
    
    for attempt in [1..max_iter]:
        // 1. 随机选取 k 个列索引作为信息集 I
        I = random_sample(range(n), k)
        J = 所有不在 I 中的列索引
        m = len(J)  // 校验位长度
        
        // 2. 提取子矩阵 G_I 和 G_J
        G_I = get_submatrix(G_pub, I)
        G_J = get_submatrix(G_pub, J)
        
        // 3. 计算 G_I 的逆矩阵
        try:
            G_I_inv = matrix_inverse(G_I)
        except:
            continue  // 矩阵不可逆，跳过本次尝试
        
        // 4. 计算 G_J' = G_I^{-1} × G_J
        G_J_prime = matrix_multiply(G_I_inv, G_J)
        
        // 5. 划分密文向量 c
        c_I = get_subvector(c, I)
        c_J = get_subvector(c, J)
        
        // 6. 计算 c' = G_I^{-1} × c_I
        c_prime = matrix_vector_multiply(G_I_inv, c_I)
        
        // 7. 将错误向量拆分：I = A ∪ B，J = C ∪ D
        split_k = k // 2
        A_indices = I[0..split_k-1]
        B_indices = I[split_k..k-1]
        
        split_m = m // 2
        C_indices = J[0..split_m-1]
        D_indices = J[split_m..m-1]
        
        // 8. 生成所有可能的 e_A 和 e_B
        for t_A in [0..min(t, split_k)]:
            for t_B in [0..min(t - t_A, k - split_k)]:
                t_C = 0
                t_D = t - t_A - t_B
                
                // 生成重量为 t_A 的所有 e_A
                e_A_candidates = generate_error_vectors(split_k, t_A)
                
                // 生成重量为 t_B 的所有 e_B
                e_B_candidates = generate_error_vectors(k - split_k, t_B)
                
                // 生成列表 A
                list_A = []
                for e_A in e_A_candidates:
                    key_A = compute_key(e_A, G_J_prime, c_prime, C_indices)
                    list_A.append((key_A, e_A))
                
                // 生成列表 B
                list_B = []
                for e_B in e_B_candidates:
                    key_B = compute_key(e_B, G_J_prime, c_prime, D_indices)
                    list_B.append((key_B, e_B))
                
                // 9. 查找碰撞
                for key_B, e_B in list_B:
                    if key_B in list_A:
                        e_A = list_A[key_B]
                        
                        // 10. 构建完整的错误向量 e
                        e = reconstruct_error_vector(e_A, e_B, I, J, G_J_prime, c)
                        
                        // 11. 验证错误向量重量是否为 t
                        if weight(e) == t:
                            // 12. 恢复明文 m
                            m = recover_message(e, c, G_pub)
                            return (m, true, attempt)
    
    return ([], false, max_iter)
```

## 6. 错误向量生成

### 函数签名
```
generate_error_vectors(n: int, t: int) -> List[BitVector]
```

### 功能描述
生成所有重量为 t 的错误向量。

### 伪代码
```
function generate_error_vectors(n, t):
    result = []
    current = []
    
    function backtrack(pos, remaining):
        if remaining == 0:
            // 生成完整的错误向量
            vec = [0] * n
            for idx in current:
                vec[idx] = 1
            result.append(vec)
            return
        
        if pos + remaining > n:
            return
        
        // 选择当前位置
        current.append(pos)
        backtrack(pos + 1, remaining - 1)
        current.pop()
        
        // 不选择当前位置
        backtrack(pos + 1, remaining)
    
    backtrack(0, t)
    return result
```

## 7. GF(2) 矩阵求逆

### 函数签名
```
mat_inv(mat: Matrix) -> Matrix
```

### 功能描述
计算GF(2)上的矩阵逆，使用高斯-约当消元法。

### 伪代码
```
function mat_inv(mat):
    n = mat的行数
    assert mat是方阵
    
    // 创建矩阵副本和单位矩阵
    A = 复制(mat)
    I = identity_matrix(n)
    
    for col in [0..n-1]:
        // 查找主元
        pivot = None
        for r in [col..n-1]:
            if A[r][col] == 1:
                pivot = r
                break
        
        if pivot is None:
            raise ValueError("矩阵不可逆")
        
        // 交换行
        if pivot != col:
            swap(A[col], A[pivot])
            swap(I[col], I[pivot])
        
        // 消元
        for r in [0..n-1]:
            if r != col and A[r][col] == 1:
                A[r] = A[r] XOR A[col]
                I[r] = I[r] XOR I[col]
    
    return I
```

## 8. GF(2) 矩阵向量乘法

### 函数签名
```
mat_vec_mul(vec: BitVector, mat: Matrix) -> BitVector
```

### 功能描述
计算GF(2)上的矩阵向量乘法。

### 伪代码
```
function mat_vec_mul(vec, mat):
    assert len(vec) == mat的行数
    
    result = [0] * mat的列数
    
    for j in [0..mat的列数-1]:
        dot = 0
        for i in [0..len(vec)-1]:
            dot ^= vec[i] & mat[i][j]
        result[j] = dot
    
    return result
```

## 9. 向量重量计算

### 函数签名
```
weight(vec: BitVector) -> int
```

### 功能描述
计算二进制向量的汉明重量（非零元素的个数）。

### 伪代码
```
function weight(vec):
    count = 0
    for bit in vec:
        if bit == 1:
            count += 1
    return count
```

## 10. 分块级联策略的数学原理解释

### 分块级联生成矩阵
分块级联策略通过将L个小码长的纠错码（如Hamming(15,11)、BCH(15,7)）通过分块对角生成矩阵扩展为大规模密码系统，其生成矩阵形式为：

$$G = \begin{pmatrix} G_b & 0 & \cdots & 0 \\ 0 & G_b & \cdots & 0 \\ \vdots & \vdots & \ddots & \vdots \\ 0 & 0 & \cdots & G_b \end{pmatrix}$$

其中，$G_b$ 是基础码生成矩阵，维度为 $k_b \times n_b$，L 是分块数。总生成矩阵 G 的维度为 $(Lk_b) \times (Ln_b)$。

### 总纠错能力
分块级联密码系统的总纠错能力为：

$$t = L \times t_b$$

其中，$t_b$ 是每个基础码的纠错能力。

### 安全性分析
分块级联策略的安全性主要来自于错误向量的分布特性，攻击者需要在L个分块中找到总重量为t的错误向量，这大大增加了攻击的难度。

### 性能优势
分块级联策略允许分块独立解码，每个分块可以并行处理，提高了解密效率。同时，使用小码长的基础码可以简化解码算法的实现。