import struct
import bitstring

"""
All types of messages may be serialized and deserialized here for ease of sending and receiving.
"""


class HandShake:
    def __init__(self, info_hash, peer_id):
        self.pstr = b"BitTorrent protocol"
        self.pstrlen = len(self.pstr)
        self.reserved = b'\x00' * 8
        self.info_hash = info_hash
        self.peer_id = peer_id

    def serialize(self):
        return struct.pack(">B{}s8s20s20s".format(self.pstrlen),
                           self.pstrlen,
                           self.pstr,
                           self.reserved,
                           self.info_hash,
                           self.peer_id)

    @classmethod
    def deserialize(cls, recvd):
        pstrlen, = struct.unpack(">B", recvd[:1])
        pstr, reserved, info_hash, peer_id = struct.unpack(">{}s8s20s20s".format(pstrlen), recvd[1:len(recvd)])
        # assert (pstr == "BitTorrent protocol")

        return HandShake(info_hash, peer_id)


class KeepAlive:
    def __init__(self):
        self.length_prefix = 0

    def serialize(self):
        return struct.pack(">I", self.length_prefix)

    @classmethod
    def deserialize(cls, recvd):
        length_prefix = struct.unpack(">I", recvd[:len(recvd)])
        assert (length_prefix == 0)
        return KeepAlive()


class Choke:
    def __init__(self):
        self.id = 0
        self.length_prefix = 1
        self.length = 5

    def serialize(self):
        return struct.pack(">IB", self.length_prefix, self.id)

    def deserialize(self, recvd):
        m_length, m_id = struct.unpack(">IB", recvd[:self.length])
        assert (m_length == 1)
        assert (m_id == 0)
        return Choke()


class UnChoke:
    def __init__(self):
        self.id = 1
        self.length_prefix = 1
        self.length = 5

    def serialize(self):
        return struct.pack(">IB", self.length_prefix, self.id)

    def deserialize(self, recvd):
        m_length, m_id = struct.unpack(">IB", recvd[:self.length])
        assert (m_length == 1)
        assert (m_id == 1)
        return UnChoke()


class Interested:
    def __init__(self):
        self.id = 2
        self.length_prefix = 1
        self.length = 5

    def serialize(self):
        return struct.pack(">IB", self.length_prefix, self.id)

    def deserialize(self, recvd):
        m_length, m_id = struct.unpack(">IB", recvd[:self.length])
        assert (m_length == 1)
        assert (m_id == 2)

        return Interested()


class NotInterested:
    def __init__(self):
        self.id = 3
        self.length_prefix = 1
        self.length = 5

    def serialize(self):
        return struct.pack(">IB", self.length_prefix, self.id)

    def deserialize(self, recvd):
        m_length, m_id = struct.unpack(">IB", recvd[:self.length])
        assert (m_length == 1)
        assert (m_id == 3)

        return Interested()


class Have:
    def __init__(self, pieceIdx):
        self.piece_index = pieceIdx
        self.length_prefix = 5
        self.id = 4
        self.length = 9

    def serialize(self):
        return struct.pack(">IBI", self.length_prefix, self.id, self.piece_index)

    @classmethod
    def deserialize(cls, recvd):
        m_length, m_id, pieceIdx = struct.unpack(">IBI", recvd[:9])
        #assert (m_id == 4)
        return Have(pieceIdx)


class Bitfield:
    def __init__(self, bitfield):
        self.bitfield = bitfield
        self.serialBf = self.bitfield.tobytes()
        self.bitfield_length = len(self.serialBf)
        self.id = 5
        self.length_prefix = 1 + self.bitfield_length
        self.length = 4 + self.bitfield_length

    def serialize(self):
        return struct.pack(">IB{}s".format(self.bitfield_length),
                           self.length_prefix,
                           self.id,
                           self.serialBf)

    @classmethod
    def deserialize(cls, recvd):
        m_length, m_id = struct.unpack(">IB", recvd[:5])
        # assert (m_id == self.id)
        bf_length = m_length - 1
        bf_serial, = struct.unpack(">{}s".format(bf_length), recvd[5:5 + bf_length])
        bitfield = bitstring.BitArray(bytes=bytes(bf_serial))
        return Bitfield(bitfield)


class Request:
    def __init__(self, index, begin, block_length):
        self.index = index
        self.begin = begin
        self.block_length = block_length
        self.prefix_length = 13
        self.id = 6
        self.tot_length = 17

    def serialize(self):
        return struct.pack(">IBIII", self.prefix_length, self.id, self.index, self.begin, self.block_length)

    def deserialize(self, recvd):
        m_length, m_id, idx, beg, block_len = struct.unpack(">IBIII", recvd[:self.tot_length])
        assert (m_id == 6)
        return Request(idx, beg, block_len)


class Piece:
    def __init__(self, index, begin, block):
        self.index = index
        self.begin = begin
        self.block = block
        self.block_length = len(self.block)
        self.id = 7
        self.prefix_length = 9 + self.block_length

    def serialize(self):
        return struct.pack(">IBII{}s".format(self.block_length),
                           self.prefix_length,
                           self.id,
                           self.index,
                           self.begin,
                           self.block)

    @classmethod
    def deserialize(cls, recvd):
        block_len = len(recvd) - 13
        m_length, m_id, idx, m_offset, blck = struct.unpack(">IBII{}s".format(block_len),
                                                            recvd[:13 + block_len])
        # assert (m_id == self.id)

        return Piece(idx, m_offset, blck)
