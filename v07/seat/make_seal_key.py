"""Make the seat's seal key (Ed25519), once, before migration day. Writes the 32-byte seed as hex to ~/.teich_seal_key
(chmod 600, outside the repo; never printed, never committed) and the public key to ~/.teich_seal_pub. The public key
is bound to the creature in its genome-amendment record at migration; the seed is installed as the worker secret
SEAL_KEY (infra/worker/put_secret.py) and may then be shredded: the seat signs, nobody else needs it.
    python3 make_seal_key.py
"""
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

KEY, PUB = Path.home() / ".teich_seal_key", Path.home() / ".teich_seal_pub"
if KEY.exists():
    sys.exit(f"{KEY} already exists: one seal key per creature, never replaced silently")
k = Ed25519PrivateKey.generate()
seed = k.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex()
pub = k.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
fd = os.open(KEY, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as f:
    f.write(seed)
PUB.write_text(pub + "\n")
print("seal public key:", pub)
print(f"seed written to {KEY} (chmod 600). Install it: python3 infra/worker/put_secret.py SEAL_KEY {KEY}")
