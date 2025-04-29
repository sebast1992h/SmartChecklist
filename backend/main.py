from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path

app = FastAPI()

# CORS für React zulassen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # oder z.B. ["http://checklisten.local:3000"]
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent / "data" / "master_items.json"

@app.get("/api/items")
def get_items():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

@app.get("/api/generate")
def generate(kategorie: str, tage: int):
    with open(DATA_PATH, "r") as f:
        items = json.load(f)

    checklist = []
    for item in items:
        if kategorie in item["kategorien"]:
            anzahl = item["verbrauch_pro_tag"] * tage if item["verbrauchbar"] else 1
            checklist.append({
                "name": item["name"],
                "anzahl": anzahl,
                "abgehakt": False
            })
    return checklist
