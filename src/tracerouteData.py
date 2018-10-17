import logging
import sys
import re
import pickle
from ripe.atlas.cousteau import AtlasRequest
from ripe.atlas.cousteau import AtlasResultsRequest
from collections import Counter

# https://en.wikipedia.org/wiki/Private_network
priv_24 = re.compile("^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
priv_20 = re.compile("^192\.168\.\d{1,3}.\d{1,3}$")
priv_16 = re.compile("^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$")
priv_lo = re.compile("^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

def isPrivateIP(ip):
    if priv_24.match(ip) or priv_20.match(ip) or priv_16.match(ip) or priv_lo.match(ip):
        return True
    else:
        return False

class TracerouteData():

    def __init__(self, starttime, endtime ):
        self.starttime = starttime
        self.endtime = endtime
        self.msmsURL = "/api/v2/measurements/?description__contains=campaign:stuck_routes&start_time__gte=%s&stop_time__lt=%s" 
        self.msms = []
        self.traceroutes = {}
        self.events = {} 


    def getMsmIds(self):
        """Get metadata for measurements corresponding to self.msmsURL"""

        nextPath = self.msmsURL % (self.starttime, self.endtime )
        while nextPath:
            request = AtlasRequest(**{"url_path": nextPath})
            (is_success, response) = request.get()
            if not is_success:
                logging.warn("Something wrong happened while fetching measurement descriptions")

            self.msms.extend( response["results"] )
            if response["next"] is not None:
                nextPath = response["next"].partition("https://atlas.ripe.net")[2]
            else:
                nextPath = False
            logging.info(nextPath)	


    def getTraceroutes(self):
        """Get traceroute results for all the measurements found with self.msmsURL"""

        for msm in self.msms:
            resPath = "/api/v2/measurements/%s/results/" % (msm["id"], )
            request = AtlasRequest(**{"url_path": resPath})
            (is_success, response) = request.get()

            if is_success:
                self.traceroutes[msm["id"]] = response
            else:
                logging.warn("Something wrong happened while fetching traceroute results")
                logging.warn(response)


    def getAll(self):
        """Get measurements metadata and corresponding traceroute data"""

        logging.info("Fetching measurements metadata...")
        self.getMsmIds()
        logging.info("Found {} msms".format(len(self.msms)))
        logging.info("Fetching traceroute results...")
        self.getTraceroutes()
        logging.info("Save events...")
        self.listEvents()

        return self.events

    
    def listEvents(self):
        """Provide descriptions (timestamp, prefix, responsive IPs) of all events
        found in the data"""

        for msm in self.msms:
            nb_only_stars = 0
            zombies = []
            clean = []
            prb_ips = set()
            prb_ids = set()
            endtimes = set()
            if msm["id"] in self.traceroutes:
                # logging.warn("No traceroutes for msm %s " % msm["id"])
                zombie_start = 1800+int(msm["creation_time"]/3600)*3600
                zombie_end = zombie_start+1740

                nb_traceroutes = 0
                for trace in self.traceroutes[msm["id"]]:
                    # ignore traceroute before/after our zombie detection
                    # period
                    if trace["timestamp"]<zombie_start or trace["endtime"]>zombie_end:
                        continue

                    nb_traceroutes += 1
                    prb_ips.add(trace["from"])
                    prb_ids.add(trace["prb_id"])
                    first_public_hop = ""
                    only_stars = True

                    for hop in trace["result"]:
                        if "result" in hop:
                            for router in hop["result"]:
                                if "from" in router:
                                    # ignore private IPs
                                    if isPrivateIP(router["from"]):
                                        continue

                                    # ignore first public hop
                                    if not first_public_hop or first_public_hop==router["from"]:
                                        first_public_hop = router["from"]
                                        continue

                                    if "err" in router:
                                        clean.append(router["from"])
                                    else:
                                        only_stars = False
                                        zombies.append(router["from"])

                    if only_stars:
                        nb_only_stars += 1


                if "." in msm["target_ip"]: 
                    prefix = msm["target_ip"].rpartition(".")[0]+".0/24"
                if ":" in msm["target_ip"]:
                    prefix = msm["target_ip"].rpartition(":")[0]+":/48"

                self.events[msm["id"]] = {
                    "nb_traceroutes": nb_traceroutes,
                    "start": msm["start_time"], 
                    "prefix": prefix, 
                    "zombie": Counter(zombies), 
                    "clean": Counter(clean),
                    "prb_ips": prb_ips,
                    "prb_ids": prb_ids,
                    "nb_only_stars": nb_only_stars,
                    "endtimes": endtimes} 


if __name__ == "__main__":
    fname = sys.argv[1]
    FORMAT = '%(asctime)s %(processName)s %(message)s'
    logging.basicConfig(format=FORMAT, filename=fname+'.log', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Started: %s" % sys.argv)
    td = pickle.load(open(fname, "rb"))
    td.getTraceroutes()
    td.listEvents()
    with open(fname+"_events.pickle","wb") as fi:
        pickle.dump(td.events,fi)
    with open(fname+"_traceroute.pickle","wb") as fi:
        pickle.dump(td,fi)

