from flask import Flask, render_template, request, redirect, url_for
import json, os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

app = Flask(__name__)
MASTER_FILE = 'master_list.json'
CATEGORIES_FILE = 'categories.json'
CHECKLIST_DIR = 'checklists'
ARCHIV_DIR = 'archiv'
MASTER_LIST_FILE = "master_list.json"

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
                    eintrag["anzahl"] = item["pro_tag"] * tage
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

        with open(os.path.join(CHECKLIST_DIR, f"{name}.json"), 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # Gruppierung nach item_kategorie
    grouped_items = defaultdict(list)
    for item in data['items']:
        kategorie = item.get("item_kategorie", "Sonstiges")
        grouped_items[kategorie].append(item)

    return render_template("checklist.html", name=name, grouped_items=grouped_items)

@app.route('/archiv', methods=['GET', 'POST'])
def archiv():
    archived_files = Path(ARCHIV_DIR).glob('*.json')
    archived = [f.stem for f in archived_files]
    if request.method == 'POST':
        name = request.form['restore']
        src = os.path.join(ARCHIV_DIR, f'{name}.json')
        dst = os.path.join(CHECKLIST_DIR, f'{name}.json')
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

@app.route('/masterliste', methods=['GET', 'POST'])
def masterliste():
    # Masterliste laden
    with open(MASTER_LIST_FILE, 'r', encoding="utf-8") as f:
        master = json.load(f)

    # Item-Kategorien laden
    if os.path.exists('item_kategorien.json'):
        with open('item_kategorien.json', 'r', encoding="utf-8") as f:
            item_kategorien = json.load(f)
    else:
        item_kategorien = []

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form['name']
            kategorien = request.form.getlist('kategorien')
            item_kategorie = request.form.get('item_kategorie')
            verbrauchbar = 'verbrauchbar' in request.form
            anzahl = int(request.form.get('anzahl_pro_tag', 0)) if verbrauchbar else 0
            master.append({
                "name": name,
                "kategorien": kategorien,
                "item_kategorie": item_kategorie,
                "verbrauchbar": verbrauchbar,
                "anzahl_pro_tag": anzahl
            })

        elif action == 'delete':
            index = int(request.form['index'])
            master.pop(index)

        elif action == 'edit':
            index = int(request.form['index'])
            master[index]['name'] = request.form['name']
            master[index]['kategorien'] = request.form.getlist('kategorien')
            master[index]['item_kategorie'] = request.form.get('item_kategorie')
            master[index]['verbrauchbar'] = 'verbrauchbar' in request.form
            if master[index]['verbrauchbar']:
                master[index]['anzahl_pro_tag'] = int(request.form.get('anzahl_pro_tag', 0))
            else:
                master[index]['anzahl_pro_tag'] = 0

        # Speichern
        with open(MASTER_LIST_FILE, 'w', encoding="utf-8") as f:
            json.dump(master, f, indent=2, ensure_ascii=False)

        return redirect(url_for('masterliste'))

    return render_template('masterliste.html', master=master, item_kategorien=item_kategorien)

@app.route('/itemkategorien', methods=['GET', 'POST'])
def itemkategorien():
    if not os.path.exists('item_kategorien.json'):
        with open('item_kategorien.json', 'w', encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    with open('item_kategorien.json', 'r', encoding="utf-8") as f:
        kategorien = json.load(f)

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



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
