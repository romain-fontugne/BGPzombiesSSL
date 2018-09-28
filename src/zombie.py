import os
import pickle
import logging
import sys
from datetime import datetime

import tracerouteData
import bgpData
import time
from collections import defaultdict

from multiprocessing import Pool

def getBGPdata( params ):
    etime = int(params[0])
    prefixes = params[1][0]

    if not os.path.exists("zombie_paths/zombies_{}_{}.txt".format(etime, prefixes[-1].replace("/","_"))):
        tmpdate = datetime.utcfromtimestamp(etime) 
        tmpdate.replace(minute = 0, second = 0)
        if tmpdate.hour < 8:
            tmpdate.replace(hour=0)
        elif tmpdate.hour < 16:
            tmpdate.replace(hour=8)
        else:
            tmpdate.replace(hour=16)

        stime = time.mktime(tmpdate.timetuple())
        itime = int(etime)-(60*60*2)

        bd = bgpData.BGPData(int(stime), itime, prefixes, )
        try:
            # Read RIB and updates until before the withdraw
            bd.readAllData()
            bd.saveGraph(fname_prefix="normal_paths/normal_")
            bd.saveZombieFile(fname_prefix="normal_paths/normal_")
            with open("normal_paths/normal_bgpdata_%s.pickle" % (bd.endts,), "wb") as fi:
                pickle.dump(bd, fi)

            # Read data during withdraw period
            bd.startts = int(itime)
            bd.endts = int(etime)
            bd.readUpdates()
            bd.saveGraph(fname_prefix="zombie_paths/")
            bd.saveZombieFile(fname_prefix="zombie_paths/")
            with open("zombie_paths/bgpdata_%s.pickle" % (bd.endts,), "wb") as fi:
                pickle.dump(bd, fi)

        except Exception as e:
            logging.error("Error while getting data")
            logging.error(e)
    
    else:
        logging.warning("Already got BGP data: {}, {}".format(etime, prefixes))

# 2018/7 and 2018/8
# starttime = 1531958400
# endtime = 1536710400

# 2017/10 and 2017/12
starttime = 1506816000
endtime = 1514764800

# 2017/03 and 2017/04
#starttime = 1488326400
#endtime = 1493596800


FORMAT = '%(asctime)s %(processName)s %(message)s'
logging.basicConfig(format=FORMAT, filename='zombie_%s.log' % starttime, level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logging.info("Started: %s" % sys.argv)

proc = Pool(32)

# Retrieve zombies found by Emile
if os.path.exists("events_%s_%s.pickle" % (starttime, endtime)):
    logging.info("Loading event list from pickle file")
    events = pickle.load(open("events_%s_%s.pickle" % (starttime, endtime), "rb"))
else:
    logging.info("Computing event list from atlas measurements")
    td = tracerouteData.TracerouteData(starttime, endtime)
    events = td.getAll()
    with open("events_%s_%s.pickle" % (starttime, endtime),"wb") as fi:
        pickle.dump(events,fi)
    with open("traceroutes_%s_%s.pickle" % (starttime, endtime),"wb") as fi:
        pickle.dump(td,fi)

# Group events by timestamp and prefix
aggEvents = defaultdict(list)
for msmid, desc in events.items():
    aggEvents[1800+int(desc["start"]/3600)*3600].append( (desc["prefix"],) )

logging.info("%s events to analyze" % (len(aggEvents)))
# map(getBGPdata, aggEvents.items())
proc.map(getBGPdata, aggEvents.items())

