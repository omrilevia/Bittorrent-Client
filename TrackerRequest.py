import requests
from bcoding import bdecode
import ipaddress
import struct
import logging
"""
The tracker connector makes a request to the torrent tracker using
the properly formatted parameters. 
"""

logging = logging.getLogger("TrackerConnector")


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
        logging.info("making request to tracker")
        return bdecode(requests.get(self.metainfo.announce, self.params).content)

    def peerByteStringToList(self):
        peerData = self.response['peers']
        peerInfo = [peerData[i:i + 6] for i in range(0, len(peerData), 6)]
        peerList = []
        if type(peerData) is list:
            for peer in peerData:
                peerDict = {
                    'IP': peer['ip'],
                    'port': peer['port']
                }
                peerList.append(peerDict)
        else:
            for peer in peerInfo:
                peerIP = peer[:4]
                peerPort = peer[4:]
                #print(peerPort)
                peerPort = bytes(peerPort)
                portNum = struct.unpack(">H", peerPort)[0]

                peerDict = {
                    'IP': ipaddress.IPv4Address(peerIP).exploded,
                    'port': portNum
                }
                peerList.append(peerDict)

        return peerList
