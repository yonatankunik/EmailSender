import pandas as pd

REQUIRED_COLUMNS = ["Email"]

def load_excel(file) -> pd.DataFrame:
    df = pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Make sure your Excel has at least an 'Email' column.")
    return df
