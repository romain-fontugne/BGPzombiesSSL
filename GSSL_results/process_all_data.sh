# This file was created on: 
# Fri May 11 15:28:23 CEST 2018
#
# Last edited on: 
# Fri May 11 15:28:10 CEST 2018
#
# Bash script to perform the classification on all data files contained in the 
# All_data folder. The program calls smaller programs used for each file, this way 
# the other programs can be run individually on their respective files if desired.
#
#
# AUTHORS: Paulo Goncalves, Patrice Abry, Esteban Bautista.
# Information: estbautista@ieee.org

#!/bin/bash
source ~/.bash_profile

# Place the files in their own folder
for i in All_data/graph*; 
do 
	name=${i#"All_data/graph_"} 
	name=${name%".txt"}	
	mkdir $name
	mkdir $name"/result"
	mkdir $name"/data"
	cp "All_data/graph_"$name".txt" $name"/data"
	cp "All_data/zombies_"$name".txt" $name"/data"
done;

# Place the necessary code to read the files 
for i in All_data/graph*; 
do 
	name=${i#"All_data/graph_"} 
	name=${name%".txt"}	
	cp Functions/extract_graph.sh $name"/data" 
	cp Functions/run* $name
	cp -R Functions/code $name
done;

# Execute the bash scripts 
for i in All_data/graph*; 
do 
	name=${i#"All_data/graph_"} 
	name=${name%".txt"}	
	cd $name"/data"
	/bin/bash extract_graph.sh
	cd -
	cd $name
	/bin/bash run_training_experiment.sh

	var=$(<"result/error_log.txt") 
	message="The labeled data belongs to a single class"
	if [ "$var" != "$message" ]; then
	/bin/bash run_classification_experiment.sh; fi;
	cd -
done;
