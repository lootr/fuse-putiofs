#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import errno
import fuse
import os
import stat
import putioapi
from node import Stat, Dir
fuse.fuse_python_api = (0, 2)

class PutIOFS(fuse.Fuse):
    def __init__(self, *args, **kwargs):
        super(PutIOFS, self).__init__(*args, **kwargs)
        self.user = None
        self.password = None

    def fsinit(self):
        """
        Will be called when the file system has finished mounting, and is
        ready to be used.
        It doesn't have to exist, or do anything.
        """
        print "Starting API with %s:%s" % (self.user, self.password)
        self.api = putioapi.Api(self.user, self.password)
        self.root_dir = Dir('/', 0, 0, stat.S_IFDIR|0755, os.getuid(), os.getgid())

    def getattr(self, path):
        """
        Given a path string, returns the Dir or File object corresponding to
        the path, or None.
        """
        print "getattr(%s)" % path
        if not path.startswith(os.sep):
            return None
        path = path.split(os.sep)[1:]
        # Walk the directory hierarchy
        self.root_dir.stat

    def readdir(self, path, offset, dh=None):
        print "readdir(%s, %s, %s)" % (path, offset, dh)
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')
        for it in self.api.get_items():
            if it.type == "folder":
                yield fuse.Direntry(it.name)

    def opendir(self, path):
        """
        Checks permissions for listing a directory.
        This should check the 'r' (read) permission on the directory.

        On success, *may* return an arbitrary Python object, which will be
        used as the "fh" argument to all the directory operation methods on
        the directory. Or, may just return None on success.
        On failure, should return a negative errno code.
        Should return -errno.EACCES if disallowed.
        """
        if path == self.root_dir.name:
            parent_id = id_ = u'0'
        else:
            parent_id = id_ = None
        return Dir(path, id_, parent_id, stat.S_IFDIR|0755, os.getuid(), os.getgid())

    def read(self, path, size, offset):
        return 0

    def write(self, path, buf, offset):
        return 0

    def release(self, path, flags):
        return 0

    def open(self, path, flags):
        return 0

    def truncate(self, path, size):
        return 0

    def utime(self, path, times):
        return 0

    def mkdir(self, path, mode):
        return 0

    def rmdir(self, path):
        return 0

    def rename(self, pathfrom, pathto):
        return 0

    def fsync(self, path, isfsyncfile):
        return 0


def main():
    server = PutIOFS(
        version="%prog " + fuse.__version__,
        dash_s_do='setsingle')
    server.parser.add_option(mountopt="user", metavar="USERNAME",
                             help="put.io API username")
    server.parser.add_option(mountopt="password", metavar="PASSWORD",
                             help="put.io API password")
    server.parse(values=server, errex=1)
    server.main()

if __name__ == '__main__':
    main()
