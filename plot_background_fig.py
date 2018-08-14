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
prefix = "84.205.76.0/24"
# startts =1533427200 # 2018/8/5
# endts =1533556200 # 2018/8/6 12:00
startts =1533556200 # 2018/8/6 12:00
endts =1533642600 # 2018/8/7 12:00
af = 4
bin_size = 900

def plot_figure(results):

    nbtimebins = len(results["timebin"])

    y = 0
    data_mat = []
    peers_to_plot = [30844 , 2914, 9002, 4777, 59689, 395152, 51405, 262757]
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
    date_pos = range(0, len(results["timebin"]), 8)
    date_label = [datetime.datetime.utcfromtimestamp(results["timebin"][i+1]) for i in date_pos]
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

    return plotted_peers

def download_data():
    peer_state = {}
    results = defaultdict(list)
    current_bin = 0

    # create a new bgpstream instance
    stream = BGPStream()
    # create a reusable bgprecord instance
    rec = BGPRecord()
    bgprFilter = "type updates"

    if af == 6:
        bgprFilter += " and ipversion 6"
    else:
        bgprFilter +=  " and ipversion 4"

    bgprFilter += " and project ris " 
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
                results["timebin"].append(i)
                for peeras, state in peer_state.items():
                    results[peeras].append(state)


            current_bin = timebins[-1] 

        elem = rec.get_next_elem()
        while(elem):
            # peerip g= elem.peer_address
            peeras = elem.peer_asn

            peer_state[peeras] = elem.type

            elem = rec.get_next_elem()

    return results

if __name__ == "__main__":
    pickle_fname = "background_fig_data_{}_{}.pickle".format(prefix.replace("/","_"), startts)
    if not os.path.exists(pickle_fname):
        results = download_data()
        pickle.dump(results, open(pickle_fname, "wb"))
    else:
        results = pickle.load(open(pickle_fname, "rb"))

    plot_figure(results)
