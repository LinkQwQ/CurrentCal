import os
import csv

CONF_DIR = os.path.join(os.path.dirname(__file__), "conf")

def load_parameters_from_conf(file_path: str) -> dict:
    params = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key == "Wk":
                    wk_list = list(map(float, value.split()))
                    params["Wk"] = {i: v for i, v in enumerate(wk_list)}
                else:
                    params[key] = float(value)
    return params

# 加？？个？段参数
PARAMS_24G = load_parameters_from_conf(os.path.join(CONF_DIR, "params_24G.conf"))
PARAMS_5G  = load_parameters_from_conf(os.path.join(CONF_DIR, "params_5G.conf"))

# 加？位置拓？
def load_topology_from_csv():
    csv_path = os.path.join(CONF_DIR, "positions.csv")
    data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                "name": row["Name"],
                "x": float(row["X"]),
                "y": float(row["Y"]),
                "type": row["Type"].strip().lower()
            })
    return data
