import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


def _get(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Missing required env variable: {key}")
    return value


# --- ROFEX ---
ROFEX_USER: str = os.getenv("ROFEX_USER", "")
ROFEX_PASSWORD: str = os.getenv("ROFEX_PASSWORD", "")
ROFEX_ACCOUNT: str = os.getenv("ROFEX_ACCOUNT", "")
ROFEX_ENVIRONMENT: str = os.getenv("ROFEX_ENVIRONMENT", "SIMULATION")

# --- Cocos Capital ---
COCOS_EMAIL: str = os.getenv("COCOS_EMAIL", "")
COCOS_PASSWORD: str = os.getenv("COCOS_PASSWORD", "")
COCOS_API_KEY: str = os.getenv("COCOS_API_KEY", "")
COCOS_TOTP_SECRET: str = os.getenv("COCOS_TOTP_SECRET", "")

# --- HomeBroker ---
HOMEBROKER_BROKER: int = int(os.getenv("HOMEBROKER_BROKER", "0"))
HOMEBROKER_DNI: str = os.getenv("HOMEBROKER_DNI", "")
HOMEBROKER_USER: str = os.getenv("HOMEBROKER_USER", "")
HOMEBROKER_PASSWORD: str = os.getenv("HOMEBROKER_PASSWORD", "")

# --- Balanz ---
BALANZ_USER: str = os.getenv("BALANZ_USER", "")
BALANZ_PASSWORD: str = os.getenv("BALANZ_PASSWORD", "")

# --- PPI ---
PPI_PUBLIC_KEY: str = os.getenv("PPI_PUBLIC_KEY", "")
PPI_PRIVATE_KEY: str = os.getenv("PPI_PRIVATE_KEY", "")

# --- Veta Capital ---
VETA_USERNAME: str = os.getenv("VETA_USERNAME", "")
VETA_PASSWORD: str = os.getenv("VETA_PASSWORD", "")

# --- MAE ---
MAE_API_KEY: str = os.getenv("MAE_API_KEY", "")

# --- Binance ---
BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET: str = os.getenv("BINANCE_SECRET", "")

# --- OpenAI ---
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# --- Tiingo ---
TIINGO_TOKEN: str = os.getenv("TIINGO_TOKEN", "")

# --- Data912 ---
DATA912_BASE_URL: str = os.getenv("DATA912_BASE_URL", "https://data912.com")
