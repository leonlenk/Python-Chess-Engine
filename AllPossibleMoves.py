"""
Checks the chess engine with test cases to see all possible moves 
"""

import torch
import ChessEngine
import time
from ChessEngine import Move, AlgToMove

# https://www.chessprogramming.org/Perft_Results
POS5FEN = "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8  "
PROMOTIONS = ('q', 'n', 'r', 'b')
"""
A recursive function that finds all possible moves x turns into the future
"""
def NoPrintSearch (depth, gameState):
    if depth == 0:
        return 1
    positions = 0
    validMoves = gameState.getValidMoves()
    # recursivly calls itself
    for move in validMoves:
        if move.isPawnPromotion:
            for i in PROMOTIONS:
                move.promotionChoice = i
                gameState.makeMove(move)
                positions += NoPrintSearch(depth - 1, gameState)
                gameState.undoMove()
        else:
            gameState.makeMove(move)
            positions += NoPrintSearch (depth - 1, gameState)
            gameState.undoMove()

    return positions

def PrintSearchTree ():
    gameState = ChessEngine.set_board(FEN = POS5FEN) # initilizes board
    #newMove = AlgToMove('e2f4', gameState)
    #gameState.makeMove(newMove)
    #print(newMove.getAlgebraicNotation())
    #newMove2 = AlgToMove('e7b4', gameState)
    #gameState.makeMove(newMove2)
    #print(newMove2.getAlgebraicNotation())
    validMoves = gameState.getValidMoves()
    total = 0
    depth = 4
    for move in validMoves:
        if move.isPawnPromotion:
            for i in PROMOTIONS:
                move.promotionChoice = i
                gameState.makeMove(move)
                counter = NoPrintSearch(depth - 1, gameState)
                gameState.undoMove()
                print(str(move.getAlgebraicNotation()) + str(i) + ": " + str(counter))
                total += counter
        else:
            gameState.makeMove(move)
            counter = NoPrintSearch(depth - 1, gameState)
            gameState.undoMove()
            print(str(move.getAlgebraicNotation()) + ": " + str(counter))
            total += counter
    print("total number of positions: " + str(total))


def BasicSearch ():
     for depth in range(1,6): # number of half turns in the future
        start = time.time()
        gameState = ChessEngine.set_board(FEN = POS5FEN) # initilizes board
        positions = NoPrintSearch(depth, gameState) 
        end = time.time()
        print("depth: " + str(depth) + " ply " + "number of positions: " + str(positions) + " time taken: " + str(round((end-start)*1000)) + " milliseconds")

     return positions


if __name__ == "__main__":
    BasicSearch()