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
    #print(torr.numPieces)
    tracker = TrackerConnector(torr)
    pieceTracker = PieceTracker.PieceTracker(torr.piecesHashList, torr.numPieces, torr.pieceSize)
    peerConnect = PeerConnector(tracker, torr, pieceTracker)
    hs = Messages.HandShake(torr.info_hash, torr.peer_id).serialize()
    peers = peerConnect.peers
    peer = peerConnect.peers[0]

    mp = MultiProcessor(1, peerConnect, pieceTracker)
    mp.run()


if __name__ == '__main__':
    main()
