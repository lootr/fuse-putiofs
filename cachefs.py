# -*- encoding: utf-8 -*-
from node import Dir, File

class Inode(object):
    def __init__(self, id_, stat_, item):
        super(Inode, self).__init__()
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
