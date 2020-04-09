from bcoding import bdecode, bencode
import hashlib


class TorrentInfo:
    def __init__(self, pathToTorrent):
        self.TorrentDict = {}
        self.path = pathToTorrent
        self.announceList = []
        self.pieceLength = 0
        self.numPieces = 0
        self.piecesHashList = ''
        self.totalLength = 0
        self.files = {}

    def decodeTorrent(self):
        with open(self.path, 'rb') as f:
            self.TorrentDict = bdecode(f)
            if 'announce-list' in self.TorrentDict:
                self.announceList = self.TorrentDict['announce-list']
            else:
                self.announceList = [self.TorrentDict['announce']]

        self.pieceLength = self.TorrentDict['info']['piece length']
        self.piecesHashList = self.TorrentDict['info']['pieces']
        




