# -*- encoding: utf-8 -*-
import fuse
import os
import stat
import time as _time

class Stat(fuse.Stat):
    """
    A Stat object. Describes the attributes of a file or directory.
    Has all the st_* attributes, as well as dt_atime, dt_mtime and dt_ctime,
    which are datetime.datetime versions of st_*time. The st_*time versions
    are in epoch time.
    """
    DIRSIZE = 4096

    def __init__(self, st_mode, st_size, st_nlink=1, st_uid=None, st_gid=None,
                 dt_atime=None, dt_mtime=None, dt_ctime=None, **kwargs):
        """
        Creates a Stat object.
        st_mode: Required. Should be stat.S_IFREG or stat.S_IFDIR ORed with a
            regular Unix permission value like 0644.
        st_size: Required. Size of file in bytes. For a directory, should be
            Stat.DIRSIZE.
        st_nlink: Number of hard-links to the file. Regular files should
            usually be 1 (default). Directories should usually be 2 + number
            of immediate subdirs (one from the parent, one from self, one from
            each child).
        st_uid, st_gid: uid/gid of file owner. Defaults to the user who
            mounted the file system.
        st_atime, st_mtime, st_ctime: atime/mtime/ctime of file.
            (Access time, modification time, stat change time).
            These must be datetime.datetime objects, in UTC time.
            All three values default to the current time.
        """
        super(Stat, self).__init__(**kwargs)
        self.st_mode = st_mode
        self.st_nlink = st_nlink
        if st_uid is None:
            st_uid = os.getuid()
        self.st_uid = st_uid
        if st_gid is None:
            st_gid = os.getgid()
        self.st_gid = st_gid
        self.st_size = st_size
        ts = _time.time()
        self.dt_atime = dt_atime or ts
        self.dt_mtime = dt_mtime or ts
        self.dt_ctime = dt_ctime or ts

    def __repr__(self):
        return ("<Stat st_mode=%#o, st_nlink=%s, st_uid=%s, st_gid=%s, "
                "st_size=%s>" % (self.st_mode, self.st_nlink, self.st_uid,
                                 self.st_gid, self.st_size))


class FSObject(object):
    """
    A file system object (subclasses are File and Dir).
    Attributes:
        name: str
        stat: Stat
        parent: Dir or None
    """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)


class Dir(FSObject):
    """
    A directory. May contain child directories and files.
    Attributes:
        name: str
        stat: Stat
        files: dict mapping str names to File and Dir objects.
    """
    def __init__(self, name, mode=stat.S_IFDIR | 0755, uid=None, gid=None):
        """
        Create a new directory object.
        """
        super(Dir, self).__init__(name)
        self.stat = Stat(mode, Stat.DIRSIZE, st_nlink=2, st_uid=uid, st_gid=gid)
        self.files = {}


class File(FSObject):
    """
    A non-directory file. May be a regular file, symlink, fifo, etc.
    Attributes:
        name: str
        stat: Stat
        data: byte string. Contents of the file.
            For a symlink, this is the link text.
            Do not edit manually; use provided methods.
    """
    def __init__(self, name, mode=stat.S_IFREG | 0644, uid=None, gid=None, size=0):
        """
        Create a new file object, with the supplied contents.
        """
        super(File, self).__init__(name)
        self.stat = Stat(mode, size, st_nlink=1, st_uid=uid, st_gid=gid)
