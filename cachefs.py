# -*- encoding: utf-8 -*-
import httplib
import threading
import urlparse

from node import Dir, File

class CacheManager(object):
    def __init__(self, creds):
        self.creds = creds
        self.map = {}

    def append(self, url):
        p = urlparse.urlparse(url)
        self.map[url] = CachedFile(p.netloc, p.path, self.creds)
        return len(self.map) + 2

    def remove(self, url):
        del self.map[url]
        return len(self.map) + 2

    def read(self, url, size, offset):
        return self.map[url].read(size, offset)

class CachedFile(object):
    def __init__(self, netloc, http_path, http_creds=()):
        self.main_c = httplib.HTTPSConnection(netloc)
        self.secn_c = httplib.HTTPSConnection(netloc)
        # self.secn_c.set_debuglevel(1)
        self.path = http_path
        self.enc_creds = ':'.join(http_creds).encode('base64').rstrip()
        self.r = None
        self.buffer = CachedFileBuffer()
        self.read_size = 0L
        # self.session_cookie = None
        self.EOF = False
        self.flock = threading.Lock()

    def get_response(self, conn, **extra_hdrs):
        hdrs = extra_hdrs
        if self.enc_creds:
            hdrs['Authorization'] = "Basic " + self.enc_creds
        conn.request("GET", self.path, None, hdrs)
        return conn.getresponse()

    @staticmethod
    def sock_read(req, amt=None):
        # print 'RECV(%#x)' % (amt or 0)
        return req.read(amt)

    def _recv(self, offset, size):
        # Check if a response is yet running
        if self.r is None:
            self.r = self.get_response(self.main_c)
        amt = offset - self.read_size + size
        # Read directly from response
        ret = self.sock_read(self.r, amt)
        n_ret = len(ret)
        # Mark EOF
        if amt > n_ret:
            self.EOF = True
        # Feed CachedFileBuffer with result
        self.buffer.feed(ret, offset)
        self.read_size += n_ret
        print 'READ(%#x) = %#x' % (amt, n_ret)
        return ret

    def _longrecv(self, offset, size):
        r = self.get_response(self.secn_c, Range='bytes=%d-%d' % (offset, offset+size-1))
        ret = self.sock_read(r)
        # Feed CachedFileBuffer with result
        self.buffer.feed(ret, offset)
        print 'LONGREAD(%#x+%#x) = %#x' % (offset, size, len(ret))
        return ret

    def read(self, size, offset):
        with self.flock:
            if self.EOF or self.read_size >= size + offset:
                return self.buffer[offset:size+offset]
            n_recv = offset - self.read_size + size
            if n_recv < 0x100000:
                return self._recv(offset, size)
            else:
                return self._longrecv(offset, size)

class CachedFileBuffer(object):
    def __init__(self):
        self.index_tab = {}

    def __getitem__(self, key):
        for idx in reversed(self.index_tab.keys()):
            if isinstance(key, slice):
                if idx <= key.start:
                    newkey = slice(key.start - idx, key.stop - idx)
                    ret = self.index_tab[idx][newkey]
                    if key.stop - key.start != len(ret):
                        self.defragment()
                    return ret
            elif idx <= key:
                return self.index_tab[idx][key - idx]
        print "Key %r not found !" % key

    def feed(self, data, offset):
        self.index_tab[offset] = data

    def get_size(self):
        raise NotImplementedError

    def defragment(self):
        klast = None
        keys = sorted(self.index_tab.keys())
        for k0, k1 in zip(keys, keys[1:]):
            try:
                v0 = self.index_tab[k0]
            except KeyError:
                k0 = klast
                v0 = self.index_tab[k0]
            if k0 + len(v0) >= k1:
                v1 = self.index_tab.pop(k1)
                # TODO: Check that overlapping data are equal
                self.index_tab[k0] += v1[k0+len(v0)-k1:]
            klast = k0

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
