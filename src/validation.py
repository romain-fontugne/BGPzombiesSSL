import cPickle as pickle
import sys

sys.path.append("../ip2asn")
import ip2asn

ia = ip2asn.ip2asn("../ip2asn/db/rib.20180201.pickle")

def asnres(ip):
    asn = ia.ip2asn(ip)
    return asn

ts = 1505287800
prefix = "84.205.67.0/24"
events = pickle.load(open("events.pickle"))

zombies = set()
for msmid, desc in events.iteritems():
    if 1800+(desc["start"]/3600)*3600 == ts and desc["prefix"] == prefix:
        for ip in desc["zombie"]:
            zombies.add(asnres(ip))

for asn in zombies:
    print asn


