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
    etime = params[0] 
    prefixes = params[1]

    tmpdate = datetime.urcfromtimestamp(etime) 
    if tmpdate.hour < 8:
       tmpdate.hour = 0
    elif tmpdate.hour < 16:
       tmpdate.hour = 8
    else:
       tmpdate.hour = 16
    tmpdate.minute = 0
    tmpdate.second = 0

    stime = time.mktime(tmpdate.timetuple())

    bd = bgpData.BGPData(stime, etime, prefix)
    bd.readAllData()
    bd.saveGraph()
    bd.saveZombieFile()


starttime = 1504224000
endtime = 1506816000

FORMAT = '%(asctime)s %(processName)s %(message)s'
logging.basicConfig(format=FORMAT, filename='zombie_%s.log' % starttime, level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logging.info("Started: %s" % sys.argv)

proc = Pool(12)

# Retrieve zombies found by Emile
td = tracerouteData.TracerouteData(starttime, endtime)
events = td.getAll()

# Group events by timestamp and prefix
aggEvents = defaultdict(list)
for msmid, desc in events.iteritems():
    aggEvents[1800+(desc["start"]/3600)*3600].append(desc["prefix"])

proc.map(aggEvents.values())
