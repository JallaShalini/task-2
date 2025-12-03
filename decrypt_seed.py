#!/usr/bin/env python3
"""
decrypt_seed.py

Usage:
    python3 decrypt_seed.py

This script:
- Reads base64 ciphertext from encrypted_seed.txt
- Reads RSA private key from student_private.pem
- Decrypts using RSA/OAEP with SHA-256 and MGF1(SHA-256)
- Validates that decrypted value is a 64-character hex string
- Writes the hex seed to ./data/seed.txt (and attempts /data/seed.txt if possible)
- Exits non-zero on failures
"""

import base64
import os
import sys
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def decrypt_seed(encrypted_seed_b64: str, private_key) -> str:
    """
    Decrypt base64-encoded encrypted seed using RSA/OAEP

    Args:
        encrypted_seed_b64: Base64-encoded ciphertext
        private_key: RSA private key object

    Returns:
        Decrypted hex seed (64-character string)

    Implementation:
    1. Base64 decode the encrypted seed string
    2. RSA/OAEP decrypt with SHA-256 (MGF1 with SHA-256)
    3. Decode bytes to UTF-8 string
    4. Validate: must be 64-character hex string (0-9, a-f)
    5. Return hex seed (lowercase)
    """
    # 1. base64 decode
    try:
        ciphertext = base64.b64decode(encrypted_seed_b64)
    except Exception as e:
        raise ValueError(f"Base64 decode failed: {e}")

    # 2. RSA/OAEP decrypt
    try:
        plaintext_bytes = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    except Exception as e:
        raise ValueError(f"RSA/OAEP decryption failed: {e}")

    # 3. decode bytes to UTF-8
    try:
        plaintext = plaintext_bytes.decode('utf-8')
    except Exception as e:
        # Show hex to help debug if non-UTF-8
        raise ValueError(f"Failed to decode decrypted bytes as UTF-8: {e}. "
                         f"Decrypted bytes (hex): {plaintext_bytes.hex()}")

    # 4. Validate: 64-character hex string
    seed = plaintext.strip()
    if len(seed) != 64:
        raise ValueError(f"Invalid seed length: expected 64 characters, got {len(seed)}. Value: {seed!r}")

    # allow uppercase hex, but convert to lowercase for canonical form
    seed_l = seed.lower()
    if not all(c in "0123456789abcdef" for c in seed_l):
        raise ValueError("Seed contains non-hex characters. Value: {!r}".format(seed))

    # 5. Return hex seed
    return seed_l

def load_private_key(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Private key file not found: {path}")
    with open(path, "rb") as f:
        data = f.read()
    try:
        key = serialization.load_pem_private_key(data, password=None)
    except Exception as e:
        raise ValueError(f"Failed to load private key from {path}: {e}")
    return key

def read_encrypted_seed_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Encrypted seed file not found: {path}")
    with open(path, "r") as f:
        b64 = f.read().strip()
    if not b64:
        raise ValueError("Encrypted seed file is empty")
    return b64

def write_seed(path: str, seed: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        f.write(seed + "\n")
    # restrict permissions locally (owner read/write)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass

def main():
    try:
        encrypted_seed_path = "encrypted_seed.txt"
        private_key_path = "student_private.pem"
        out_local = "data/seed.txt"      # repo-local data directory
        out_container = "/data/seed.txt" # container expected path (attempt)

        print(f"Loading encrypted seed from {encrypted_seed_path}...")
        encrypted_b64 = read_encrypted_seed_file(encrypted_seed_path)
        print("Loading private key from", private_key_path)
        priv = load_private_key(private_key_path)

        print("Decrypting...")
        seed = decrypt_seed(encrypted_b64, priv)
        print("Decrypted seed (hex):", seed)

        print("Writing seed to", out_local)
        write_seed(out_local, seed)
        print("Wrote:", out_local)

        # Try to write to /data/seed.txt as requested (may require container or permissions)
        try:
            write_seed(out_container, seed)
            print("Also wrote seed to", out_container)
        except PermissionError:
            print(f"Permission denied writing to {out_container}. If you are running in a container, mount a volume to /data or run with appropriate permissions.")
        except Exception as e:
            # non-fatal, just warn
            print(f"Could not write to {out_container}: {e}")

        print("Done. IMPORTANT: do NOT commit seed files to git.")
        return 0
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
