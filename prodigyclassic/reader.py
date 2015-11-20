

import mmap
import os
import struct
import io


class Reader:
    def __init__(self, data, little_endian, length=0,
                 access=mmap.ACCESS_WRITE, offset=0):
        if isinstance(data, io.IOBase):
            data = data.fileno()
        if isinstance(data, int):
            self.fd = data
            self.mmap = mmap.mmap(self.fd, length, access=access,
                                  offset=offset)
        elif isinstance(data, bytes):
            self.fd = False
            self.mmap = mmap.mmap(-1, length or len(data), access=access,
                                  offset=offset)
            # Write the data to the anonymous map
            self.write(data)
            self.seek(0)
        elif isinstance(data, mmap.mmap):
            self.fd = True
            self.mmap = data
        else:
            raise TypeError('first arg must be a file object, a file '
                            'descriptor, or bytes')
        self.set_little_endian(little_endian)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        # DON'T suppress exceptions
        return False

    def __str__(self):
        return str(self.mmap[:])

    def __len__(self):
        return len(self.mmap)

    def __getitem__(self, k):
        return self.mmap.__getitem__(k)

    def __setitem__(self, k, v):
        return self.mmap.__setitem__(k, v)

    def __delitem__(self, k):
        raise NotImplementedError("cannot delete")

    def close(self):
        return self.mmap.close()

    @property
    def closed(self):
        return self.mmap.closed

    def flush(self, offset=0, size=0):
        return self.mmap.flush(offset, size)

    def seek(self, pos, whence=os.SEEK_SET):
        self.mmap.seek(pos, whence)

    def size(self):
        if self.fd:
            return self.mmap.size()
        else:
            return len(self)

    def tell(self):
        return self.mmap.tell()

    def write(self, data):
        return self.mmap.write(data)

    def get_little_endian(self):
        """Get little endian boolean

        Returns True for little endian, False for big endian."""
        return self._little_endian

    def set_little_endian(self, little_endian):
        """Set default to little endian

        Specify True for little endian, False for big endian."""
        if little_endian is True:
            self.read_short = self.read_short_le
            self.read_ushort = self.read_ushort_le
            self.read_long = self.read_long_le
            self.read_ulong = self.read_ulong_le
            self.read_int = self.read_int_le
            self.read_uint = self.read_uint_le
            self.read_long_long = self.read_long_long_le
            self.read_ulong_long = self.read_ulong_long_le
        elif little_endian is False:
            self.read_short = self.read_short_be
            self.read_ushort = self.read_ushort_be
            self.read_long = self.read_long_be
            self.read_ulong = self.read_ulong_be
            self.read_int = self.read_int_be
            self.read_uint = self.read_uint_be
            self.read_long_long = self.read_long_long_be
            self.read_ulong_long = self.read_ulong_long_be
        else:
            raise TypeError('little_endian must be either True or False')
        self._little_endian = little_endian

    little_endian = property(get_little_endian, set_little_endian,
                             doc='little endian boolean')

    def _add_endian_code(self, fmt=''):
        if fmt.startswith(('@', '=', '<', '>', '!')):
            return fmt
        else:
            return ('<' if self.little_endian else '>') + fmt

    def make_struct(self, fmt):
        return struct.Struct(self._add_endian_code(fmt))

    def unpack_struct(self, struct_obj):
        return struct_obj.unpack(self.read(struct_obj.size))

    def unpack(self, fmt):
        """Unpack data using the given format

        Endianness may be overridden. See Python documentation for struct.
        """
        fmt = self._add_endian_code(fmt)
        return struct.unpack(fmt, self.read(struct.calcsize(fmt)))

    def get_reader(self, length=1, little_endian=None,
                   access=mmap.ACCESS_WRITE):
        """Like read() except returns a new Reader object"""
        if not length:
            raise ValueError("'length' cannot be {}".format(length))
        if little_endian is None:
            little_endian = self.little_endian
        return self.__class__(self.read(length), little_endian, access=access)

    def ismore(self):
        """Returns True if the pointer is not at the end of the data"""
        return self.tell() < len(self)

    def read(self, length=1):
        if length == 0:
            return b''
        data = self.mmap.read(length)
        if length and len(data) < abs(length):
            raise EOFError('only {0} of {1} byte(s) were available'
                           .format(len(data), abs(length)))
        return data

    def read_bool(self):
        """Read a boolean

        Null returns False, anything else returns True.
        """
        return struct.unpack('?', self.read(1))[0]

    def read_char(self):
        """Read a signed char (8 bits) integer"""
        return struct.unpack('b', self.read(1))[0]

    def read_uchar(self):
        """Read an unsigned char (8 bits) integer"""
        return struct.unpack('B', self.read(1))[0]

    ### big-endian

    def read_short_be(self):
        """Read a signed short (16 bits), big-endian integer"""
        return struct.unpack('>h', self.read(2))[0]

    def read_ushort_be(self):
        """Read an unsigned short (16 bits), big-endian integer"""
        return struct.unpack('>H', self.read(2))[0]

    def read_long_be(self):
        """Read a signed long (32 bits), big-endian integer"""
        return struct.unpack('>l', self.read(4))[0]

    def read_ulong_be(self):
        """Read an unsigned long (32 bits), big-endian integer"""
        return struct.unpack('>L', self.read(4))[0]

    # ints are longs on anything this will be running on
    read_int_be = read_long_be
    read_uint_be = read_ulong_be

    def read_long_long_be(self):
        """Read a signed long long (64 bits), big-endian integer"""
        return struct.unpack('>q', self.read(8))[0]

    def read_ulong_long_be(self):
        """Read an unsigned long long (64 bits), big-endian integer"""
        return struct.unpack('>Q', self.read(8))[0]

    ### little-endian

    def read_short_le(self):
        """Read a signed short (16 bits), little-endian integer"""
        return struct.unpack('<h', self.read(2))[0]

    def read_ushort_le(self):
        """Read an unsigned short (16 bits), little-endian integer"""
        return struct.unpack('<H', self.read(2))[0]

    def read_long_le(self):
        """Read a signed long (32 bits), little-endian integer"""
        return struct.unpack('<l', self.read(4))[0]

    def read_ulong_le(self):
        """Read an unsigned long (32 bits), little-endian integer"""
        return struct.unpack('<L', self.read(4))[0]

    # ints are longs on anything this will be running on
    read_int_le = read_long_le
    read_uint_le = read_ulong_le

    def read_long_long_le(self):
        """Read a signed long long (64 bits), little-endian integer"""
        return struct.unpack('<q', self.read(8))[0]

    def read_ulong_long_le(self):
        """Read an unsigned long long (64 bits), little-endian integer"""
        return struct.unpack('<Q', self.read(8))[0]
