import random
import math
from collections import defaultdict

# $B<(Nc?.F;!)9g!J!)J8Cf>oMQ!$??!)2D:,?x9E7oDj@)!K(B
CB_CHANNEL_PAIRS_2G = [(1, 5), (9, 13)]
CB_CHANNEL_PAIRS_5G = [(36, 40), (44, 48)]

# === $B=i;O2=?.F;J,G[(B ===
def initialize_channel_assignment(aps):
    assignment = {}
    for ap in aps:
        assignment[ap['name']] = {
            '11n': random.choice(CB_CHANNEL_PAIRS_2G),
            '11ac': random.choice(CB_CHANNEL_PAIRS_5G)
        }
    return assignment

# === $B@\8}43!)PF;;!J!)!)3h!)(B AP$B!K(B ===
def compute_interference(ap_channels, active_aps):
    interference = 0
    ap_list = [(k, v) for k, v in ap_channels.items() if k in active_aps]
    for i in range(len(ap_list)):
        for j in range(i + 1, len(ap_list)):
            ap1, ch1 = ap_list[i]
            ap2, ch2 = ap_list[j]
            for band in ['11n', '11ac']:
                if ch1[band][0] == ch2[band][0] or ch1[band][1] == ch2[band][1]:
                    interference += 1
    return interference

# === $BLO!)B`2P;;K!!)9T?.F;J,G[!)2=(B ===
def simulated_annealing_channel_assignment(aps, init_assignment, active_aps, max_iter=1000, temp=100.0, cooling=0.95):
    current = init_assignment.copy()
    best = current.copy()
    best_score = compute_interference(current, active_aps)

    for _ in range(max_iter):
        new = {k: v.copy() for k, v in current.items()}
        rand_ap = random.choice(aps)['name']
        if random.random() < 0.5:
            new[rand_ap]['11n'] = random.choice(CB_CHANNEL_PAIRS_2G)
        else:
            new[rand_ap]['11ac'] = random.choice(CB_CHANNEL_PAIRS_5G)

        new_score = compute_interference(new, active_aps)
        delta = new_score - best_score

        if delta < 0 or random.random() < math.exp(-delta / temp):
            current = new
            if new_score < best_score:
                best = new
                best_score = new_score

        temp *= cooling
        if temp < 1e-3:
            break

    return best, best_score
