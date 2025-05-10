from ThrCal import srf

def rebalance_hosts(tp_table, assignment, ap_to_hosts_band, threshold):
    changed = False
    hosts = list(assignment.keys())
    for host in hosts:
        current_ap, current_band = assignment[host]
        current_tp = tp_table[(host, current_ap, current_band)] * srf(len(ap_to_hosts_band[current_ap][current_band]))

        for ap in ap_to_hosts_band:
            for band in ap_to_hosts_band[ap]:
                if (host, ap, band) in tp_table:
                    m = len(ap_to_hosts_band[ap][band]) + 1
                    tp = tp_table[(host, ap, band)] * srf(m)
                    if tp > current_tp and tp >= threshold:
                        # 移除旧？？
                        ap_to_hosts_band[current_ap][current_band].remove(host)
                        # 添加新？？
                        ap_to_hosts_band[ap][band].append(host)
                        assignment[host] = (ap, band)
                        changed = True
                        print(f"[Rebalanced] Host {host} => AP {ap} [{band}] | improved_tp={tp:.2f} Mbps")
                        break
            if changed:
                break

    return assignment, ap_to_hosts_band
