#!/usr/bin/env python3
import sys
import datetime
import base64
import traceback

try:
    import pyotp
except:
    print(f"{datetime.datetime.utcnow():%Y-%m-%d %H:%M:%S} - ERROR: pyotp module missing")
    sys.exit(0)

def hex_to_base32(hex_seed: str) -> str:
    raw = bytes.fromhex(hex_seed)
    return base64.b32encode(raw).decode().rstrip('=')

def main():
    try:
        seed_file = "/data/seed.txt"
        try:
            with open(seed_file, "r") as f:
                hex_seed = f.read().strip()
        except FileNotFoundError:
            print(f"{datetime.datetime.utcnow():%Y-%m-%d %H:%M:%S} - ERROR: seed file missing")
            return

        if len(hex_seed) != 64:
            print(f"{datetime.datetime.utcnow():%Y-%m-%d %H:%M:%S} - ERROR: invalid seed")
            return

        seed_b32 = hex_to_base32(hex_seed)
        totp = pyotp.TOTP(seed_b32)
        code = totp.now()

        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{ts} - 2FA Code: {code}")

    except Exception as e:
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{ts} - ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
