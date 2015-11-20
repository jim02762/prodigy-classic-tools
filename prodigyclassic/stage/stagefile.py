
import os

from prodigyclassic.stage import structures


class _StageStructure:
    def __init__(self, stage, *args, **kwargs):
        self.stage = stage
        super().__init__(*args, **kwargs)


class _StagePrologue(_StageStructure, structures.Prologue):
    def load(self):
        data = self.stage.read_offset(0, self.size)
        self.unpack(data)


class _StageAUM(_StageStructure, structures.AUM):
    def __init__(self, stage):
        super().__init__(stage, stage.prologue.mapwidth,
                         stage.prologue.prologuestartid,
                         stage.prologue.maxmapentries)

    def load(self, index):
        stage = self.stage
        stage.seek_AUid(stage.prologue.startids[index].mapstartid)
        self.unpack(stage.read(self.size))

    def get_next(self, AUid=None):
        if AUid is None:
            AUid = self.stage.tell_AUid()
        return super().get_next(AUid)

    def get_chain(self, AUid=None):
        if AUid is None:
            AUid = self.stage.tell_AUid()
        return super().get_chain(AUid)


class _StageDirectory(_StageStructure, structures.Directory):
    @property
    def size(self):
        return self.stage.prologue.dirtotbytesize

    def load(self, index):
        # Everything except the prologue and AUMs are chain read
        AUid = self.stage.prologue.startids[index].dirstartid
        data = self.stage.read_chain(AUid)
        data = data[:self.size]
        self.unpack(data)


class _StageObject(_StageStructure, structures.Object):
    def load(self, obj_id):
        stage = self.stage
        dir_entry = stage.dir.get_entry(obj_id)
        data = stage.read_chain(dir_entry.startid)
        data = data[:dir_entry.length]
        self.unpack(data)


class StageFile:
    def __init__(self, stage_map):
        self.stage_map = stage_map

        self.prologue = None
        self.AUMaps = [None, None]
        self.dirs = [None, None]
        self.index = 0

    @property
    def AUM(self):
        return self.AUMaps[self.index]

    @property
    def dir(self):
        return self.dirs[self.index]

    def change_index(self, index=None):
        if index is None:
            index = self.prologue.curstartidx
        self.index = index

    def load(self):
        self.load_prologue()
        self.load_AUMaps()
        self.load_dirs()
        self.change_index()

    def load_prologue(self):
        self.prologue = _StagePrologue(self)
        self.prologue.load()

    def load_AUMaps(self):
        self.load_AUM(0)
        self.load_AUM(1)

    def load_AUM(self, index):
        self.AUMaps[index] = _StageAUM(self)
        self.AUMaps[index].load(index)

    def load_dirs(self):
        self.load_dir(0)
        self.load_dir(1)

    def load_dir(self, index):
        self.dirs[index] = _StageDirectory(self)
        self.dirs[index].load(index)

    def offset_to_AUid(self, offset):
        if offset < 0:
            raise ValueError('offset must be >= 0')
        return ((offset - self.prologue.austartoffset) //
                self.prologue.auquantasize + self.prologue.prologuestartid)

    def AUid_to_offset(self, AUid):
        if AUid < self.prologue.prologuestartid:
            raise ValueError('AUid must be >= {0}'
                             .format(self.prologue.prologuestartid))
        return (self.prologue.austartoffset +
                (AUid - self.prologue.prologuestartid) *
                self.prologue.auquantasize)

    def seek(self, offset):
        self.stage_map.seek(offset, os.SEEK_CUR)

    def seek_offset(self, offset):
        self.stage_map.seek(offset, os.SEEK_SET)

    def seek_AUid(self, AUid):
        self.seek_offset(self.AUid_to_offset(AUid))

    def read(self, length=1):
        return self.stage_map.read(length)

    def read_offset(self, offset, length=1):
        self.seek_offset(offset)
        return self.read(length)

    def read_AUid(self, AUid, length=1):
        self.seek_AUid(AUid)
        return self.read(self.prologue.auquantasize * length)

    def read_chain(self, chain=None):
        if not isinstance(chain, list):
            chain = self.AUM.get_chain(chain)
        data = []
        for AUid in chain:
            data.append(self.read_AUid(AUid))
        return b''.join(data)

    def tell(self):
        return self.stage_map.tell()

    def tell_offset(self):
        return self.tell()

    def tell_AUid(self):
        return self.offset_to_AUid(self.tell_offset())

    def get_object(self, obj_id):
        o = _StageObject(self)
        o.load(obj_id)
        return o


class StageException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
