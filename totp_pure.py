#!/usr/bin/env python3
"""
Pure-Python TOTP generator/validator (SHA-1, 30s, 6 digits).
Usage:
  python3 totp_pure.py show
  python3 totp_pure.py verify <6-digit-code>
"""
import base64, hashlib, hmac, time, sys, os

def hex_to_base32_nopad(hex_seed):
    b = bytes.fromhex(hex_seed.strip())
    return base64.b32encode(b).decode().rstrip('=')

def int_to_bytes(i, length=8):
    return i.to_bytes(length, 'big')

def hotp_from_secret(b32_secret, counter, digits=6):
    key = base64.b32decode(b32_secret + '=' * ((8 - len(b32_secret) % 8) % 8))
    counter_bytes = int_to_bytes(counter, 8)
    h = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = (int.from_bytes(h[offset:offset+4], 'big') & 0x7fffffff) % (10 ** digits)
    return str(code).zfill(digits)

def totp_now(b32_secret, interval=30, digits=6):
    counter = int(time.time() // interval)
    return hotp_from_secret(b32_secret, counter, digits)

def verify_totp(b32_secret, code, window=1, interval=30, digits=6):
    cur = int(time.time() // interval)
    for dt in range(-window, window+1):
        if hotp_from_secret(b32_secret, cur + dt, digits) == code:
            return True
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: show | verify <code>"); sys.exit(2)
    if not os.path.exists("data/seed.txt"):
        print("Need data/seed.txt"); sys.exit(3)
    hex_seed = open("data/seed.txt").read().strip()
    b32 = hex_to_base32_nopad(hex_seed)
    cmd = sys.argv[1].lower()
    if cmd == "show":
        print(totp_now(b32))
    elif cmd == "verify":
        if len(sys.argv) < 3: print("verify needs code"); sys.exit(2)
        print("VALID" if verify_totp(b32, sys.argv[2]) else "INVALID")
    else:
        print("Unknown command")
