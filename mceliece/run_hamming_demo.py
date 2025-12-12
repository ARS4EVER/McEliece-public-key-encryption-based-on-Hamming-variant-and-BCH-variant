import os
import sys
import random
import numpy as np

# 添加code目录到模块搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

from hamming_mceliece.keygen_hamming import generate_hamming_key, save_keys, load_public_key, load_private_key
from hamming_mceliece.encrypt_hamming import hamming_encrypt
from hamming_mceliece.decrypt_hamming import hamming_decrypt

# 固定随机种子以保障可重复性
random.seed(42)
np.random.seed(42)

def main():
    # 1. 生成密钥对
    print("=== 生成分块汉明码McEliece密钥对 ===")
    public_key, private_key = generate_hamming_key(L=20)
    save_keys(public_key, private_key, prefix="hamming")
    print(f"公钥尺寸：{public_key['G_prime'].nbytes} 字节")
    print(f"私钥尺寸：{private_key['S'].nbytes + private_key['P'].nbytes} 字节")
    
    # 2. 生成随机明文（220比特）
    k = public_key["G_prime"].shape[0]
    plaintext = [random.randint(0, 1) for _ in range(k)]
    print(f"\n明文（前20比特）：{plaintext[:20]}...")
    
    # 3. 加密
    print("\n=== 加密中 ===")
    ciphertext = hamming_encrypt(plaintext, public_key)
    print(f"密文（前20比特）：{ciphertext[:20]}...")
    print(f"密文扩张率：{len(ciphertext)/len(plaintext):.2f}")
    
    # 4. 解密
    print("\n=== 解密中 ===")
    decrypted_plaintext = hamming_decrypt(ciphertext, private_key)
    print(f"解密后明文（前20比特）：{decrypted_plaintext[:20]}...")
    
    # 5. 验证正确性
    if np.array_equal(decrypted_plaintext, plaintext):
        print("\n✅ 解密成功！明文一致")
    else:
        print("\n❌ 解密失败！明文不一致")

if __name__ == "__main__":
    main()