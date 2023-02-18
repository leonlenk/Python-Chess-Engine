"""
Handels user input and displays game animation
"""

import pygame as pyg
import torch
import ChessEngine
from ChessEngine import Move, set_board, LASTWHITEPIECE, LASTBLACKPIECE, inverseDecoder, inverseALGNDIC
import ChessBot

pyg.init()

WIDTH = HEIGHT = 512 # for pygame resolution
BOARD_DIM = 8 # board is 8 x 8
SQ_SIZE = WIDTH // BOARD_DIM
MAX_FPS = 60 # animation frame rate
IMAGES = {}
COLORS = [pyg.Color("#eeeed2"), pyg.Color("#769656")] # light color first dark second
HIGHLIGHT = [pyg.Color("#CCCCFF"), pyg.Color("#AA98A9")] # highlights the square the piece came 
ATTACK_HIGHLIGHT = [pyg.Color("#FFBF00"), pyg.Color("#CD7F32")] # highlights squares piece can be moved to
SIDE_LETTERS = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')

"""
loads images into pygame
"""
def load_images():
    # loads in white pieces
    for pieces in range(1,LASTWHITEPIECE+1):
        IMAGES[pieces] = pyg.transform.smoothscale(pyg.image.load("whitePieces/" + inverseDecoder[pieces] + ".png"), (SQ_SIZE, SQ_SIZE))

    # loads in black pieces
    for pieces in range(LASTWHITEPIECE + 1,LASTBLACKPIECE + 1):
        IMAGES[pieces] = pyg.transform.smoothscale(pyg.image.load("blackPieces/" + inverseDecoder[pieces] + ".png"), (SQ_SIZE, SQ_SIZE))

"""
draw the squares on the board
top left squre is white
"""
def drawBoard(screen):
    font = pyg.font.SysFont('arial', 15)
    for row in range(BOARD_DIM):
        for col in range(BOARD_DIM):
            color = COLORS[(row+col) % 2]
            pyg.draw.rect(screen, color, pyg.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))

            # draw side letters and numbers for algebraic notation
            # draw letters
            if row == 7:
                letterColor = COLORS[1-((7+col) % 2)]
                text = font.render(SIDE_LETTERS[col], True, letterColor, None)
                screen.blit(text, pyg.Rect((col + .85) *SQ_SIZE, (row + .7) *SQ_SIZE, SQ_SIZE, SQ_SIZE))
            # draw numbers
            if col == 0:
                numberColor = COLORS[1-((row) % 2)]
                text = font.render(str(8 - row), True, numberColor, None)
                screen.blit(text, pyg.Rect((col + .05) *SQ_SIZE, (row + .1) *SQ_SIZE, SQ_SIZE, SQ_SIZE))

              
"""
draws the pieces on the board based on gameState
"""
def drawPieces(screen, board):
    for row in range(BOARD_DIM):
        for col in range(BOARD_DIM):
            piece = board[row][col].item()
            if piece != 0: # is not empty square
                screen.blit(IMAGES[piece], pyg.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))

"""
draws previous move highlights
"""
def drawPreviousMoveHighlight(screen, gameState, moveUndone):
    # draws previous move highlights
    if (gameState.turn > 0 or (not gameState.whitesMove) or moveUndone) and len(gameState.moveLog) > 0:
        previousMove = gameState.moveLog[-1]
        # highlights square piece moved to
        movedSquareColor = HIGHLIGHT[(previousMove.endCol+previousMove.endRow) % 2]
        pyg.draw.rect(screen, movedSquareColor, pyg.Rect(previousMove.endCol*SQ_SIZE, previousMove.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        # highlights square piece moved from
        movedFromSquareColor = HIGHLIGHT[(previousMove.startCol+previousMove.startRow) % 2]
        pyg.draw.rect(screen, movedFromSquareColor, pyg.Rect(previousMove.startCol*SQ_SIZE, previousMove.startRow*SQ_SIZE, SQ_SIZE, SQ_SIZE))

"""
will handle user input and updating graphics
drag and drop
"""
def main():
    SinglePlayer = False
    PlayerColorWhite = True

    screen = pyg.display.set_mode((WIDTH, HEIGHT))
    clock = pyg.time.Clock()
    screen.fill(pyg.Color("grey"))
    # set the pygame window name
    pyg.display.set_caption('Chess')
    gameState = set_board()
    validMoves = gameState.getValidMoves()
    load_images()
    running = True
    dragging = False
    highlightingPotMoves = False
    moveUndone = False
    validMoveSquaresToHighlight = []
    # initial drawing of game
    drawBoard(screen) # draw squares
    drawPieces(screen, gameState.board) # draw pieces
    pyg.display.flip()

    whitesMove = gameState.whitesMove
    
    if SinglePlayer:
        print("Bot on")
    else:
        print("Bot off")

    while running:

        # play bots move
        if SinglePlayer and not (PlayerColorWhite and whitesMove):
            botMove = ChessBot.RandomBot(gameState)
            gameState.makeMove(botMove)
            print(botMove.getAlgebraicNotation())
            validMoves = gameState.getValidMoves()
            drawBoard(screen) # draw squares
            movedSquareColor = HIGHLIGHT[(botMove.startCol+botMove.startRow) % 2]
            # highlights square piece moved to
            pyg.draw.rect(screen, movedSquareColor, pyg.Rect(botMove.startCol*SQ_SIZE, botMove.startRow*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            # highlights square piece moved from
            movedFromSquareColor = HIGHLIGHT[(botMove.endCol+botMove.endRow) % 2]
            pyg.draw.rect(screen, movedFromSquareColor, pyg.Rect(botMove.endCol*SQ_SIZE, botMove.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            drawPieces(screen, gameState.board) # draw pieces
            pyg.display.flip()
            whitesMove = not whitesMove

        for event in pyg.event.get():
            # closes game window
            if event.type == pyg.QUIT:
                running = False
            ### MOUSE PRESS DRAG AND DROP FUNCTION ###
            # locates which piece player is clicking on
            elif event.type == pyg.MOUSEBUTTONDOWN:
                if event.button == 1:     
                    location = pyg.mouse.get_pos()
                    mouse_down_col = location[0] // SQ_SIZE
                    mouse_down_row = location[1] // SQ_SIZE
                    piece = int(gameState.board[mouse_down_row][mouse_down_col].item())
                    for pieceOfIntrest in validMoves:
                            if piece == pieceOfIntrest.movingPiece and mouse_down_row == pieceOfIntrest.startRow and mouse_down_col == pieceOfIntrest.startCol:
                                validMoveSquaresToHighlight.append(pieceOfIntrest)
                    if gameState.board[mouse_down_row][mouse_down_col] != 0:
                        dragging = True
                        # highlight potential move squares
                        highlightingPotMoves = True
            
            # checks when player drops piece
            elif event.type == pyg.MOUSEBUTTONUP:
                if event.button == 1:
                    if dragging:
                        location = pyg.mouse.get_pos()
                        mouse_up_col = location[0] // SQ_SIZE
                        mouse_up_row = location[1] // SQ_SIZE
                        originalPos = (mouse_down_row, mouse_down_col)
                        newPos = (mouse_up_row, mouse_up_col)
                        proposedMove = Move(originalPos, newPos, gameState.board)

                        # checks if move is a valid move
                        for eachMove in validMoves:
                            if  eachMove == proposedMove:
                                gameState.makeMove(eachMove)
                                print(eachMove.getAlgebraicNotation())
                                validMoves = gameState.getValidMoves()
                                drawBoard(screen) # draw squares
                                movedSquareColor = HIGHLIGHT[(mouse_down_col+mouse_down_row) % 2]
                                # highlights square piece moved to
                                pyg.draw.rect(screen, movedSquareColor, pyg.Rect(mouse_down_col*SQ_SIZE, mouse_down_row*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                                # highlights square piece moved from
                                movedFromSquareColor = HIGHLIGHT[(mouse_up_col+mouse_up_row) % 2]
                                pyg.draw.rect(screen, movedFromSquareColor, pyg.Rect(mouse_up_col*SQ_SIZE, mouse_up_row*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                                drawPieces(screen, gameState.board) # draw pieces
                                pyg.display.flip()
                                whitesMove = not whitesMove
                        else: 
                            drawBoard(screen) # draw squares
                            drawPreviousMoveHighlight(screen, gameState, moveUndone)
                            drawPieces(screen, gameState.board) # draw pieces
                            pyg.display.flip()
                    dragging = False
                    highlightingPotMoves = False
                    validMoveSquaresToHighlight = []
                    

            # checks when player is dragging piece
            if dragging:
                    mouse_x, mouse_y = pyg.mouse.get_pos() # tracks mouse
                    drawBoard(screen) # draw squares
                    # draws previous move highlights
                    drawPreviousMoveHighlight(screen, gameState, moveUndone)

                    # adds dots and circles on tiles piece can be moved to
                    if highlightingPotMoves:
                        for potentialSquares in validMoveSquaresToHighlight:
                            potentialSquareColor = ATTACK_HIGHLIGHT[(potentialSquares.endRow+potentialSquares.endCol) % 2]
                            # circles piece for capture
                            if potentialSquares.capturedPiece > 0:
                                pyg.draw.circle(screen, potentialSquareColor, ((potentialSquares.endCol * SQ_SIZE) + (0.5 * SQ_SIZE), (potentialSquares.endRow * SQ_SIZE) + (0.5 * SQ_SIZE)), SQ_SIZE * .5, int(SQ_SIZE * .1))
                            # draws circle on empty tiles
                            else:
                                pyg.draw.circle(screen, potentialSquareColor, ((potentialSquares.endCol * SQ_SIZE) + (0.5 * SQ_SIZE), (potentialSquares.endRow * SQ_SIZE) + (0.5 * SQ_SIZE)), SQ_SIZE * .2)
                    drawPieces(screen, gameState.board) # draw pieces
                    color = HIGHLIGHT[(mouse_down_row+mouse_down_col) % 2]
                    # highlights square piece is coming from
                    pyg.draw.rect(screen, color, pyg.Rect(mouse_down_col*SQ_SIZE, mouse_down_row*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                    # draws pieces under mouse cursor
                    screen.blit(IMAGES[piece], pyg.Rect(mouse_x - (0.5 * SQ_SIZE), mouse_y - (0.5 * SQ_SIZE), SQ_SIZE, SQ_SIZE))
                    pyg.display.flip()
            
            ### KEY HANDLER ###
            elif event.type == pyg.KEYDOWN:
                # undo when z is pressed
                if event.key == pyg.K_z: 
                    if len(gameState.moveLog) > 0:
                        gameState.undoMove()
                        validMoves = gameState.getValidMoves()
                        drawBoard(screen) # draw squares
                        # draws previous move highlights
                        drawPreviousMoveHighlight(screen, gameState, moveUndone)
                        drawPieces(screen, gameState.board) # draw pieces
                        pyg.display.flip()
                        moveUndone = True
                        whitesMove = not whitesMove

                # reset board when r is pressed
                if event.key == pyg.K_r:
                    gameState = set_board()
                    validMoves = gameState.getValidMoves()
                    dragging = False
                    highlightingPotMoves = False
                    moveUndone = False
                    whitesMove = gameState.whitesMove
                    drawBoard(screen) # draw squares
                    drawPieces(screen, gameState.board) # draw pieces
                    pyg.display.flip()
                    print("Board Reset")

                # toggle the bot on or off
                if event.key == pyg.K_b:
                    PlayerColorWhite = True
                    SinglePlayer = not SinglePlayer
                    if SinglePlayer:
                        print("Bot on")
                    else:
                        print("Bot off")

        clock.tick(MAX_FPS)
        

if __name__ == "__main__":
    main()