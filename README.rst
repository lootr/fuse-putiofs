fuse-putiofs
============

fuse-python is a fuse filesystem utilizing the put.io API.
This is a *very early implementation*.

Dependencies
------------
fuse-python requires the following packages:

- python:2
- fuse
- fuse-python

Usage
-----
--version           show program's version number and exit
-h, --help          show this help message and exit
-o <opt[,opt...]>   mount options
-o <key=KEY>        put.io API key
-o <secret=SECRET>  put.io API secret

``./putiofs.py MOUNTPOINT -okey=KEY,secret=SECRET``
