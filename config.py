import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "1438313297"))
CARD_NUMBER = os.getenv("CARD_NUMBER", "9860 1606 3439 0605")
CARD_HOLDER = os.getenv("CARD_HOLDER", "K.E.")

DB_PATH = BASE_DIR / "bot_database.db"

# VIP Tarif narxlari (so'mda)
TARIFS = {
    "3_days": {
        "name": "3 kunlik VIP",
        "days": 3,
        "price": "5 000",
        "amount": 5000
    },
    "7_days": {
        "name": "7 kunlik VIP",
        "days": 7,
        "price": "10 000",
        "amount": 10000
    },
    "30_days": {
        "name": "1 oylik VIP",
        "days": 30,
        "price": "25 000",
        "amount": 25000
    }
}
