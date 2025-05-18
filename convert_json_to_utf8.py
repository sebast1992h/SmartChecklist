import os
import json

def convert_to_utf8(root_dir):
    encodings_to_try = ['utf-8', 'iso-8859-1', 'windows-1252']
    converted_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".json"):
                full_path = os.path.join(dirpath, filename)
                for enc in encodings_to_try:
                    try:
                        with open(full_path, "r", encoding=enc) as f:
                            data = json.load(f)
                        # Wenn erfolgreich: Speichern als UTF-8
                        with open(full_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        converted_files.append((full_path, enc))
                        break  # Erfolg → nächste Datei
                    except Exception as e:
                        continue  # Nächste Kodierung probieren

    return converted_files

if __name__ == "__main__":
    project_dir = "./"  # Oder z. B. "./checklisten"
    result = convert_to_utf8(project_dir)
    print("Konvertiert:")
    for path, enc in result:
        print(f"{path} (ursprünglich: {enc})")
