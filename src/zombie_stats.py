import os
import logging
import sys
from matplotlib import pylab as plt
plt.switch_backend('agg')
import glob
import pickle
from collections import defaultdict
import collections
import itertools
import datetime
import numpy as np
from rftb import plot as rfplt
import requests

esteban_results_directory = "20181001_BGPcount/"
input_graphs = "zombie_paths/"

def asnres(ip):
    """Find the ASN corresponding to the given IP address"""

    asn = ia.ip2asn(ip)
    if asn == "unknown":
        asn="0"
    return str(asn)


def nbOutbreak(e):
    af = set([str(int(event["start"]/3600))+event["prefix"].rpartition("/")[2] for event in e.values()])
    count = Counter([e[-2:] for e in af])
    print(count)
    return count


def peerZombieLikelihood():

    for ts in ["1"]:
        
        for af, af_pfx in [(4, "24"),(6, "48")]:
            nb_msm_days = 31+28+31+28+13+31
            nb_zombie_per_peer = defaultdict(int)
            nb_clean_per_peer = defaultdict(int)
            print("IPv{}".format(af))
            for fname in glob.glob( input_graphs+"zombies_{}*_{}.txt".format(ts, af_pfx,)):
                beacon = fname.split("_")[-2]

                for line in open(fname):
                    asn, zombie = [x for x in line.split()]
                    
                    if int(zombie):
                        nb_zombie_per_peer[asn+"_"+beacon]+=1
                    else:
                        nb_clean_per_peer[asn+"_"+beacon]+=1


            ratio_all_zombie = [ nb_zombie_per_peer[asn]/(nb_zombie_per_peer[asn]+nb_clean_per_peer[asn])
                    for asn in set(itertools.chain(nb_zombie_per_peer.keys(), nb_clean_per_peer.keys())) ]

            plt.figure(10)
            rfplt.ecdf(ratio_all_zombie, label="IPv{}".format(af))
            plt.ylabel("CDF")
            plt.xlabel("ratio zombie(peer)/all outbreaks")
            plt.legend(loc="best")
            plt.tight_layout()
            plt.savefig("fig/CDF_ratio_zombieasn_alloutbreaks.pdf")

            print("Ratio to all outbreaks, mean={}, median={}".format(np.mean(ratio_all_zombie),np.median(ratio_all_zombie)))
            
            ratio_all_withdraws = [ nb_zombie_per_peer[asn]/(nb_msm_days*6)
                    for asn in set(itertools.chain(nb_zombie_per_peer.keys(), nb_clean_per_peer.keys())) ]

            plt.figure(11)
            cdf = rfplt.ecdf(ratio_all_withdraws, label="IPv{}".format(af))
            plt.ylabel("CDF")
            plt.xlabel("Zombie Emergence Rate")
            plt.legend(loc="best")
            plt.tight_layout()
            plt.savefig("fig/CDF_ratio_zombieasn_allwithdraws.pdf")

            print("Ratio to all withdraws, mean={}, median={}".format(np.mean(ratio_all_withdraws),np.median(ratio_all_withdraws)))

            print("Max. <peer, beacon>: {} ({} times)".format(
                max(nb_zombie_per_peer, key=nb_zombie_per_peer.get),
                max(nb_zombie_per_peer.values())))

            # print(cdf)


def pathLenComparions(normal_folder="./normal_paths/", zombie_folder="./zombie_paths/"):

    zombie_path_len = []
    normal_path_for_zombie_len = []
    normal_path_len = []

    for af in [4,6]:
        for fname in glob.glob(zombie_folder+"bgpdata_*.pickle"):
            zombie_data = pickle.load(open(fname, "rb"))
            fname_normal = fname.replace(zombie_folder, normal_folder).replace("bgpdata","normal_bgpdata")
            tsz = int(fname_normal.rpartition("_")[2].partition(".")[0])
            tsn = tsz-3600*2
            fname_normal = fname_normal.replace(str(tsz), str(tsn))
            normal_data = pickle.load(open(fname_normal, "rb"))

            for pfx, zombie_withdaws in zombie_data.withdraws.items():
                if (af == 4 and ":" in pfx) or (af==6 and "." in pfx):
                    continue
                for asn, withdrawn in zombie_withdaws.items():
                    if asn in normal_data.paths[pfx]:
                        if withdrawn:
                            normal_path_len.append( len(normal_data.paths[pfx][asn].split(" ")) )
                        else:
                            zombie_path_len.append( len(zombie_data.paths[pfx][asn].split(" ")) )
                            normal_path_for_zombie_len.append( len(normal_data.paths[pfx][asn].split(" ")) )

        plt.figure()
        rfplt.ecdf(normal_path_for_zombie_len, label="Normal Path (zombie peer)")
        rfplt.ecdf(normal_path_len, label="Normal Path (normal peer)")
        rfplt.ecdf(zombie_path_len, label="Zombie Path")
        plt.legend(loc="best")
        plt.xlabel("AS path length")
        plt.ylabel("CDF")
        plt.tight_layout()
        plt.savefig("fig/CDF_path_length_IPv{}.pdf".format(af))

def get_classification_results(ts = 1505287800, prefix = "84.205.67.0/24"):
    """Return infered zombie (and normal) ASN.
    """    

    ##### Esteban's results #####
    fname = esteban_results_directory+"/%s_%s/result/classification.txt" % (ts, prefix.replace("/","_"))

    zombie_asns = set()
    normal_asns = set()
    if os.path.exists(fname):
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
        # No zombie mean that the input was too unbalanced. Use bgp data
        # instead
        prefix= prefix.replace("-",":")
        fname = input_graphs+"zombies_%s_%s.txt" % (ts, prefix.replace("/", "_"))

        for line in open(fname):
            asn, zombie = [x for x in line.split()]
            
            if int(zombie):
                zombie_asns.add(asn)
            else:
                normal_asns.add(asn)


    if len(zombie_asns) > 180:
        print(ts, prefix, end=",", sep=", ")
        print("{} zombies".format(len(zombie_asns)))

    return {"zombie": zombie_asns, "normal": normal_asns}

def get_hegemony(asns, af):

    if os.path.exists("hegemony_ipv{}_cache.pickle".format(af)):
        return pickle.load(open("hegemony_ipv{}_cache.pickle".format(af), "rb"))

    hegemony_scores = defaultdict(int)
    url = 'https://ihr.iijlab.net/ihr/api/hegemony/'

    for asn in asns:
        params = dict(
            asn=asn,
            originasn=0,
            timebin='2018-03-10T00:00',
            af=af,
        )

        resp = requests.get(url=url, params=params)
        data = resp.json() # Check the JSON Response Content documentation below
        if "results" in data and len(data["results"])>0:
            hege = data["results"][0]
            hegemony_scores[hege["asn"]] = hege["hege"]
        else:
            print(resp)
            print("Couldn't get hegemony for {}".format(params))



    pickle.dump(hegemony_scores, open("hegemony_ipv{}_cache.pickle".format(af), "wb"))

    return hegemony_scores



def compute_all_stats():
    """ Fetch all classification results and compute basic stats."""

    h_x = []
    h_label = []


    ### Fetch all results
    # timestamp_prefix = "14"
    # timestamp_prefix = "15[1,2]"
    # timestamp_prefix = "153"
    timestamp_prefix = "1"
    for af, pfx_len in [(4, "24"),(6, "48")]:
        all_classification_results = defaultdict(dict)

        countNone = 0
        all_files = glob.glob(esteban_results_directory+"/{}*_{}".format(timestamp_prefix, pfx_len))
        print("Reading {} input files...".format(len(all_files)))
        for path in all_files:
            dname = path.rpartition("/")[2]
            ts, _, prefix = dname.partition("_")
            prefix = prefix.replace("_","/")
            ts = int(ts)

            # print("Processing %s %s..." % (ts, prefix))
            asns = get_classification_results(ts, prefix)
            if asns is not None and len(asns["zombie"])>200:
                print("Large outbreak: {} {}".format(ts, prefix))

            if asns is not None:
                all_classification_results[ts][prefix] = asns
            else:
                countNone +=1


        nb_outbreak = sum([len(pfx_res.keys()) for ts, pfx_res in all_classification_results.items()])
        print("number of outbreaks: {}".format(nb_outbreak))
        print("number of ts: {}".format(len(all_classification_results)))
        print("number of nones: {}".format(countNone))

        ### AS hegemony
        # if af == 4:
        all_zombies = set([asn for pfx_res in all_classification_results.values() 
            for res in pfx_res.values() for asn in res["zombie"]])
        hegemony = get_hegemony(all_zombies, af)
        max_hege = []
        outbreak_size = []
        for ts, pfx_res in all_classification_results.items():
            for pfx, res in pfx_res.items():
                # for zombie in res["zombie"]:
                    hege = [hegemony[int(zombie)] for zombie in res["zombie"]]
                    max_hege.append(max(hege))
                    # max_hege.append(np.log(hegemony[int(zombie)]))
                    
                    if max_hege[-1] == 0:
                        max_hege[-1] = min(hegemony.values())
                        print("max hege = 0! {}".format(res["zombie"]))
                    outbreak_size.append(len(res["zombie"]))


        color_map = plt.cm.Spectral_r
        plt.figure(100+af)
        heatmap = plt.hexbin(max_hege, outbreak_size, cmap=color_map, 
                mincnt=1, bins="log", gridsize=30, xscale="log")
        plt.xlabel("Max. AS Hegemony")
        plt.ylabel("Outbreak size")
        cb = plt.colorbar(heatmap, spacing='uniform', extend='max')
        plt.tight_layout()
        plt.savefig("fig/hege_outbreaksize_ipv{}.pdf".format(af))


        ### Temporal characteristics
        ts_start = min(all_classification_results.keys())
        ts_end = max(all_classification_results.keys())
        # duration = (ts_end - ts_start)/3600 #hours
        # nb_withdraws = duration/4
        duration = 31+28+31+28+13+31 #days
        nb_withdraws = duration*6
        
        print("First zombie detected at {} and last one at {}".format(
            datetime.datetime.utcfromtimestamp(ts_start),
            datetime.datetime.utcfromtimestamp(ts_end)
            ))
        
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

        plt.figure(1)
        cdf = rfplt.ecdf(nb_zombie_per_outbreak, label="IPv{}".format(af))
        plt.xlabel("Outbreak size")
        plt.ylabel("CDF")
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig("fig/CDF_nb_zombie_per_outbreak.pdf")
        print("CDF nb. ASes per outbreak:")
        print(cdf)


        # Zombie Frequency for all beacons
        asn_zombie_frequency = collections.Counter(itertools.chain.from_iterable(zombies_per_timebin))

        # add normal ASes:
        for asn in set(itertools.chain.from_iterable(normal_per_timebin)):
            if not asn in asn_zombie_frequency:
                asn_zombie_frequency[asn]=0

        nb_outbreak = sum([len(pfx_res.keys()) for ts, pfx_res in all_classification_results.items()])
        all_zombies = [[asn for pfx, res in pfx_res.items() for asn in res["zombie"]] 
                for ts, pfx_res in all_classification_results.items()]
        all_asn_zombie_frequency = collections.Counter(itertools.chain.from_iterable(all_zombies))

        print("Top zombie transit (nb. outbreak={}): ".format(nb_outbreak))
        for asn, freq in all_asn_zombie_frequency.most_common(100):
            if hegemony[int(asn)]>0.001:
                print("\t AS{}: {:.02f}% ({} times) hegemony={:.03f}".format(asn, 100*freq/nb_outbreak, freq, hegemony[int(asn)]))

        plt.figure(2)
        rfplt.ecdf(np.array(list(asn_zombie_frequency.values()))/nb_zombie_timebin, label="IPv{}".format(af))
        plt.xlabel("freq. AS as zombie/total nb. of outbreaks")
        plt.ylabel("CDF")
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig("fig/CDF_zombie_freq_per_asn.pdf")
        # plt.show()

        unique_pairs = [set([asn+"_"+pfx for pfx, res in pfx_res.items() for asn in res["zombie"]]) 
                for ts, pfx_res in all_classification_results.items()]
        zombie_emergence = collections.Counter(itertools.chain.from_iterable(unique_pairs))
        plt.figure(22)
        rfplt.ecdf(np.array(list(zombie_emergence.values()))/nb_withdraws, label="IPv{}".format(af))
        plt.xlabel("Zombie Emergence Rate")
        plt.ylabel("CDF")
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig("fig/CDF_zombie_emergence_per_asn.pdf")
        # plt.show()

        print("Max. <ASN, beacon>: {} ({} times)".format(
            max(zombie_emergence, key=zombie_emergence.get),
            max(zombie_emergence.values())))
        print("number of outbreaks: {}".format(nb_zombie_timebin))

        for key, freq in zombie_emergence.items():
            if freq>590:
                print("High. <ASN, beacon>: {} ({} times)".format(key, freq))


    ### Zombie frequency per beacon
        all_beacons = set([pfx for pfx_res in all_classification_results.values() for pfx in pfx_res.keys()])
        plt.figure(3)
        print(all_beacons)
        for pfx in all_beacons: 
            zombies_per_timebin_per_beacon = [set([asn for asn in pfx_res[pfx]["zombie"]]) 
                for ts, pfx_res in all_classification_results.items() if pfx in pfx_res]

            asn_zombie_frequency = collections.Counter(itertools.chain.from_iterable(zombies_per_timebin_per_beacon))
            # add normal ASes:
            for asn in set(itertools.chain.from_iterable(normal_per_timebin)):
                if not asn in asn_zombie_frequency:
                    asn_zombie_frequency[asn]=0

            # print("Top 10 zombie ASN for {}: ".format(pfx))
            # for asn, freq in asn_zombie_frequency.most_common(10):
                # print("\t AS{}: {:.02f}% ({} times)".format(asn, 100*freq/len(zombies_per_timebin_per_beacon), freq))

            rfplt.ecdf(np.array(list(asn_zombie_frequency.values()))/len(zombies_per_timebin_per_beacon), label=pfx)
            plt.xlabel("freq. AS as zombie/total nb. of outbreaks")
            plt.ylabel("CDF")
            plt.legend(loc="best", prop={"size":8}, ncol=2)
            plt.tight_layout()
            plt.savefig("fig/CDF_zombie_freq_per_asn_per_beacon.pdf")
            # plt.show()






        # from efficient_apriori import apriori

        # itemsets, rules = apriori(zombies_per_timebin, min_support=0.3, min_confidence=1)
        # print(zombies_per_timebin)
        # for nb_elem, items in itemsets.items():
            # if nb_elem > 1:
                # print(nb_elem)
                # print(items)

        # rules_rhs = filter(lambda rule: len(rule.lhs)==1 and len(rule.rhs)>4, rules)
        # print(list(rules_rhs))


        nb_outbreak_per_prefix = defaultdict(int)
        for ts, events in all_classification_results.items():
            for prefix, classification in events.items():
                nb_outbreak_per_prefix[prefix] += 1

        # print(nb_outbreak_per_prefix)
        h_values = list(nb_outbreak_per_prefix.values())
        plt.figure()
        h_x.append(h_values)
        h_label.append("IPv{}".format(af))
        plt.hist(h_x, label=h_label)
        plt.xlabel("Number of outbreaks per beacon")
        plt.ylabel("Number of beacons")
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig("fig/hist_nb_outbreak_per_prefix.pdf")

        print("On average {} outbreaks per beacon (max={})".format(np.mean(h_values), np.max(h_values)))


        nb_beacon_per_ts = {ts: len(events) for ts, events in all_classification_results.items()}
        # print(nb_beacon_per_ts)

        plt.figure(5)
        cdf = rfplt.ecdf(list(nb_beacon_per_ts.values()), label="IPv{}".format(af))
        plt.xlabel("Number of simultaneous outbreaks")
        plt.ylabel("CDF")
        plt.legend(loc="best")
        plt.xlim([0.5,14.5])
        plt.tight_layout()
        plt.savefig("fig/CDF_nb_simult_zombie.pdf")
        print(cdf)
        print(max(nb_beacon_per_ts, key=nb_beacon_per_ts.get))

        # for ts, val in nb_beacon_per_ts.items():
            # if val==13:
                # print(ts)

if __name__ == "__main__":
    compute_all_stats()    
    pathLenComparions()
    peerZombieLikelihood()
