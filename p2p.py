import socket
import Messages
import TorrentInfo
import select
import multiprocessing
import struct


class MultiProcessor(multiprocessing.Process):
    def __init__(self, tId, peerConnect, pieceTracker):
        multiprocessing.Process.__init__(self)
        self.tId = tId
        self.peerConnector = peerConnect
        self.pieceTracker = pieceTracker
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)

    def run(self):
        for peer in self.peerConnector.peers:
            try:
                self.sock.connect((peer.ip, peer.port))
            except socket.error:
                pass

        while not self.pieceTracker.haveAllPieces():
            write = [peer for peer in self.peerConnector.peers if peer.write_data != '']
            read = self.peerConnector.peers[:]
            rx_list, tx_list, x_list = select.select(read, write, [])

        for peer in tx_list:
            write_message = peer.write_data
            try:
                if peer.healthy_connection:
                    self.sock.send(write_message)
            except socket.error:
                peer.healthy_connection = False
                continue
            peer.write_data = ''

        for peer in rx_list:
            try:
                if peer.healthy_connection:
                    read_data = self.sock.recv(4096)
            except socket.error:
                peer.healthy_connection = False
                continue
            self.peerConnector.handleMessage(read_data)


class PeerConnector:
    def __init__(self, trackerconnector, torrentinfo):
        self.peerList = trackerconnector.peers
        self.info_hash = torrentinfo.info_hash
        self.peers = self.makePeers()

    def makePeers(self):
        peers = []
        for peer in self.peerList:
            peers.append(Peer(peer['IP'], peer['port'], self.info_hash))
        return peers

    def handleMessage(self, message):
        length, = struct.unpack(">I", message[:1])
        



class Peer:
    def __init__(self, ip, port, info_hash):
        self.ip = ip
        self.port = port
        self.my_peer_id = TorrentInfo.MetaInfo.makePeerID()
        self.peer_id = b''
        self.info_hash = info_hash
        self.made_handshake = False
        self.healthy_connection = True
        self.peer_state = {"am_choking": 1,
                           "am_interested": 0,
                           "peer_choking": 1,
                           "peer_interested": 0
                           }
        self.write_data = Messages.HandShake(self.my_peer_id, self.info_hash).serialize
