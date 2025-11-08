import re

def replace_placeholders(text:str, row:dict) -> str:
    def repl(m):
        key = m.group(1)
        return "" if row.get(key) is None else str(row.get(key))
    return re.sub(r"\{\{([^}]+)\}\}", repl, text)

def format_subject(pattern:str, row:dict) -> str:
    class SafeDict(dict):
        def __missing__(self, key): return ""
    try:
        return pattern.format_map(SafeDict(row))
    except Exception:
        return pattern
