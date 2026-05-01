import hashlib
from typing import Any, Dict


def generate_signature(data: dict, password: str) -> str:
    items = []

    def flatten(d: Dict[str, Any]):
        for k, v in d.items():
            if isinstance(v, (list, tuple, dict)):
                continue
            items.append((k, v))
            
    flatten(data)
    items.append(("Password", password))
    
    items.sort(key=lambda x: str(x[0]).lower())

    res = "".join(str(value) for _, value in items)

    return hashlib.sha256(res.encode()).hexdigest()

def verify_signature(data: dict, password: str, token: str) -> bool:
    return generate_signature(data, password) == token