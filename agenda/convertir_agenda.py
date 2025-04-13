import csv
import json
from datetime import datetime
import re

entrada = "agenda/agenda_original.csv"
salida = "agenda/gemba_agenda.json"

def parse_fecha(fecha_str):
    match = re.search(r"(\d{1,2})/(\d{1,2})", fecha_str)
    if match:
        d, m = match.groups()
        return f"2025-{int(m):02d}-{int(d):02d}"
    return None

agenda = {}
with open(entrada, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        fecha = parse_fecha(row["Fecha"])
        if not fecha:
            continue
        actividad = {
            "hora": row["Hora"],
            "actividad": row["Actividad"],
            "direccion": row["Dirección"],
            "maps": row["Maps"] if row["Maps"].startswith("http") else ""
        }
        agenda.setdefault(fecha, []).append(actividad)

with open(salida, "w", encoding="utf-8") as f:
    json.dump(agenda, f, indent=2, ensure_ascii=False)

print(f"✅ Agenda convertida a {salida}")