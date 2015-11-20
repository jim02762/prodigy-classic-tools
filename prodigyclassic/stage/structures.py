
import struct
import math

from prodigyclassic import reader


class Reader(reader.Reader):
    def read_object_id(self):
        v = ObjectID()
        v.unpack(self.read(v.size))
        return v


class Check:
    _format = struct.Struct('<HH')
    size = _format.size

    def __init__(self, mapcheck=None, dircheck=None):
        self.mapcheck = mapcheck
        self.dircheck = dircheck

    def unpack(self, data):
        if len(data) != self.size:
            raise UnpackError('expecting {} bytes'.format(self.size))
        self.mapcheck, self.dircheck = self._format.unpack(data)

    def pack(self):
        return self._format.pack(self.mapcheck, self.dircheck)

    def __repr__(self):
        return ('{0}(mapcheck={1:#x}, dircheck={2:#x})'
                .format(self.__class__.__name__, self.mapcheck, self.dircheck))


class VersionID:
    # byte1 is byte #17 in the object header (a/k/a version)
    # byte2 is byte #15 in the object header (a/k/a storage control)
    _format = struct.Struct('BB')
    size = _format.size

    # This list is certainly incomplete/outdated
    CacheCandidacy = 0
    NoCandidacy = 1
    StageCandidacy = 2
    StageNoVCandidacy = 3
    RequiredCandidacy = 4
    RequiredNoVCandidacy = 5

    # TODO: Patent (pretty sure) and source says 3 bits but it looks like 5 to me!
    storage_width = 5

    def __init__(self, byte1=None, byte2=None):
        self.byte1 = byte1
        self.byte2 = byte2

    
    def unpack(self, data):
        if len(data) != self.size:
            raise UnpackError('expecting {} bytes'.format(self.size))
        self.byte1, self.byte2 = self._format.unpack(data)

    def pack(self):
        return self._format.pack(self.byte1, self.byte2)

    @property
    def versionvalue(self):
        versionfields = (self.byte1 << 8) | self.byte2
        return versionfields >> self.storage_width

    @property
    def storecandidacy(self):
        versionfields = (self.byte1 << 8) | self.byte2
        return versionfields & (1 << self.storage_width) - 1

    def __repr__(self):
        return ('{0}(byte1={1:#x}, byte2={2:#x})'
                .format(self.__class__.__name__, self.byte1, self.byte2))


class ObjectID:
    _format = struct.Struct('11sBB')
    size = _format.size

    def __init__(self, name=None, location=None, type_=None):
        self.name = name
        self.location = location
        self.type = type_
    
    def unpack(self, data):

        if len(data) != self.size:
            raise UnpackError('expecting {} bytes'.format(self.size))
        self.name, self.location, self.type = self._format.unpack(data)
        self.name = self.name.rstrip()

        # nonexistent?
        if self.name == bytes([0]) * 11:
            self.name = None

    def pack(self):
        return self._format.pack('{:11}'.format(self.name), self.location,
                                 self.type)

    def __repr__(self):
        return ('{0}(name={1}, location={2}, type_=0x{3:#x})'
                .format(self.__class__.__name__, self.name, self.location,
                        self.type))

    def __str__(self):
        return self.get_id(delim=True)

    # TODO: name???
    def get_id(self, delim=False, nonascii=False):
        return '{0} {1:#x} {2:#x}'.format(self.get_name(delim, nonascii),
                                          self.location, self.type)

    def get_name(self, delim=False, nonascii=False):

        if delim is True:
            delim = '.'
        elif delim is False:
            delim = ''

        if nonascii is True:
            nonascii = '_'
        elif nonascii is False:
            nonascii = None

        # TODO: get rid of this, Handle elsewhere.
        # Handle non-printable ASCII, which is between 32 and 126, inclusive
        name = [(31 < i < 127 and chr(i)) or 
                (nonascii or '\\x{:02x}'.format(i))
                for i in self.name]
        if delim:
            # Make a standard 8.3 type file name
            name.insert(8, delim)
        return ''.join(name)


class StartID:
    _format = struct.Struct('<HH')
    size = _format.size

    def __init__(self, mapstartid=None, dirstartid=None):
        self.mapstartid = mapstartid
        self.dirstartid = dirstartid

    def unpack(self, data):
        if len(data) != self.size:
            raise UnpackError('expecting {} bytes'.format(self.size))
        self.mapstartid, self.dirstartid = self._format.unpack(data)

    def pack(self):
        return self._format.pack(self.mapstartid, self.dirstartid)

    def __repr__(self):
        return ('{0}(mapstartid={1:#x}, dirstartid={2:#x})'
                .format(self.__class__.__name__, self.mapstartid,
                        self.dirstartid))


class Prologue:
    _format = struct.Struct('<8H4s4s2H')
    size = _format.size

    def __init__(self):
        self.structurelevel = 0
        self.class_ = 0  # originally StoreClasst
        self.auquantasize = 0
        self.austartoffset = 0
        self.mapwidth = 0
        self.maxmapentries = 0
        self.dirtotbytesize = 0
        self.curstartidx = 0
        self.startids = [StartID(), StartID()]
        self.prologuestartid = 0
        self.check = 0

    def unpack(self, data):
        if len(data) != self.size:
            raise UnpackError('expecting {} bytes'.format(self.size))
        (
            self.structurelevel,
            self.class_,
            self.auquantasize,
            self.austartoffset,
            self.mapwidth,
            self.maxmapentries,
            self.dirtotbytesize,
            self.curstartidx,
            startids_0,
            startids_1,
            self.prologuestartid,
            self.check,
        ) = self._format.unpack(data)
        self.startids[0].unpack(startids_0)
        self.startids[1].unpack(startids_1)

        # I have a Windows version that follows with an object-id for
        # RCO id and 00 1D 63. None of these are used for reading from or
        # writing to the STAGE.DAT.
        # TODO: Are those last three bytes like DirectoryEntry's status?


class AUM:
    FreeEntryValue = 0x00
    EolEntryValue = 0x01

    def __init__(self, width, startid, entries):
        self.width = width
        self.startid = startid
        self.entries = entries

        self.checks = Check()
        self.table = []

    @property
    def size(self):
        return self.checks.size + math.ceil(self.entries * (self.width / 8))

    def unpack(self, data):

        if len(data) != self.size:
            raise UnpackError('expecting {} bytes'.format(self.size))

        # Get and remove the checks from the data
        self.checks.unpack(data[0:self.checks.size])
        # We're working with bytes so this creates a nice list of integers
        # for us
        data = list(data[self.checks.size:])

        # The first couple entries aren't real
        self.table = [self.EolEntryValue] * self.startid
        mask = (1 << self.width) - 1
        reg = 0
        bit_count = 0
        # Remember that we already added some entries
        for dummy in range(0, self.entries - self.startid):

            # If we don't have the required number of bytes then
            # shift in another byte and put it on the left of any
            # remaining bits. (little-endian)
            while bit_count < self.width:
                reg |= data.pop(0) << bit_count
                bit_count += 8

            self.table.append(reg & mask)

            # Shift out the used bits
            reg >>= self.width
            bit_count -= self.width

    def get_next(self, AUid):
        try:
            n = self.table[AUid]
        except IndexError:
            raise AUdoesNotExistError('AU {} does not exist'.format(AUid))
        if n == self.EolEntryValue:
            raise AUendOfList('AU {} is last in chain'.format(AUid))
        elif n == self.FreeEntryValue:
            raise AUnotAllocatedError('AU {} is not allocated'.format(AUid))
        return n

    def get_chain(self, AUid):
        chain = []
        while True:
            chain.append(AUid)
            try:
                AUid = self.get_next(AUid)
            except AUendOfList:
                break
        return chain


class Directory:
    @property
    def size(self):

        # 22 for the header +
        # 2 (short) per entry in the usagelist +
        # 24 (DirectoryEntry.size) per entry in the entrylist
        return 22 + (2 * self.maximum) + (DirectoryEntry.size * self.maximum)

    def __init__(self):

        self.checks = Check()
        # TODO: timestamps should be passed as tuples.
        self.createdate = None
        self.modifydate = None
        self.novclass = VersionID()
        self.inuse = 0
        self.maximum = 0
        self.usageoff = None
        self.entryoff = None
        self.usagelist = []
        self.entrylist = []

        self._create_index()

    _format = struct.Struct('<4sLL2s4H')

    def unpack(self, data):

        if len(data) != self.size:
            raise UnpackError('expecting {} bytes'.format(self.size))
        data = Reader(data, True)

        (
            checks,
            self.createdate,
            self.modifydate,
            novclass,
            self.inuse,
            self.maximum,
            self.usageoff,
            self.entryoff,
        ) = data.unpack_struct(self._format)
        self.checks.unpack(checks)
        self.novclass.unpack(novclass)

        # TODO: Adjust base 1900 timestamps. Convert timestamps into tuples.

        # TODO: test!
        # Load and re-base usage list
        struct_obj = data.make_struct('{}H'.format(self.maximum))
        self.usagelist = [v - 1 for v in data.unpack_struct(struct_obj)]

        # Grab the remaining data. We're going to use (faster) slicing now.
        data = data.read(-1)
        if len(data) % DirectoryEntry.size != 0:
            raise UnpackError('wrong amount of data!')
        self.entrylist = []
        for i in range(0, len(data), DirectoryEntry.size):
            entry = DirectoryEntry()
            entry.unpack(data[i: i + DirectoryEntry.size])
            self.entrylist.append(entry)
        self._create_index()

    def _create_index(self):
        self._entrylist_index = {entry.id.name: index
                                 for (index, entry) in
                                 enumerate(self.entrylist)
                                 if entry.id.name is not None}

    def get_entry(self, entry):
        if not isinstance(entry, int):
            entry = self.get_index(entry)
        return self.entrylist[entry]

    def get_index(self, name):
        if isinstance(name, ObjectID):
            name = name.name
        elif isinstance(name, bytes):
            name = name.rstrip()
        else:
            raise TypeError('specify bytes or ObjectID')
        return self._entrylist_index[name]


class DirectoryEntry:
    _format = struct.Struct('<13sBHHH2sH')
    size = _format.size

    def __init__(self):
        self.id = ObjectID()
        self.status = None
        self.length = None
        self.startid = None  # originally AUidt (Wordt)
        self.version = VersionID()
        self.check = None

    _format = struct.Struct('<13sBHHH2sH')

    def unpack(self, data):
        if len(data) != self.size:
            raise UnpackError('expecting {} bytes'.format(self.size))
        (
            id_,
            dummy,  # seemingly unused
            self.status,
            self.length,
            self.startid,
            version,
            self.check,
        ) = self._format.unpack(data)
        self.id.unpack(id_)
        self.version.unpack(version)

    def set_from_object(self, obj):
        """Create a bare-bones directory entry from an object's header"""

        self.id = obj.id
        self.length = obj.length
        self.version = obj.version

        self.status = None
        self.startid = None
        self.check = None


class Object:
    # TODO: allow creating with length, etc.?????
    def __init__(self):

        self.id = ObjectID()
        self.length = 0
        self.setsize = 0
        self.version = VersionID()
        self.header = b''
        self.data = b''

        self._data = b''

    @property
    def size(self):
        return self.length or self._format.size

    _format = struct.Struct('<13sHBBB')

    def unpack(self, data):

        self._data = data

        if (self.length and len(data) != self.size) or len(data) < self.size:
            raise UnpackError('expecting {} bytes'.format(self.size))
        (
            id_,
            self.length,
            storeflags,
            self.setsize,
            version,
        ) = self._format.unpack(data[0:18])
        self.id.unpack(id_)
        self.version = VersionID(version, storeflags)

        # We might not have been able to check before
        if len(data) != self.size:
            raise UnpackError('expecting {} bytes'.format(self.size))

        # Loose the header and save the data
        self.data = data[18:]

    def get_header(self):
        return self._data[:self._format.size]

    def get_data(self, with_header=False):
        if not with_header:
            return self.data
        return self._data


class StructureException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class AUendOfList(StructureException):
    pass


class AUnotAllocatedError(StructureException):
    pass


class AUdoesNotExistError(StructureException):
    pass


class UnpackError(StructureException):
    pass
