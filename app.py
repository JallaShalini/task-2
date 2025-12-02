from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import os
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import time
import base64 as _b64
import pyotp

DATA_DIR = "/data"
LOCAL_DATA_DIR = "data"
SEED_FILENAME = "seed.txt"
LOCAL_SEED_PATH = os.path.join(LOCAL_DATA_DIR, SEED_FILENAME)
CONTAINER_SEED_PATH = os.path.join(DATA_DIR, SEED_FILENAME)
PRIVATE_KEY_PATH = "student_private.pem"

app = FastAPI(title="Instructor TOTP Service")

class DecryptRequest(BaseModel):
    encrypted_seed: str

class VerifyRequest(BaseModel):
    code: str

def load_private_key(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError("Private key not found")
    with open(path, "rb") as f:
        data = f.read()
    return serialization.load_pem_private_key(data, password=None)

def save_seed(seed_hex: str):
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    try:
        with open(LOCAL_SEED_PATH, "w") as f:
            f.write(seed_hex.strip().lower() + "\n")
        os.chmod(LOCAL_SEED_PATH, 0o600)
    except Exception:
        pass
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONTAINER_SEED_PATH, "w") as f:
            f.write(seed_hex.strip().lower() + "\n")
        try:
            os.chmod(CONTAINER_SEED_PATH, 0o600)
        except Exception:
            pass
    except Exception:
        pass

def read_seed():
    if os.path.exists(LOCAL_SEED_PATH):
        return open(LOCAL_SEED_PATH).read().strip()
    if os.path.exists(CONTAINER_SEED_PATH):
        return open(CONTAINER_SEED_PATH).read().strip()
    raise FileNotFoundError("Seed not decrypted yet")

def decrypt_oaep_sha256(private_key, ciphertext_bytes: bytes) -> str:
    plaintext = private_key.decrypt(
        ciphertext_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plaintext.decode("utf-8").strip()

@app.post("/decrypt-seed")
async def decrypt_seed(req: DecryptRequest):
    try:
        priv = load_private_key(PRIVATE_KEY_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Private key not available")
    try:
        ct = base64.b64decode(req.encrypted_seed)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid base64 for encrypted_seed")
    try:
        plaintext = decrypt_oaep_sha256(priv, ct)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Decryption failed")
    seed = plaintext.strip().lower()
    if len(seed) != 64 or any(c not in "0123456789abcdef" for c in seed):
        raise HTTPException(status_code=500, detail="Decrypted seed is invalid")
    try:
        save_seed(seed)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save seed")
    return {"status": "ok"}

@app.get("/generate-2fa")
async def generate_2fa():
    try:
        seed = read_seed()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Seed not decrypted yet")
    try:
        key_bytes = bytes.fromhex(seed)
    except Exception:
        raise HTTPException(status_code=500, detail="Stored seed invalid")
    b32 = _b64.b32encode(key_bytes).decode('utf-8').rstrip('=')
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    code = totp.now()
    period = 30
    now = int(time.time())
    elapsed = now % period
    remaining = period - elapsed
    return {"code": code, "valid_for": remaining}

@app.post("/verify-2fa")
async def verify_2fa(req: VerifyRequest):
    code = (req.code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    try:
        seed = read_seed()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Seed not decrypted yet")
    try:
        key_bytes = bytes.fromhex(seed)
    except Exception:
        raise HTTPException(status_code=500, detail="Stored seed invalid")
    b32 = _b64.b32encode(key_bytes).decode('utf-8').rstrip('=')
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    valid = totp.verify(code, valid_window=1)
    return {"valid": valid}
