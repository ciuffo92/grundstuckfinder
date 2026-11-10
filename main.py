import argparse
import time
import schedule
from datetime import datetime
from config.config import load_settings
from db.database import Database
from notifiers.dispatcher import NotificationDispatcher
from scrapers.zvg_portal import ZvgPortalScraper
from scrapers.deep_infrastructure import DeepInfrastructureScraper
from scrapers.municipal_bplan import MunicipalBPlanScraper
from scrapers.rss_monitor import RssMonitorScraper
from scrapers.manual_importer import ManualListingImporter

def run_pipeline(db: Database, dispatcher: NotificationDispatcher, settings: dict):
    """
    Esegue il ciclo completo di monitoraggio su tutte le fonti attive:
    1. Aste ZVG (Amtsgericht Hanau e Frankfurt)
    2. Deep Search Infrastrutture / Tubi / Bandi (HAD e Bund.de)
    3. Piani di lottizzazione comunali (B-Plan Schöneck e Nidderau)
    4. Feed RSS
    5. Deduplicazione su SQLite e invio notifiche WhatsApp
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Avvio scansione fonti...")

    scrapers = [
        ZvgPortalScraper(settings),
        DeepInfrastructureScraper(settings),
        MunicipalBPlanScraper(settings),
        RssMonitorScraper(settings),
    ]

    new_items_count = 0

    for scraper in scrapers:
        scraper_name = scraper.__class__.__name__
        print(f"-> Esecuzione {scraper_name}...")
        try:
            items = scraper.fetch_listings()
            print(f"   Trovati {len(items)} elementi da {scraper_name}.")
            for item in items:
                inserted = db.insert_listing(item.to_dict())
                if inserted:
                    new_items_count += 1
        except Exception as e:
            print(f"   Errore su {scraper_name}: {e}")

    print(f"Scansione completata. Nuovi annunci/segnali registrati: {new_items_count}")

    # Invio notifiche per tutti i nuovi elementi non ancora inviati
    pending = db.get_pending_notifications()
    if pending:
        print(f"Invio di {len(pending)} notifiche WhatsApp in corso...")
        for item in pending:
            success = dispatcher.notify_listing(item)
            if success:
                db.mark_as_notified(item["id"])
                # Piccola pausa tra messaggi per non saturare la connessione
                time.sleep(1)
        print("Notifiche inviate!")
    else:
        print("Nessuna nuova notifica in sospeso.")

def main():
    parser = argparse.ArgumentParser(description="Bot Monitoraggio Terreni Edificabili (Schöneck / Nidderau / Francoforte)")
    parser.add_argument("--run-once", action="store_true", help="Esegue una singola scansione ed esce")
    parser.add_argument("--schedule", action="store_true", help="Avvia il monitoraggio periodico programmato")
    parser.add_argument("--test-notify", action="store_true", help="Invia un messaggio di prova su WhatsApp")
    parser.add_argument("--import-url", type=str, help="Analizza e notifica manualmente un URL specifico (es. Kleinanzeigen)")
    parser.add_argument("--status", action="store_true", help="Mostra lo stato e il riepilogo del database locale")

    args = parser.parse_args()

    settings = load_settings()
    db = Database()
    dispatcher = NotificationDispatcher(settings)

    if args.test_notify:
        print("Invio messaggio di prova WhatsApp...")
        test_item = {
            "title": "Terreno di Prova - Schöneck Büdesheim (Test)",
            "link": "https://www.schoeneck.de",
            "source": "Test Automatico",
            "category": "Land",
            "location": "Schöneck (Büdesheim)",
            "price": "350.000 €",
            "area_sqm": "520 m²",
            "train_info": "RB34 (Niddertalbahn -> Frankfurt Hbf in 30 min)",
            "details": "Questo è un messaggio di test dal tuo bot Python. Il sistema di allerta WhatsApp è attivo e funzionante!"
        }
        success = dispatcher.notify_listing(test_item)
        if success:
            print("Messaggio di prova inviato con successo sul tuo WhatsApp!")
        else:
            print("Invio fallito. Controlla il numero di telefono e la chiave API in config/settings.yaml.")
        return

    if args.import_url:
        print(f"Analisi manuale URL: {args.import_url}")
        importer = ManualListingImporter(settings)
        item = importer.parse_url(args.import_url)
        if item:
            item_dict = item.to_dict()
            inserted = db.insert_listing(item_dict)
            if inserted:
                print("Elemento inserito nel database. Invio notifica WhatsApp...")
                dispatcher.notify_listing(item_dict)
                db.mark_as_notified(db.generate_id(item_dict["link"], item_dict["title"]))
            else:
                print("L'annuncio è già presente nel database (nessun duplicato inviato).")
        else:
            print("Impossibile estrarre informazioni dall'URL fornito.")
        return

    if args.status:
        with db._get_connection() as conn:
            c = conn.cursor()
            total = c.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
            notified = c.execute("SELECT COUNT(*) FROM listings WHERE notified = 1").fetchone()[0]
            by_cat = c.execute("SELECT category, COUNT(*) FROM listings GROUP BY category").fetchall()
            print(f"=== STATO DATABASE ===")
            print(f"Totale elementi tracciati: {total}")
            print(f"Notifiche inviate: {notified}")
            print(f"Per categoria:")
            for cat, count in by_cat:
                print(f"  - {cat}: {count}")
        return

    if args.schedule:
        interval = settings.get("scheduler", {}).get("interval_minutes", 60)
        print(f"Avvio monitoraggio pianificato ogni {interval} minuti.")
        # Esegui subito al lancio
        run_pipeline(db, dispatcher, settings)
        schedule.every(interval).minutes.do(run_pipeline, db, dispatcher, settings)
        try:
            while True:
                schedule.run_pending()
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nMonitoraggio interrotto dall'utente.")
        return

    # Default se nessun flag passato: esegui una volta
    run_pipeline(db, dispatcher, settings)

if __name__ == "__main__":
    main()
