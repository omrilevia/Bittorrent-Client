"""
This file contains classes and operations focused on the peer wire protocol.
Multiprocessor:
    Contains a loop which proceeds until all pieces for the torrent are received.
    Using a select statement, messages are sent to peers using the peer field peer.write_data.
    Data is read from peers using socket.recv(). The message received is then passed to a handler
    that determines the message type and decides the appropriate response.
"""
import socket
import Messages
import math
from TorrentInfo import MetaInfo
import select
import multiprocessing
import struct
import bitstring
import PieceTracker
import logging
import time
from threading import Thread

logging = logging.getLogger('mp')


class MultiProcessor(multiprocessing.Process):
    def __init__(self, tId, peerConnect, pieceTracker):
        multiprocessing.Process.__init__(self)
        self.tId = tId
        self.peerConnector = peerConnect
        self.pieceTracker = pieceTracker

    def run(self):
        # for peer in self.peerConnector.peers:
        #     print('here')
        #     try:
        #         peer.socket.connect((peer.ip, peer.port))
        #         print('connection made')
        #     except Exception as e:
        #         print("something's wrong with %s:%d. Exception is %s" % (peer.ip, peer.port, e))
        while not self.pieceTracker.haveAllPieces():
            # print('entering while loop')
            write = [peer for peer in self.peerConnector.peers if peer.write_data != '']
            read = self.peerConnector.peers[:]
            rx_list, tx_list, x_list = select.select(read, write, [])

            for peer in tx_list:
                write_message = peer.write_data
                try:
                    if peer.healthy_connection:
                        # print('writing to peers')
                        peer.socket.send(write_message)
                except socket.error as e:
                    peer.healthy_connection = False
                    # print("something's wrong with %s:%d. Exception is %s" % (peer.ip, peer.port, e))
                    continue
                peer.write_data = ''

            for peer in rx_list:
                try:
                    if peer.healthy_connection:
                        peer.read_data += peer.socket.recv(1024)
                        self.peerConnector.handleMessage(peer)
                except socket.error as e:
                    # peer.healthy_connection = False
                    # print("something's wrong with %s:%d. Exception is %s" % (peer.ip, peer.port, e))
                    continue
                # print(peer.ip)
                # time.sleep(.2)
                # if peer.made_handshake and peer.peer_state["peer_choking"] == 0:
                #     peer.timer = time.time()
                #     #print(peer.ip, "entering request")
                #     self.peerConnector.makePieceRequest(peer)
        print("have all pieces")


class PeerConnector:
    def __init__(self, trackerconnector, metainfo, pieceTracker: PieceTracker):
        self.peerList = trackerconnector.peers
        self.info_hash = metainfo.info_hash
        self.my_peer_id = metainfo.peer_id
        self.piece_tracker = pieceTracker
        self.num_pieces = metainfo.numPieces
        self.peers = self.makePeers()
        self.endgame = False
        self.piece_order = []

    def makePeers(self):
        peers = []
        for peer in self.peerList:
            try:
                sock = socket.create_connection((peer['IP'], peer['port']), timeout=2)
                sock.setblocking(False)
                peers.append(Peer(self.num_pieces, peer['IP'], peer['port'], self.info_hash, self.my_peer_id, sock))
            except socket.error:
                pass
        return peers

    def handleMessage(self, peer):
        # total_length = len(message)
        while len(peer.read_data) > 4:
            if not peer.made_handshake:
                rx = peer.read_data[:68]
                rx_handshake = Messages.HandShake.deserialize(rx)
                if rx_handshake.info_hash != peer.info_hash:
                    self.peers.remove(peer)
                peer.peer_id = rx_handshake.peer_id
                peer.made_handshake = True
                interested = Messages.Interested().serialize()
                peer.write_data = interested
                peer.peer_state["am_interested"] = 1
                peer.read_data = peer.read_data[68:]
            else:
                # print(len(peer.read_data))
                m_len, m_id = struct.unpack(">IB", peer.read_data[:5])
                # print(m_len, m_id, peer.ip)
                content = peer.read_data[5:4 + m_len]
                # print(m_len, m_id, len(peer.read_data), peer.ip)
                full_message = peer.read_data[:4 + m_len]
                if len(content) < m_len - 1:
                    return
                peer.read_data = peer.read_data[4 + m_len:]
                if m_id == 0:
                    peer.peer_state["peer_choking"] = 1
                    continue
                elif m_id == 1:
                    peer.peer_state["peer_choking"] = 0
                    peer.can_send = True
                    self.makePieceRequest()
                    # peer.timer = time.time()
                elif m_id == 2:
                    peer.peer_state["peer_interested"] = 1
                elif m_id == 3 and m_len == 1:
                    peer.peer_state["peer_interested"] = 0
                elif m_id == 4:
                    have = Messages.Have.deserialize(full_message)
                    peer.bitfield[have.piece_index] = True
                    self.rarestFirstPieces()
                elif m_id == 5:
                    print("received bitfield from ", peer.ip, "with length ", len(full_message))

                    bf = Messages.Bitfield.deserialize(full_message)
                    peer.bitfield = bf.bitfield
                    self.rarestFirstPieces()
                # print("Bitfield bytes length:", len(peer.bitfield))
                # print("Binary length:", len(peer.bitfield.bin))
                elif m_id == 6:
                    # peer requests piece
                    pass
                elif m_id == 7:
                    piece = Messages.Piece.deserialize(full_message)
                    # print("Received piece with index: ", piece.index)
                    peer.num_requests -= 1
                    # peer.write_data = ''

                    self.piece_tracker.handlePiece(piece)
                    if self.piece_tracker.completedPieces() / self.num_pieces < .99:
                        self.makePieceRequest()
                    elif self.endgame is False:
                        self.endGame()
                        self.endgame = True
                    elif self.endgame is True:
                        index = piece.index
                        offset = piece.begin
                        length = piece.block_length
                        cancel = Messages.Cancel(index, offset, length).serialize()
                        for pr in self.peers:
                            if peer != pr:
                                pr.write_data = cancel
                        # self.endGame()

        return

    def rarestFirstPieces(self):
        rarest_first = [{"index": x, "count": 0} for x in range(self.num_pieces)]
        for peer in self.peers:
            for pc in range(self.num_pieces):
                if peer.has_piece(pc):
                    rarest_first[pc]["count"] += 1
        self.piece_order = sorted(rarest_first, key=lambda i: i['count'])

    def makePieceRequest(self):
        for peer in self.peers:
            # time.sleep(.125)
            idx = self.piece_order[0]["index"]
            # print(peer.ip, idx)
            block_length = 2 ** 14
            offset = 0
            block_idx = math.floor(offset / block_length)
            # print(peer.peer_state['peer_choking'], peer.ip)
            if peer.bitfield and peer.peer_state['peer_choking'] == 0 and idx < self.num_pieces \
                    and peer.num_requests < 5:
                while not peer.has_piece(idx) or self.piece_tracker.block_requested[idx][block_idx]:
                    offset += block_length
                    # print(offset)
                    block_idx = int(offset / block_length)
                    if offset == self.piece_tracker.piece_size:
                        idx += 1
                        offset = 0
                        block_idx = 0
                # print(idx)
                if idx == self.num_pieces - 1:
                    request = Messages.Request(idx, offset, self.piece_tracker.last_block_size).serialize()
                else:
                    request = Messages.Request(idx, offset, block_length).serialize()
                peer.write_data = request
                peer.num_requests += 1
                self.piece_tracker.block_requested[idx][block_idx] = True
                # self.requests_outstanding += 1
                peer.can_send = False
                offset += block_length
                if offset == self.piece_tracker.piece_size:
                    idx += 1
                    offset = 0
                    block_idx = 0
                    # self.piece_tracker.current_piece = {"index": idx, "offset": offset}

    def endGame(self):
        pieces_remaining = [pc for pc in self.piece_tracker.pieces if pc.complete is False]
        pieces_not_requested = []
        for i in range(self.num_pieces):
            if i not in [pc.idx for pc in self.piece_tracker.pieces]:
                pieces_not_requested.append(i)

        request = b''
        for peer in self.peers:
            if peer.peer_state["peer_choking"] == 0:
                for pc in pieces_remaining:
                    index = pc.idx
                    # print(pc.idx)
                    for block in range(len(pc.blocks)):
                        offset = block * pc.block_size
                        if pc.block_bool[block] is False and peer.has_piece(index):
                            if index == self.num_pieces - 1 and block == pc.num_blocks - 1:
                                request += Messages.Request(index, offset, pc.last_block_size).serialize()
                            else:
                                request += Messages.Request(index, offset, pc.block_size).serialize()

                for index in pieces_not_requested:
                    # print(index)
                    if index == self.num_pieces - 1:
                        for block in range(self.piece_tracker.num_blocks_in_last_piece):
                            offset = block * self.piece_tracker.block_size
                            if block == self.piece_tracker.num_blocks_in_last_piece - 1:
                                request += Messages.Request(index, offset,
                                                            self.piece_tracker.last_block_size).serialize()
                            else:
                                request += Messages.Request(index, offset, self.piece_tracker.block_size).serialize()
                    else:
                        for block in range(self.piece_tracker.num_blocks):
                            offset = block * self.piece_tracker.block_size
                            request += Messages.Request(index, offset, self.piece_tracker.block_size).serialize()

                peer.write_data = request


class Peer:
    def __init__(self, num_pieces, ip, port, info_hash, my_peer_id, sock):
        self.ip = ip
        self.port = port
        self.socket = sock
        self.read_data = b''
        self.can_send = False
        self.my_peer_id = my_peer_id
        self.peer_id = b''
        self.info_hash = info_hash
        self.bitfield = bitstring.BitArray(num_pieces)
        self.made_handshake = False
        self.healthy_connection = True
        self.num_requests = 0
        self.current_piece = {"index": 0, "offset": 0}
        self.peer_state = {"am_choking": 1,
                           "am_interested": 0,
                           "peer_choking": 1,
                           "peer_interested": 0
                           }
        self.write_data = Messages.HandShake(self.info_hash, self.peer_id).serialize()

    def fileno(self):
        return self.socket.fileno()

    def has_piece(self, index):
        # print(index, self.bitfield, self.ip)
        if 0 <= index < len(self.bitfield):
            return self.bitfield[index]
        else:
            return False
