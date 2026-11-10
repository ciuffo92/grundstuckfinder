import requests
from typing import Dict, Any
from .base import BaseNotifier

class TelegramNotifier(BaseNotifier):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bot_token = config.get("bot_token", "").strip()
        self.chat_id = config.get("chat_id", "").strip()

    def send_message(self, message: str) -> bool:
        if not self.bot_token or not self.chat_id or "YOUR_" in self.bot_token:
            print("[Telegram] Token o Chat ID mancante in settings.yaml")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }

        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                print("[Telegram] Notifica inviata con successo!")
                return True
            else:
                print(f"[Telegram] Errore HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"[Telegram] Errore di invio: {e}")
            return False
