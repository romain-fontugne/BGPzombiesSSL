import os
import logging
import sys
from matplotlib import pylab as plt
import glob
import pickle
from collections import defaultdict
import collections
import itertools
import datetime
import numpy as np
from rftb import plot as rfplt

esteban_results_directory = "20180623_BGPcount"

def asnres(ip):
    """Find the ASN corresponding to the given IP address"""

    asn = ia.ip2asn(ip)
    if asn == "unknown":
        asn="0"
    return str(asn)

def get_classification_results(ts = 1505287800, prefix = "84.205.67.0/24"):
    """Return infered zombie (and normal) ASN.
    """    

    ##### Esteban's results #####
    fname = esteban_results_directory+"/%s_%s/result/classification.txt" % (ts, prefix.replace("/","_"))

    zombie_asns = set()
    normal_asns = set()
    if not os.path.exists(fname):
        # No zombie mean that the input was too unbalanced. Use bgp data
        # instead
        fname = "results/zombies_%s_%s.txt" % (ts, prefix.replace("/", "_"))

        for line in open(fname):
            asn, zombie = [x for x in line.split()]
            
            if int(zombie):
                zombie_asns.add(asn)
            else:
                normal_asns.add(asn)

    else:
        for i, line in enumerate(open(fname)):
            # skip the header
            if i ==0:
                continue

            cluster, asn = [x.partition(".")[0] for x in line.split()]

            if int(cluster) == 2:
                zombie_asns.add(asn)
            else:
                normal_asns.add(asn)

    if len(zombie_asns) == 0:
        return None

    if len(zombie_asns) > 40:
        print(ts, prefix, end=",", sep=", ")
        print("{} zombies".format(len(zombie_asns)))

    return {"zombie": zombie_asns, "normal": normal_asns}


def compute_all_stats():
    """ Fetch all classification results and compute basic stats."""

    ### Fetch all results
    all_classification_results = defaultdict(dict)

    for path in glob.glob(esteban_results_directory+"/*_24"):
        dname = path.rpartition("/")[2]
        ts, _, prefix = dname.partition("_")
        prefix = prefix.replace("_","/")
        ts = int(ts)

        # print("Processing %s %s..." % (ts, prefix))
        asns = get_classification_results(ts, prefix)

        if asns is not None:
            all_classification_results[ts][prefix] = asns

    ### Temporal characteristics
    ts_start = min(all_classification_results.keys())
    ts_end = max(all_classification_results.keys())
    duration = (ts_end - ts_start)/3600
    
    print("First zombie detected at {} and last one at {}".format(
        datetime.datetime.utcfromtimestamp(ts_start),
        datetime.datetime.utcfromtimestamp(ts_end)
        ))
    
    nb_withdraws = duration/4
    nb_zombie_timebin = len(all_classification_results.keys())

    perc_zombie_timebins = nb_zombie_timebin/nb_withdraws*100
    print("Percentage of withdraw periods with at least one zombie: {:.02f}%".format(perc_zombie_timebins))
    print("Number of withdraw periods with zombies: {}".format(len(all_classification_results)))

    zombie_timebins_v4 = [ts for ts, res in all_classification_results.items() for pfx in res.keys() if "." in pfx]
    zombie_timebins_v6 = [ts for ts, res in all_classification_results.items() for pfx in res.keys() if ":" in pfx]
    perc_zombie_timebins_v4 = len(set(zombie_timebins_v4))/nb_withdraws*100
    perc_zombie_timebins_v6 = len(set(zombie_timebins_v6))/nb_withdraws*100
    print("Percentage of withdraw periods with one v4 zombie: {:.02f}%".format(perc_zombie_timebins_v4))
    print("Percentage of withdraw periods with one v6 zombie: {:.02f}%".format(perc_zombie_timebins_v6))

    zombies_per_timebin = [set([asn for pfx, res in pfx_res.items() for asn in res["zombie"]]) 
            for ts, pfx_res in all_classification_results.items()]
    normal_per_timebin = [set([asn for pfx, res in pfx_res.items() for asn in res["normal"]]) 
            for ts, pfx_res in all_classification_results.items()]


    nb_zombie_per_outbreak = [len(z) for z in zombies_per_timebin]
    print("On average we have {:.02f} zombie AS per outbreak (median={})".format(np.mean(nb_zombie_per_outbreak),np.median(nb_zombie_per_outbreak)))
    print("On average we have {:.02f} AS in the AS graph".format(
        np.mean(
            [len(z.union(n)) for z,n in zip(zombies_per_timebin, normal_per_timebin)]
        )))
    print("That's {:.02f}% zombie AS per outbreak".format(
        np.mean(
            [100*len(z)/(len(z)+len(n)) for z,n in zip(zombies_per_timebin, normal_per_timebin)]
        )))

    plt.figure()
    rfplt.ecdf(nb_zombie_per_outbreak)
    plt.xlabel("Number zombie ASN per outbreak")
    plt.ylabel("CDF")
    plt.tight_layout()
    plt.savefig("fig/CDF_nb_zombie_per_outbreak.pdf")

    asn_zombie_frequency = collections.Counter(itertools.chain.from_iterable(zombies_per_timebin))
    # add normal ASes:
    for asn in set(itertools.chain.from_iterable(normal_per_timebin)):
        if not asn in asn_zombie_frequency:
            asn_zombie_frequency[asn]=0

    print("Top 50 zombie ASN: ")
    for asn, freq in asn_zombie_frequency.most_common(50):
        print("\t AS{}: {:.02f}% ({} times)".format(asn, 100*freq/nb_zombie_timebin, freq))

    plt.figure()
    rfplt.ecdf(np.array(list(asn_zombie_frequency.values()))/nb_zombie_timebin)
    plt.xlabel("freq. AS as zombie/total nb. of outbreaks")
    plt.ylabel("CDF")
    plt.tight_layout()
    plt.savefig("fig/CDF_zombie_freq_per_asn.pdf")
    # plt.show()

    from efficient_apriori import apriori

    itemsets, rules = apriori(zombies_per_timebin, min_support=0.3, min_confidence=1)
    # print(zombies_per_timebin)
    # for nb_elem, items in itemsets.items():
        # if nb_elem > 1:
            # print(nb_elem)
            # print(items)

    # rules_rhs = filter(lambda rule: len(rule.lhs)==1 and len(rule.rhs)>4, rules)
    # print(list(rules_rhs))

if __name__ == "__main__":
    compute_all_stats()    
