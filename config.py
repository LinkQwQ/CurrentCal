import os
import csv

# === 配置路径 ===
CONF_DIR = os.path.join(os.path.dirname(__file__), "conf")

# === 参数文件？取（含 Wk）===
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
                    # 例：Wk = 3.2 5.1 2.0 1.8 2.5 1.2
                    wk_list = list(map(float, value.split()))
                    params["Wk"] = {i + 1: v for i, v in enumerate(wk_list)}  # 1-based：w1是1
                else:
                    params[key] = float(value)
    return params

# === 加？参数 ===
PARAMS_24G = load_parameters_from_conf(os.path.join(CONF_DIR, "params_24G.conf"))
PARAMS_5G  = load_parameters_from_conf(os.path.join(CONF_DIR, "params_5G.conf"))

# === 拓？位置文件？取 ===
def load_topology_from_csv():
    csv_path = os.path.join(CONF_DIR, "positions.csv")
    data = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                "name": row["Name"],
                "x": float(row["X"]),
                "y": float(row["Y"]),
                "type": row["Type"].strip().lower()
            })
    return data

# === ？面数量？？？取（host, ap, w1, ..., w6）===
def load_wall_matrix_from_csv(filepath: str) -> dict:
    wall_matrix = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:  # ← ？？在于 utf-8-sig
        reader = csv.DictReader(f)
        for row in reader:
            host = row["host"]
            ap = row["ap"]
            wall_counts = {}
            for i in range(1, 7):  # ？取 w1 ~ w6
                key = f"w{i}"
                count = int(row[key])
                if count > 0:
                    wall_counts[key] = count
            wall_matrix[(host, ap)] = wall_counts
    return wall_matrix
