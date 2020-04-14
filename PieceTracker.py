import math


class PieceTracker:
    def __init__(self, piecesHashList, num_pieces):
        self.pieces_hash = piecesHashList
        self.pieces = []
        self.num_pieces = num_pieces

    def haveAllPieces(self):
        if len(self.pieces) == self.num_pieces:
            return True
        else:
            return False


class Piece:
    def __init__(self, idx, piece_hash, piece_size, num_pieces):
        self.idx = idx
        self.piece_hash = piece_hash
        self.num_pieces = num_pieces
        self.piece_size = piece_size
        self.block_size = 2 ** 14
        self.num_blocks = math.ceil(float(self.piece_size) / self.block_size)
        self.piece_data = b''
        self.blocks = [None] * self.num_blocks
        self.complete = False
