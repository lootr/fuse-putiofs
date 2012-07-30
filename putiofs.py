#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import errno
import fuse
import os
import stat
import pdb
import putioapi
from node import Dir, File
fuse.fuse_python_api = (0, 2)

class CacheFS(object):
    def __init__(self):
        super(CacheFS, self).__init__()
        self.inode_index = {}
        self.path_index = {}
        item = putioapi.Item(None, {'name': u'/', 'type': 'folder',
                                    'id': 0, 'parent_id': 0})
        self.root = self.register_inode(item.name, item)

    def find_inode(self, path):
        try:
            return self.inode_index[self.path_index[path]]
        except:
#            pdb.set_trace()
            raise

    def register_inode(self, path, item):
        if item.type == "folder":
            st = Dir(item.name.encode('utf-8'), stat.S_IFDIR | 0755,
                     os.getuid(), os.getgid())
        else:
            st = File(item.name.encode('utf-8'), stat.S_IFREG | 0644,
                      os.getuid(), os.getgid(), int(item.size))
        inode = CacheFSInode(item.id, item.parent_id, st, vars(item))
        self.inode_index[inode.id] = inode
        self.path_index[path] = inode.id
        return inode

class CacheFSInode(object):
    def __init__(self, id, parent_id, stat, item):
        super(CacheFSInode, self).__init__()
        self.id = int(id)
        self.parent_id = int(parent_id)
        self.stat = stat
        self.item = item

class PutIOFS(fuse.Fuse):
    def __init__(self, *args, **kwargs):
        super(PutIOFS, self).__init__(*args, **kwargs)
        self.api = None
        self.root_dir = None
        self.key = None
        self.secret = None
        self.__fs_cache = CacheFS()

    def updateAPI(self):
        self.api = putioapi.Api(self.key, self.secret)

    def fsinit(self):
        """
        Will be called when the file system has finished mounting, and is
        ready to be used.
        It doesn't have to exist, or do anything.
        """
        self.root_dir = self.__fs_cache.root.stat

    def getattr(self, path):
        """
        Given a path string, returns the Dir or File object corresponding to
        the path, or None.
        """
        print "getattr(%r)" % path
        if not path.startswith(os.sep):
            return None
        path = path.split(os.sep)[1:]
        print path
        # Walk the directory hierarchy
        return self.root_dir.stat

    def readdir(self, path, offset, dh=None):
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
        inode = self.__fs_cache.find_inode(path)
        for it in self.api.get_items(parent_id=inode.id):
            name = it.name.encode('utf-8')
            it_path = path + name
            try:
                inode = self.__fs_cache.find_inode(it_path)
            except KeyError:
                inode = self.__fs_cache.register_inode(it_path, it)
            yield fuse.Direntry(name)

#    def opendir(self, path):
#        """
#        Checks permissions for listing a directory.
#        This should check the 'r' (read) permission on the directory.
#
#        On success, *may* return an arbitrary Python object, which will be
#        used as the "fh" argument to all the directory operation methods on
#        the directory. Or, may just return None on success.
#        On failure, should return a negative errno code.
#        Should return -errno.EACCES if disallowed.
#        """
#        if path == self.root_dir.name:
#            return self.root_dir
#        return Dir(path, stat.S_IFDIR | 0755, os.getuid(), os.getgid())

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
