import os
import logging
import sys
from matplotlib import pylab as plt
plt.switch_backend('agg')
import glob
import pickle
import networkx as nx
from collections import defaultdict
import multiprocessing

sys.path.append("../ip2asn")
import ip2asn

ia = ip2asn.ip2asn("../ip2asn/db/rib.20180201.pickle")
esteban_results_directory = "20181001_BGPcount"

def asnres(ip):
    """Find the ASN corresponding to the given IP address"""

    asn = ia.ip2asn(ip)
    if asn == "unknown":
        asn="0"
    return str(asn)

def validation(events, ts = 1505287800, prefix = "84.205.67.0/24"):
    """Validate SSL results using traceroute data.
    
    Compare SSL results to BGP results and responding IP addresses found in 
    traceroute data. Also plot the results in a graph where node shape stands 
    for SSL results (triangle=zombie, circle=normal) and the color represents 
    the ground truth (red=zombie, green=normal, orange means results from 
    traceroutes and BGP are inconsistent, and gray means unknown)"""

    print("Processing %s %s..." % (ts, prefix))
    fname = "zombie_paths/graph_%s_%s.txt" % (ts, prefix.replace("/", "_").replace("-",":"))
    G = nx.read_adjlist(fname)

    ##### Traceroute data #####

    ztr = set()
    ntr = set()
    asn2ip = defaultdict(list) 
    for msmid, desc in events.items():
        if 1800+(desc["start"]/3600)*3600 == ts and desc["prefix"] == prefix:
            for ip in desc["zombie"]:
                asn = asnres(ip)
                asn2ip[asn].append(ip)
                if asn in G:
                    ztr.add(asn)

            for ip in desc["clean"]:
                asn = asnres(ip)
                if asn in G:
                    ntr.add(asn)

    # Remove ASN 0 from results
    if "0" in ztr:
        ztr.remove("0")
    if "0" in ntr:
        ntr.remove("0")

    ##### BGP data #####
    fname = "zombie_paths/zombies_%s_%s.txt" % (ts, prefix.replace("/", "_").replace("-",":"))

    zbgp = set()
    nbgp = set()
    for line in open(fname):
        asn, zombie = [x for x in line.split()]
        
        if asn in G:
            if int(zombie):
                zbgp.add(asn)
            else:
                nbgp.add(asn)


    ##### Ground Truth: Merge BGP and traceroute #####
    zgt = set()
    ngt = set()
    cgt = set()

    zgt = ztr.union(zbgp)
    ngt = ntr.union(nbgp)
    # ASNs labelled both normal and zombies are set as unknown
    cgt = zgt.intersection(ngt)
    zgt = zgt.difference(cgt)
    ngt = ngt.difference(cgt)


    ##### Esteban's results #####
    fname = esteban_results_directory+"/%s_%s/result/classification.txt" % (ts, prefix.replace("/","_"))

    if not os.path.exists(fname):
        logging.error("Error no classification results: {}".format(fname))
        return

    zpr = set()
    npr = set()
    for i, line in enumerate(open(fname)):
        # skip the header
        if i ==0:
            continue

        cluster, asn = [x.partition(".")[0] for x in line.split()]

        if int(cluster) == 2:
            zpr.add(asn)
        else:
            npr.add(asn)



    ##### Validation Results #####
    try:
        os.makedirs("validation/%s_%s/" % (ts, prefix.replace("/","_")))
    except :
        pass
    fname = "validation/%s_%s/validation.txt" % (ts, prefix.replace("/","_"))
    fi = open(fname,"w")
    fi.write("%s nodes in total\n" % (len(G)))
    fi.write("Traceroute: %s zombies, %s normal\n" % (len(ztr), len(ntr)))
    fi.write("BGP: %s zombies, %s normal\n" % (len(zbgp), len(nbgp)))
    fi.write("Ground Truth: %s zombies, %s normal, %s conflicting\n" % (len(zgt), len(ngt), len(cgt)))
    fi.write("Page Rank: %s zombies, %s normal\n" % (len(zpr), len(npr)))
    # print "Intersection: zombies gt&pr %s" % (len(zgt.intersection(zpr)))
    # print "Intersection: normal gt&pr %s" % (len(ngt.intersection(npr)))
    # print "Intersection: unk/zombies gt&pr %s" % (len(cgt.intersection(zpr)))
    res ="""
                        Ground Truth
            zombie    normal    conflict     unknown

    zombie      %s          %s          %s          %s
    normal      %s          %s          %s          %s
    """ % (len(zpr.intersection(zgt)), len(zpr.intersection(ngt)), len(zpr.intersection(cgt)), len(zpr.difference(zgt.union(ngt.union(cgt)))),
        len(npr.intersection(zgt)), len(npr.intersection(ngt)), len(npr.intersection(cgt)), len(npr.difference(zgt.union(ngt.union(cgt)))))

    fi.write(res)
    fi.close()

    ### Plot the graph ###
    # pos = nx.spring_layout(G)
    pos = nx.kamada_kawai_layout(G)

    # INPUT Graph
    plt.figure(figsize=(12,12))
    nx.draw_networkx_nodes(G,pos, nodelist=["12654"], node_color='b',  node_size=700)
    nx.draw_networkx_nodes(G,pos, nodelist=zbgp, node_color='r', node_shape="o", node_size=300)
    nx.draw_networkx_nodes(G,pos, nodelist=nbgp, node_color='g', node_shape="o", node_size=300)
    nx.draw_networkx_nodes(G,pos, nodelist=zpr.union(npr).difference(zbgp).difference(nbgp), node_color='gray', node_shape="o", node_size=300)

    nx.draw_networkx_edges(G,pos,width=1.0,alpha=0.5, edge_color="k")

    plt.grid(False)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("validation/%s_%s/graph_input.pdf" % (ts, prefix.replace("/","_")))
    nx.draw_networkx_labels(G, pos, {x:x for x in G.nodes()})
    plt.savefig("validation/%s_%s/graph_input_labelled.pdf" % (ts, prefix.replace("/","_")))
    # plt.show()

    # OUTPUT Graph and groud truth
    plt.figure(figsize=(12,12))
    nx.draw_networkx_nodes(G,pos, nodelist=["12654"], node_color='b',  node_size=700)
    nx.draw_networkx_nodes(G,pos, nodelist=zpr.intersection(zgt), node_color='r', node_shape="^", node_size=300)
    nx.draw_networkx_nodes(G,pos, nodelist=zpr.intersection(ngt), node_color='g', node_shape="^", node_size=300)
    nx.draw_networkx_nodes(G,pos, nodelist=zpr.intersection(cgt), node_color='orange', node_shape="^", node_size=300)
    nx.draw_networkx_nodes(G,pos, nodelist=zpr.difference(ngt).difference(zgt).difference(cgt), node_color='gray', node_shape="^", node_size=300)
    nx.draw_networkx_nodes(G,pos, nodelist=npr.difference(ngt).difference(zgt).difference(cgt), node_color='gray', node_shape="o", node_size=300)
    nx.draw_networkx_nodes(G,pos, nodelist=npr.intersection(ngt), node_color='g', node_shape="o", node_size=300)
    nx.draw_networkx_nodes(G,pos, nodelist=npr.intersection(zgt), node_color='r', node_shape="o", node_size=300)
    nx.draw_networkx_nodes(G,pos, nodelist=npr.intersection(cgt), node_color='orange', node_shape="o", node_size=300)

    nx.draw_networkx_edges(G,pos,width=1.0,alpha=0.5, edge_color="k")

    plt.grid(False)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("validation/%s_%s/graph.pdf" % (ts, prefix.replace("/","_")))
    nx.draw_networkx_labels(G, pos, {x:x for x in G.nodes()})
    plt.savefig("validation/%s_%s/graph_labelled.pdf" % (ts, prefix.replace("/","_")))
    # plt.show()

    return {"ZZ":len(zpr.intersection(zgt)), "ZN":len(zpr.intersection(ngt)), 
            "ZC":len(zpr.intersection(cgt)), "ZU":len(zpr.difference(zgt.union(ngt.union(cgt)))),
            "NZ":len(npr.intersection(zgt)), "NN":len(npr.intersection(ngt)), 
            "NC":len(npr.intersection(cgt)), "NU":len(npr.difference(zgt.union(ngt.union(cgt))))}

if __name__ == "__main__":
    if len(sys.argv) == 1:
        pool = multiprocessing.Pool()
        params = []
        all_events = [
                pickle.load(open("events_1488326400_1493596800.pickle", "rb")),
                pickle.load(open("events_1506816000_1514764800.pickle", "rb")),
                pickle.load(open("events_1531958400_1537401600.pickle", "rb"))
                ]
        
        for i, path in enumerate(glob.glob(esteban_results_directory+"/*_[24,48]")):
            dname = path.rpartition("/")[2]
            ts, _, prefix = dname.partition("_")
            prefix = prefix.replace("_","/")

            # print("Processing %s %s..." % (ts, prefix))
            if ts<1500000000:
                events = all_events[0]
            elif ts<1530000000:
                events = all_events[1]
            else:
                events = all_events[2]
            params.append( (events, int(ts), prefix) )
            # validation(int(ts), prefix)

            # if i == 10:
                # break

        all_results = pool.starmap(validation, params)

        agg_results = defaultdict(int)
        for res in all_results:
            if res is None:
                continue
            for k, v in res.items():
                agg_results[k]+=v

        print("""
                        Ground Truth
            zombie    normal    conflict     unknown

    zombie      %s          %s          %s          %s
    normal      %s          %s          %s          %s
    """ % (agg_results["ZZ"], agg_results["ZN"], agg_results["ZC"],
        agg_results["ZU"], agg_results["NZ"], agg_results["NN"],
        agg_results["ZC"], agg_results["ZU"])
        )

    elif len(sys.argv)==3:
        ts = int(sys.argv[1])
        prefix = sys.argv[2]
        if ts<1500000000:
            events = pickle.load(open("events_1488326400_1493596800.pickle", "rb"))
        elif ts<1530000000:
            events = pickle.load(open("events_1506816000_1514764800.pickle", "rb"))
        else:
            events = pickle.load(open("events_1531958400_1537401600.pickle", "rb"))
        validation(events, ts, prefix)

    else:
        print("usage: %s timestamp prefix" % sys.argv[0])
        print("usage: %s \n(In this case it looks for results in the folder ./esteban/)" % sys.argv[0])
        quit()
    
