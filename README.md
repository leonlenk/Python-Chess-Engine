# Python-Chess-Engine

### Graphics

The engine utilizes pygame to have a drag and drop GUI with possible moves, previous moves, and captures highlighted. 

### Engine

The chess engine calculates all legal moves and won't allow a move to be made if it is not legal. The engine matches already known PERFTs from the chess programming wikipedia up to a ply of 4. The board is internally represented as a pytorch tensor for ease of doing machine learning.

### Speed

Right now the engine is really slow, taking several seconds to get up to a PERFT ply of 4 from the starting position. I am currently working on a much faster implimentation.

### Bots

The only bot currently avalible is one that moves pieces at random.
