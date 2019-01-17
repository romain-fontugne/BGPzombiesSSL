% This file was created on: 
% Thu Oct 26 11:03:14 CEST 2017
%
% Last edited on: 
% Fri May 11 13:45:10 CEST 2018
%
% Usage: graph = perform_classification(zombieFile,graphData,mu)
% Function that performs the classification of the graph nodes according to the
% labeled information provided in the zombieFile
%
% INPUT: zombieFile: path to the zombie file
%	 graphData: graph structure
%	 mu: regularization parameter of the GSSL
%
% OUTPUT: classification result printed in a file stored in the result folder
%
% AUTHORS: Paulo Goncalves, Patrice Abry, Esteban Bautista.
% Information: estbautista@ieee.org

function perform_classification(zombieFile,graphData,mu)
	labels = zombies_to_labels(zombieFile,graphData);
	[~,~,classification] = standard_SSL_PR(graphData.A,mu,labels.labels);

	% save result to a file
	fileID = fopen('result/classification.txt','w');
	fprintf(fileID,'%s\t%s\n','Class','Node Name');
	for i = 1 : length(classification)
		fprintf(fileID,'%f\t%s\n',classification(i), graphData.nodesNames{i});
	end
	fclose(fileID);
end
