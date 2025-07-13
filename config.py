import os
import csv

# === $BG[CVO)7B(B ===
CONF_DIR = os.path.join(os.path.dirname(__file__), "conf")

# === $B;2?tJ87o!)<h!J4^(B Wk$B!K(B===
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
                    # $BNc!'(BWk = 3.2 5.1 2.0 1.8 2.5 1.2
                    wk_list = list(map(float, value.split()))
                    params["Wk"] = {i + 1: v for i, v in enumerate(wk_list)}  # 1-based$B!'(Bw1$B@'(B1
                else:
                    params[key] = float(value)
    return params

# === $B2C!);2?t(B ===
PARAMS_24G = load_parameters_from_conf(os.path.join(CONF_DIR, "params_24G.conf"))
PARAMS_5G  = load_parameters_from_conf(os.path.join(CONF_DIR, "params_5G.conf"))

# === $BBs!)0LCVJ87o!)<h(B ===
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

# === $B!)LL?tNL!)!)!)<h!J(Bhost, ap, w1, ..., w6$B!K(B===
def load_wall_matrix_from_csv(filepath: str) -> dict:
    wall_matrix = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:  # $B"+(B $B!)!):_P2(B utf-8-sig
        reader = csv.DictReader(f)
        for row in reader:
            host = row["host"]
            ap = row["ap"]
            wall_counts = {}
            for i in range(1, 7):  # $B!)<h(B w1 ~ w6
                key = f"w{i}"
                count = int(row[key])
                if count > 0:
                    wall_counts[key] = count
            wall_matrix[(host, ap)] = wall_counts
    return wall_matrix
