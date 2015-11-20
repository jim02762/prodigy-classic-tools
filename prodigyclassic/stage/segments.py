
import collections
import struct

from prodigyclassic import hexdump
from prodigyclassic.stage import structures


class Reader(structures.Reader):
    pass


class Segment:

    _segment_hdr_size = 3

    def __init__(self, id_, st, sl):
        self._id = id_      # Should we pass an object instead?
        self._st = st
        self._sl = sl

        self._data = b''
        self._exceptions = []

    def __str__(self):
        output = []
        dump = hexdump.HexDump()
        short_dump_len = 8  # This many or below and we'll use short_dump
        short_dump = hexdump.HexDump('{h[0]:23}  |{s[0]}|')

        for exception in self._exceptions:
            output.append(str(exception))

        for k, v in sorted(self.__dict__.items()):
            if k.startswith('_'):
                continue
            if isinstance(v, bytes):
                if len(v) > short_dump_len:
                    output.append('{0}: ({1} bytes)'.format(k, len(v)))
                    output.append(dump(v))
                else:
                    output.append('{0}:   {1}'.format(k, short_dump(v)))
            elif isinstance(v, int):
                output.append('{0}: {1:#x} ({1})'.format(k, v))
            else:
                output.append('{0}: {1}'.format(k, v))

        return "\n".join(output)

    def get_header(self):
        return self._data[:self._segment_hdr_size]

    def get_data(self, with_header=False):
        if not with_header:
            return self._data[self._segment_hdr_size:]
        return self._data

    def add_exception(self, exception):
        self._exceptions.append(exception)

    def set_exceptions(self, exceptions):
        self._exceptions = exceptions

    def get_exceptions(self):
        return self._exceptions

    def set_seg_type(self, st):
        self._st = st

    def get_seg_type(self):
        return self._st

    def set_seg_length(self, sl):
        self._sl = sl

    def get_seg_length(self):
        return self._sl

    def unpack(self, data):
        self._data = data


class ProgramCallSegment(Segment):

    _segment_type = 0x01

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.event = None
        self.prefix = None
        self.id = None
        self.parm_length = None
        self.parm = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.event = data.read_uchar()
        self.prefix = data.read_uchar()

        if self.prefix == 0xd:
            self.id = data.read_object_id()
            self.parm = data.read(None) or None
        elif self.prefix == 0xf:
            # TODO: verify in source
            self.parm_length = data.read_ushort()
            self.parm = data.read(self.parm_length) or None
        else:
            raise SegmentDataError('prefix={0}, data={1}'
                                   .format(self.prefix, data))

        assert data.ismore() is False


class FieldProgramCallSegment(Segment):

    _segment_type = 0x02

    # TODO: params for imbedded objects???????

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.event = self.field = self.prefix = None
        self.id = self.parm_length = self.parm = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.event = data.read_uchar()
        self.field = data.read_uchar()
        self.prefix = data.read_uchar()

        if self.prefix == 0xd:
            self.id = data.read_object_id()
            self.parm = data.read(None) or None
        elif self.prefix == 0xf:
            # TODO: verify in source
            self.parm_length = data.read_ushort()
            self.parm = data.read(self.parm_length) or None
        else:
            raise SegmentDataError('prefix={0}, data={1}'
                                   .format(self.prefix, data))

        assert data.ismore() is False


class CompDescSegment(Segment):

    _segment_type = 0x03

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.table_num = self.length1 = self.length2 = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.table_num = data.read_uchar()
        self.length1 = data.read_ushort()
        if data.ismore():
            self.length2 = data.read_ushort()

        assert data.ismore() is False


class FieldDefSegment(Segment):

    _segment_type = 0x04

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.attributes = self.origin = self.size = self.name = None
        self.text_id = self.cursor_id = self.cursor_origin = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.attributes = data.read_ushort()
        self.origin = data.read(3)
        self.size = data.read(3)
        self.name = data.read_uchar()

        # TODO: not sure about this
        if data.ismore():
            self.text_id = data.read_uchar()
        if data.ismore():
            self.cursor_id = data.read_uchar()
        if data.ismore():
            self.cursor_origin = data.read(3)

        assert data.ismore() is False


class ArrayDefSegment(Segment):

    _segment_type = 0x05

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.occurrences = self.vertical_gap = self.field_name = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.occurrences = data.read_uchar()
        self.vertical_gap = data.read(3)

        # TODO: not anywhere in Benj's STAGE.DAT. Check RS source.
        self.field_name = data.read(-1)

        assert data.ismore() is False


class CustomTextDefSegment(Segment):

    _segment_type = 0x0a

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.id = self.naplps = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.id = data.read_uchar()
        self.naplps = data.read(-1)


class CustomCursorDefSegment(Segment):

    _segment_type = 0x0b

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.id = self.size = self.naplps = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.id = data.read_uchar()
        self.size = data.read(3)
        self.naplps = data.read(-1)

        # TODO: What about Custom Cursor Type 2? Check RS source.


class SelectorCallSegment(Segment):

    _segment_type = 0x20

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.part_id = self.priority = self.prefix = None
        self.id = self.parm_length = self.parm = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.part_id = data.read_uchar()
        self.priority = data.read_uchar()
        self.prefix = data.read_uchar()

        if self.prefix == 0xd:
            self.id = data.read_object_id()
            self.parm = data.read(None) or None
        elif self.prefix == 0xf:
            # TODO: verify in source
            self.parm_length = data.read_ushort()
            self.parm = data.read(self.parm_length) or None
        else:
            raise SegmentDataError('prefix={0}, data={1}'
                                   .format(self.prefix, data))

        assert data.ismore() is False


class ElementCallSegment(Segment):

    _segment_type = 0x21

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.part_id = self.priority = self.prefix = None
        self.id = self.parm_length = self.parm = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.part_id = data.read_uchar()
        self.priority = data.read_uchar()
        self.prefix = data.read_uchar()

        if self.prefix == 0xd:
            self.id = data.read_object_id()
        elif self.prefix == 0xf:
            # TODO: verify in source
            self.parm_length = data.read_ushort()
            self.parm = data.read(self.parm_length) or None
        else:
            raise SegmentDataError('prefix={0}, data={1}'
                                   .format(self.prefix, data))

        assert data.ismore() is False


# TODO: can't verify because not in Benj's STAGE.DAT. Check RS source.
class InventoryCtlSegment(Segment):

    _segment_type = 0x26

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.type = self.number = self.subnumber = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.type = data.read_uchar()
        self.number = data.read_ushort()
        if data.ismore():
            self.subnumber = data.read_ushort()

        assert data.ismore() is False


class PageFormatCallSegment(Segment):

    _segment_type = 0x31

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.prefix = self.id = self.parm_length = self.parm = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.prefix = data.read_uchar()

        if self.prefix == 0xd:
            self.id = data.read_object_id()
        elif self.prefix == 0xf:
            # TODO: verify in source
            self.parm_length = data.read_ushort()
            self.parm = data.read(self.parm_length) or None
        else:
            raise SegmentDataError('prefix={0}, data={1}'
                                   .format(self.prefix, data))

        assert data.ismore() is False


# TODO: not used in Benj's STAGE.DAT. Check RS source.
class PageFormatDefaultSegment(Segment):

    _segment_type = 0x32

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.naplps = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.naplps = data.read(-1)


class PartitionDefSegment(Segment):

    _segment_type = 0x33

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.part_id = self.origin = self.size = self.naplps = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.part_id = data.read_uchar()
        self.origin = data.read(3)
        self.size = data.read(3)

        # TODO: Is this ever used? The patent text doesn't mention it.
        if data.ismore():
            self.naplps = data.read(-1)

        assert data.ismore() is False


class PresentationDataSegment(Segment):

    _segment_type = 0x51

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.type = self.size = self.data = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.type = data.read_uchar()
        self.size = data.read(3)
        self.data = data.read(-1)


# TODO: ImbeddedObjectSegment and ImbeddedElementSegment aren't in the patent!
class ImbeddedObjectSegment(Segment):

    _segment_type = 0x52

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.object = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.object = structures.Object()
        self.object.unpack(data)


# TODO: no samples
class ImbeddedElementSegment(Segment):

    _segment_type = 0x53

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.data = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.data = data.read(-1)


class ProgramDataSegment(Segment):

    _segment_type = 0x61

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.type = self.data = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        self.type = data.read_uchar()
        self.data = data.read(-1)


class NavigateSegment(Segment):

    _segment_type = 0x71

    def __init__(self, id_, st, sl):
        super().__init__(id_, st, sl)
        self.data = None

    def unpack(self, data):
        super().unpack(data)
        data = structures.Reader(data[self._segment_hdr_size:], True)
        # TODO: patent is wrong/out of date. Check RS source.
        self.data = data.read(-1)


class UnknownSegment(Segment):

    _segment_type = None
    
    def __str__(self):
        output = []
        dump = hexdump.HexDump()
        short_dump_len = 8  # This many or below and we'll use short_dump
        short_dump = hexdump.HexDump('{h[0]:23}  |{s[0]}|')

        for exception in self._exceptions:
            output.append(str(exception))

        if self._data:
            if len(self._data) > short_dump_len:
                output.append('data: ({} bytes)'.format(len(self.get_data())))
                output.append(dump(self.get_data()))
            else:
                output.append('data:   {}'.format(short_dump(self.get_data())))

        return "\n".join(output)


class SegmentFactory:

    # segment header structure
    _hdr_struct = struct.Struct('<BH')

    def __init__(self, base=Segment, unknown=UnknownSegment):
        # Create a dictionary of segment classes indexed by their type (st).
        # Undefined segment types get a special "unknown segment" class.
        self.segment_subclasses = collections.defaultdict(lambda: unknown,
                {cls._segment_type: cls for cls in base.__subclasses__()
                    if cls._segment_type})

    def create_segment(self, id_, st, sl):
        return self.segment_subclasses[st](id_, st, sl)

    def parse_segments(self, obj):

        with Reader(obj.data, True) as data:
            while data.ismore():
                loc = data.tell()
                try:
                    # Read in segment header
                    st, sl = data.unpack_struct(self._hdr_struct)
                except EOFError:
                    # Go back and get all the data we can and put it into a
                    # special segment
                    segment = self.create_segment(obj.id, None, None)
                    data.seek(loc)
                    segment.unpack(data.read(None))
                    segment.add_exception(
                        SegmentDataError('invalid segment header'))

                    # We're obviously done with this object
                    yield segment
                    break

                # Create a segment object
                segment = self.create_segment(obj.id, st, sl)

                # Rewind and read in the entire segment, including the header
                data.seek(loc)
                try:
                    segment_data = data.read(sl)
                except EOFError:
                    segment.add_exception(
                        SegmentDataError('segment extends beyond '
                                         'end of object'))

                    # Try again, this time getting everything we can.
                    data.seek(loc)
                    segment_data = data.read(None)

                # Process the segment's data
                try:
                    segment.unpack(segment_data)
                except EOFError:
                    segment.add_exception(
                        SegmentDataError('segment missing data'))
                except SegmentDataError as e:
                    segment.add_exception(e)

                yield segment


class SegmentException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SegmentDataError(SegmentException):
    pass
