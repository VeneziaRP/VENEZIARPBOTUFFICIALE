# utils/iban.py
from __future__ import annotations

# Parametri fittizi della "VeneziaRP Bank"
ABI = "12345"  # 5 cifre
CAB = "67890"  # 5 cifre
CIN = "X"      # 1 lettera

def _alnum_to_digits(s: str) -> str:
    out = []
    for ch in s:
        if ch.isdigit():
            out.append(ch)
        else:
            out.append(str(ord(ch.upper()) - 55))  # A->10 ... Z->35
    return "".join(out)

def _iban_check_digits(country: str, bban: str) -> str:
    rearranged = bban + country + "00"
    number = _alnum_to_digits(rearranged)
    rem = 0
    for ch in number:
        rem = (rem * 10 + int(ch)) % 97
    return f"{98 - rem:02d}"

def generate_iban(user_id: int) -> str:
    conto12 = f"{user_id % 10**12:012d}"
    bban = f"{CIN}{ABI}{CAB}{conto12}"  # 1+5+5+12=23
    check = _iban_check_digits("IT", bban)
    return f"IT{check}{bban}"