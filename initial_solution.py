import math
import random
from collections import defaultdict
from config import load_topology_from_csv
from ThrCal import euclidean_distance, compute_rss, estimate_throughput, srf
from load_balancer import rebalance_hosts

# === 示例：？体信息（全部？？ 0 ？） ===
def dummy_wall_matrix(nodes):
    wall_matrix = {}
    for host in nodes:
        if host['type'] != 'host':
            continue
        for ap in nodes:
            if ap['type'] != 'ap':
                continue
            wall_matrix[(host['name'], ap['name'])] = {}  # 无？体阻？
    return wall_matrix


# === 初始？吐量表估算 ===
def compute_initial_link_speed_table(nodes: list, wall_count_matrix: dict) -> dict:
    link_table = {}
    for host in nodes:
        if host['type'] != 'host':
            continue
        for ap in nodes:
            if ap['type'] != 'ap':
                continue
            d = euclidean_distance(host['x'], host['y'], ap['x'], ap['y'])
            walls = wall_count_matrix.get((host['name'], ap['name']), {})
            for band in ['11n', '11ac']:
                rss = compute_rss(d, band, walls)
                tp = estimate_throughput(rss, band)
                link_table[(host['name'], ap['name'], band)] = tp
    return link_table


# === Greedy AP 激活与 Host 分配（双接口） ===
def greedy_ap_selection_dual_interface(nodes, tp_table, threshold):
    hosts = [n for n in nodes if n['type'] == 'host']
    aps = [n for n in nodes if n['type'] == 'ap']

    active_aps = set()
    host_assignment = {}
    ap_to_hosts_band = defaultdict(lambda: defaultdict(list))  # ap_name -> band -> [host]

    for host in hosts:
        candidates = []
        for ap in aps:
            for band in ['11n', '11ac']:
                key = (host['name'], ap['name'], band)
                if key in tp_table:
                    m = len(ap_to_hosts_band[ap['name']][band]) + 1
                    base_tp = tp_table[key]
                    s = srf(m)
                    adjusted_tp = base_tp * s
                    candidates.append((ap['name'], band, adjusted_tp, base_tp))

        candidates.sort(key=lambda x: x[2], reverse=True)  # 按最？？吐量排序

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

    for _ in range(max_iter):
        random.shuffle(nodes)  # 打乱 host ？序
        active_aps, host_assignment, ap_to_hosts_band = greedy_ap_selection_dual_interface(nodes, tp_table, threshold)

        # ？算当前最小 adjusted ？吐量
        min_tp = float('inf')
        for host, (ap, band) in host_assignment.items():
            m = len(ap_to_hosts_band[ap][band])
            base_tp = tp_table[(host, ap, band)]
            adjusted = base_tp * srf(m)
            min_tp = min(min_tp, adjusted)

        if min_tp > best_min_tp:
            best_min_tp = min_tp
            best_assignment = host_assignment.copy()
            best_active_aps = active_aps.copy()
            best_ap_to_hosts_band = ap_to_hosts_band.copy()

        for host, (ap, band) in best_assignment.items():
            other_band = '11ac' if band == '11n' else '11n'
            key_new = (host, ap, other_band)
            if key_new in tp_table:
                m_new = len(best_ap_to_hosts_band[ap][other_band]) + 1
                base_tp_new = tp_table[key_new]
                adjusted_tp_new = base_tp_new * srf(m_new)

                m_old = len(best_ap_to_hosts_band[ap][band])
                base_tp_old = tp_table[(host, ap, band)]
                adjusted_tp_old = base_tp_old * srf(m_old)

                if adjusted_tp_new > adjusted_tp_old:
                    # 更新接口分配
                    best_ap_to_hosts_band[ap][band].remove(host)
                    best_ap_to_hosts_band[ap][other_band].append(host)
                    best_assignment[host] = (ap, other_band)

    return best_active_aps, best_assignment, best_ap_to_hosts_band


# === 示例？用 ===
from Channel import initialize_channel_assignment, simulated_annealing_channel_assignment

if __name__ == '__main__':
    from Channel import initialize_channel_assignment, simulated_annealing_channel_assignment

    nodes = load_topology_from_csv()
    walls = dummy_wall_matrix(nodes)
    tp_table = compute_initial_link_speed_table(nodes, walls)

    print("--- Estimated Link Speed Table (11n + 11ac) ---")
    for (h, a, b), tp in tp_table.items():
        print(f"Host {h} - AP {a} [{b}]: {tp:.2f} Mbps")

    print("\n--- Greedy AP Activation with Dual Interfaces + SRF (Optimized) ---")
    G = 10.0
    active_aps, host_assignment, ap_to_hosts_band = refine_assignment_by_perturbation(nodes, tp_table, G, max_iter=20)
    print(f"Active APs: {sorted(active_aps)}")
    for host, (ap, band) in host_assignment.items():
        m = len(ap_to_hosts_band[ap][band])
        base_tp = tp_table[(host, ap, band)]
        adjusted = base_tp * srf(m)
        print(
            f"Host {host} assigned to AP {ap} [{band}] | base_tp={base_tp:.2f} Mbps => adjusted_tp={adjusted:.2f} Mbps")

    print("--- Optimized Channel Assignment(After Phase 2) ---")
    aps = [n for n in nodes if n['type'] == 'ap']
    init_assign = initialize_channel_assignment(aps)
    final_assign, score = simulated_annealing_channel_assignment(aps, init_assign, active_aps)
    for ap_name, chs in final_assign.items():
        print(f"AP {ap_name}: 11n => {chs['11n']}, 11ac => {chs['11ac']}")
    print(f"Total Interference Score: {score}")

    print("\n--- Load Rebalancing (Phase 3) ---")
    host_assignment, ap_to_hosts_band = rebalance_hosts(tp_table, host_assignment, ap_to_hosts_band, G)

    print("\n--- Final Host Assignment (After Rebalancing) ---")
    for host, (ap, band) in host_assignment.items():
        m = len(ap_to_hosts_band[ap][band])
        base_tp = tp_table[(host, ap, band)]
        adjusted = base_tp * srf(m)
        print(f"Host {host} => AP {ap} [{band}] | adjusted_tp={adjusted:.2f} Mbps")
