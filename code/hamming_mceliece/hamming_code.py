import random
from dataclasses import dataclass
from typing import List, Tuple

from code.gf2 import (
    BitVector,
    Matrix,
    apply_permutation,
    apply_permutation_matrix,
    mat_inv,
    mat_mul,
    mat_vec_mul,
    pack_bits,
    random_invertible_matrix,
    random_permutation,
    weight,
)

# (15,11) Hamming 单块参数
PARITY_POS = [1, 2, 4, 8]
DATA_POS = [i for i in range(1, 16) if i not in PARITY_POS]


def encode_block(msg11: BitVector) -> BitVector:
    if len(msg11) != 11:
        raise ValueError("消息块必须 11 比特")
    code = [0] * 16  # 1-indexed
    for bit, pos in zip(msg11, DATA_POS):
        code[pos] = bit & 1
    p1 = sum(code[i] for i in range(1, 16) if i & 1) & 1
    p2 = sum(code[i] for i in range(1, 16) if i & 2) & 1
    p4 = sum(code[i] for i in range(1, 16) if i & 4) & 1
    p8 = sum(code[i] for i in range(1, 16) if i & 8) & 1
    code[1], code[2], code[4], code[8] = p1, p2, p4, p8
    return [code[i] for i in range(1, 16)]


def syndrome_decode_block(code15: BitVector) -> Tuple[BitVector, bool]:
    if len(code15) != 15:
        raise ValueError("码长必须 15 比特")
    code = [0] + code15[:]
    s1 = sum(code[i] for i in range(1, 16) if i & 1) & 1
    s2 = sum(code[i] for i in range(1, 16) if i & 2) & 1
    s4 = sum(code[i] for i in range(1, 16) if i & 4) & 1
    s8 = sum(code[i] for i in range(1, 16) if i & 8) & 1
    syn = s1 | (s2 << 1) | (s4 << 2) | (s8 << 3)
    corrected = False
    if syn and 1 <= syn <= 15:
        code[syn] ^= 1
        corrected = True
    msg = [code[pos] for pos in DATA_POS]
    return msg, corrected


def base_generator() -> Matrix:
    rows: Matrix = []
    for i in range(11):
        msg = [1 if j == i else 0 for j in range(11)]
        rows.append(encode_block(msg))
    return rows


def block_generator(L: int) -> Matrix:
    base = base_generator()
    k, n = 11 * L, 15 * L
    G = [[0] * n for _ in range(k)]
    for blk in range(L):
        for r in range(11):
            row_idx = blk * 11 + r
            for c, v in enumerate(base[r]):
                G[row_idx][blk * 15 + c] = v
    return G


@dataclass
class PublicKey:
    G_pub: Matrix
    n: int
    k: int
    L: int
    errors_per_block: int
    P: List[int]

    def serialize_size(self) -> int:
        size_G = len(pack_bits([b for row in self.G_pub for b in row]))
        size_P = len(self.P) * 2
        return size_G + size_P


@dataclass
class PrivateKey:
    S_inv: Matrix
    P_inv: List[int]
    L: int
    errors_per_block: int

    def serialize_size(self) -> int:
        size_S = len(pack_bits([b for row in self.S_inv for b in row]))
        size_P = len(self.P_inv) * 2
        return size_S + size_P


class HammingMcEliece:
    def __init__(self, L: int, errors_per_block: int = 1, rng=random):
        if errors_per_block > 1:
            raise ValueError("Hamming(15,11) 仅能纠正 1 比特错误")
        self.L = L
        self.errors_per_block = errors_per_block
        self.n = 15 * L
        self.k = 11 * L
        self.rng = rng
        self._G = block_generator(L)

    def keygen(self) -> Tuple[PublicKey, PrivateKey]:
        S = random_invertible_matrix(self.k)
        S_inv = mat_inv(S)
        P = random_permutation(self.n)
        P_inv = [0] * self.n
        for i, p in enumerate(P):
            P_inv[p] = i
        G_pub = apply_permutation_matrix(mat_mul(S, self._G), P)
        return (
            PublicKey(G_pub, self.n, self.k, self.L, self.errors_per_block, P),
            PrivateKey(S_inv, P_inv, self.L, self.errors_per_block),
        )

    def _sample_error_private(self) -> BitVector:
        e = [0] * self.n
        for blk in range(self.L):
            positions = list(range(blk * 15, (blk + 1) * 15))
            self.rng.shuffle(positions)
            for pos in positions[: self.errors_per_block]:
                e[pos] = 1
        return e

    def encrypt(self, m_bits: BitVector, pub: PublicKey) -> BitVector:
        if len(m_bits) != pub.k:
            raise ValueError(f"明文长度必须 {pub.k}")
        u = mat_vec_mul(m_bits, pub.G_pub)
        e_private = self._sample_error_private()
        e_public = apply_permutation(e_private, pub.P)
        return [(u[i] ^ e_public[i]) for i in range(pub.n)]

    def decrypt(self, c_bits: BitVector, pub: PublicKey, priv: PrivateKey) -> Tuple[BitVector, bool]:
        if len(c_bits) != pub.n:
            raise ValueError(f"密文长度必须 {pub.n}")
        c_perm = apply_permutation(c_bits, priv.P_inv)
        decoded: BitVector = []
        success = True
        for blk in range(pub.L):
            block = c_perm[blk * 15 : (blk + 1) * 15]
            msg, ok = syndrome_decode_block(block)
            decoded.extend(msg)
            success = success and ok
        m = mat_vec_mul(decoded, priv.S_inv)
        return m, success

