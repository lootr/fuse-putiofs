# -*- encoding: utf-8 -*-
import httplib
import urlparse

from node import Dir, File

class CacheDescriptor(object):
    def __init__(self, creds):
        self.creds = creds
        self._ = {}

    def append(self, url):
        p = urlparse.urlparse(url)
        c = httplib.HTTPSConnection(p.netloc)
        self._[url] = HTTPContent(c, p.path, self.creds)

    def remove(self, url):
        del self._[url]

    def read(self, url, size, offset):
        return self._[url].read(size, offset)

class HTTPContent(object):
    def __init__(self, http_conn, http_path, http_creds=()):
        self.c = http_conn
        self.path = http_path
        self.b64_creds = ':'.join(http_creds).encode('base64')[:-1]
        self.r = None
        self.buffer = str()
        self.EOF = False

    def _recv(self, amt):
        if self.r is None:
            hdrs = {}
            if self.b64_creds:
                hdrs['Authorization'] = "Basic " + self.b64_creds
            self.c.request("GET", self.path, None, hdrs)
            self.r = self.c.getresponse()
        ret = self.r.read(amt)
        if amt > len(ret):
            self.EOF = True
        self.buffer += ret
        return ret

    def read(self, size, offset):
        bufsize = len(self.buffer)
        if not self.EOF and size + offset > bufsize:
            self._recv(size + offset - bufsize)
        return self.buffer[offset:size+offset]

class Inode(object):
    def __init__(self, id_, stat_, item):
        self.id = int(id_)
        self.stat = stat_
        self.item = item

    def find_inode(self, name):
        raise FSNotAvailable

class CacheFS(Inode):
    def __init__(self, id_, stat_, item):
        super(CacheFS, self).__init__(id_, stat_, item)
        self._inode_index = {}

    def get_entries(self):
        return self._inode_index.values()

    def find_inode(self, name):
        return self._inode_index[name]

    def register_inode(self, item):
        name = item.name
        if isinstance(name, unicode):
            name = name.encode('utf-8')
        if item.type == "folder":
            stat_ = Dir(name).stat
            inode = CacheFS(item.id, stat_, item)
        else:
            stat_ = File(name, size=int(item.size)).stat
            inode = Inode(item.id, stat_, item)
        self._inode_index[name] = inode
        return inode

class FSNotAvailable(Exception):
    def __init__(self):
        msg = "Function not available"
        super(FSNotAvailable, self).__init__(msg)
