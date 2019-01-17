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

### Processed results
Zombie paths: https://github.com/romain-fontugne/BGPzombiesSSL/tree/master/zombie_paths
Contains two type of files: graph*.txt and zombies*.txt
Normal paths: https://github.com/romain-fontugne/BGPzombiesSSL/tree/master/normal_paths
Contains two type of files: normal_graph*.txt and normal_zombies*.txt

### Traceroute data
All traceroute results analyzed in our dataset are available through the RIPE Atlas API. 
The description of the corresponding measuerments contains the words "campaign:stuck_routes".
You can access to all these measurements at the following links:
https://atlas.ripe.net/measurements/?page=1&search=description:campaign:stuck_routes#tab-traceroute

You will find much more results there than there is in the paper as we keep running these experiments.
