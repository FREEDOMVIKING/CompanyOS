
from __future__ import annotations
import base64, json
from dataclasses import dataclass
from typing import Optional

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
IDX={c:i for i,c in enumerate(ALPH)}

def b58decode(s:str)->bytes:
    s=s.strip()
    if not s: raise ValueError("empty_base58")
    n=0
    for ch in s:
        if ch not in IDX: raise ValueError("invalid_base58_character")
        n=n*58+IDX[ch]
    out=b"" if n==0 else n.to_bytes((n.bit_length()+7)//8,"big")
    return b"\x00"*(len(s)-len(s.lstrip("1")))+out

def b58encode(raw:bytes)->str:
    raw=bytes(raw); n=int.from_bytes(raw,"big"); chars=[]
    while n:
        n,r=divmod(n,58); chars.append(ALPH[r])
    return "1"*(len(raw)-len(raw.lstrip(b"\x00")))+("".join(reversed(chars)) if chars else "")

@dataclass(frozen=True)
class SolanaKeyInfo:
    encoding:str
    key_length:int
    valid_length:bool
    public_key:Optional[str]
    public_key_derivable_without_crypto_backend:bool

def decode_solana_private_key(value:str, encoding:str="auto"):
    enc=(encoding or "auto").strip().lower(); value=value.strip()
    def j():
        obj=json.loads(value)
        if not isinstance(obj,list) or not all(isinstance(x,int) and 0<=x<=255 for x in obj):
            raise ValueError("invalid_json_key")
        return bytes(obj)
    def b64(): return base64.b64decode(value,validate=True)
    if enc in ("json","json-array","array"): return j(),"json"
    if enc in ("base58","b58"): return b58decode(value),"base58"
    if enc in ("base64","b64"): return b64(),"base64"
    if enc!="auto": raise ValueError("unsupported_encoding")
    if value.startswith("["):
        try:
            raw=j()
            if len(raw) in (32,64): return raw,"json"
        except Exception: pass
    try:
        raw=b58decode(value)
        if len(raw) in (32,64): return raw,"base58"
    except Exception: pass
    try:
        raw=b64()
        if len(raw) in (32,64): return raw,"base64"
    except Exception: pass
    raise ValueError("unable_to_decode_supported_solana_key")

def inspect_solana_private_key(value:str, encoding:str="auto")->SolanaKeyInfo:
    raw,det=decode_solana_private_key(value,encoding)
    pub=None; derivable=False
    if len(raw)==64:
        pub=b58encode(raw[32:]); derivable=True
    return SolanaKeyInfo(det,len(raw),len(raw) in (32,64),pub,derivable)
