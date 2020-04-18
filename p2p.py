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
                        read_data = peer.socket.recv(1028)
                        if read_data:
                            # print('received from peer')
                            if peer.made_handshake:
                                m_len, m_id = struct.unpack(">IB", read_data[:5])
                                if m_len <= 16393:
                                    self.peerConnector.handleMessage(read_data, peer)
                            else:
                                self.peerConnector.handleMessage(read_data, peer)
                except socket.error as e:
                    # peer.healthy_connection = False
                    # print("something's wrong with %s:%d. Exception is %s" % (peer.ip, peer.port, e))
                    continue
                #print(peer.ip)
                time.sleep(.2)
                if peer.made_handshake and peer.peer_state["peer_choking"] == 0:
                    peer.timer = time.time()
                    #print(peer.ip, "entering request")
                    self.peerConnector.makePieceRequest(peer)


class PeerConnector:
    def __init__(self, trackerconnector, metainfo, pieceTracker: PieceTracker):
        self.peerList = trackerconnector.peers
        self.info_hash = metainfo.info_hash
        self.my_peer_id = metainfo.peer_id
        self.piece_tracker = pieceTracker
        self.num_pieces = metainfo.numPieces
        self.peers = self.makePeers()

    def makePeers(self):
        peers = []
        for peer in self.peerList:
            try:
                sock = socket.create_connection((peer['IP'], peer['port']), timeout=2)
                peers.append(Peer(self.num_pieces, peer['IP'], peer['port'], self.info_hash, self.my_peer_id, sock))
            except socket.error:
                pass
        return peers

    def handleMessage(self, message, peer):
        total_length = len(message)
        remaining = False
        if not peer.made_handshake:
            if total_length > 68:
                rx_handshake = Messages.HandShake.deserialize(message[:68])
                remaining = True
            else:
                rx_handshake = Messages.HandShake.deserialize(message)
            if rx_handshake.info_hash != peer.info_hash:
                self.peers.remove(peer)
            peer.peer_id = rx_handshake.peer_id
            peer.made_handshake = True
            interested = Messages.Interested().serialize()
            peer.write_data = interested
            peer.peer_state["am_interested"] = 1
            if remaining:
                self.handleMultiple(message[68:], peer)
        else:
            m_len, m_id = struct.unpack(">IB", message[:5])
            if m_id == 0:
                peer.peer_state["peer_choking"] = 1
            elif m_id == 1:
                peer.peer_state["peer_choking"] = 0
                peer.can_send = True
                # self.makePieceRequest(peer)
                # peer.timer = time.time()
            elif m_id == 2:
                peer.peer_state["peer_interested"] = 1
            elif m_id == 3:
                peer.peer_state["peer_interested"] = 0
            elif m_id == 4:
                # need to test bitfield logic
                pass
            elif m_id == 5:
                bf = Messages.Bitfield.deserialize(message)
                peer.bitfield = bf.bitfield
            elif m_id == 6:
                # peer requests piece
                pass
            elif m_id == 7 and m_len == 16393:
                piece = Messages.Piece.deserialize(message)
                self.piece_tracker.handlePiece(piece)
                peer.can_send = True

    def handleMultiple(self, message, peer):
        total_length = len(message)
        parsed = 0
        while parsed < total_length:
            m_len, m_id = struct.unpack(">IB", message[parsed:parsed + 5])
            m_total = m_len + 4
            self.handleMessage(message[parsed:m_total + parsed], peer)
            parsed += m_total

    def makePieceRequest(self, peer):
        current_piece = peer.current_piece
        idx = int(current_piece["index"])
        # print(peer.ip, idx)
        block_length = 2 ** 14
        offset = current_piece["offset"]
        block_idx = int(offset / block_length)
        while not peer.has_piece(idx) or self.piece_tracker.block_requested[idx][block_idx]:
            offset += block_length
            # print(offset)
            block_idx = int(offset / block_length)
            if offset == self.piece_tracker.piece_size:
                idx += 1
                offset = 0
                block_idx = 0
        request = Messages.Request(idx, offset, block_length).serialize()
        peer.write_data = request
        self.piece_tracker.block_requested[idx][block_idx] = True
        peer.can_send = False
        offset += block_length
        if offset == self.piece_tracker.piece_size:
            idx += 1
            offset = 0
            block_idx = 0
        peer.current_piece = {"index": idx, "offset": offset}


class Peer:
    def __init__(self, num_pieces, ip, port, info_hash, my_peer_id, sock):
        self.ip = ip
        self.port = port
        self.socket = sock
        self.timer = 0.0
        self.can_send = False
        self.my_peer_id = my_peer_id
        self.peer_id = b''
        self.info_hash = info_hash
        self.bitfield = bitstring.BitArray(num_pieces)
        self.made_handshake = False
        self.healthy_connection = True
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
        return self.bitfield[index]
