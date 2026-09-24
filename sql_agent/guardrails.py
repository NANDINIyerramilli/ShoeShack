import re

BLOCKED_PATTERNS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bUNION\b",
    r"--",
    r";.*\S",
]

REDACT_FIELDS = {
    "email", "phone", "address", "password", "user_id"
}
MAX_ROWS = 5


def validate_input(query: str) -> str:
    """Raise if the text contains obviously dangerous SQL keywords or operators."""
    upper_query = query.upper()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, upper_query):
            raise ValueError(f"Blocked dangerous pattern: {pattern}")
    return query


def validate_sql(sql: str) -> str:
    """Allow only single-statement SELECT queries."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped.upper().startswith("SELECT"):
        raise ValueError("Only SELECT statements are allowed")
    if ";" in stripped:
        raise ValueError("Multi-statement queries are not allowed")
    validate_input(stripped)
    return stripped


def validate_output(rows: list) -> list:
    """Cap row count and redact sensitive fields."""
    rows = rows[:MAX_ROWS]
    cleaned = []
    for row in rows:
        if isinstance(row, dict):
            cleaned.append({k: v for k, v in row.items() if k not in REDACT_FIELDS})
        else:
            cleaned.append(row)
    return cleaned
