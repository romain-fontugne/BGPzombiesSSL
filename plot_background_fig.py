import pickle
import os
import logging
from collections import defaultdict
from _pybgpstream import BGPStream, BGPRecord, BGPElem
import numpy as np
from matplotlib import pylab as plt
from matplotlib.colors import ListedColormap
import matplotlib.dates as mdates
import datetime


# prefix = "84.205.67.0/24"
# prefix = "84.205.68.0/24"
prefixes = ["84.205.64.0/24", "84.205.65.0/24", "84.205.67.0/24", "84.205.68.0/24",
        "84.205.69.0/24", "84.205.70.0/24", "84.205.71.0/24", "84.205.74.0/24",
        "84.205.75.0/24", "84.205.76.0/24", "84.205.77.0/24", "84.205.78.0/24", 
        "84.205.79.0/24", "84.205.73.0/24", "84.205.82.0/24", "93.175.149.0/24",
        "93.175.151.0/24", 
        "2001:7FB:FE00::/48", "2001:7FB:FE01::/48", "2001:7FB:FE03::/48", 
        "2001:7FB:FE04::/48", "2001:7FB:FE05::/48", "2001:7FB:FE06::/48",
        "2001:7FB:FE07::/48", "2001:7FB:FE0A::/48", "2001:7FB:FE0B::/48",
        "2001:7FB:FE0C::/48", "2001:7FB:FE0D::/48", "2001:7FB:FE0E::/48",
        "2001:7FB:FE0F::/48", "2001:7FB:FE10::/48", "2001:7FB:FE12::/48",
        "2001:7FB:FE13::/48", "2001:7FB:FE14::/48", "2001:7FB:FE15::/48",
        "2001:7FB:FE16::/48", "2001:7FB:FE17::/48"]
# "84.205.76.0/24"
startts =1533427200 # 2018/8/5
# endts =1533556200 # 2018/8/6 12:00
# startts =1533556200 # 2018/8/6 12:00
endts =1533642600 # 2018/8/7 12:00
af = 4
bin_size = 900

def plot_figure(results_all_prefixes):

    nbtimebins = len(results_all_prefixes["other"]["timebin"])
    for prefix, results in results_all_prefixes.items():

        y = 0
        data_mat = []
        peers_to_plot = [14907, 30844 , 2914, 9002, 4777, 59689, 395152, 51405, 262757]
        plotted_peers = []
        for peerasn, states in results.items():
            if len(states) < nbtimebins-2 or  peerasn=="timebin":
                continue

            if peerasn in peers_to_plot:
                data_mat.append(states)
                plotted_peers.append("AS{}".format(peerasn))


        arr = np.vstack(data_mat)
        arr[arr=="A"] = 1
        arr[arr=="W"] = 0
        arr = arr.astype(np.int)
        

        fig, ax = plt.subplots(figsize=(10,3))
        cmap = ListedColormap(['red','limegreen'])
        im = plt.pcolor(arr, cmap=cmap, edgecolors='w', axes=ax)
        plt.yticks(np.arange(0.5,len(plotted_peers)+0.5), plotted_peers)
        date_pos = range(0, len(results_all_prefixes["other"]["timebin"]), 8)
        date_label = [datetime.datetime.utcfromtimestamp(results_all_prefixes["other"]["timebin"][i]) for i in date_pos]
        date_label = ["{}/{} {:02d}:{:02d}".format( d.month, d.day, d.hour, d.minute) for d in date_label ]
        plt.xticks(date_pos, date_label)
        plt.ylabel("BGP peer ASN")
        fig.autofmt_xdate()
        plt.grid(False)
        for edge, spine in ax.spines.items():
            spine.set_visible(False)
        # Create colorbar

        cbar = ax.figure.colorbar(im, ax=ax, ticks=[])
        cbar.ax.set_ylabel(" Reachable     Unreachable", rotation=-90, va="bottom")
        plt.title(prefix)
        plt.tight_layout()
        plt.savefig("fig/background_figure_{}.pdf".format(prefix.replace("/","_")))

        # return plotted_peers

def defaultdict_list():
        return defaultdict(list)

def download_data():
    peer_state = defaultdict(dict)
    results = defaultdict(defaultdict_list)
    current_bin = 0

    # create a new bgpstream instance
    stream = BGPStream()
    # create a reusable bgprecord instance
    rec = BGPRecord()
    bgprFilter = "type updates"

    bgprFilter += " and project ris " 
    for prefix in prefixes:
        bgprFilter += " and prefix more %s " % prefix

    logging.info("Connecting to BGPstream... (%s)" % bgprFilter)
    logging.info("Timestamps: %s, %s" % (startts, endts))
    stream.parse_filter_string(bgprFilter)
    stream.add_interval_filter(startts, endts)

    stream.start()
    while(stream.get_next_record(rec)):
        if rec.status  != "valid":
            print(rec.project, rec.collector, rec.type, rec.time, rec.status)
            # from IPython import embed
            # embed()

        if current_bin == 0:
            current_bin = rec.time

        # slide the time window:
        if current_bin+bin_size < rec.time:
            timebins = range(current_bin, rec.time, bin_size)
            for i in timebins[:-1]: 
                results["other"]["timebin"].append(i)
                for pfx, p_s in peer_state.items():
                    for peeras, state in p_s.items():
                        results[pfx][peeras].append(state)


            current_bin = timebins[-1] 

        elem = rec.get_next_elem()
        while(elem):
            # peerip g= elem.peer_address
            peeras = elem.peer_asn
            prefix = elem.fields["prefix"]

            peer_state[prefix][peeras] = elem.type

            elem = rec.get_next_elem()

    return results

if __name__ == "__main__":
    pickle_fname = "background_fig_data_{}_{}.pickle".format("all_beacons", startts)
    if not os.path.exists(pickle_fname):
        results = download_data()
        pickle.dump(results, open(pickle_fname, "wb"))
    else:
        results = pickle.load(open(pickle_fname, "rb"))

    plot_figure(results)
