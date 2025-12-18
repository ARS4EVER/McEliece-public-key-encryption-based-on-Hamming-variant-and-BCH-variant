import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

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
)

# (15,7) BCH, t=2, g(x)=x^8 + x^7 + x^6 + x^4 + 1
N = 15
K = 7
T = 2
G_POLY = (1 << 8) | (1 << 7) | (1 << 6) | (1 << 4) | 1


def poly_degree(p: int) -> int:
    return p.bit_length() - 1 if p else -1


def poly_mul(a: int, b: int) -> int:
    res = 0
    while b:
        if b & 1:
            res ^= a
        a <<= 1
        b >>= 1
    return res


def poly_divmod(dividend: int, divisor: int) -> Tuple[int, int]:
    if divisor == 0:
        raise ZeroDivisionError
    ddeg = poly_degree(divisor)
    rem = dividend
    quot = 0
    while poly_degree(rem) >= ddeg:
        shift = poly_degree(rem) - ddeg
        quot ^= 1 << shift
        rem ^= divisor << shift
    return quot, rem


def compute_h_poly() -> int:
    x15_minus_1 = (1 << 15) | 1
    quot, rem = poly_divmod(x15_minus_1, G_POLY)
    assert rem == 0
    return quot


H_POLY = compute_h_poly()


def poly_to_bits(p: int, length: int) -> BitVector:
    return [(p >> i) & 1 for i in range(length)]


def encode_block(msg7: BitVector) -> BitVector:
    if len(msg7) != K:
        raise ValueError("消息块必须 7 比特")
    m = 0
    for i, b in enumerate(msg7):
        if b:
            m |= 1 << i
    code_poly = poly_mul(m, G_POLY)
    return poly_to_bits(code_poly, N)


def compute_syndrome_vec(vec: BitVector) -> int:
    poly = 0
    for i, b in enumerate(vec):
        if b:
            poly |= 1 << i
    _, rem = poly_divmod(poly, G_POLY)
    return rem


def syndrome_table(t: int) -> Dict[int, BitVector]:
    table: Dict[int, BitVector] = {0: [0] * N}
    for i in range(N):
        e = [0] * N
        e[i] = 1
        table.setdefault(compute_syndrome_vec(e), e)
    if t >= 2:
        for i in range(N):
            for j in range(i + 1, N):
                e = [0] * N
                e[i] = e[j] = 1
                table.setdefault(compute_syndrome_vec(e), e)
    return table


def parity_check_matrix() -> Matrix:
    rows: Matrix = []
    h = H_POLY
    for shift in range(N - K):
        poly = (h << shift) & ((1 << N) - 1)
        overflow = poly >> N
        poly = (poly & ((1 << N) - 1)) ^ overflow
        rows.append(poly_to_bits(poly, N))
    return rows


def decode_block(r: BitVector, synd_table: Dict[int, BitVector]) -> Tuple[BitVector, bool]:
    if len(r) != N:
        raise ValueError("码长必须 15 比特")
    syn = compute_syndrome_vec(r)
    if syn not in synd_table:
        return r[:K], False
    e = synd_table[syn]
    c = [r[i] ^ e[i] for i in range(N)]
    c_poly = 0
    for i, b in enumerate(c):
        if b:
            c_poly |= 1 << i
    msg, rem = poly_divmod(c_poly, G_POLY)
    return poly_to_bits(msg, K), rem == 0


def base_generator() -> Matrix:
    rows: Matrix = []
    for i in range(K):
        msg = [1 if j == i else 0 for j in range(K)]
        rows.append(encode_block(msg))
    return rows


def block_generator(L: int) -> Matrix:
    base = base_generator()
    k, n = K * L, N * L
    G = [[0] * n for _ in range(k)]
    for blk in range(L):
        for r in range(K):
            row_idx = blk * K + r
            for c, v in enumerate(base[r]):
                G[row_idx][blk * N + c] = v
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
    synd_table: Dict[int, BitVector]
    L: int
    errors_per_block: int

    def serialize_size(self) -> int:
        size_S = len(pack_bits([b for row in self.S_inv for b in row]))
        size_P = len(self.P_inv) * 2
        size_table = sum(2 + len(pack_bits(v)) for v in self.synd_table.values())
        return size_S + size_P + size_table


class BCHMcEliece:
    def __init__(self, L: int, errors_per_block: int = T, rng=random):
        if errors_per_block > T:
            raise ValueError("BCH(15,7) 最多纠正 2 比特")
        self.L = L
        self.errors_per_block = errors_per_block
        self.n = N * L
        self.k = K * L
        self.rng = rng
        self._G = block_generator(L)
        self._synd_table = syndrome_table(errors_per_block)

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
            PrivateKey(S_inv, P_inv, self._synd_table, self.L, self.errors_per_block),
        )

    def _sample_error_private(self) -> BitVector:
        e = [0] * self.n
        for blk in range(self.L):
            positions = list(range(blk * N, (blk + 1) * N))
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
            block = c_perm[blk * N : (blk + 1) * N]
            msg, ok = decode_block(block, priv.synd_table)
            decoded.extend(msg)
            success = success and ok
        m = mat_vec_mul(decoded, priv.S_inv)
        return m, success

