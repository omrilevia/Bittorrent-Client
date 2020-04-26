from TorrentInfo import MetaInfo
from TrackerRequest import TrackerConnector
import Messages
from p2p import PeerConnector
from p2p import MultiProcessor
import socket
import time
import PieceTracker


def main():
    time1 = time.time()
    torr = MetaInfo('torrents/vince2005-01-15.flac16.torrent')
    torr.storeMetaData()

    tracker = TrackerConnector(torr)
    pieceTracker = PieceTracker.PieceTracker(torr.piecesHashList, torr.numPieces, torr.pieceSize, torr.totalLength)
    peerConnect = PeerConnector(tracker, torr, pieceTracker)

    mp = MultiProcessor(1, peerConnect, pieceTracker)
    mp.run()
    torr.writeFiles('C:', pieceTracker)
    time2 = time.time() - time1
    print("Total time: ", time2)
    print("Download speed: ", torr.totalLength / time2)


if __name__ == '__main__':
    main()
