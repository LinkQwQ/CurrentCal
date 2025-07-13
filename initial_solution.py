import math
import os
import random
from collections import defaultdict
from config import load_topology_from_csv
from ThrCal import euclidean_distance, compute_rss, estimate_throughput, rational, RATIONAL_PARAMS
from load_balancer import rebalance_hosts_rational as rebalance_hosts
from config import load_wall_matrix_from_csv

# === 示例：？造空？体矩？（无？体影？） ===
def dummy_wall_matrix(nodes):
    wall_matrix = {}
    for host in nodes:
        if host['type'] != 'host':
            continue
        for ap in nodes:
            if ap['type'] != 'ap':
                continue
            wall_matrix[(host['name'], ap['name'])] = {}
    return wall_matrix

def ap_id_from_name(ap_name: str) -> int:
    return int(''.join(filter(str.isdigit, ap_name)))

def compute_initial_link_speed_table(nodes: list, wall_count_matrix: dict) -> dict:
    link_table = {}
    print("--- Estimated Link Speed Table (5G + 24G, by AP ID rule) ---")
    for host in nodes:
        if host['type'] != 'host':
            continue
        for ap in nodes:
            if ap['type'] != 'ap':
                continue
            ap_id = ap_id_from_name(ap['name'])
            # 只保留？ AP ？？？段
            band = "5G" if ap_id % 2 == 1 else "24G"
            d = euclidean_distance(host['x'], host['y'], ap['x'], ap['y'])
            walls = wall_count_matrix.get((host['name'], ap['name']), {})
            rss = compute_rss(d, band, walls)
            tp = estimate_throughput(rss, band)
            link_table[(host['name'], ap['name'], band)] = tp
            print(f"Host {host['name']} - AP {ap['name']} [{band}]: {tp:.2f} Mbps (RSS={rss:.2f} dBm)")
    return link_table



# === Greedy AP 激活与 Host 分配（双接口） ===
def greedy_ap_selection_dual_interface(nodes, tp_table, threshold):
    hosts = [n for n in nodes if n['type'] == 'host']
    aps = [n for n in nodes if n['type'] == 'ap']

    active_aps = set()
    host_assignment = {}
    ap_to_hosts_band = defaultdict(lambda: defaultdict(list))
    a0, a1, a2, b1 = RATIONAL_PARAMS
    r_1 = rational(1, a0, a1, a2, b1)

    for host in hosts:
        candidates = []
        for ap in aps:
            for band in ['5G', '24G']:
                key = (host['name'], ap['name'], band)
                if key in tp_table:
                    # 模？当前 host 加入？ AP-band 后的？吐
                    m = len(ap_to_hosts_band[ap['name']][band]) + 1
                    base_tp = tp_table[key]
                    r_m = rational(m, a0, a1, a2, b1)
                    adjusted_tp = base_tp * (r_m / r_1) / m
                    candidates.append((ap['name'], band, adjusted_tp, base_tp))

        candidates.sort(key=lambda x: x[2], reverse=True)

        for ap_name, band, adj_tp, base_tp in candidates:
            if adj_tp >= threshold:
                host_assignment[host['name']] = (ap_name, band)
                ap_to_hosts_band[ap_name][band].append(host['name'])
                active_aps.add(ap_name)
                break

    return active_aps, host_assignment, ap_to_hosts_band

# === 局部？？？化 ===
def refine_assignment_by_perturbation(nodes, tp_table, threshold, max_iter=10):
    best_min_tp = 0
    best_assignment = None
    best_active_aps = None
    best_ap_to_hosts_band = None
    a0, a1, a2, b1 = RATIONAL_PARAMS

    for _ in range(max_iter):
        random.shuffle(nodes)
        active_aps, host_assignment, ap_to_hosts_band = greedy_ap_selection_dual_interface(nodes, tp_table, threshold)

        min_tp = float('inf')
        for host, (ap, band) in host_assignment.items():
            m = len(ap_to_hosts_band[ap][band])
            base_tp = tp_table[(host, ap, band)]
            r_m = rational(m, a0, a1, a2, b1)
            r_1 = rational(1, a0, a1, a2, b1)
            adjusted = base_tp * (r_m / r_1) / m
            min_tp = min(min_tp, adjusted)

        if min_tp > best_min_tp:
            best_min_tp = min_tp
            best_assignment = host_assignment.copy()
            best_active_aps = active_aps.copy()
            best_ap_to_hosts_band = ap_to_hosts_band.copy()

        for host, (ap, band) in best_assignment.items():
            other_band = '24G' if band == '5G' else '5G'
            key_new = (host, ap, other_band)
            if key_new in tp_table:
                m_new = len(best_ap_to_hosts_band[ap][other_band]) + 1
                base_tp_new = tp_table[key_new]
                r_m_new = rational(m_new, a0, a1, a2, b1)
                r_1 = rational(1, a0, a1, a2, b1)
                adjusted_tp_new = base_tp_new * (r_m_new / r_1) / m_new

                m_old = len(best_ap_to_hosts_band[ap][band])
                base_tp_old = tp_table[(host, ap, band)]
                r_m_old = rational(m_old, a0, a1, a2, b1)
                adjusted_tp_old = base_tp_old * (r_m_old / r_1) / m_old

                if adjusted_tp_new > adjusted_tp_old:
                    best_ap_to_hosts_band[ap][band].remove(host)
                    best_ap_to_hosts_band[ap][other_band].append(host)
                    best_assignment[host] = (ap, other_band)

    return best_active_aps, best_assignment, best_ap_to_hosts_band

# === 示例主流程 ===
from Channel import initialize_channel_assignment, simulated_annealing_channel_assignment

if __name__ == '__main__':
    nodes = load_topology_from_csv()


    walls = load_wall_matrix_from_csv(os.path.join("conf", "wall_stats.csv"))
    tp_table = compute_initial_link_speed_table(nodes, walls)


    print("\n--- Greedy AP Activation with Dual Interfaces + Rational Model ---")
    G = 10.0
    active_aps, host_assignment, ap_to_hosts_band = refine_assignment_by_perturbation(nodes, tp_table, G, max_iter=20)
    print(f"Active APs: {sorted(active_aps)}")

    a0, a1, a2, b1 = RATIONAL_PARAMS
    r_1 = rational(1, a0, a1, a2, b1)
    for host, (ap, band) in host_assignment.items():
        m = len(ap_to_hosts_band[ap][band])
        base_tp = tp_table[(host, ap, band)]
        r_m = rational(m, a0, a1, a2, b1)
        adjusted = base_tp * (r_m / r_1) / m
        print(f"Host {host} assigned to AP {ap} [{band}] | base_tp={base_tp:.2f} Mbps => adjusted_tp={adjusted:.2f} Mbps")

    print("--- Optimized Channel Assignment (After Phase 2) ---")
    aps = [n for n in nodes if n['type'] == 'ap']
    init_assign = initialize_channel_assignment(aps)
    final_assign, score = simulated_annealing_channel_assignment(aps, init_assign, active_aps)
    for ap_name, chs in final_assign.items():
        print(f"AP {ap_name}: 5G => {chs['5G']}, 24G => {chs['24G']}")
    print(f"Total Interference Score: {score}")

    print("\n--- Load Rebalancing (Phase 3) ---")
    host_assignment, ap_to_hosts_band = rebalance_hosts(tp_table, host_assignment, ap_to_hosts_band, G)

    print("\n--- Final Host Assignment (After Rebalancing) ---")
    for host, (ap, band) in host_assignment.items():
        m = len(ap_to_hosts_band[ap][band])
        base_tp = tp_table[(host, ap, band)]
        r_m = rational(m, a0, a1, a2, b1)
        adjusted = base_tp * (r_m / r_1) / m
        print(f"Host {host} => AP {ap} [{band}] | adjusted_tp={adjusted:.2f} Mbps")
