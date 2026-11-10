import urllib.parse
import requests
from typing import Dict, Any
from .base import BaseNotifier

class WhatsAppNotifier(BaseNotifier):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get("provider", "callmebot").lower()

    def send_message(self, message: str) -> bool:
        if self.provider == "callmebot":
            return self._send_via_callmebot(message)
        elif self.provider == "twilio":
            return self._send_via_twilio(message)
        else:
            print(f"[WhatsApp] Provider sconosciuto: {self.provider}")
            return False

    def _send_via_callmebot(self, message: str) -> bool:
        """
        Invia messaggi WhatsApp usando CallMeBot API (completamente gratuito per uso personale).
        Doc: https://www.callmebot.com/blog/free-api-whatsapp-messages/
        """
        bot_cfg = self.config.get("callmebot", {})
        phone = bot_cfg.get("phone_number", "").strip().replace(" ", "")
        api_key = bot_cfg.get("api_key", "").strip()

        if not phone or not api_key or "YOUR_" in api_key:
            print("[WhatsApp/CallMeBot] Configurazione non completa: imposta phone_number e api_key in settings.yaml")
            return False

        encoded_message = urllib.parse.quote_plus(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey={api_key}"

        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                print("[WhatsApp/CallMeBot] Messaggio inviato con successo!")
                return True
            else:
                print(f"[WhatsApp/CallMeBot] Errore risposta HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"[WhatsApp/CallMeBot] Eccezione di rete: {e}")
            return False

    def _send_via_twilio(self, message: str) -> bool:
        """Invia messaggi WhatsApp tramite Twilio API."""
        twilio_cfg = self.config.get("twilio", {})
        account_sid = twilio_cfg.get("account_sid", "").strip()
        auth_token = twilio_cfg.get("auth_token", "").strip()
        from_number = twilio_cfg.get("from_number", "").strip()
        to_number = twilio_cfg.get("to_number", "").strip()

        if not account_sid or not auth_token or not to_number:
            print("[WhatsApp/Twilio] Parametri mancanti in settings.yaml")
            return False

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        data = {
            "From": from_number,
            "To": to_number,
            "Body": message
        }

        try:
            response = requests.post(url, data=data, auth=(account_sid, auth_token), timeout=15)
            if response.status_code in (200, 201):
                print("[WhatsApp/Twilio] Messaggio inviato con successo!")
                return True
            else:
                print(f"[WhatsApp/Twilio] Errore Twilio HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"[WhatsApp/Twilio] Eccezione Twilio: {e}")
            return False
