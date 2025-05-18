from flask import Flask, render_template, request, redirect, url_for, jsonify
import json, os
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from flask import current_app  # Wichtig für Konfiguration

app = Flask(__name__)
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
MASTER_FILE = os.path.join(DATA_FOLDER,'master_list.json')
CATEGORIES_FILE = os.path.join(DATA_FOLDER,'categories.json')
CHECKLIST_DIR = os.path.join(DATA_FOLDER,'checklists')
ARCHIV_DIR = os.path.join(DATA_FOLDER,'archiv')
ITEMKATEGORIEN_FILE = os.path.join(DATA_FOLDER,"item_kategorien.json")


os.makedirs(CHECKLIST_DIR, exist_ok=True)
os.makedirs(ARCHIV_DIR, exist_ok=True)

def load_master_list():
    if not os.path.exists(MASTER_FILE):
        return []
    with open(MASTER_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_master_list(data):
    with open(MASTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_categories():
    if not os.path.exists(CATEGORIES_FILE):
        return []
    with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_categories(data):
    with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_checklist(name, data, archive=False):
    directory = ARCHIV_DIR if archive else CHECKLIST_DIR
    with open(os.path.join(directory, f"{name}.json"), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_checklist(name, archive=False):
    directory = ARCHIV_DIR if archive else CHECKLIST_DIR
    path = os.path.join(directory, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def load_json(path, default=[]):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/', methods=['GET', 'POST'])
def index():
    categories = load_categories()
    if request.method == 'POST':
        titel = request.form['titel']
        kategorie = request.form['kategorie']
        tage = int(request.form['tage'])
        master_list = load_master_list()
        items = []
        for item in master_list:
            if kategorie in item['kategorien']:
                eintrag = {
                    "name": item["name"],
                    "checked": False,
                    "item_kategorie": item.get("item_kategorie", "Sonstiges")
                }
                if item.get("verbrauchbar"):
                    eintrag["anzahl"] = item["anzahl_pro_tag"] * tage
                items.append(eintrag)
        checklist_data = {
            "titel": titel,
            "kategorie": kategorie,
            "tage": tage,
            "items": items,
            "erstellt": datetime.now().isoformat()
        }
        filename = f"{titel.lower().replace(' ', '_')}"
        save_checklist(filename, checklist_data)
        return redirect(url_for('view_checklist', name=filename))

    files = Path(CHECKLIST_DIR).glob('*.json')
    checklisten = [f.stem for f in files]
    return render_template('index.html', checklisten=checklisten, categories=categories)

@app.route('/checkliste/<name>', methods=['GET', 'POST'])
def view_checklist(name):
    with open(os.path.join(CHECKLIST_DIR, f"{name}.json"), 'r', encoding="utf-8") as f:
        data = json.load(f)

    if os.path.exists(ITEMKATEGORIEN_FILE):
        with open(ITEMKATEGORIEN_FILE, 'r', encoding='utf-8') as f:
            itemkategorien = json.load(f)

    if request.method == 'POST':
        if 'update_checklist' in request.form:
            for item in data['items']:
                checkbox_name = f"checked_{item['name']}"
                item['checked'] = checkbox_name in request.form



        elif 'archivieren' in request.form:
            src = os.path.join(CHECKLIST_DIR, f"{name}.json")
            dst = os.path.join(ARCHIV_DIR, f"{name}.json")
            if os.path.exists(src):
                os.rename(src, dst)
                return redirect(url_for('index'))
            
        elif 'add_item' in request.form:
            item_name = request.form['name']
            item_kategorie = request.form['item_kategorie']
            verbrauchbar = 'verbrauchbar' in request.form
            anzahl_pro_tag = int(request.form['anzahl_pro_tag']) if verbrauchbar and request.form.get('anzahl_pro_tag') else 0

            neues_item = {
                "name": item_name,
                "item_kategorie": item_kategorie,
                "verbrauchbar": verbrauchbar,
                "anzahl_pro_tag": anzahl_pro_tag,
                "checked": False
            }

            data['items'].append(neues_item)

        with open(os.path.join(CHECKLIST_DIR, f"{name}.json"), 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # Gruppierung nach item_kategorie
    grouped_items = defaultdict(list)
    for item in data['items']:
        kategorie = item.get("item_kategorie", "Sonstiges")
        grouped_items[kategorie].append(item)

    return render_template("checklist.html", name=name, grouped_items=grouped_items, itemkategorien=itemkategorien)

@app.route('/archiv', methods=['GET', 'POST'])
def archiv():
    archiv_dir = current_app.config.get('ARCHIV_DIR', ARCHIV_DIR)
    checklist_dir = current_app.config.get('CHECKLIST_DIR', CHECKLIST_DIR)

    archived_files = Path(archiv_dir).glob('*.json')
    archived = [f.stem for f in archived_files]
    if request.method == 'POST':
        name = request.form['restore']
        src = os.path.join(archiv_dir, f'{name}.json')
        dst = os.path.join(checklist_dir, f'{name}.json')
        os.rename(src, dst)
        return redirect(url_for('archiv'))
    return render_template('archiv.html', checklisten=archived)

@app.route('/kategorien', methods=['GET', 'POST'])
def kategorien():
    categories = load_categories()
    if request.method == 'POST':
        if 'neue_kategorie' in request.form:
            new_cat = request.form['neue_kategorie'].strip()
            if new_cat and new_cat not in categories:
                categories.append(new_cat)
        elif 'delete' in request.form:
            to_delete = request.form['delete']
            categories = [cat for cat in categories if cat != to_delete]
        save_categories(categories)
    return render_template('kategorien.html', categories=categories)

@app.route("/masterliste", methods=["GET", "POST"])
def masterliste():
    items = load_master_list()
    itemkategorien = load_json(ITEMKATEGORIEN_FILE)
    categories = load_categories()

    # Item löschen
    if request.method == "POST" and "delete_item" in request.form:
        delete_name = request.form["delete_item"]
        items = [item for item in items if item["name"] != delete_name]
        save_json(MASTER_FILE, items)
        return redirect(url_for("masterliste"))

    # Neues Item hinzufügen
    if request.method == "POST" and "add_item" in request.form:
        name = request.form["name"]
        item_kategorie = request.form["item_kategorie"]
        verbrauchbar = "verbrauchbar" in request.form
        anzahl_pro_tag = request.form.get("anzahl_pro_tag")
        

        neues_item = {
            "name": name,
            #"categories": categories,
            "item_kategorie": item_kategorie,
            "verbrauchbar": verbrauchbar,
            "kategorien": request.form.getlist("kategorie") 
        }

        if verbrauchbar and anzahl_pro_tag:
            try:
                neues_item["anzahl_pro_tag"] = int(anzahl_pro_tag)
            except ValueError:
                neues_item["anzahl_pro_tag"] = 1

        items.append(neues_item)
        save_json(MASTER_FILE, items)
        return redirect(url_for("masterliste"))

    return render_template("masterliste.html", items=items, itemkategorien=itemkategorien, categories=categories)

@app.route('/itemkategorien', methods=['GET', 'POST'])
def itemkategorien():
    #if not os.path.exists('item_kategorien.json'):
    #    with open('item_kategorien.json', 'w', encoding="utf-8") as f:
    #        json.dump([], f, indent=2, ensure_ascii=False)

    #with open('item_kategorien.json', 'r', encoding="utf-8") as f:
    #    kategorien = json.load(f)

    kategorien = load_json(ITEMKATEGORIEN_FILE)

    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name', '').strip()
        if action == 'add' and name and name not in kategorien:
            kategorien.append(name)
        elif action == 'delete' and name in kategorien:
            kategorien.remove(name)

        with open('item_kategorien.json', 'w', encoding="utf-8") as f:
            json.dump(kategorien, f, indent=2, ensure_ascii=False)

        return redirect(url_for('itemkategorien'))

    return render_template('itemkategorien.html', kategorien=kategorien)

@app.route("/checkliste/<name>/toggle", methods=["POST"])
def toggle_check_item(name):
    file_path = os.path.join(CHECKLIST_DIR, f"{name}.json")
    if not os.path.exists(file_path):
        return "Datei nicht gefunden", 404

    data = request.get_json()
    item_name = data.get("item_name")
    checked = data.get("checked")

    with open(file_path, "r", encoding="utf-8") as f:
        checkliste = json.load(f)

    # Zugriff auf checkliste["items"]
    for item in checkliste.get("items", []):
        if item["name"] == item_name:
            item["checked"] = checked
            break

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(checkliste, f, indent=2, ensure_ascii=False)

    return "", 204

@app.route("/checkliste/<name>/delete", methods=["POST"])
def delete_checkliste(name):
    # Pfad zur Checkliste
    pfad = os.path.join(CHECKLIST_DIR, f"{name}.json")
    if os.path.exists(pfad):
        os.remove(pfad)
    return redirect(url_for("index"))

@app.route('/update_item_field', methods=['POST'])
def update_item_field():
    data = request.json
    index = int(data.get('index'))
    field = data.get('field')
    value = data.get('value')

    with open(MASTER_FILE, 'r', encoding="utf-8") as f:
        master = json.load(f)

    # Typkonvertierungen
    if field == 'verbrauchbar':
        value = value == 'true'
    elif field == 'anzahl_pro_tag':
        value = int(value)

    master[index][field] = value

    with open(MASTER_FILE, 'w', encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)

    return jsonify(success=True)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
