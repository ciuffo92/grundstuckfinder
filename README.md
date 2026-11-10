# 🏡 Baugrundstück Finder & Early Infrastructure Monitor
### Bot Python per il monitoraggio di terreni edificabili a Schöneck, Nidderau e circondario di Francoforte sul Meno con avvisi WhatsApp

---

## 🎯 Obiettivo del Progetto
Questo bot locale monitora costantemente la comparsa di **terreni edificabili (Baugrundstücke)** e soprattutto intercetta **segnali anticipati di nuove lottizzazioni** nelle zone strategiche collegate a Francoforte sul Meno tramite treno:
- **Schöneck** (Kilianstädten, Büdesheim, Oberdorfelden) -> Linea ferroviaria **RB34 (Niddertalbahn)** diretta verso Frankfurt Hbf / Bad Vilbel.
- **Nidderau** (Heldenbergen, Windecken, Ostheim, Erbstadt, Eichen) -> Linee **RB34** e **RB49** (diretto verso Hanau e Friedberg).
- **Circondario collegato** (Bad Vilbel - S6, Karben - S6, Maintal, Hanau).

---

## 🚜 La Funzionalità "Deep Search" (Tubi, Fognature & Bandi Comunali)
I normali acquirenti cercano su ImmoScout o Kleinanzeigen quando i lotti sono già in vendita (e spesso contesi o venduti a prezzi gonfiati). 

Questo bot esegue una **Deep Search** interrogando le fonti a monte:
1. **Lavori Stradali e Tubazioni ("The man who builds the tubes")**:
   Prima che un terreno possa essere edificato, il comune deve approvare la lottizzazione ed emanare bandi pubblici per l'**Erschließung** (posa di tubi per l'acqua potabile, fognature *Kanalbau*, strade di accesso, posa cavi e *Tiefbau*).
   Il bot monitora la **HAD (Hessische Ausschreibungsdatenbank)** e **Bund.de** per intercettare i bandi di posa tubi a Schöneck e Nidderau: **questo ti avvisa da 6 a 18 mesi prima che i terreni compaiano sul mercato!**
2. **Piani di Lottizzazione Comunali (Bebauungspläne / B-Plan)**:
   Scansione periodica di `bauleitplanung.hessen.de` e delle delibere dei comuni di Schöneck (`schoeneck.de`) e Nidderau (`nidderau.de`) per *Offenlagen* e *Aufstellungsbeschlüsse*.
3. **Aste Giudiziarie Ufficiali Tedesche (`zvg-portal.de`)**:
   Monitoraggio per l'**Amtsgericht Hanau** (che ha competenza su Schöneck e Nidderau) e **Amtsgericht Frankfurt am Main** per terreni (*Unbebaute Grundstücke* / *Baugrundstücke*) venduti all'asta.
4. **Analisi Manuale & Importazione**:
   Per evitare che portali come Kleinanzeigen o ImmoScout blocchino l'IP con CAPTCHA/Cloudflare, puoi passare qualsiasi link o file esportato al bot per estrarre dati, verificare che non sia duplicato e ricevere la notifica WhatsApp formattata.

---

## 📱 Configurazione Notifiche WhatsApp (CallMeBot)
Il bot usa **CallMeBot**, un gateway gratuito per messaggi WhatsApp personali che non richiede carte di credito o account business:

1. Aggiungi alla tua rubrica WhatsApp il numero di CallMeBot: **`+34 941 12 00 20`** (o clicca [qui](https://api.whatsapp.com/send?phone=34941120020)).
2. Invia a questo numero il seguente messaggio WhatsApp:
   ```text
   I allow callmebot to send me messages
   ```
3. Riceverai immediatamente una risposta con il tuo **API Key** personale.
4. Apri il file `config/settings.yaml` e inserisci il tuo numero di telefono e la chiave:
   ```yaml
   notifications:
     whatsapp:
       enabled: true
       provider: "callmebot"
       callmebot:
         phone_number: "+491701234567" # Oppure +39340...
         api_key: "123456"
   ```

---

## 🚀 Installazione & Avvio

### 1. Installazione librerie Python
Assicurati di avere Python installato sul computer, quindi apri il terminale nella cartella del progetto ed esegui:
```bash
pip install -r requirements.txt
```

### 2. Test Notifica WhatsApp
Verifica che WhatsApp riceva i messaggi dal bot con:
```bash
python main.py --test-notify
```

### 3. Esecuzione Scansione Completa
Per eseguire una scansione immediata di tutte le fonti (ZVG, Delibere comunali, Bandi tubi/Erschließung):
```bash
python main.py --run-once
```

### 4. Monitoraggio Continuo in Background
Per lasciare il bot attivo e farlo scansionare ogni ora (configurabile in `settings.yaml`):
```bash
python main.py --schedule
```

### 5. Importazione Rapida Link (Kleinanzeigen / ImmoScout)
Se trovi un annuncio interessante sul web e vuoi salvarlo nel database e inviarti la notifica formattata:
```bash
python main.py --import-url "https://www.kleinanzeigen.de/s-anzeige/baugrundstueck-in-schoeneck/..."
```

### 6. Controllo Stato Database
Per visualizzare quanti annunci e bandi sono stati registrati:
```bash
python main.py --status
```

---

## 📁 Struttura del Progetto
```text
baugrundstueck_finder/
│
├── config/
│   ├── settings.yaml            # Configurazione zone, treni, parole chiave, WhatsApp
│   └── config.py                # Loader configurazione
│
├── db/
│   ├── database.py              # Gestore SQLite (memorizza ID, deduplica, segna notifiche)
│   └── baugrundstueck.db        # Database locale generato automaticamente
│
├── notifiers/
│   ├── base.py                  # Formattatore messaggi per WhatsApp / Telegram
│   ├── whatsapp.py              # Client WhatsApp (CallMeBot & Twilio)
│   ├── telegram.py              # Client Telegram (opzionale)
│   └── dispatcher.py            # Smistamento notifiche
│
├── scrapers/
│   ├── base.py                  # Classe base e rilevamento linee treno RB34/RB49/S6
│   ├── zvg_portal.py            # Aste giudiziarie AG Hanau e AG Frankfurt
│   ├── deep_infrastructure.py   # Deep Search: Bandi tubazioni, fognature ed Erschließung
│   ├── municipal_bplan.py       # Piani urbanistici e delibere comunali Schöneck e Nidderau
│   ├── rss_monitor.py           # Feed RSS e Google Alerts
│   └── manual_importer.py       # Parser URL e file esportati da Kleinanzeigen/ImmoScout
│
├── main.py                      # Orchestratore, CLI e Scheduler
├── requirements.txt             # Dipendenze Python
└── README.md                    # Documentazione completa
```
