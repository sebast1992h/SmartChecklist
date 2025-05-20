import os
import json
import uuid

CHECKLIST_DIR = os.path.join('transform')

def add_uuids_to_checklist(filename):
    path = os.path.join("transform", f"{filename}.json")
    with open(path, "r", encoding="utf-8") as f:
        checklist = json.load(f)

    items = checklist.get("items", [])
    for item in items:
        if isinstance(item, dict) and "uuid" not in item:
            item["uuid"] = str(uuid.uuid4())

    with open(path, "w", encoding="utf-8") as f:
        json.dump(checklist, f, indent=2, ensure_ascii=False)




if __name__ == '__main__':
    add_uuids_to_checklist("whv_besuch_23.05.-25.05.")