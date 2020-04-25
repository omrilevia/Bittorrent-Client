# Bittorrent-Client
Bittorrent client written in python by Omri Levia


This is a rudimentary Bittorrent Client written following the Bittorrent wiki (https://wiki.theory.org/index.php/BitTorrentSpecification) 
and Kristen Widman's Bittorrent Client tutorials (http://www.kristenwidman.com/blog/33/how-to-write-a-bittorrent-client-part-1/). 

My implementation handles single torrent at a time piece downloading, with a simple rarest piece first strategy. When the torrent is 
nearing completion, the client will request all unobtained pieces to each peer and subsequently send cancels for each new block that is recevied.

This client does not yet support accepting requests from other peers. 

This bittorrent client can:
* Connect to the tracker and receive a list of peers
* Connect and handshake with peers
* Request pieces from peers
* Write torrent to disk in desired output folder

Possible extensions:
* Revision of rarest piece and endgame strategy (needs further optimizations)
* Support uploading to peers (satisfy requests)
* Graphical user interface
* Implement recommended extensions by the Bittorrent Wiki

Some comments on optimization:
As it stands now, the program waits until all pieces are obtained before writing to disk, so for systems with minimal RAM this may be cumbersome.
There are some other optimizations that can be made in piece selection strategy. 

Big thanks to Alexis Gallepe (https://github.com/gallexis) and Lita Cho (https://github.com/lita) whose Bittorrent client implementations 
helped me learn enough to implement my own. 
