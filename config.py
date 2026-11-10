import os
import yaml
from pathlib import Path
from typing import Dict, Any, List

CONFIG_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = CONFIG_DIR / "settings.yaml"

def load_settings() -> Dict[str, Any]:
    """Carica le impostazioni da settings.yaml."""
    if not SETTINGS_FILE.exists():
        raise FileNotFoundError(f"File di configurazione non trovato: {SETTINGS_FILE}")
    
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_monitored_locations() -> List[str]:
    """Restituisce l'elenco di tutte le località e frazioni monitorate."""
    settings = load_settings()
    locations = []
    
    # Località primarie (Schöneck, Nidderau e frazioni)
    for loc in settings.get("locations", {}).get("primary", []):
        locations.append(loc["name"])
        for sub in loc.get("subdistricts", []):
            locations.append(sub)
            
    # Circondario
    for loc in settings.get("locations", {}).get("surrounding", []):
        locations.append(loc["name"])
        
    return list(set(locations))

def get_train_routes() -> Dict[str, List[str]]:
    """Restituisce le linee ferroviarie associate a ogni comune monitorato."""
    settings = load_settings()
    routes = {}
    for group in ["primary", "surrounding"]:
        for loc in settings.get("locations", {}).get(group, []):
            routes[loc["name"]] = loc.get("train_lines", [])
    return routes
