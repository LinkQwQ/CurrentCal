import math
import os

def load_params_from_file(filename: str) -> dict:
    params = {}
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Parameter file not found: {filename}")

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key == "Wk":
                    vals = list(map(float, value.split()))
                    params["Wk"] = {f"w{i+1}": vals[i] for i in range(len(vals))}
                else:
                    params[key] = float(value)
    return params

# 加？参数
PARAMS_24G = load_params_from_file(os.path.join("conf", "params_24g.conf"))
PARAMS_5G = load_params_from_file(os.path.join("conf", "params_5g.conf"))

def get_params(band: str):
    if band == '24G':
        return PARAMS_24G
    elif band == '5G':
        return PARAMS_5G
    else:
        raise ValueError(f"Unknown band: {band}")

def infer_band_by_ap_id(ap_id: int) -> str:
    return "5G" if ap_id % 2 == 1 else "24G"

def euclidean_distance(x1, y1, x2, y2) -> float:
    return ((x1 - x2)**2 + (y1 - y2)**2)**0.5

def compute_rss(distance: float, band: str, wall_counts: dict) -> float:
    params = get_params(band)
    P1 = params["P_1"]
    alpha = params["alpha"]
    Wk = params["Wk"]
    attenuation = sum([wall_counts.get(k, 0) * Wk.get(k, 0) for k in wall_counts])
    return P1 - 10 * alpha * math.log10(distance) - attenuation

def estimate_throughput(rss: float, band: str) -> float:
    params = get_params(band)
    a = params["a"]
    b = params["b"]
    c = params["c"]
    return a / (1 + math.exp(-((120 + rss - b) / c)))

def srf(m: int) -> float:
    if m <= 1:
        return 1.0
    return (1 / (m + 0.1 * (m - 1) / 4)) * (1 - (0.1 * m - 1))

def rational(m, a0, a1, a2, b1):
    return (a0 + a1 * m + a2 * m**2) / (1 + b1 * m)

RATIONAL_PARAMS = (392.124, -13.3311, -1.2629, -0.0439)

def final_throughput(x1, y1, x2, y2, wall_counts: dict, m: int, band: str) -> float:
    d = euclidean_distance(x1, y1, x2, y2)
    rss = compute_rss(d, band, wall_counts)
    tp_single = estimate_throughput(rss, band)
    a0, a1, a2, b1 = RATIONAL_PARAMS
    reduction = rational(m, a0, a1, a2, b1)
    return (tp_single * reduction) / m

# ？ 新？：根据 AP ？号自？判断？段版本
def final_throughput_by_ap_id(x1, y1, x2, y2, wall_counts: dict, m: int, ap_id: int) -> float:
    band = infer_band_by_ap_id(ap_id)
    return final_throughput(x1, y1, x2, y2, wall_counts, m, band)
