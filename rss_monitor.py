import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from .base import BaseScraper, ListingItem

class RssMonitorScraper(BaseScraper):
    """
    Monitora feed RSS pubblici per annunci di terreni, bandi comunali e notizie regionali
    (ad esempio Google Alerts configurati su 'Baugrundstück Schöneck', 'Neubaugebiet Nidderau', ecc.).
    I feed RSS sono 100% puliti da CAPTCHA e blocchi Cloudflare.
    """

    # Esempi di feed RSS mirati. È possibile aggiungere link di Google Alerts RSS personalizzati
    DEFAULT_FEEDS = [
        # Google Alerts RSS per 'Baugrundstück Schöneck Nidderau'
        "https://www.google.com/alerts/feeds/placeholder_schoeneck_baugrund",
        # Notizie locali / portali regionali
    ]

    def __init__(self, settings: Dict[str, Any], custom_feeds: List[str] = None):
        super().__init__(settings)
        self.feeds = custom_feeds or []

    def fetch_listings(self) -> List[ListingItem]:
        items: List[ListingItem] = []
        for feed_url in self.feeds:
            if not feed_url or "placeholder" in feed_url:
                continue

            try:
                resp = requests.get(feed_url, headers=self.headers, timeout=15)
                if resp.status_code != 200:
                    continue

                root = ET.fromstring(resp.content)
                # Supporto per Atom feed (Google Alerts) e RSS standard
                for entry in root.findall("{http://www.w3.org/2005/Atom}entry") or root.findall(".//item"):
                    title = entry.findtext("{http://www.w3.org/2005/Atom}title") or entry.findtext("title", "")
                    link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
                    link = link_elem.attrib.get("href", "") if link_elem is not None else entry.findtext("link", "")
                    content = entry.findtext("{http://www.w3.org/2005/Atom}content") or entry.findtext("description", "")

                    location = "Schöneck / Nidderau"
                    if "schöneck" in title.lower() or "schöneck" in content.lower():
                        location = "Schöneck"
                    elif "nidderau" in title.lower() or "nidderau" in content.lower():
                        location = "Nidderau"

                    items.append(ListingItem(
                        title=f"RSS Alert: {title[:90]}",
                        link=link,
                        source="Feed RSS / News",
                        category="Land",
                        location=location,
                        price="Vedi annuncio",
                        area_sqm="Vedi annuncio",
                        train_info=self.determine_train_connection(location),
                        details=content[:250] if content else "Rilevato tramite feed RSS automatico."
                    ))
            except Exception as e:
                print(f"[RSS Monitor] Errore elaborazione feed {feed_url}: {e}")

        return items
