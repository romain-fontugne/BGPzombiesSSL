# This file was created on: 
# Fri May 11 15:28:23 CEST 2018
#
# Last edited on: 
# Fri May 11 15:28:10 CEST 2018
#
#
# AUTHORS: Paulo Goncalves, Patrice Abry, Esteban Bautista.
# Information: estbautista@ieee.org

#!/bin/bash
source ~/.bash_profile
GRAPH_PATH="data/graph.mat"
ZOMBIE_PATH=$(ls data/zombie*)
TOOLBOX_PATH="../My-toolboxes"
MU="[0.01,0.05,0.1:0.15:1,2:1:10,20]"
TRIALS="30"

matlab -nodesktop -nosplash -r \
	"load('$GRAPH_PATH'); addpath('code'); addpath(genpath('$TOOLBOX_PATH'));\
	perform_training('$ZOMBIE_PATH',graphData,$MU,$TRIALS); \
	quit"
