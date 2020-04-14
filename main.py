from TorrentInfo import MetaInfo
from TrackerRequest import TrackerConnector
import Messages
from p2p import PeerConnector
import socket


def main():
    torr = MetaInfo('charlie_chaplin_film_fest_archive.torrent')
    torr.storeMetaData()

    tracker = TrackerConnector(torr)
    print(tracker.peers)
    pMessage = Messages.HandShake(torr.info_hash, torr.peer_id).serialize()
    print(pMessage)
    pConnector = PeerConnector(tracker, pMessage, 1)
    pConnector.assignIPandPort()
    sock = socket.create_connection((pConnector.ip, pConnector.port), timeout=2)
    sock.send(pMessage)
    r = sock.recv(4096)
    print(r)


if __name__ == '__main__':
    main()
