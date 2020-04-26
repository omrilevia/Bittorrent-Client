import math
import Messages
import hashlib

"""
    The piece tracker contains information about all pieces.
"""


class PieceTracker:
    def __init__(self, piecesHashList, num_pieces, piece_size, total_length):
        self.pieces_hash = piecesHashList
        self.pieces = []
        self.num_pieces = num_pieces
        self.piece_size = piece_size
        self.block_size = 2 ** 14
        self.total_length = total_length
        self.last_piece_size = self.total_length - (self.num_pieces - 1) * piece_size
        self.num_blocks_in_last_piece = int(math.ceil(float(self.last_piece_size) / self.block_size))
        self.last_block_size = self.last_piece_size - (self.num_blocks_in_last_piece - 1) * self.block_size
        self.num_blocks = math.ceil(float(self.piece_size) / self.block_size)
        self.current_piece = {"index": 0, "offset": 0}
        self.block_requested = [[False for x in range(self.num_blocks)] for y in range(self.num_pieces)]

    def haveAllPieces(self):
        if len(self.pieces) == self.num_pieces:
            if len([pc for pc in self.pieces if pc.complete is True]) == self.num_pieces:
                return True
        else:
            return False

    def completedPieces(self):
        return len([pc for pc in self.pieces if pc.complete is True])

    def handlePiece(self, piece: Messages.Piece):
        # check if new piece or existing piece
        index = piece.index
        begin = piece.begin
        block = piece.block
        if not [pc for pc in self.pieces if pc.idx == index]:
            hash_offset = 20 * index
            piece_hash = self.pieces_hash[hash_offset: 20 + hash_offset]

            new_piece = Piece(index, piece_hash, self.piece_size, self.num_pieces, self.last_piece_size,
                              self.num_blocks_in_last_piece)
            # print("new piece added with index: ", new_piece.idx)
            block_index = int(begin / self.block_size)
            new_piece.blocks[block_index] = block
            new_piece.block_bool[block_index] = True
            new_piece.blocks_added += 1
            self.pieces.append(new_piece)
        else:
            pc = [pc for pc in self.pieces if pc.idx == index]
            pc = pc[0]
            # print("Existing piece block added: ", pc.idx)
            block_index = int(begin / pc.block_size)
            if pc.block_bool[block_index] is False:
                pc.blocks[block_index] = block
                pc.block_bool[block_index] = True
                pc.blocks_added += 1
                if pc.blocks_added == pc.num_blocks:
                    # print('Joining piece with index', pc.idx)
                    pc.piece_data = b''.join(pc.blocks)
                    if pc.verify():
                        pc.complete = True
                        print("Piece complete with index: ", pc.idx, "Percentage: ",
                              self.completedPieces() / self.num_pieces)
                    else:
                        pc.reset()
                    # verify piece with piece_hash
                    # if not match reset


class Piece:
    def __init__(self, idx, piece_hash, piece_size, num_pieces, last_piece_size, num_blocks_last_piece):
        self.idx = idx
        self.piece_hash = piece_hash
        self.num_pieces = num_pieces
        self.block_size = 2 ** 14
        self.last_block_size = last_piece_size - (num_blocks_last_piece - 1) * self.block_size
        if self.idx == self.num_pieces - 1:
            self.num_blocks = int(math.ceil(float(last_piece_size) / self.block_size))
            self.piece_size = last_piece_size
        else:
            self.piece_size = piece_size
            self.num_blocks = int(math.ceil(float(self.piece_size) / self.block_size))
        self.piece_data = b''
        self.blocks = [None] * self.num_blocks
        self.block_bool = [False] * self.num_blocks
        self.blocks_added = 0
        self.complete = False

        # To do add piece verification

    def verify(self):
        data_hash = hashlib.sha1(self.piece_data).digest()
        return self.piece_hash == data_hash

    def reset(self):
        self.piece_data = b''
        self.blocks = [None] * self.num_blocks
        self.block_bool = [False] * self.num_blocks
        self.blocks_added = 0
        self.complete = False
