#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import errno
import fuse
import os
import putioapi
from cachefs import CacheFS
from node import Dir
fuse.fuse_python_api = (0, 2)

class PutIOFS(fuse.Fuse):
    def __init__(self, *args, **kwargs):
        super(PutIOFS, self).__init__(*args, **kwargs)
        self.api = None
        self.key = None
        self.secret = None
        self.root_fs = None

    def updateAPI(self):
        self.api = putioapi.Api(self.key, self.secret)
        item = putioapi.Item(self.api, {'type': 'folder', 'name': '.',
                                        'id': 0, 'parent_id': 0})
        self.root_fs = CacheFS(item.id, Dir(item.name).stat, item)

    def get_inode(self, path, item):
        try:
            return self.find_inode(path)
        except KeyError:
            return self.register_inode(path, item)

    def find_inode(self, path):
        dir_node = self.root_fs
        for name in path.split(os.sep):
            if name:
                dir_node = dir_node.find_inode(name)
        return dir_node

    def register_inode(self, path, item):
        dirname = os.path.dirname(path)
        return self.find_inode(dirname).register_inode(item)

    def getattr(self, path):
        """
        Given a path string, returns the Dir or File object corresponding to
        the path, or None.
        """
        print "getattr(%r)" % path
        if not path.startswith(os.sep):
            return None
        while True:
            try:
                return self.find_inode(path).stat
            except KeyError:
                list(self.readdir(os.path.dirname(path)))

    def readdir(self, path, offset=0, dh=None):
        """
        Generator function. Produces a directory listing.
        Yields individual fuse.Direntry objects, one per file in the
        directory. Should always yield at least "." and "..".
        Should yield nothing if the file is not a directory or does not exist.
        (Does not need to raise an error).

        offset: I don't know what this does, but I think it allows the OS to
        request starting the listing partway through (which I clearly don't
        yet support). Seems to always be 0 anyway.
        """
        print "readdir(%r, %r, %r)" % (path, offset, dh)
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')
        inode = self.find_inode(path)
        items = [_.item for _ in inode.get_entries()]
        if not items:
            try:
                items = self.api.get_items(parent_id=inode.id)
            except putioapi.PutioError:
                pass
        for it in items:
            name = it.name.encode('utf-8')
            it_path = os.sep.join([path, name])
            inode = self.get_inode(it_path, it)
            yield fuse.Direntry(name)

    def read(self, path, size, offset):
        return -errno.ENOSYS

    def write(self, path, buf, offset):
        return -errno.ENOSYS

    def release(self, path, flags):
        return -errno.ENOSYS

    def open(self, path, flags):
        return -errno.ENOSYS

    def truncate(self, path, size):
        return -errno.ENOSYS

    def utime(self, path, times):
        return -errno.ENOSYS

    def mkdir(self, path, mode):
        return -errno.ENOSYS

    def rmdir(self, path):
        return -errno.ENOSYS

    def rename(self, pathfrom, pathto):
        return -errno.ENOSYS

    def fsync(self, path, isfsyncfile):
        return -errno.ENOSYS


def main():
    server = PutIOFS(
        version="%prog " + fuse.__version__,
        dash_s_do='setsingle')
    server.parser.add_option(mountopt="key", metavar="KEY",
                             help="put.io API key")
    server.parser.add_option(mountopt="secret", metavar="SECRET",
                             help="put.io API secret")
    server.parse(values=server, errex=1)
    server.updateAPI()
    server.main()

if __name__ == '__main__':
    main()