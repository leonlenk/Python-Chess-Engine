"""
Generates chess moves using a NN (probably gonna be a recurrent nn or an lstm idk)
"""

import torch
import ChessEngine
import random

# https://blogs.cornell.edu/info2040/2022/09/30/game-theory-how-stockfish-mastered-chess/

# random moves
def RandomBot (gameState):
    allMoves = gameState.getValidMoves()
    move = random.randint(0, len(allMoves) - 1)
    return allMoves[move]

