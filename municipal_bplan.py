import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseScraper, ListingItem

class MunicipalBPlanScraper(BaseScraper):
    """
    Monitora le pagine ufficiali dei comuni e della Regione Assia (Hessen):
      - Bauleitplanung Hessen (bauleitplanung.hessen.de)
      - Pagine ufficiali Comune di Schöneck (schoeneck.de - Bauleitplanung / Bekanntmachungen)
      - Pagine ufficiali Città di Nidderau (nidderau.de - Baugebiete / Bekanntmachungen)
    Intercetta le delibere per nuovi quartieri residenziali (Bebauungspläne)
    molto prima che i singoli terreni vengano messi all'asta o in vendita ai privati.
    """

    MUNICIPAL_SOURCES = [
        {
            "name": "Gemeinde Schöneck Bauleitplanung",
            "url": "https://www.schoeneck.de/buergerservice-politik/bauen-wohnen/bauleitplanung/",
            "location": "Schöneck",
            "train": "RB34 (Niddertalbahn -> Frankfurt Hbf)"
        },
        {
            "name": "Gemeinde Schöneck Bekanntmachungen",
            "url": "https://www.schoeneck.de/aktuelles/bekanntmachungen/",
            "location": "Schöneck",
            "train": "RB34"
        },
        {
            "name": "Stadt Nidderau Baugebiete",
            "url": "https://www.nidderau.de/bauen-wohnen/baugebiete/",
            "location": "Nidderau",
            "train": "RB34 & RB49"
        },
        {
            "name": "Stadt Nidderau Bekanntmachungen",
            "url": "https://www.nidderau.de/aktuelles/amtliche-bekanntmachungen/",
            "location": "Nidderau",
            "train": "RB34 & RB49"
        },
        {
            "name": "Bauleitplanung Hessen (Portal)",
            "url": "https://bauleitplanung.hessen.de/bebauungsplaene",
            "location": "Schöneck / Nidderau",
            "train": "RB34 / RB49 / S6"
        }
    ]

    KEYWORDS = [
        "bebauungsplan", "b-plan", "neubaugebiet", "wohngebiet", 
        "aufstellungsbeschluss", "offenlage", "baugrundstücke", "erschließungsgebiet",
        "bauland", "wohnbauland"
    ]

    def fetch_listings(self) -> List[ListingItem]:
        items: List[ListingItem] = []

        for source in self.MUNICIPAL_SOURCES:
            try:
                resp = requests.get(source["url"], headers=self.headers, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Cerca tutti i link e paragrafi rilevanti
                elements = soup.find_all(["a", "div", "article", "li"])
                for el in elements:
                    text = el.get_text(separator=" ", strip=True)
                    text_lower = text.lower()

                    if any(kw in text_lower for kw in self.KEYWORDS):
                        # Evita stringhe troppo brevi o generiche del menu
                        if len(text) < 25 or len(text) > 400:
                            continue

                        link_tag = el if el.name == "a" else el.find("a", href=True)
                        if link_tag and link_tag.has_attr("href"):
                            href = link_tag["href"]
                            link = href if href.startswith("http") else f"{source['url'].rstrip('/')}/{href.lstrip('/')}"
                        else:
                            link = source["url"]

                        items.append(ListingItem(
                            title=f"Nuova Delibera/Area: {text[:90]}",
                            link=link,
                            source=source["name"],
                            category="DeepSearch-BPlan",
                            location=source["location"],
                            price="Prezzo comunale da definire (Bodenrichtwert)",
                            area_sqm="Zona di nuova lottizzazione comunale",
                            train_info=source["train"],
                            details=f"Pianificazione urbanistica / Delibera comunale per nuove aree edificabili: {text[:250]}"
                        ))

            except Exception as e:
                print(f"[MunicipalBPlan] Errore durante la scansione di {source['name']}: {e}")

        return items
