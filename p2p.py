import socket


class PeerConnector:
    def __init__(self, trackerconnector, messages, peerIndex):
        self.peerList = trackerconnector.peers


class Peer:
    def __init__(self, ip, port, peer_id, sock, info_hash):
        self.ip = ip
        self.port = port
        self.peer_id = peer_id
        self.info_hash = info_hash
        self.socket = sock
        self.made_handshake = False
        self.peer_state = {"am_choking": 1,
                           "am_interested": 0,
                           "peer_choking": 1,
                           "peer_interested": 0
                           }


