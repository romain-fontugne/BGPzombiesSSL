import logging
import pickle
import networkx as nx
from _pybgpstream import BGPStream, BGPRecord, BGPElem
from collections import defaultdict

class BGPData():

    def __init__(self, startts, endts, prefixes):
        self.events = pickle.load(open("events.pickle","rb"))
        self.paths = defaultdict(dict)
        self.withdraws = defaultdict(dict)
        self.startts = startts
        self.endts = endts
        self.prefixes = prefixes
        self.af=4


    def readRIB(self):
        # create a new bgpstream instance
        stream = BGPStream()
        # create a reusable bgprecord instance
        rec = BGPRecord()
        bgprFilter = "type ribs"

        if self.af == 6:
            bgprFilter += " and ipversion 6"
        else:
            bgprFilter +=  " and ipversion 4"

        bgprFilter += " and project ris " 

        for prefix in self.prefixes:
            bgprFilter += " and prefix more %s " % prefix
        
        logging.info("Connecting to BGPstream... (%s)" % bgprFilter)
        logging.info("Timestamps: %s, %s" % (self.startts-3600, self.startts+3600))
        stream.parse_filter_string(bgprFilter)
        stream.add_interval_filter(self.startts-3600, self.startts+3600)

        stream.start()
        while(stream.get_next_record(rec)):
            if rec.status  != "valid":
                print(rec.project, rec.collector, rec.type, rec.time, rec.status)

            zDt = rec.time
            elem = rec.get_next_elem()
            while(elem):
                # peerip g= elem.peer_address
                peeras = elem.peer_asn
                sPath = elem.fields["as-path"]
                sPrefix = elem.fields["prefix"]

                self.paths[sPrefix][peeras] = sPath
                self.withdraws[sPrefix][peeras] = False

                elem = rec.get_next_elem()

    
    def readUpdates(self):
        # create a new bgpstream instance
        stream = BGPStream()
        # create a reusable bgprecord instance
        rec = BGPRecord()
        bgprFilter = "type updates"

        if self.af == 6:
            bgprFilter += " and ipversion 6"
        else:
            bgprFilter +=  " and ipversion 4"

        bgprFilter += " and project ris " 
        for prefix in self.prefixes:
            bgprFilter += " and prefix more %s " % prefix

        logging.info("Connecting to BGPstream... (%s)" % bgprFilter)
        logging.info("Timestamps: %s, %s" % (self.startts, self.endts))
        stream.parse_filter_string(bgprFilter)
        stream.add_interval_filter(self.startts, self.endts)

        stream.start()
        while(stream.get_next_record(rec)):
            if rec.status  != "valid":
                print(rec.project, rec.collector, rec.type, rec.time, rec.status)

            zDt = rec.time
            elem = rec.get_next_elem()
            while(elem):
                # peerip g= elem.peer_address
                peeras = elem.peer_asn
                sPrefix = elem.fields["prefix"]

                if elem.type == "W":
                    self.withdraws[sPrefix][peeras] = True

                else:
                    sPath = elem.fields["as-path"]
                    self.paths[sPrefix][peeras] = sPath
                    self.withdraws[sPrefix][peeras] = False

                elem = rec.get_next_elem()


    def readAllData(self):
        self.readRIB()
        self.readUpdates()


    def saveGraph(self):
        for prefix in self.prefixes:
            asgraph = nx.Graph()

            for lastPath in self.paths[prefix].values():
                path = lastPath.split(" ")

                for a0, a1 in zip(path[:-1], path[1:]):
                    asgraph.add_edge(a0,a1)

            nx.write_adjlist(asgraph, "graph_%s_%s.txt" % (self.endts ,prefix.replace("/", "_")))


    def saveZombieFile(self):
        for prefix in self.prefixes:
            with open("zombies_%s_%s.txt" % (self.endts, prefix.replace("/", "_")), "w") as fi:
                for asn, w in self.withdraws[prefix].items():
                    label = 0
                    if not w:
                        label = 1

                    fi.write("%s\t%s\n" % (asn, label))

                fi.close()

