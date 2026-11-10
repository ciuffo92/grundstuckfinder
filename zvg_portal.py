import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseScraper, ListingItem

class ZvgPortalScraper(BaseScraper):
    """
    Scraper per il portale ufficiale delle aste giudiziarie tedesche (zvg-portal.de).
    Monitora le vendite all'asta di terreni (Amtsgericht Hanau, Frankfurt am Main, Friedberg).
    Nota: Schöneck e Nidderau appartengono alla giurisdizione dell'Amtsgericht Hanau!
    """

    BASE_URL = "https://www.zvg-portal.de/index.php"

    COURTS = [
        {"name": "Hanau", "land_id": "HE", "court_id": "B1103"}, # AG Hanau (include Schöneck, Nidderau, Maintal)
        {"name": "Frankfurt am Main", "land_id": "HE", "court_id": "B1101"}, # AG Frankfurt
        {"name": "Friedberg", "land_id": "HE", "court_id": "B1102"}, # AG Friedberg (include Karben)
    ]

    def fetch_listings(self) -> List[ListingItem]:
        items: List[ListingItem] = []
        session = requests.Session()
        session.headers.update(self.headers)

        for court in self.COURTS:
            try:
                # 1. Richiesta iniziale del modulo di ricerca
                search_url = f"{self.BASE_URL}?button=Suchen"
                init_res = session.get(search_url, timeout=15)
                if init_res.status_code != 200:
                    continue

                # 2. Invio ricerca per tribunale e terreni (Land Hessen)
                # Nel portale ZVG il parametro ger_id identifica il tribunale
                post_data = {
                    "ger_name": court["name"],
                    "land_abk": "he",
                    "order_by": "2",
                    "button": "Suchen",
                }

                res = session.post(search_url, data=post_data, timeout=20)
                if res.status_code != 200:
                    continue

                soup = BeautifulSoup(res.text, "html.parser")
                rows = soup.find_all("tr")

                for row in rows:
                    text = row.get_text(separator=" ", strip=True)
                    text_lower = text.lower()

                    # Cerchiamo terreni / baugrund / unbebaute Grundstücke o località target
                    is_target_location = any(loc.lower() in text_lower for loc in ["schöneck", "nidderau", "frankfurt", "vilbel", "karben", "maintal"])
                    is_land = any(kw.lower() in text_lower for kw in ["grundstück", "unbebaut", "baugrund", "acker", "bauland"])

                    if is_target_location or (is_land and court["name"] in ["Hanau", "Frankfurt am Main"]):
                        # Estrai link ai dettagli se presente
                        link_tag = row.find("a", href=True)
                        link = self.BASE_URL
                        if link_tag:
                            href = link_tag["href"]
                            link = href if href.startswith("http") else f"https://www.zvg-portal.de/{href}"

                        # Estrai prezzo di stima (Verkehrswert)
                        price = "Vedi perizia"
                        if "eur" in text_lower or "€" in text:
                            for part in text.split():
                                if "eur" in part.lower() or "€" in part:
                                    price = part

                        location = court["name"]
                        for loc in ["Schöneck", "Nidderau", "Bad Vilbel", "Karben", "Maintal", "Frankfurt"]:
                            if loc.lower() in text_lower:
                                location = loc
                                break

                        train_info = self.determine_train_connection(location)

                        items.append(ListingItem(
                            title=f"Asta ZVG: {text[:80]}",
                            link=link,
                            source=f"ZVG Amtsgericht {court['name']}",
                            category="Auction",
                            location=location,
                            price=price,
                            area_sqm="Specificata in perizia (Gutachten)",
                            train_info=train_info,
                            details=f"Procedura d'asta giudiziaria presso AG {court['name']}. Estratto: {text[:200]}"
                        ))

            except Exception as e:
                print(f"[ZVG Scraper] Errore durante la consultazione per {court['name']}: {e}")

        return items
