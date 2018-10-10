% This file was created on: 
% Fri May 11 15:26:14 CEST 2018
%
% Last edited on: 
% Fri May 11 15:26:22 CEST 2018
%
% Usage: labels = zombies_to_labels(zombieFile,graph,varargin)
% Function that reads the zombies file and returns a vector of labeled points
% that is consistent with the node's name tags given in the graph file
%
% INPUT: zombieFile: path to the zombie file
%	 graph: graph in mat format 
% 	 
% OPTIONAL: 'CrossValidation': draw two label matrices one for testing and 
% 	     			the other for training purposes 
%	    'OneTrainingSample': select only one labeled points per class for training
% 	     ratio: the ratio of nodes advocated to the training matrix
%
% OUTPUT: zombies: Nx2 vector of label points
%	     with matrices of full labeled points or test and training, depending
%	     if the 'Cross-Validation' option was used
%
% AUTHORS: Paulo Goncalves, Patrice Abry, Esteban Bautista.
% Information: estbautista@ieee.org

function zombies = zombies_to_labels(zombieFile,graph,varargin)
testType = 'Normal';
if length(varargin) > 0 
	testType = varargin{1};
	if length(varargin) > 1
		ratio = varargin{2};
	end
end

% nodes number 
nodesNumber = size(graph.A,1);

% store the tag for nodes names 
LabelNodesNames = cell(1);

% variable to store the class
classLabel = cell(1);

% read the zombie file until the end
fid = fopen(zombieFile);
tline = fgets(fid);
while ischar(tline)  

    % skip comments
    if tline(1) ~= '#'

	% read the i-th line of the file
        Nodes = textscan(tline,'%s');
        
	% store the name of the node
        if isempty(LabelNodesNames{1})
           LabelNodesNames(1) = Nodes{1}(1);
        else
           LabelNodesNames(length(LabelNodesNames)+1,:) = Nodes{1}(1);
        end
	
	% store the node's class. 1 is normal 2 is zombie
        classLabel{strcmp(LabelNodesNames,Nodes{1}(1)) == 1} = str2double(Nodes{1}(2)) + 1;
    end
    tline = fgets(fid);
end
fclose(fid);

% create file to report inconsistencies in the zombies file
fileID = fopen('result/error_log.txt','w+');
fclose(fileID);

% Verify how many elements are in each class and stop the code if only one class is present
idxNormal = find(cell2mat(classLabel) == 1);
idxZombie = find(cell2mat(classLabel) == 2);
if isempty(idxNormal) || isempty(idxZombie)
	fileID = fopen('result/error_log.txt','a');
	fprintf(fileID,'%s\n','The labeled data belongs to a single class');
	fclose(fileID);
	zombies = 'error';
	return;
end

% If the OneTrainingSample is set then select at random the two elements for the training set
randomIndexNormal = idxNormal(randi(length(idxNormal),1,1));
randomIndexZombie = idxZombie(randi(length(idxZombie),1,1));

% initialize matrices
switch testType
	case 'Normal'
		zombies.labels = zeros(nodesNumber,2);
	case 'CrossValidation'
		zombies.train = zeros(nodesNumber,2);
		zombies.test = zeros(nodesNumber,2);
	case 'OneTrainingSample'
		zombies.train = zeros(nodesNumber,2);
		zombies.test = zeros(nodesNumber,2);
	otherwise
end


% fill the matrix of labels with the information retrieved from the zombies file
for i = 1 : length(classLabel)
	% find the position of the labeled node in the graph and fill the matrix accordingly
	idx = find(strcmp(LabelNodesNames(i),graph.nodesNames) == 1);
	if any(idx)

		% check if we have normal or Cross-Validation experiment
		switch testType
			case 'Normal'
				zombies.labels(idx,classLabel{i}) = 1;
			case 'CrossValidation'
				% ratio of train samples
				isTrain = ratio - rand(1);
				if isTrain > 0
					zombies.train(idx,classLabel{i}) = 1;
				else
					zombies.test(idx,classLabel{i}) = 1;
				end
			case 'OneTrainingSample'
				if i == randomIndexNormal || i == randomIndexZombie
					zombies.train(idx,classLabel{i}) = 1;
				else
					zombies.test(idx,classLabel{i}) = 1;
				end
			otherwise
		end
	% if the node is not found in the graph report it
	else 
		b = str2double(LabelNodesNames{i});
		fileID = fopen('result/error_log.txt','a');
		fprintf(fileID,'%s\n',['Node number ',num2str(b),' was labeled but not found in graph']);
		fclose(fileID);
	end
end
