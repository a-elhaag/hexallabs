import os

DAILY_BASE_TOKENS: int = int(os.getenv("DAILY_BASE_TOKENS", "100"))
ROLLOVER_RATE: float = float(os.getenv("ROLLOVER_RATE", "0.5"))
ROLLOVER_WINDOW_DAYS: int = int(os.getenv("ROLLOVER_WINDOW_DAYS", "3"))
HARD_CAP_MULTIPLIER: float = float(os.getenv("HARD_CAP_MULTIPLIER", "1.5"))
GLOBAL_COST_RATE: float = float(os.getenv("GLOBAL_COST_RATE", "0.05"))

MODEL_WEIGHTS: dict[str, float] = {
    "Apex":    float(os.getenv("MODEL_WEIGHT_APEX", "2.0")),
    "Pulse":   float(os.getenv("MODEL_WEIGHT_PULSE", "2.0")),
    "Swift":   float(os.getenv("MODEL_WEIGHT_SWIFT", "1.0")),
    "Prism":   float(os.getenv("MODEL_WEIGHT_PRISM", "1.5")),
    "Depth":   float(os.getenv("MODEL_WEIGHT_DEPTH", "1.5")),
    "Atlas":   float(os.getenv("MODEL_WEIGHT_ATLAS", "1.0")),
    "Horizon": float(os.getenv("MODEL_WEIGHT_HORIZON", "1.5")),
}
