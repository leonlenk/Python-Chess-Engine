"""
Stores board state and determines valid moves and keeps game history
"""
import torch

# initial board set up from whites veiw
STARTINGFEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

LASTWHITEPIECE = 6
LASTBLACKPIECE = 12
BOARD_DIM = 8

# creates dictionary of distances from edge
distanceToEdge = {}
for row in range(BOARD_DIM):
    for col in range(BOARD_DIM):
        code = row*10 + col
        northDis = row + 1
        westDis = col + 1
        southDis = BOARD_DIM - row
        eastDis = BOARD_DIM - col
        maxDisToEdge = max((northDis,westDis,southDis,eastDis))
        distanceToEdge[code] = maxDisToEdge

# algebraic notation dictionary
ALGNDIC = {
    0 : 'a',
    1 : 'b',
    2 : 'c',
    3 : 'd',
    4 : 'e',
    5 : 'f',
    6 : 'g',
    7 : 'h'
}

# piece chars to internal ints code
decoder  = {
    ### FEN TO INTERNAL CODE ###
    # empty space
    '*' : 0,
    # white pieces
    'K' : 1,
    'Q' : 2,
    'R' : 3,
    'B' : 4,
    'N' : 5,
    'P' : 6,
    # black pieces
    'k' : 7,
    'q' : 8,
    'r' : 9,
    'b' : 10,
    'n' : 11,
    'p' : 12,
}

inverseDecoder = {v: k for k, v in decoder.items()}
inverseALGNDIC = {v: k for k, v in ALGNDIC.items()}

"""
Create move object from algebraic notation
Only creates real moves by taking from possible moves list
"""
def AlgToMove (AlgN, gameState):
    startCol = inverseALGNDIC[AlgN[0]]
    startRow = 8 - int(AlgN[1])
    endCol = inverseALGNDIC[AlgN[2]]
    endRow = 8 - int(AlgN[3])
    promotionPiece = 'q'
    if len(AlgN) > 4:
        promotionPiece = AlgN[4]
    AlgMove = Move((startRow,startCol), (endRow, endCol), gameState.board, promotionChoice = promotionPiece)
    moves = gameState.getValidMoves()
    for move in moves:
        if AlgMove == move: # get move from possible moves to account for en 
            return move
    return "invalid move"

# sets board according to the Forsyth?Edwards Notation (FEN) string passed in
def set_board (FEN = STARTINGFEN):
    board = torch.zeros(8,8)
    row = 0
    col = 0
    whiteKingLoc = ()
    blackKingLoc = ()
    # sets board
    splitFen = FEN.split()
    for letter in splitFen[0]:
        if letter == ' ':
            break
        
        # new row
        if (col > 8 or letter == '/'):
            row += 1
            col = 0

        # skips x number of coloumns 
        if letter.isnumeric():
            col += int(letter)

        # adds piece
        if letter.isalpha():
            board[row][col] = decoder[letter]
            if letter == 'K':
                whiteKingLoc = (row, col)
            elif letter == 'k':
                blackKingLoc = (row, col)
            col += 1

    # initilizes the game
    gameState = GameState(board)
    gameState.whiteKingLoc = whiteKingLoc
    gameState.blackKingLoc = blackKingLoc
    if splitFen[1] == 'b': # determines turn
        gameState.whitesMove = False

    # set castling rights
    gameState.noWKRMove = 'K' in splitFen[2] # white king side castle
    gameState.noWQRMove = 'Q' in splitFen[2] # white queen side castle
    gameState.noBKRMove = 'k' in splitFen[2] # black king side castle
    gameState.noBQRMove = 'q' in splitFen[2] # black queen side castle
    # here we ignore en passant and half move counter
    # set full move counter
    gameState.turn = int(splitFen[5])

    return gameState


class GameState():
    def __init__(self, board):
        # board is 8 x 8 array with ints represeting pieces according to decoder above
        # 0 represents no piece
        self.board = board
        self.whitesMove = True
        # holds objects from class Move
        self.moveLog = [] 
        self.turn = 1
        self.whiteKingLoc = (7,4)
        self.blackKingLoc = (0,4)
        self.inCheck = False
        self.enPassant = () # holds which square en passant is possible on
        self.pins = []
        self.checks = []
        # castling rights
        self.noWKRMove = True
        self.noWQRMove = True
        self.noBKRMove = True
        self.noBQRMove = True
        self.castleLog = []
        # end game conditions
        self.WhiteInCheckMate = False
        self.BlackInCheckMate = False
        self.isStaleMate = False
        self.repition = 0
        self.movesSinceCapture = 0

    # updates board when move is made
    def makeMove(self, thisMove):
        thisMove.executeMove(self.board)
        # losing castling rights
        self.castleLog.append((self.noWQRMove, self.noWKRMove, self.noBQRMove,  self.noBKRMove))
        # toggles castling right off forever if king or rook is moved
        self.noWQRMove = self.noWQRMove and ((not (thisMove.movingPiece == 1 or (thisMove.movingPiece == 3 and thisMove.startRow == 7 and thisMove.startCol == 0))) and (not (thisMove.endRow == 7 and thisMove.endCol == 0)))
        self.noWKRMove = self.noWKRMove and ((not (thisMove.movingPiece == 1 or (thisMove.movingPiece == 3 and thisMove.startRow == 7 and thisMove.startCol == 7))) and (not (thisMove.endRow == 7 and thisMove.endCol == 7)))
        self.noBQRMove = self.noBQRMove and ((not (thisMove.movingPiece == 7 or (thisMove.movingPiece == 9 and thisMove.startRow == 0 and thisMove.startCol == 0))) and (not (thisMove.endRow == 0 and thisMove.endCol == 0)))
        self.noBKRMove = self.noBKRMove and ((not (thisMove.movingPiece == 7 or (thisMove.movingPiece == 9 and thisMove.startRow == 0 and thisMove.startCol == 7))) and (not (thisMove.endRow == 0 and thisMove.endCol == 7)))
        # castling move
        if thisMove.isCastling:
            if self.whitesMove: # white castle
                if thisMove.endCol == 2: # white queen side castle
                    self.board[7][0] = 0 # remove white queen side rook
                    self.board[7][3] = 3 # sets new position to white rook
                else: # king side castle
                    self.board[7][7] = 0 # remove white king side rook
                    self.board[7][5] = 3 # sets new position to white rook
            else: # black castle
                if thisMove.endCol == 2: # black queen side castle
                    self.board[0][0] = 0 # remove black queen side rook
                    self.board[0][3] = 9 # sets new position to black rook
                else: # king side castle
                    self.board[0][7] = 0 # remove black king side rook
                    self.board[0][5] = 9 # sets new position to black rook
        # pawn promotion
        if thisMove.isPawnPromotion:
            piece = thisMove.promotionChoice
            if self.whitesMove:
                piece = piece.upper()
            else:
                piece = piece.lower()
            self.board[thisMove.endRow][thisMove.endCol] = decoder[piece] # changes piece to chosen piece

        # enpassant
        if thisMove.isEnPassant:
            self.board[thisMove.startRow][thisMove.endCol] = 0 # captures pawn

        # update if enpassant is possible
        if (thisMove.movingPiece == 6 or thisMove.movingPiece == 12) and abs(thisMove.startRow - thisMove.endRow) == 2: # checks that pawn advanced two sqaures
            self.enPassant = ((thisMove.startRow + thisMove.endRow)//2, thisMove.endCol)
        else:
            self.enPassant = ()
        
        # keeps track of moves since pawn move or piece capture for 50 move rule
        if not (thisMove.movingPiece == 6 or thisMove.movingPiece == 12) and thisMove.capturedPiece == 0:
            self.movesSinceCapture += 1
        else:
            self.movesSinceCapture = 0

        # 50 move rule
        if self.movesSinceCapture >= 50:
            self.isStaleMate = True

        # checks that move is the same as two half moves ago
        # three fold repition stalemate checker
        if len(self.moveLog) > 4:
            if thisMove == self.moveLog[-4]: # this is 4 half moves, or two whole moves in the past
                self.repition += 1
            else:
                self.repition = 0

        if self.repition == 6: # six half moves, ie 3 move repitions
            self.isStaleMate = True

        if not self.whitesMove:
            self.turn += 1
        self.moveLog.append(thisMove)
        self.whitesMove = not self.whitesMove # swap players
        if thisMove.movingPiece == 1:
            self.whiteKingLoc = (thisMove.endRow, thisMove.endCol)
        elif thisMove.movingPiece == 7:
            self.blackKingLoc = (thisMove.endRow, thisMove.endCol)

    # undoes the previous move
    def undoMove(self):
        if len(self.moveLog) != 0: # make sure there is a move to undo
            previousMove = self.moveLog.pop() # removes last index in list and returns its value
            # resets piece moved
            self.board[previousMove.startRow][previousMove.startCol] = previousMove.movingPiece
            # resets piece taken
            self.board[previousMove.endRow][previousMove.endCol] = previousMove.capturedPiece
            self.whitesMove = not self.whitesMove # switch turns back
            if previousMove.movingPiece == 1:
                self.whiteKingLoc = (previousMove.startRow, previousMove.startCol)
            elif previousMove.movingPiece == 7:
                self.blackKingLoc = (previousMove.startRow, previousMove.startCol)
            # undo enpassant
            if previousMove.isEnPassant:
                self.board[previousMove.endRow][previousMove.endCol] = 0 # make square pawn ends up on blank
                self.board[previousMove.startRow][previousMove.endCol] = previousMove.capturedPiece
                self.enPassant = (previousMove.endRow, previousMove.endCol)
            # undo 2 square pawn move
            if (previousMove.movingPiece == 6 or previousMove.movingPiece == 12) and abs(previousMove.startRow - previousMove.endRow) == 2:
                if len(self.moveLog) != 0:
                    moveBefore = self.moveLog[-1]
                    # in case two double pawn moves were made in sequence
                    if (moveBefore.movingPiece == 6 or moveBefore.movingPiece == 12) and abs(moveBefore.startRow - moveBefore.endRow) == 2:
                        self.enPassant = ((moveBefore.startRow + moveBefore.endRow)//2, moveBefore.endCol)
                    else:
                        self.enPassant = ()
                else:
                    self.enPassant = ()

            # undo castling
            if previousMove.isCastling:
                if self.whitesMove: # white castle
                    if previousMove.endCol == 2: # white queen side castle
                        self.board[7][0] = 3 # undoes rook move
                        self.board[7][3] = 0
                    else: # king side castle
                        self.board[7][7] = 3 
                        self.board[7][5] = 0 
                else: # black castle
                    if previousMove.endCol == 2: # black queen side castle
                        self.board[0][0] = 9 # undoes rook move
                        self.board[0][3] = 0 
                    else: # king side castle
                        self.board[0][7] = 9 
                        self.board[0][5] = 0 
            
            # reset stalemate conditions
            if self.repition > 0:
                self.repition -= 1
            if self.movesSinceCapture > 0:
                self.movesSinceCapture -= 1
            if self.isStaleMate:
                self.isStaleMate = False
            if self.BlackInCheckMate:
                self.BlackInCheckMate = False
            if self.WhiteInCheckMate:
                self.WhiteInCheckMate = False

            # reset castling rights forfeiture  
            castlingFlags = self.castleLog.pop()
            self.noWQRMove = castlingFlags[0]
            self.noWKRMove = castlingFlags[1]
            self.noBQRMove = castlingFlags[2]
            self.noBKRMove = castlingFlags[3]

            self.turn -= 1

    # checks for valid moves considering checks
    def getValidMoves(self):
        moves = []
        self.inCheck, self.pins, self.checks = self.getPinsChecks()
        if self.whitesMove:
            kingRow = self.whiteKingLoc[0]
            kingCol = self.whiteKingLoc[1]
        else:
            kingRow = self.blackKingLoc[0]
            kingCol = self.blackKingLoc[1]

        if self.inCheck:
            if len(self.checks) == 1: # only one check so can block check
                moves = self.getAllPossibleMoves()
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = int(self.board[checkRow][checkCol].item())
                validSquares = [] # squares that king can move to
                if pieceChecking == 5 or pieceChecking == 11: # knights
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1,BOARD_DIM):
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i) # Check 2 and 3 are the directions the attack is coming from
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol: # once iterable gets to tile with piece doing the checking
                            break
                # get rid of moves that dont block check or move the king
                for j in range(len(moves) - 1, -1, -1): # removing items from list so decrementing through moves
                    if moves[j].movingPiece != 1 and moves[j].movingPiece != 7: # if move doesn't move king
                        if not (moves[j].endRow, moves[j].endCol) in validSquares: # move doesnt block check
                            moves.remove(moves[j])
            else: # double king check, king has to move
                self.getKingMoves(kingRow, kingCol, moves)
        else: # not in check so all moves are fine
            moves = self.getAllPossibleMoves()
            self.getCanCastle(self.board,moves)

        # if no moves are left determine type of game end
        if moves == []:
            if self.inCheck:
                if self.whitesMove:
                    self.WhiteInCheckMate = True
                else:
                    self.BlackInCheckMate = True
            else:
                self.isStaleMate = True
        return moves

    def getPinsChecks(self):
        pins = []
        checks = []
        inCheck = False
        if self.whitesMove:
            startRow = self.whiteKingLoc[0]
            startCol = self.whiteKingLoc[1]
        else:
            startRow = self.blackKingLoc[0]
            startCol = self.blackKingLoc[1]
        # checks outward in each direction
        directions = ((-1,0), (0,-1), (1,0), (0,1), (-1,-1), (-1,1), (1,-1), (1,1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = () # temp potential pin counter
            # i is distance to attacker
            for i in range(1, BOARD_DIM):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow < BOARD_DIM and 0 <= endCol < BOARD_DIM:
                    endPiece = int(self.board[endRow][endCol].item())
                    # checks for pins 
                    if (0 < endPiece <= LASTWHITEPIECE and self.whitesMove) or (LASTWHITEPIECE < endPiece and (not self.whitesMove)):
                        # excluding same color kings because we call this function with a new king position without removing the old one
                        if (self.whitesMove and endPiece != 1) or (not self.whitesMove and endPiece != 7):
                            if possiblePin == (): # no other piece is in the way yet
                                possiblePin = (endRow, endCol, d[0], d[1]) 
                            else: # second allied piece
                                break
                    
                    # checks type of pin
                    elif endPiece != 0:
                        # checks if its a rook and moves in the first 4 directions
                        # checks if its a bishop and moves in last four directions
                        # checks if its a pawn and which directions it can attack
                        # checks if its a queen or a king
                        if (0 <= j <= 3 and (endPiece == 9 or endPiece == 3)) or \
                                (4 <= j <= 7 and (endPiece == 10 or endPiece == 4)) or \
                                (i == 1 and (endPiece == 6 or endPiece == 12) and ((not self.whitesMove and 6 <= j <= 7) or (self.whitesMove and 4 <= j <= 5))) or \
                                (endPiece == 2 or endPiece == 8) or (i == 1 and (endPiece == 1 or endPiece == 7)):
                            if possiblePin == (): # no piece blocking
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else: #piece is blocking so pin
                                pins.append(possiblePin)
                                break
                        else: # piece is not checking
                            break
                else:
                    break # off board
        
        # check in knight directions
        knightDirs = ((2,1), (1,2), (-2,1), (-1,2), (2,-1), (1,-2), (-2,-1), (-1,-2))
        for k in knightDirs:
            endRow = startRow + k[0]
            endCol = startCol + k[1]
            if 0 <= endRow < BOARD_DIM and 0 <= endCol < BOARD_DIM:
                endPiece = int(self.board[endRow][endCol].item())
                if ((endPiece == 5 and not self.whitesMove) or (endPiece == 11 and self.whitesMove)): # enemy knight attacking
                    inCheck = True
                    checks.append((endRow, endCol, k[0], k[1]))
        return inCheck, pins, checks

    # all moves without considering checks
    def getAllPossibleMoves(self):
        moves = []  
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col].item()
                if (piece != 0 and ((piece <= LASTWHITEPIECE and self.whitesMove) or (piece > LASTWHITEPIECE and (not self.whitesMove)))):
                    if piece == 1 or piece == 7:
                        self.getKingMoves(row, col, moves)
                    elif piece == 2 or piece == 8:
                        self.getQueenMoves(row, col, moves)
                    elif piece == 3 or piece == 9:
                        self.getRookMoves(row, col, moves)
                    elif piece == 4 or piece == 10:
                        self.getBishopMoves(row, col, moves)
                    elif piece == 5 or piece == 11:
                        self.getKnightMoves(row, col, moves)
                    elif piece == 6 or piece == 12:
                        self.getPawnMoves(row, col, moves)
        return moves

    # finds if king can castle
    def getCanCastle (self, board, moves):
        # handle white queen side castling
        if self.noWQRMove and self.whitesMove: # rook and king haven't moved
            if board[7][1] == 0 and board[7][2] == 0 and board[7][3] == 0:
                for i in (2,3):
                    self.whiteKingLoc = (7,i)
                    inCheck, pins, checks = self.getPinsChecks()
                    if inCheck:
                        break
                self.whiteKingLoc = (7,4)
                if not inCheck:
                    moves.append(Move((7,4), (7,2), self.board, isCastling = True))

        # white king side
        if self.noWKRMove and self.whitesMove:
            if board[7][5] == 0 and board[7][6] == 0:
                for i in (5,6):
                    self.whiteKingLoc = (7,i)
                    inCheck, pins, checks = self.getPinsChecks()
                    if inCheck:
                        break
                self.whiteKingLoc = (7,4)
                if not inCheck:
                    moves.append(Move((7,4), (7,6), self.board, isCastling = True))

        # handle black queen side castling
        if self.noBQRMove  and not self.whitesMove:
            if board[0][1] == 0 and board[0][2] == 0 and board[0][3] == 0:
                for i in (2,3):
                    self.blackKingLoc = (0,i)
                    inCheck, pins, checks = self.getPinsChecks()
                    if inCheck:
                        break
                self.blackKingLoc = (0,4)
                if not inCheck:
                    moves.append(Move((0,4), (0,2), self.board, isCastling = True))

        # black king side
        if self.noBKRMove and not self.whitesMove:
            if board[0][5] == 0 and board[0][6] == 0:
                for i in (5,6):
                    self.blackKingLoc = (0,i)
                    inCheck, pins, checks = self.getPinsChecks()
                    if inCheck:
                        break
                self.blackKingLoc = (0,4)
                if not inCheck:
                    moves.append(Move((0,4), (0,6), self.board, isCastling = True))

    # get all king  moves and adds the moves to the list
    def getKingMoves(self, r, c, moves):
        directions = ((r-1,c), (r,c+1), (r+1,c), (r,c-1), (r+1,c+1), (r-1,c+1), (r+1,c-1), (r-1,c-1))
        for d in directions:
            # checks that new direction is in bounds
            if d[0] >= 0 and d[0] < BOARD_DIM and d[1] >= 0 and d[1] < BOARD_DIM:
                piece = self.board[d[0]][d[1]]
                # checks that piece is capturable
                if piece == 0 or (piece <= LASTWHITEPIECE and (not self.whitesMove)) or (piece > LASTWHITEPIECE and self.whitesMove):
                    # temporarily set kings location to potential move location
                    if self.whitesMove:
                        self.whiteKingLoc = (d[0], d[1])
                    else:
                        self.blackKingLoc = (d[0], d[1])
                    inCheck, pins, checks = self.getPinsChecks()
                    if not inCheck:
                        moves.append(Move((r,c), d, self.board)) # if not in check it is a valid move
                    # set kings back to origianal location
                    if self.whitesMove:
                        self.whiteKingLoc = (r, c)
                    else:
                        self.blackKingLoc = (r, c)

    # get all queen moves and adds the moves to the list
    def getQueenMoves(self, r, c, moves):
        # a queen is just a bishop and rook
        self.getRookMoves(r, c, moves) # rook has to go first based on how pins are handled
        self.getBishopMoves(r, c, moves)

    # get all rook moves and adds the moves to the list
    def getRookMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1): # decrement through pin list
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c] != 2 and self.board[r][c] != 8: # this does not remove the queen pin, that is done in the bishop moves
                    self.pins.remove(self.pins[i])
                break
        code = r*10 + c
        maxDisToEdge = distanceToEdge[code]
        directions = ((1,0), (-1,0), (0,1), (0,-1))
        for d in directions:
            for tile in range(1, maxDisToEdge):
                endRow = r + d[0] * tile
                endCol = c + d[1] * tile
                if 0 <= endRow < BOARD_DIM and 0 <= endCol < BOARD_DIM:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = int(self.board[endRow][endCol].item())
                        if endPiece == 0: # empty space
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif (endPiece <= LASTWHITEPIECE and (not self.whitesMove)) or (endPiece > LASTWHITEPIECE and self.whitesMove): # capturable piece
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else: # friendly piece
                            break
                else: # off board
                    break

    # get all bishop moves and adds the moves to the list
    def getBishopMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1): # decrement through pin list
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        code = r*10 + c
        maxDisToEdge = distanceToEdge[code]
        directions = ((1,1), (-1,1), (1,-1), (-1,-1))
        for d in directions:
            for tile in range(1, maxDisToEdge):
                endRow = r + d[0] * tile
                endCol = c + d[1] * tile
                if 0 <= endRow < BOARD_DIM and 0 <= endCol < BOARD_DIM:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = int(self.board[endRow][endCol].item())
                        if endPiece == 0: # empty space
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif (endPiece <= LASTWHITEPIECE and (not self.whitesMove)) or (endPiece > LASTWHITEPIECE and self.whitesMove): # capturable piece
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else: # friendly piece
                            break
                else: # off board
                    break

    # get all knight moves and adds the moves to the list
    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        for i in range(len(self.pins) - 1, -1, -1): # decrement through pin list
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break
               
        directions = ((r+2,c+1), (r+1,c+2), (r-2,c+1), (r-1,c+2), (r+2,c-1), (r+1,c-2), (r-2,c-1), (r-1,c-2))
        for d in directions:
            # checks that new direction is in bounds
            if d[0] >= 0 and d[0] < BOARD_DIM and d[1] >= 0 and d[1] < BOARD_DIM:
                if not piecePinned:
                    piece = self.board[d[0]][d[1]]
                    # checks that piece is capturable
                    if piece == 0 or (piece <= LASTWHITEPIECE and (not self.whitesMove)) or (piece > LASTWHITEPIECE and self.whitesMove):
                        moves.append(Move((r,c), d, self.board))

    # get all pawn moves and adds the moves to the list
    def getPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1): # decrement through pin list
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        # moves for white pawn
        if self.whitesMove and r - 1 >= 0:
            # move forward
            if self.board[r-1][c] == 0: # square in front of pawn is empty
                if not piecePinned or pinDirection == (-1,0): # check if pawn is pinned
                    moves.append(Move((r,c), (r-1,c), self.board))
                    if r == 6 and self.board[r-2][c] == 0: # two square pawn advance
                        moves.append(Move((r,c), (r-2,c), self.board))

            # capture to the left
            if c - 1 >= 0 and r - 1 >= 0:
                if not piecePinned or pinDirection == (-1, -1): # check if pawn is pinned
                    if self.board[r-1][c-1] > LASTWHITEPIECE:          
                        moves.append(Move((r,c), (r-1,c-1), self.board))    
                    elif (r-1,c-1) == self.enPassant:
                        moves.append(Move((r,c), (r-1,c-1), self.board, isEnPassant = True)) 

            # capture to the right
            if c + 1 < BOARD_DIM and r - 1 >= 0:
                if not piecePinned or pinDirection == (-1,1): # check if pawn is pinned
                    if self.board[r-1][c+1] > LASTWHITEPIECE:
                            moves.append(Move((r,c), (r-1,c+1), self.board))
                    elif (r-1,c+1) == self.enPassant:
                        moves.append(Move((r,c), (r-1,c+1), self.board, isEnPassant = True)) 

        # moves for black pawn
        elif r+1 < BOARD_DIM and not self.whitesMove:
            # move forward
            if self.board[r+1][c] == 0: # square in front of pawn is empty
                if not piecePinned or pinDirection == (1,0): # check if pawn is pinned
                    moves.append(Move((r,c), (r+1,c), self.board))
                    if r == 1 and self.board[r+2][c] == 0: # two square pawn advance
                        moves.append(Move((r,c), (r+2,c), self.board))

            # capture to the left
            if c - 1 >= 0 and r + 1 < BOARD_DIM:
                if not piecePinned or pinDirection == (1,-1): # check if pawn is pinned
                    if self.board[r+1][c-1] != 0 and self.board[r+1][c-1] <= LASTWHITEPIECE:
                        moves.append(Move((r,c), (r+1,c-1), self.board))
                    elif (r+1,c-1) == self.enPassant:
                        moves.append(Move((r,c), (r+1,c-1), self.board, isEnPassant = True)) 

            # capture to the right
            if c + 1 < BOARD_DIM and r + 1 < BOARD_DIM:
                if not piecePinned or pinDirection == (1,1): # check if pawn is pinned
                    if self.board[r+1][c+1] != 0 and self.board[r+1][c+1] <= LASTWHITEPIECE:
                        moves.append(Move((r,c), (r+1,c+1), self.board))
                    elif (r+1,c+1) == self.enPassant:
                        moves.append(Move((r,c), (r+1,c+1), self.board, isEnPassant = True)) 


class Move():
    def __init__(self, startPos, endPos, board, promotionChoice = 'Q', isEnPassant = False, isCastling = False):
        self.startRow = startPos[0]
        self.startCol = startPos[1]
        self.endRow = endPos[0]
        self.endCol = endPos[1]
        self.movingPiece = int(board[self.startRow][self.startCol].item())
        self.capturedPiece = int(board[self.endRow][self.endCol].item())
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol
        self.promotionChoice = promotionChoice # defaults pawn promotion to queen
        self.isEnPassant = isEnPassant
        if isEnPassant: # note that enpassant moves capture pawns
            if self.movingPiece == 6:
                self.capturedPiece = 12
            else:
                self.capturedPiece = 6
        self.isPawnPromotion = ((self.movingPiece == 6 or self.movingPiece == 12) and (self.endRow == 0 or self.endRow == 7)) # a pawn reaches the back row
        self.isCastling = isCastling

    """
    overriding == method
    """
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def executeMove(self, board):
        board[self.endRow][self.endCol] = self.movingPiece # moves piece to new pos
        board[self.startRow][self.startCol] = 0 # sets old position to 0

    def getAlgebraicNotation (self):
        return (ALGNDIC[self.startCol] + str(8 - self.startRow) + ALGNDIC[self.endCol] + str(8 - self.endRow))
            