#!/usr/bin/env python3
"""
totp_tools.py

Usage:
  python3 totp_tools.py show      # prints current 6-digit TOTP
  python3 totp_tools.py verify <code>  # verifies given 6-digit code (uses window=1)

Functions:
  generate_totp_code(hex_seed: str) -> str
  verify_totp_code(hex_seed: str, code: str, valid_window: int = 1) -> bool

Notes:
- TOTP config: SHA-1, 30-sec period, 6 digits (standard).
- Seed conversion: hex -> bytes -> base32 (uppercase, no padding).
"""
import base64
import os
import sys
import time
from typing import Optional

try:
    import pyotp
except Exception:
    pyotp = None

def hex_to_base32(hex_seed: str) -> str:
    """
    Convert 64-char hex seed to base32 string (no '=' padding, uppercase).
    """
    # validate basic hex length and characters
    s = hex_seed.strip().lower()
    if len(s) != 64:
        raise ValueError(f"hex seed length must be 64 characters, got {len(s)}")
    try:
        b = bytes.fromhex(s)
    except Exception as e:
        raise ValueError(f"Invalid hex seed: {e}")
    b32 = base64.b32encode(b).decode('utf-8')  # produces uppercase with '=' padding
    # remove padding, return uppercase (pyotp accepts uppercase)
    return b32.rstrip('=')

def generate_totp_code(hex_seed: str) -> str:
    """
    Generate current 6-digit TOTP code from hex seed.
    """
    b32 = hex_to_base32(hex_seed)
    if pyotp is None:
        raise RuntimeError("pyotp not installed. Run: pip install pyotp")
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    return totp.now()

def verify_totp_code(hex_seed: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify a TOTP code with time window tolerance (default ±1 period).
    """
    b32 = hex_to_base32(hex_seed)
    if pyotp is None:
        raise RuntimeError("pyotp not installed. Run: pip install pyotp")
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    # returns True if code is valid within +/- valid_window intervals
    return totp.verify(code, valid_window=valid_window)

def load_hex_seed_from_file(path: str = "data/seed.txt") -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Seed file not found: {path}")
    s = open(path, "r").read().strip()
    if not s:
        raise ValueError("Seed file is empty")
    return s

def main(argv):
    if len(argv) < 2:
        print("Usage:\n  python3 totp_tools.py show\n  python3 totp_tools.py verify <6-digit-code>")
        return 2

    cmd = argv[1].lower()
    try:
        hex_seed = load_hex_seed_from_file()
    except Exception as e:
        print("ERROR reading seed:", e, file=sys.stderr)
        return 3

    if cmd == "show":
        try:
            code = generate_totp_code(hex_seed)
            print(code)
            # also show friendly info
            print("TOTP generated (6 digits). Period:30s, Algorithm: SHA-1")
            return 0
        except Exception as e:
            print("ERROR generating TOTP:", e, file=sys.stderr)
            return 4

    if cmd == "verify":
        if len(argv) < 3:
            print("Usage: python3 totp_tools.py verify <code>")
            return 2
        code = argv[2].strip()
        if not code.isdigit() or len(code) != 6:
            print("Code must be 6 digits", file=sys.stderr); return 5
        try:
            ok = verify_totp_code(hex_seed, code, valid_window=1)
            print("VALID" if ok else "INVALID")
            return 0
        except Exception as e:
            print("ERROR verifying TOTP:", e, file=sys.stderr)
            return 6

    print("Unknown command:", cmd)
    return 2

if __name__ == "__main__":
    sys.exit(main(sys.argv))
