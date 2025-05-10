import math
from config import PARAMS_24G, PARAMS_5G

def get_params(band: str):
    if band == '24G':
        return PARAMS_24G
    elif band == '5G':
        return PARAMS_5G
    else:
        raise ValueError(f"Unknown band: {band}")

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

    # ？个 host ？？？得的？吐量
    return (tp_single * reduction) / m

