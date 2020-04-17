import math
import Messages
import hashlib

"""
    The piece tracker contains information about all pieces.
"""


class PieceTracker:
    def __init__(self, piecesHashList, num_pieces, piece_size):
        self.pieces_hash = piecesHashList
        self.pieces = []
        self.num_pieces = num_pieces
        self.piece_size = piece_size
        self.block_size = 2 ** 14
        self.num_blocks = math.ceil(float(self.piece_size) / self.block_size)
        self.current_piece = {"index": 0, "offset": 0}
        self.block_requested = [[False for x in range(self.num_blocks)] for y in range(self.num_pieces)]

    def haveAllPieces(self):
        if len(self.pieces) == self.num_pieces:
            if len([pc for pc in self.pieces if pc.complete is True]) == len(self.num_pieces):
                return True
        else:
            return False

    def handlePiece(self, piece: Messages.Piece):
        # check if new piece or existing piece
        index = piece.index
        begin = piece.begin
        block = piece.block
        #self.current_piece["index"] += 1
        self.current_piece["offset"] += self.block_size
        if self.current_piece["offset"] == self.piece_size:
            self.current_piece["index"] += 1
            self.current_piece["offset"] = 0
        if not [pc for pc in self.pieces if pc.idx == index]:
            if index == self.num_pieces - 1:
                # handle last piece
                pass
            else:
                hash_offset = 20 * index
                piece_hash = self.pieces_hash[hash_offset: 20 + hash_offset]
                new_piece = Piece(index, piece_hash, self.piece_size, self.num_pieces)
                block_index = int(begin / self.block_size)
                new_piece.blocks[block_index] = block
                new_piece.block_bool[block_index] = True
                new_piece.blocks_added += 1
                self.pieces.append(new_piece)
        else:
            pc = [pc for pc in self.pieces if pc.idx == index]
            pc = pc[0]
            block_index = int(begin / pc.block_size)
            pc.blocks[block_index] = block
            pc.block_bool[block_index] = True
            pc.blocks_added += 1
            if pc.blocks_added == pc.num_blocks:
                pc.complete = True
                # verify piece with piece_hash
                # if not match reset


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
        self.block_bool = [False] * self.num_blocks
        self.blocks_added = 0
        self.complete = False

        # To do add piece verification
