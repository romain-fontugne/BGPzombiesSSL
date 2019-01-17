# This file was created on: 
#
# Last edited on: 
#
# Bash script to perform the classification on the folders who
# the matlab had issues and did not operate
#
# AUTHORS: Paulo Goncalves, Patrice Abry, Esteban Bautista.
# Information: estbautista@ieee.org

#!/bin/bash
source ~/.bash_profile

# Place the files in their own folder
for i in `find [1-9]*/result -type d`
do	
	string=$(ls $i)
	if [ -z "$string" ];
       	then
		echo "Folder $i processed" >> ~/Desktop/report.txt
		name=${i%"/result"}
		cd $name"/data"
		/bin/bash extract_graph.sh
		cd -
		cd $name
		/bin/bash run_training_experiment.sh

		var=$(<"result/error_log.txt")
		message="The labeled data belongs to a single class"
		if [ "var" != "message" ]; then
		/bin/bash run_classification_experiment.sh; fi
		cd -
	else
		:
	fi
done;
