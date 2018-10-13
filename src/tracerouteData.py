import logging
from ripe.atlas.cousteau import AtlasRequest
from ripe.atlas.cousteau import AtlasResultsRequest

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
            zombies = set()
            clean = set()
            prb_ips = set()
            prb_ids = set()
            endtimes = set()
            if msm["id"] in self.traceroutes:
                logging.warn("No traceroutes for msm %s " % msm["id"])

                for trace in self.traceroutes[msm["id"]]:
                    endtimes.add(trace["endtime"])
                    prb_ips.add(trace["from"])
                    prb_ids.add(trace["prb_id"])
                    for hop in trace["result"]:
                        if "result" in hop:
                            for router in hop["result"]:
                                if "from" in router:
                                    if "err" not in router:
                                        zombies.add(router["from"])
                                    else:
                                        clean.add(router["from"])

            if "." in msm["target_ip"]: 
                prefix = msm["target_ip"].rpartition(".")[0]+".0/24"
            if ":" in msm["target_ip"]:
                prefix = msm["target_ip"].rpartition(":")[0]+":/48"
            self.events[msm["id"]] = {
                    "start": msm["start_time"], 
                    "prefix":prefix, 
                    "zombie":zombies, 
                    "clean":clean,
                    "prb_ips": prb_ips,
                    "prb_ids": prb_ids,
                    "endtimes": endtimes} 

if __name__ == "__main__":
    fname = sys.argv[1]
    td = pickle.load(open(fname, "rb"))
    td.getTraceroutes()
    td.listEvents()
    with open(fname+"_events.pickle","wb") as fi:
        pickle.dump(td.events,fi)
    with open(fname+"_traceroute.pickle","wb") as fi:
        pickle.dump(td,fi)
