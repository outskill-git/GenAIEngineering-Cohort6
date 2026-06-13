# from __future__ import annotations
import pandas as pd
import os
from typing import Optional, Dict, Any


DEFAULT_CSV_PATH = "user_db.csv"


def mask_email(email: str) -> str:
    """
    Mask email into format like 'ravXXXX@gmaXXXX'
    (local: first 3 chars + 'XXXX', domain (before dot): first 3 chars + 'XXXX')
    """
    if not isinstance(email, str) or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    domain_base = domain.split(".", 1)[0] if "." in domain else domain
    local_part = (local[:3] if len(local) >= 3 else local).lower()
    domain_part = (domain_base[:3] if len(domain_base) >= 3 else domain_base).lower()
    return f"{local_part}XXXX@{domain_part}XXXX"


def mask_phone(phone: str) -> str:
    """
    Mask phone of form '+91-XXXXX-XXXXX' keeping first 2 and last 2 digits visible:
    e.g. '+91-98765-43210' -> '+91-98XXX-XXX10'
    
    """
    if not isinstance(phone, str):
        return phone

    # Extract digits
    digits = "".join(ch for ch in phone if ch.isdigit())
    # If there are 10 digits (Indian mobile), mask as required
    if len(digits) >= 10:
        digits = digits[-10:]  # take last 10 digits just in case
        first2 = digits[:2]
        last2 = digits[-2:]
        # produce grouped formatting XXXXX-XXXXX with mask
        masked = f"+91-{first2}XXX-XXX{last2}"
        return masked

    # fallback: if shorter, mask middle portion 
    if len(digits) <= 4:
        return phone  # nothing meaningful to mask
    first = digits[:max(1, len(digits)//4)]
    last = digits[-max(1, len(digits)//4):]
    middle_mask = "X" * (len(digits) - len(first) - len(last))
    return f"+91-{first}{middle_mask}{last}"



def _read_df(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        # create an empty dataframe with expected columns if missing
        cols = ["user_id", "name", "age", "city", "email", "phone_number"]
        return pd.DataFrame(columns=cols)
    return pd.read_csv(csv_path, dtype=str)



def read_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Read details for user_id and return a dict with masked email and phone.
    Returns Error if user not found.
    """
    df = _read_df(DEFAULT_CSV_PATH)
    if df.empty:
        return "Data not found"
    df = df.astype(str)
    row = df.loc[df["user_id"] == user_id]
    if row.empty:
        return "Data not found"
    r = row.iloc[0].to_dict()
    
    # mask email and phone in the returned payload
    r["email"] = mask_email(r.get("email", ""))
    r["phone_number"] = mask_phone(r.get("phone_number", ""))

    return r


def update_user(user_id: str, **fields) -> str:
    """
    Update user identified by user_id with provided keyword fields.
    Allowed fields: name, age, city, email, phone_number
    Returns confirmation message.
    Raises ValueError if user not found.
    """
    allowed = {"name", "age", "city", "email", "phone_number"}
    update_fields = {k: v for k, v in fields.items() if k in allowed}

    if not update_fields:
        return "No updatable fields provided."

    df = _read_df(DEFAULT_CSV_PATH)
    if df.empty:
        raise ValueError(f"user {user_id} not found")

    mask = df["user_id"] == user_id
    if not mask.any():
        raise ValueError(f"user {user_id} not found")

    # Update values (convert everything to str for CSV consistency)
    for col, val in update_fields.items():
        df.loc[mask, col] = str(val)

    # write data
    df.to_csv (DEFAULT_CSV_PATH, index=False)
    return f"user {user_id} updated successfully."


def add_user(user: Dict[str, Any]) -> str:
    """
    Add a new user. user is a dict with keys: name, age, city, email, phone_number
    Generates next user_id in format U_nnnn (zero-padded 4 digits).
    Returns the new user_id.
    """
    required = {"name", "age", "city", "email", "phone_number"}
    if not required.issubset(set(user.keys())):
        missing = required - set(user.keys())
        raise ValueError(f"Missing fields for add_user: {missing}")

    df = _read_df(DEFAULT_CSV_PATH)

    # Determine next id
    if df.empty:
        next_num = 1
    else:
        # Extract numeric part of user_id starting after 'U_' (robust)
        nums = []
        for val in df["user_id"].astype(str).tolist():
            try:
                if isinstance(val, str) and val.startswith("U_"):
                    nums.append(int(val.split("_", 1)[1]))
            except Exception:
                continue
        next_num = max(nums) + 1 if nums else 1

    new_id = f"U_{next_num:04d}"

    # Append and persist: ensure we keep columns consistent
    new_row = {
        "user_id": new_id,
        "name": str(user["name"]),
        "age": str(user["age"]),
        "city": str(user["city"]),
        "email": str(user["email"]),
        "phone_number": str(user["phone_number"]),
    }

    new_df = pd.DataFrame([new_row])
    if df.empty:
        out_df = new_df
    else:
        out_df = pd.concat([df, new_df], ignore_index=True)

    # Write the data to file
    out_df.to_csv (DEFAULT_CSV_PATH, index=False)    
    return new_id

