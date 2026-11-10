from typing import List, Dict, Any
from .whatsapp import WhatsAppNotifier
from .telegram import TelegramNotifier
from .base import BaseNotifier

class NotificationDispatcher:
    def __init__(self, settings: Dict[str, Any]):
        self.notifiers: List[BaseNotifier] = []
        notif_cfg = settings.get("notifications", {})

        if notif_cfg.get("whatsapp", {}).get("enabled", False):
            self.notifiers.append(WhatsAppNotifier(notif_cfg["whatsapp"]))

        if notif_cfg.get("telegram", {}).get("enabled", False):
            self.notifiers.append(TelegramNotifier(notif_cfg["telegram"]))

    def notify_listing(self, item: Dict[str, Any]) -> bool:
        """Invia la notifica dell'annuncio a tutti i canali attivi."""
        if not self.notifiers:
            print("[Dispatcher] Nessun servizio di notifica attivo o configurato.")
            return False

        success = False
        for notifier in self.notifiers:
            msg = notifier.format_listing_message(item)
            if notifier.send_message(msg):
                success = True
        return success
