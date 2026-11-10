from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseNotifier(ABC):
    @abstractmethod
    def send_message(self, message: str) -> bool:
        """Invia un messaggio di testo."""
        pass

    def format_listing_message(self, item: Dict[str, Any]) -> str:
        """
        Formatta il messaggio per WhatsApp / Telegram con icone e dettagli puliti.
        """
        category_icons = {
            "Land": "🏡 *NUOVO TERRENO EDIFICABILE*",
            "Auction": "⚖️ *ASTA GIUDIZIARIA (ZVG)*",
            "DeepSearch-Tender": "🚜 *NUOVO BANDO LAVORI / TUBI (Deep Search)*",
            "DeepSearch-BPlan": "📜 *NUOVO PIANO DI LOTTIZZAZIONE (B-Plan)*",
        }
        
        header = category_icons.get(item.get("category", "Land"), "📢 *AVVISO IMMOBILIARE*")
        
        train_line = ""
        if item.get("train_info"):
            train_line = f"🚆 *Treno per Francoforte:* {item['train_info']}\n"

        msg = (
            f"{header}\n\n"
            f"📌 *Titolo:* {item.get('title', 'N/D')}\n"
            f"📍 *Zona:* {item.get('location', 'N/D')}\n"
            f"{train_line}"
            f"💰 *Prezzo/Stima:* {item.get('price', 'N/D')}\n"
            f"📐 *Metratura:* {item.get('area_sqm', 'N/D')}\n"
            f"🏷️ *Fonte:* {item.get('source', 'Web')}\n"
        )

        if item.get("details"):
            clean_details = item['details'][:280] + ("..." if len(item['details']) > 280 else "")
            msg += f"ℹ️ *Dettagli:* {clean_details}\n"

        msg += f"\n🔗 *Link:* {item.get('link', '')}"
        return msg
