% This file was created on: 
% Thu Oct 26 11:03:14 CEST 2017
%
% Last edited on: 
% Fri May 11 13:45:10 CEST 2018
%
% Usage: perform_training(zombieFile,graphData,muGrid,trials)
% Function that performs a cross-validation type of training of the classifier to 
% find the best $mu$ value to tune it
%
% INPUT: zombieFile: path to the zombie file
%	 graphData: graph structure 
%	 muGrid: grid of values of mu to try
%	 trials: number of realizations to perform average results
%
%
% OUTPUT: result is stored in a text file in result folder 
%	  called parameter_tuning and also printed in a figure
%
% AUTHORS: Paulo Goncalves, Patrice Abry, Esteban Bautista.
% Information: estbautista@ieee.org

function perform_training(zombieFile,graphData,muGrid,trials)
	AvgMCC = zeros(length(muGrid),1);
	for m = 1 : length(muGrid)
		MCC = zeros(trials,1);
 		for j = 1 : trials
 			labels = zombies_to_labels(zombieFile,graphData,'OneTrainingSample');
			if ischar(labels); return; end;
			[~,~,classification] = standard_SSL_PR(graphData.A,muGrid(m),labels.train); 
			[TP,TN,FP,FN] = accuracy(classification,labels.test,'Type','CrossValidation'); 
			MCC(j) = Matthews_correlation_coefficient(TP,TN,FP,FN);
 		end
		AvgMCC(m) = mean(MCC);
	end

	% save to a file
	fileID = fopen('result/parameter_tuning.txt','w+');
	fprintf(fileID,'%s\t%s\n','mu','MCC');
	fprintf(fileID,'%f\t%f\n',[muGrid;AvgMCC']);
	fclose(fileID);

	% print image
	%print_figure('result/parameter_tuning.txt','result/parameter_tuning','PlotType','XY','mu','MCC','xlabel','\mu','ylabel','MCC','ylim','-1,1');
end
