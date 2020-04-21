from TorrentInfo import MetaInfo
from TrackerRequest import TrackerConnector
import Messages
from p2p import PeerConnector
from p2p import MultiProcessor
import socket
import PieceTracker


def main():
    torr = MetaInfo('Bromberg2012-07-19.Creekside.MilabVM-44Link.flac16.torrent')
    torr.storeMetaData()
    # print(torr.numPieces)
    tracker = TrackerConnector(torr)
    pieceTracker = PieceTracker.PieceTracker(torr.piecesHashList, torr.numPieces, torr.pieceSize, torr.totalLength)
    peerConnect = PeerConnector(tracker, torr, pieceTracker)
    tot = (pieceTracker.num_pieces - 1) * pieceTracker.piece_size + pieceTracker.last_piece_size
    print(pieceTracker.total_length, tot)
    hs = Messages.HandShake(torr.info_hash, torr.peer_id).serialize()
    peers = peerConnect.peers
    # print(peers)
    # peer = peerConnect.peers[0]

    #mp = MultiProcessor(1, peerConnect, pieceTracker)
    #mp.run()


if __name__ == '__main__':
    main()
