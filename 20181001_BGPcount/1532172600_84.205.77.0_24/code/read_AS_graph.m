% This file was created on: 
% Thu Oct 26 11:03:14 CEST 2017
%
% Last edited on: 
% Fri May 11 13:45:10 CEST 2018
%
% Usage: graph = read_AS_graph(fileName)
% Function that extracts the adjacency matrix of the modified AS graph text file
%
% INPUT: fileName: path towards the AS graph text file
%
% OUTPUT: graph: structure with two atributes
% graph.A: NxN sparse matrix representing the adjacency matrix of the graph
% graph.nodesNames: Name Tag for the 'i-th' row (node) of the adjacency matrix
%
% AUTHORS: Paulo Goncalves, Patrice Abry, Esteban Bautista.
% Information: estbautista@ieee.org

function graph = read_AS_graph(fileName)

% Matrix to store the sparse graph
A = sparse(1,1,0,56000,56000);

% Var to store the node name of the i-th row of A
NodesNames = cell(1);

% open the file to be read
fid = fopen(fileName);

% get the first line and run while until I finish to read the file
tline = fgets(fid);
while ischar(tline)   

	% If the line I am reading is a char skip it otherwise enter if
   	if tline(1) ~= '#'

		% Nodes involved in the i-th line of the graph file. 
		% The first one refers to a node and the rest are the nodes connected to it
       		Nodes = textscan(tline,'%s');
      		
	        % First element in the list is the first node
		if isempty(NodesNames{1})
			NodesNames(1) = Nodes{1}(1);
		end

	        % I need to store the index (row line) of nodes that already are were processed 	
		idx = zeros(length(Nodes{1}),1);

		% for all the nodes involved in the i-th line of the file find which ones were already
		% processed and add the pertinent links to the ones it already has 
		for i = 1 : length(Nodes{1})
			srch = strcmp(NodesNames,Nodes{1}(i));

			% if node was not previously processed add it to the list and in a row of A
			if sum(srch) == 0
				idx(i) = length(NodesNames)+1;
				NodesNames(idx(i),1) = Nodes{1}(i);
			% if it was already processeced find in which row of A it was already included
			else
				idx(i) = find(srch == 1);
			end      
		end
       
		% Link the node to the others	
		if length(idx) ~= 1
			for j = 2 : length(idx)
				A = A + sparse([idx(1) idx(j)],[idx(j) idx(1)],[1,1],56000,56000);
			end
		end
       
		clear idx;
	else
end
    tline = fgets(fid);
end
fclose(fid);

% normalize weights to be one and delete extra entries of A
A(A >= 1) = 1;
A = A - diag(diag(A));
A = A(1:length(NodesNames),1:length(NodesNames));

graph.A = A;
graph.nodesNames = NodesNames;
