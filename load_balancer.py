# load_balancer.py

from ThrCal import rational, RATIONAL_PARAMS

def rebalance_hosts_rational(tp_table, assignment, ap_to_hosts_band, threshold):
    a0, a1, a2, b1 = RATIONAL_PARAMS
    r_1 = rational(1, a0, a1, a2, b1)
    changed = False
    hosts = list(assignment.keys())

    for host in hosts:
        current_ap, current_band = assignment[host]
        m_curr = len(ap_to_hosts_band[current_ap][current_band])
        base_curr = tp_table[(host, current_ap, current_band)]
        r_curr = rational(m_curr, a0, a1, a2, b1)
        current_tp = base_curr * (r_curr / r_1) / m_curr

        for ap in ap_to_hosts_band:
            for band in ap_to_hosts_band[ap]:
                key = (host, ap, band)
                if key in tp_table:
                    m_new = len(ap_to_hosts_band[ap][band]) + 1
                    base_new = tp_table[key]
                    r_new = rational(m_new, a0, a1, a2, b1)
                    new_tp = base_new * (r_new / r_1) / m_new

                    if new_tp > current_tp and new_tp >= threshold:
                        # 更新？？
                        ap_to_hosts_band[current_ap][current_band].remove(host)
                        ap_to_hosts_band[ap][band].append(host)
                        assignment[host] = (ap, band)
                        changed = True
                        print(f"[Rebalanced] Host {host} => AP {ap} [{band}] | improved_tp={new_tp:.2f} Mbps")
                        break
            if changed:
                break

    return assignment, ap_to_hosts_band
