# This file was created on: 
# Fri May 11 14:05:15 CEST 2018
#
# Last edited on: 
# Fri May 11 14:05:25 CEST 2018
#
# Bash script to extract the AS graph from the text file 
#
# AUTHORS: Paulo Goncalves, Patrice Abry, Esteban Bautista.
# Information: estbautista@ieee.org

#!/bin/bash
source ~/.bash_profile
CODE_PATH="../code"
FILE=$(ls graph_*)
echo $FILE
matlab -nojvm -nodesktop -nosplash -r \
"addpath('$CODE_PATH'); \
graphData = read_AS_graph('$FILE'); \
save('graph.mat','graphData'); quit"
