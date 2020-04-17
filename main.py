from TorrentInfo import MetaInfo
from TrackerRequest import TrackerConnector
import Messages
from p2p import PeerConnector
from p2p import MultiProcessor
import socket
import PieceTracker


def main():
    torr = MetaInfo('charlie_chaplin_film_fest_archive.torrent')
    torr.storeMetaData()
    tracker = TrackerConnector(torr)
    pieceTracker = PieceTracker.PieceTracker(torr.piecesHashList, torr.numPieces, torr.pieceSize)
    peerConnect = PeerConnector(tracker, torr, pieceTracker)
    hs = Messages.HandShake(torr.info_hash, torr.peer_id).serialize()
    #print(hs)
    peers = peerConnect.peers
    peer = peerConnect.peers[0]
    #print(peer.write_data)
    # try:
    #     peer.socket.send(hs)
    #     data = peer.socket.recv(1028)
    #     print(data)
    # except socket.error as e:
    #     print(e)
    # peers = peerConnect.peers
    #
    mp = MultiProcessor(1, peerConnect, pieceTracker)
    mp.run()


if __name__ == '__main__':
    main()
