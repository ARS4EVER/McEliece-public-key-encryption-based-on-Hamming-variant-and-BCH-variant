import sys
import os

# 便于直接运行
sys.path.append(os.path.dirname(__file__))
from code.hamming_mceliece.hamming_code import HammingMcEliece  # noqa: E402


def main():
    scheme = HammingMcEliece(L=3, errors_per_block=1)
    pub, priv = scheme.keygen()
    msg = [int(os.urandom(1)[0] & 1) for _ in range(pub.k)]
    c = scheme.encrypt(msg, pub)
    m2, ok = scheme.decrypt(c, pub, priv)
    print("Hamming demo -> 成功:", ok, "消息一致:", msg == m2)


if __name__ == "__main__":
    main()

