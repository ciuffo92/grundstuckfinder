import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseScraper, ListingItem

class DeepInfrastructureScraper(BaseScraper):
    """
    DEEP SEARCH: 'The man who builds the tubes in the street'.
    Monitora i bandi pubblici di gara d'appalto (Öffentliche Ausschreibungen) in Hessen
    per lavori di:
      - Erschließung (urbanizzazione primaria)
      - Kanalbau & Tiefbau (scavi, posa fognature e tubazioni)
      - Wasserleitungsbau (tubi acqua potabile)
      - Straßenbau per nuove lottizzazioni (Neubaugebiete)

    Fonti monitorate:
      1. HAD (Hessische Ausschreibungsdatenbank / had.de)
      2. Bund.de Vergabeplattform (circondario Main-Kinzig / Frankfurt)
      3. Bandi diretti dei comuni di Schöneck e Nidderau
    """

    # Feed e pagine pubbliche per appalti pubblici in Hessen / Germania
    TENDER_FEEDS = [
        {
            "name": "Bund.de Ausschreibungen Hessen",
            "url": "https://www.service.bund.de/Content/DE/Ausschreibungen/Suche/Ausschreibungssuche_Formular.html?view=renderRss&nn=4641496",
            "type": "rss"
        },
        {
            "name": "HAD Hessische Ausschreibungsdatenbank",
            "url": "https://www.had.de/onlinesuche_einfach.html",
            "type": "had_portal"
        }
    ]

    TARGET_LOCATIONS = ["schöneck", "nidderau", "kilianstädten", "büdesheim", "oberdorfelden", 
                        "windecken", "heldenbergen", "ostheim", "erbstadt", "main-kinzig", "bad vilbel", "karben"]

    INFRASTRUCTURE_KEYWORDS = [
        "erschließung", "erschliessung", "neubaugebiet", "kanalbau", 
        "tiefbau", "rohrleitungsbau", "wasserleitung", "baulanderschließung",
        "erschließungsstraße", "wohngebiet"
    ]

    def fetch_listings(self) -> List[ListingItem]:
        items: List[ListingItem] = []

        # 1. Scansione Feed RSS gare d'appalto Bund.de
        items.extend(self._check_bund_rss())

        # 2. Consultazione HAD (Hessische Ausschreibungsdatenbank)
        items.extend(self._check_had_tenders())

        return items

    def _check_bund_rss(self) -> List[ListingItem]:
        items = []
        try:
            feed_info = self.TENDER_FEEDS[0]
            resp = requests.get(feed_info["url"], headers=self.headers, timeout=20)
            if resp.status_code != 200:
                return items

            root = ET.fromstring(resp.content)
            channel = root.find("channel")
            if channel is None:
                return items

            for item_elem in channel.findall("item"):
                title = item_elem.findtext("title", "")
                link = item_elem.findtext("link", "")
                description = item_elem.findtext("description", "")
                full_text = f"{title} {description}".lower()

                # Verifica se riguarda le nostre località target
                matches_location = any(loc in full_text for loc in self.TARGET_LOCATIONS)
                # Verifica se riguarda lavori infrastrutturali / tubi / lottizzazione
                matches_infra = any(kw in full_text for kw in self.INFRASTRUCTURE_KEYWORDS)

                if matches_location and matches_infra:
                    # Identifica il comune
                    detected_loc = "Circondario Francoforte / MKK"
                    for loc in ["Schöneck", "Nidderau", "Bad Vilbel", "Karben"]:
                        if loc.lower() in full_text:
                            detected_loc = loc
                            break

                    train_info = self.determine_train_connection(detected_loc)

                    items.append(ListingItem(
                        title=f"Nuova Erschließung/Tubi rilevata: {title}",
                        link=link,
                        source="Bund.de Appalti Pubblici (Tiefbau/Kanal)",
                        category="DeepSearch-Tender",
                        location=detected_loc,
                        price="Appalto pubblico (anticipa vendita lotti)",
                        area_sqm="In fase di lottizzazione/posa tubi",
                        train_info=train_info,
                        details=(
                            f"⚠️ SEGNALE ANTICIPATO: È stato pubblicato un bando per posa tubi/fognature/strade. "
                            f"Qui nasceranno nuovi terreni edificabili prima dell'uscita sui portali! Estratto: {description[:200]}"
                        )
                    ))
        except Exception as e:
            print(f"[DeepInfrastructure] Errore RSS Bund.de: {e}")

        return items

    def _check_had_tenders(self) -> List[ListingItem]:
        """
        Simula/interroga la banca dati appalti dell'Assia (HAD)
        per parole chiave di lottizzazione stradale e idrica.
        """
        items = []
        try:
            url = "https://www.had.de/onlinesuche_einfach.html"
            for term in ["Erschließung Schöneck", "Kanalbau Nidderau", "Neubaugebiet Schöneck", "Neubaugebiet Nidderau"]:
                params = {"suchtext": term, "action": "suche"}
                resp = requests.get(url, params=params, headers=self.headers, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                # Analizza i risultati trovati
                results = soup.find_all("div", class_="suchergebnis") or soup.find_all("tr")
                for res in results:
                    text = res.get_text(separator=" ", strip=True)
                    text_lower = text.lower()
                    if any(kw in text_lower for kw in ["erschließung", "kanalbau", "tiefbau", "straße"]):
                        link_elem = res.find("a", href=True)
                        link = link_elem["href"] if link_elem else url
                        if not link.startswith("http"):
                            link = f"https://www.had.de/{link.lstrip('/')}"

                        loc = "Schöneck" if "schöneck" in term.lower() else "Nidderau"
                        items.append(ListingItem(
                            title=f"HAD Appalto Lavori {term}: {text[:80]}",
                            link=link,
                            source="HAD Hessische Ausschreibungsdatenbank",
                            category="DeepSearch-Tender",
                            location=loc,
                            price="Bando di gara infrastrutture",
                            area_sqm="Lottizzazione in corso",
                            train_info=self.determine_train_connection(loc),
                            details=f"Posa tubazioni / fognature / opere stradali comunali: {text[:220]}"
                        ))
        except Exception as e:
            print(f"[DeepInfrastructure] Errore consultazione HAD: {e}")

        return items
