from TorrentInfo import MetaInfo
from TrackerRequest import TrackerConnector


def main():
    torr = MetaInfo('charlie_chaplin_film_fest_archive.torrent')
    torr.storeMetaData()

    tracker = TrackerConnector(torr)
    print(tracker.response)
    print(tracker.peers)


if __name__ == '__main__':
    main()
