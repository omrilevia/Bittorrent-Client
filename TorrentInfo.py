from bcoding import bdecode, bencode
import math
import time
import os
import hashlib
import PieceTracker


class MetaInfo:
    def __init__(self, pathToTorrent):
        self.torrentdict = {}
        self.path = pathToTorrent
        self.announce = ''
        self.announceList = []
        self.pieceSize = 0
        self.numPieces = 0
        self.piecesHashList = ''
        self.info_hash = ''
        self.totalLength = 0
        self.files = {}
        self.peer_id = ''
        self.all_pieces = b''

    def storeMetaData(self):
        with open(self.path, 'rb') as f:
            self.torrentdict = bdecode(f)
            if 'announce-list' in self.torrentdict:
                for a in self.torrentdict['announce-list']:
                    self.announceList.append(a[0])
                self.announce = self.announceList[0]

            else:
                self.announce = self.torrentdict['announce']

        self.pieceSize = self.torrentdict['info']['piece length']
        self.piecesHashList = self.torrentdict['info']['pieces']
        self.fileOperations()
        self.numPieces = math.ceil(self.totalLength / self.pieceSize)
        self.generateInfoHash()
        self.makePeerID()

    def fileOperations(self):
        home = self.torrentdict['info']['name']
        if 'files' in self.torrentdict['info']:
            self.files = self.torrentdict['info']['files']
            for f in self.files:
                path = f['path']
                self.totalLength += f['length']

        else:
            self.files['name'] = home
            self.files['length'] = self.torrentdict['info']['length']
            self.totalLength = self.files['length']

    def generateInfoHash(self):
        info = self.torrentdict['info']
        bencodeInfo = bencode(info)
        self.info_hash = hashlib.sha1(bencodeInfo).digest()

    def makePeerID(self):
        ts = str(time.time())
        pid = str(os.getpid())
        toHash = ts + pid
        self.peer_id = hashlib.sha1(toHash.encode('utf-8')).digest()

    def writeFiles(self, path, pieceTracker: PieceTracker):
        piece_data = [pc.piece_data for pc in pieceTracker.pieces]
        self.all_pieces = b''.join(piece_data)
        bytes_written = 0
        if 'files' in self.torrentdict['info']:
            path += '/' + self.torrentdict['info']['name'] + '/'
            for file in self.files:
                fpath = path + '/'.join(file['path'])
                if not os.path.exists(os.path.dirname(fpath)):
                    os.makedirs(os.path.dirname(fpath))
                with open(fpath, 'wb') as outfile:
                    length = file['length']
                    outfile.write(self.all_pieces[bytes_written:length+bytes_written])
                    bytes_written += length
                    outfile.close()



