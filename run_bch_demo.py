import sys
import os

sys.path.append(os.path.dirname(__file__))
from code.bch_mceliece.bch_code import BCHMcEliece  # noqa: E402


def main():
    scheme = BCHMcEliece(L=3, errors_per_block=2)
    pub, priv = scheme.keygen()
    msg = [int(os.urandom(1)[0] & 1) for _ in range(pub.k)]
    c = scheme.encrypt(msg, pub)
    m2, ok = scheme.decrypt(c, pub, priv)
    print("BCH demo -> 成功:", ok, "消息一致:", msg == m2)


if __name__ == "__main__":
    main()

