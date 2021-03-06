%%%%%%%%%
sorts
%%%%%%%%%
#digit = 1..9.
#location = 1..9.
#block_number = 1..3.
#cell = cell(#location,#location).
#row = row(#location).
#column = column(#location).
#block_row = block_row(#block_number).
#block_column = block_column(#block_number).
#block = block(#block_number,#block_number).

%%%%%%%%%%
predicates
%%%%%%%%%%
in_row(#cell,#row).
in_column(#cell,#column).
in_block(#cell,#block).
value(#cell,#digit).
assignated_value(#cell).
%%%%%%%%%
rules
%%%%%%%%%

in_row(cell(L1,L2),row(L1)).
in_column(cell(L1,L2),column(L2)).
in_block(cell(L1,L2),block(B1,B2)) :- (L1+2)/3 = B1, (L2+2)/3 = B2.
value(C,D) :+ #cell(C), #digit(D).
assignated_value(C) :- value(C,D).
:- not assignated_value(C).
:-value(C1,D), value(C2,D), in_row(C1,R), in_row(C2,R), C1!=C2.
:-value(C1,D), value(C2,D), in_block(C1,B), in_block(C2,B), C1!=C2.
:-value(C1,D), value(C2,D), in_column(C1,C), in_column(C2,C), C1!=C2.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Need to add lines below as shown.

% value(cell(1,6),7).
% value(cell(1,7),8).

% display

% value.
value(cell(1,1),5).
value(cell(1,4),8).
value(cell(1,5),3).
value(cell(1,7),2).
value(cell(2,1),3).
value(cell(2,3),4).
value(cell(2,6),5).
value(cell(3,4),7).
value(cell(3,5),9).
value(cell(3,6),1).
value(cell(3,7),4).
value(cell(4,2),5).
value(cell(4,3),8).
value(cell(4,4),4).
value(cell(4,5),1).
value(cell(4,8),9).
value(cell(4,9),2).
value(cell(5,3),3).
value(cell(5,5),7).
value(cell(5,7),1).
value(cell(5,8),5).
value(cell(5,9),8).
value(cell(6,2),9).
value(cell(6,5),8).
value(cell(6,6),6).
value(cell(7,1),6).
value(cell(7,2),3).
value(cell(7,3),5).
value(cell(7,4),1).
value(cell(8,4),3).
value(cell(8,5),4).
value(cell(8,6),7).
value(cell(9,7),3).
value(cell(9,8),8).
value(cell(9,9),1).
%%%%%%%%%%%%
display
%%%%%%%%%%%%
value.