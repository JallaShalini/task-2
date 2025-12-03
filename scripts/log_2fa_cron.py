#!/usr/bin/env python3
import sys
import datetime
import base64
import traceback

try:
    import pyotp
except Exception:
    # if pyotp missing, print helpful message for cron logs and exit gracefully
    ts = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{ts} - ERROR: pyotp not installed")
    sys.exit(0)

def hex_to_base32(hex_seed: str) -> str:
    b = bytes.fromhex(hex_seed)
    return base64.b32encode(b).decode('utf-8').rstrip('=')

def main():
    ts = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    seed_path = '/data/seed.txt'
    try:
        with open(seed_path, 'r') as f:
            hex_seed = f.read().strip()
    except FileNotFoundError:
        print(f"{ts} - ERROR: seed file not found: {seed_path}")
        return
    if not hex_seed:
        print(f"{ts} - ERROR: empty seed")
        return
    if len(hex_seed) != 64 or any(c not in '0123456789abcdef' for c in hex_seed.lower()):
        print(f"{ts} - ERROR: invalid seed format")
        return

    try:
        b32 = hex_to_base32(hex_seed)
        totp = pyotp.TOTP(b32)  # defaults: SHA1, 30s, 6 digits
        code = totp.now()
        ts = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{ts} - 2FA Code: {code}")
    except Exception as e:
        ts = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{ts} - ERROR: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    main()
