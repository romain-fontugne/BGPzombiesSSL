# This file was created on: 
# Fri May 11 15:28:23 CEST 2018
#
# Last edited on: 
# Fri May 11 15:28:10 CEST 2018
#
# Call the corresponding matlab code to perform the classification on the data
#
# AUTHORS: Paulo Goncalves, Patrice Abry, Esteban Bautista.
# Information: estbautista@ieee.org

#!/bin/bash
source ~/.bash_profile
GRAPH_PATH="data/graph.mat"
ZOMBIE_PATH=$(ls data/zombie*)
TOOLBOX_PATH="../My-toolboxes"

matlab -nodesktop -nosplash -r \
	"load('$GRAPH_PATH'); addpath('code'); addpath(genpath('$TOOLBOX_PATH'));\
	data = importdata('result/parameter_tuning.txt','\t',1);\
	[~,idx] = max(data.data(:,2)); mu=data.data(idx(1),1); \
	perform_classification('$ZOMBIE_PATH',graphData,mu); \
	quit"
