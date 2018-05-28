import os
import cPickle as pickle
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
    prefixes = params[1]

    tmpdate = datetime.utcfromtimestamp(etime) 
    if tmpdate.hour < 8:
       tmpdate.replace(hour=0)
    elif tmpdate.hour < 16:
       tmpdate.replace(hour=8)
    else:
       tmpdate.replace(hour=16)
    tmpdate.replace(minute = 0, second = 0)

    stime = time.mktime(tmpdate.timetuple())

    bd = bgpData.BGPData(int(stime), int(etime), prefixes)
    bd.readAllData()
    bd.saveGraph()
    bd.saveZombieFile()


starttime = 1506816000
endtime = 1514764800

FORMAT = '%(asctime)s %(processName)s %(message)s'
logging.basicConfig(format=FORMAT, filename='zombie_%s.log' % starttime, level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logging.info("Started: %s" % sys.argv)

proc = Pool(12)

# Retrieve zombies found by Emile
if os.path.exists("events_%s_%s.pickle" % (starttime, endtime)):
    logging.info("Loading event list from pickle file")
    events = pickle.load(open("events_%s_%s.pickle" % (starttime, endtime)))
else:
    logging.info("Computing event list from atlas measurements")
    td = tracerouteData.TracerouteData(starttime, endtime)
    events = td.getAll()
    with open("events_%s_%s.pickle" % (starttime, endtime),"w") as fi:
        pickle.dump(events,fi)

# Group events by timestamp and prefix
aggEvents = defaultdict(list)
for msmid, desc in events.iteritems():
    aggEvents[1800+(desc["start"]/3600)*3600].append(desc["prefix"])

# map(getBGPdata, aggEvents.items())
proc.map(getBGPdata, aggEvents.items())

