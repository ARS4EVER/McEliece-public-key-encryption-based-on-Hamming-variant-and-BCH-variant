import random
from typing import List, Sequence, Tuple

BitVector = List[int]
Matrix = List[List[int]]


def bits_to_int(bits: Sequence[int]) -> int:
    val = 0
    for i, b in enumerate(bits):
        if b & 1:
            val |= 1 << i
    return val


def int_to_bits(value: int, length: int) -> BitVector:
    return [(value >> i) & 1 for i in range(length)]


def parity(x: int) -> int:
    return bin(x).count("1") & 1


def mat_identity(n: int) -> Matrix:
    return [int_to_bits(1 << i, n) for i in range(n)]


def mat_inv(mat: Matrix) -> Matrix:
    n = len(mat)
    assert all(len(row) == n for row in mat), "矩阵必须为方阵"
    A = [row[:] for row in mat]
    I = mat_identity(n)
    for col in range(n):
        pivot = None
        for r in range(col, n):
            if A[r][col]:
                pivot = r
                break
        if pivot is None:
            raise ValueError("矩阵不可逆")
        if pivot != col:
            A[col], A[pivot] = A[pivot], A[col]
            I[col], I[pivot] = I[pivot], I[col]
        for r in range(n):
            if r != col and A[r][col]:
                for c in range(n):
                    A[r][c] ^= A[col][c]
                    I[r][c] ^= I[col][c]
    return I


def mat_mul(A: Matrix, B: Matrix) -> Matrix:
    k, m = len(A), len(A[0])
    assert len(B) == m
    n = len(B[0])
    res = [[0] * n for _ in range(k)]
    # 预计算 B 列向量
    cols = []
    for j in range(n):
        col_mask = 0
        for i in range(m):
            if B[i][j]:
                col_mask |= 1 << i
        cols.append(col_mask)
    for r in range(k):
        row_mask = bits_to_int(A[r])
        for c in range(n):
            res[r][c] = parity(row_mask & cols[c])
    return res


def mat_vec_mul(vec: BitVector, mat: Matrix) -> BitVector:
    assert len(vec) == len(mat)
    n = len(mat[0])
    res = [0] * n
    cols = []
    for j in range(n):
        col_mask = 0
        for i in range(len(vec)):
            if mat[i][j]:
                col_mask |= 1 << i
        cols.append(col_mask)
    row_mask = bits_to_int(vec)
    for j in range(n):
        res[j] = parity(row_mask & cols[j])
    return res


def random_invertible_matrix(size: int) -> Matrix:
    while True:
        mat = [[random.randint(0, 1) for _ in range(size)] for _ in range(size)]
        try:
            _ = mat_inv(mat)
            return mat
        except ValueError:
            continue


def random_permutation(n: int) -> List[int]:
    perm = list(range(n))
    random.shuffle(perm)
    return perm


def apply_permutation(vec: BitVector, perm: Sequence[int]) -> BitVector:
    return [vec[perm[i]] for i in range(len(perm))]


def apply_permutation_matrix(mat: Matrix, perm: Sequence[int]) -> Matrix:
    return [[row[j] for j in perm] for row in mat]


def pack_bits(bits: Sequence[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits) and bits[i + j]:
                byte |= 1 << j
        out.append(byte)
    return bytes(out)


def unpack_bits(data: bytes, length: int) -> BitVector:
    bits: BitVector = []
    for byte in data:
        for j in range(8):
            bits.append((byte >> j) & 1)
            if len(bits) == length:
                return bits
    return bits[:length]


def weight(vec: Sequence[int]) -> int:
    return sum(1 for b in vec if b)

