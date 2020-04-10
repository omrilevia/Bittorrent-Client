import requests
from bcoding import bdecode
import ipaddress
import struct


class TrackerConnector:
    def __init__(self, metainfo):
        self.metainfo = metainfo
        self.params = self.populateRequest()
        self.response = self.makeRequest()
        self.peers = self.peerByteStringToList()

    def populateRequest(self):
        params = {'info_hash': self.metainfo.info_hash,
                  'peer_id': self.metainfo.peer_id,
                  'port': 6881,
                  'uploaded': 0,
                  'downloaded': 0,
                  'left': self.metainfo.totalLength,
                  'compact': 1,
                  'event': 'started'
                  }
        return params

    def makeRequest(self):
        return bdecode(requests.get(self.metainfo.announce, self.params).content)

    def peerByteStringToList(self):
        peerData = self.response['peers']
        peerInfo = [peerData[i:i + 6] for i in range(0, len(peerData), 6)]
        peerList = []
        for peer in peerInfo:
            peerIP = peer[:4]
            peerPort = peer[4:]
            peerPort = bytes(peerPort)
            portNum = struct.unpack(">H", peerPort)[0]

            peerDict = {
                'IP': peerIP,
                'port': portNum
            }
            peerList.append(peerDict)

        return peerList
