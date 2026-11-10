import re
import json
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from .base import BaseScraper, ListingItem

class ManualListingImporter(BaseScraper):
    """
    Gestisce l'analisi di URL singoli o elenchi esportati/salvati
    da portali come Kleinanzeigen o ImmoScout24.
    In questo modo si evitano i blocchi antibot/Cloudflare delle scansioni ripetitive,
    permettendo di inviare tempestivamente la notifica WhatsApp con tutti i metadati estratti.
    """

    def fetch_listings(self) -> List[ListingItem]:
        # Questa classe viene richiamata esplicitamente tramite import_url o import_file
        return []

    def parse_url(self, url: str) -> Optional[ListingItem]:
        """Estrae dettagli da un singolo URL Kleinanzeigen o ImmoScout."""
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code != 200:
                print(f"[ManualImporter] Errore HTTP {resp.status_code} su {url}")
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            title = soup.find("title").get_text(strip=True) if soup.find("title") else "Annuncio Terreno"

            # Rilevamento prezzo con regex
            text_content = soup.get_text()
            price_match = re.search(r"(\d{1,3}(?:\.\d{3})*)\s*€", text_content)
            price = f"{price_match.group(1)} €" if price_match else "Su richiesta"

            # Rilevamento metratura m²
            area_match = re.search(r"(\d{1,4}(?:[.,]\d+)?)\s*(?:m²|qm|Quadratmeter)", text_content, re.IGNORECASE)
            area_sqm = f"{area_match.group(1)} m²" if area_match else "Da verificare"

            # Riconoscimento località
            location = "Circondario Francoforte"
            for loc in ["Schöneck", "Kilianstädten", "Büdesheim", "Oberdorfelden", 
                        "Nidderau", "Windecken", "Heldenbergen", "Ostheim", "Erbstadt",
                        "Bad Vilbel", "Karben", "Hanau", "Frankfurt"]:
                if loc.lower() in text_content.lower() or loc.lower() in url.lower():
                    location = loc
                    break

            train_info = self.determine_train_connection(location)

            source = "Kleinanzeigen" if "kleinanzeigen" in url.lower() else "ImmoScout24" if "immobilienscout24" in url.lower() else "Portale Web"

            return ListingItem(
                title=title[:100],
                link=url,
                source=source,
                category="Land",
                location=location,
                price=price,
                area_sqm=area_sqm,
                train_info=train_info,
                details=f"Annuncio analizzato direttamente: {title}"
            )
        except Exception as e:
            print(f"[ManualImporter] Errore analisi URL {url}: {e}")
            return None

    def parse_exported_file(self, file_path: str) -> List[ListingItem]:
        """
        Analizza un file HTML o JSON esportato contenente elenchi di annunci.
        """
        items: List[ListingItem] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if file_path.endswith(".json"):
                data = json.loads(content)
                if isinstance(data, list):
                    for entry in data:
                        items.append(ListingItem(
                            title=entry.get("title", "Terreno"),
                            link=entry.get("link", ""),
                            source=entry.get("source", "Export File"),
                            category="Land",
                            location=entry.get("location", "N/D"),
                            price=entry.get("price", "N/D"),
                            area_sqm=entry.get("area_sqm", "N/D"),
                            train_info=self.determine_train_connection(entry.get("location", "")),
                            details=entry.get("details", "")
                        ))
            else: # HTML
                soup = BeautifulSoup(content, "html.parser")
                links = soup.find_all("a", href=True)
                for l in links:
                    href = l["href"]
                    text = l.get_text(strip=True)
                    if any(w in text.lower() for w in ["grundstück", "baugrund", "land"]):
                        items.append(ListingItem(
                            title=text[:90],
                            link=href,
                            source="File HTML Esportato",
                            category="Land",
                            location="Schöneck / Nidderau",
                            price="Vedi file",
                            area_sqm="Vedi file",
                            train_info=self.determine_train_connection(text),
                            details=text
                        ))
        except Exception as e:
            print(f"[ManualImporter] Errore lettura file esportato: {e}")

        return items
