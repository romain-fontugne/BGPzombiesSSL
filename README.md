# BGP Zombies: an Analysis of Beacons Stuck Routes

This repository complements our [PAM 2019 paper](https://www.iij-ii.co.jp/en/members/romain/pdf/romain_pam2019.pdf) on BGP Zombies.
Please cite this paper if you want to refer to this work:
```
@inproceedings{fontugne2019zombies,
  title={{BGP Zombies:} an Analysis of Beacons Stuck Routes},
  author={R. Fontugne, E. Bautista, C. Petrie, Y. Nomura, P. Abry, P. Goncalves, K. Fukuda, E. Aben},
  booktitle={Proceedings of PAM'19},
  year={2019},
  organization={LNCS}
}
```

## Datasets
We provide both our results from processed BGP data and traceroute data for validation.

### Results

#### Processed BGP data (Zombies observed with RIS)
The [zombie_paths folder](https://github.com/romain-fontugne/BGPzombiesSSL/tree/master/zombie_paths) and [normal_paths folder](https://github.com/romain-fontugne/BGPzombiesSSL/tree/master/normal_paths) provide the zombie paths detected during zombie outbreaks and the normal paths observed before the outbreaks. There is two types of files, the graph_ts_beacon.txt files contain the full AS graph for the given timestamp (ts) and beacon prefix. The zombies_ts_beacon.txt files contain the list of observed ASNs and their classification results, 1 means a zombie AS and 0 a normal AS.

#### Classification results (Zombies inferred with G-SSL)
Using the above data G-SSL classify unknown ASes as zombie or normal ASes. The classification results are available in the [GSSL_results](https://github.com/romain-fontugne/BGPzombiesSSL/tree/master/GSSL_results). For each beacon and timestamp there is a classification.txt file that contains the classification results. In this file 1.0 represent a normal ASN and 2.0 represents a zombie ASN.


### Traceroute data
All traceroute results analyzed in our dataset are available through the RIPE Atlas API. 
The description of the corresponding measuerments contains the words "campaign:stuck_routes".
You can access to all these measurements at the following links:
https://atlas.ripe.net/measurements/?page=1&search=description:campaign:stuck_routes#tab-traceroute

You will find much more results there than there is in the paper as we keep running these experiments.
