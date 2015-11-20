#!/usr/bin/env python3


import mmap
import argparse
import collections

from prodigyclassic.stage import stagefile, segments, structures
from prodigyclassic import hexdump
import arghelpers
import conditions


VERSION = '0.1.0'


def load_stage_file(stage_fd):
    stage_map = mmap.mmap(stage_fd.fileno(), 0, access=mmap.ACCESS_READ)
    stage_obj = stagefile.StageFile(stage_map)
    stage_obj.load()
    return stage_obj


# noinspection PyUnusedLocal
def list_segment_types(args):
    factory = segments.SegmentFactory()
    subclasses = factory.segment_subclasses
    for type_, cls in sorted(subclasses.items()):
        print('{0:35} {1:<#8x}({1})'.format(cls.__name__, type_))
    print("\n'{}' matches all others".format(subclasses[None].__name__))


def show_aum(args):
    # symbols
    invalid = 'X'
    consecutive = "-"
    eol = '%'
    unused = 'U'

    # formats
    row_fmt = lambda x, y: '{:#5x}:  {}'.format(x, y)
    char_fmt = lambda x: '{0:^4}'.format(x)
    hex_fmt = lambda x: '{0:^4x}'.format(x)

    stage_obj = load_stage_file(args.stagefile)
    # allocation unit id's before the prologue aren't valid
    start_auid = stage_obj.prologue.prologuestartid
    table = stage_obj.AUM.table[start_auid:]
    if args.no_symbols:
        out = [char_fmt('')] * start_auid
        out.extend([hex_fmt(v) for v in table])
    else:
        out = [char_fmt(invalid)] * start_auid
        for i, v in enumerate(table, start_auid):
            if v == i + 1:
                out.append(char_fmt(consecutive))
            elif v == structures.AUM.EolEntryValue:
                out.append(char_fmt(eol))
            elif v == structures.AUM.FreeEntryValue:
                out.append(char_fmt(unused))
            else:  # object is fragmented
                out.append(hex_fmt(v))

    # present output as row address + 16 columns
    row_size = 16
    for i in range(0, len(out), row_size):
        print(row_fmt(i, ''.join(out[i:i + row_size])))


def directory(args):
    stage_obj = load_stage_file(args.stagefile)
    segment_factory = segments.SegmentFactory()

    if not args.no_header:
        print('line      name     loc type   length   stat auid  ver stor '
              'check ssize')

    obj_idx = 0
    segment_list = []
    line = 0
    while True:

        # Time to get another object?
        if not segment_list:

            if obj_idx >= stage_obj.dir.inuse:
                break
            dir_ = stage_obj.dir.get_entry(obj_idx)
            obj = stage_obj.get_object(obj_idx)
            obj_idx += 1
            segment_list = list(segment_factory.parse_segments(obj))

            line += 1
            if not conditions.Objects.check(args, dir_):
                continue
            print('{0:04}  {1:12} {2:2x}   {3:2x} {4:4x}({4:5}) {5:4x}'
                  ' {6:4x}  {7:3x}   {8:2x}  {9:04x}    {10:2x}'
                  .format(line, 
                          obj.id.get_name(args.obj_delim, 
                                          args.obj_nonascii),
                          obj.id.location, obj.id.type, dir_.length,
                          dir_.status, dir_.startid, 
                          dir_.version.versionvalue,
                          dir_.version.storecandidacy,
                          dir_.check, obj.setsize))

        segment = segment_list.pop(0)
        line += 1

        if (isinstance(segment, segments.ImbeddedObjectSegment) and not
                args.skip_imbedded):
            obj = segment.object
            segment_list = (list(segment_factory.parse_segments(obj)) +
                            segment_list)

            line += 1
            if not conditions.Objects.check(args, obj):
                continue
            print('{0:04}  {1:12} {2:2x}   {3:2x} {4:4x}({4:5})            '
                  '{5:3x}   {6:2x}          {7:2x}'
                  .format(line, 
                          obj.id.get_name(args.obj_delim, 
                                          args.obj_nonascii),
                          obj.id.location, obj.id.type, obj.length,
                          obj.version.versionvalue, 
                          obj.version.storecandidacy,
                          obj.setsize))


def view(args):

    class Indent:

        def __init__(self, prefix='', pad=' ' * 4, count=0):
            self.prefix = prefix
            self.pad = pad
            self.indent_count = count

        def indent(self, count=None):
            if count is None:
                self.indent_count += 1
            else:
                self.indent_count = count

        def outdent(self):
            if self.indent_count > 0:
                self.indent_count -= 1

        @property
        def padding(self):
            return self.__call__(prefix=True)

        def __call__(self, prefix=True):
            if prefix is True:
                prefix = self.prefix
            elif prefix is False:
                prefix = ''
            return prefix + (self.pad * self.indent_count)

        def __str__(self):
            return self.padding

    stage_obj = load_stage_file(args.stagefile)
    segment_factory = segments.SegmentFactory()

    obj_idx = 0
    segment_list = []
    line = 0
    pad = Indent(prefix=' ' * 5, pad='|   ')
    dump = hexdump.HexDump(
        '  {addr:04x}  {h[0]:23}  {h[1]:23}  |{s[0]}{s[1]}|'
    )
    short_dump_len = 8  # This many or below and we'll use short_dump
    short_dump = hexdump.HexDump('{h[0]:23}  |{s[0]}|')
    while True:

        # Time to get another object?
        if not segment_list:

            if obj_idx >= stage_obj.dir.inuse:
                break
            dir_ = stage_obj.dir.get_entry(obj_idx)
            obj = stage_obj.get_object(obj_idx)
            obj_idx += 1
            segment_list = list(segment_factory.parse_segments(obj))

            pad.indent(0)
            if line > 0:
                print()
            line += 1

            print('{0:04} {1} {2} {3:#x}   length={5:#x}({5}) status={4:#x} '
                  'startid={6:#x}({6})'
                  .format(line, 
                          obj.id.get_name(delim=True, nonascii=True), 
                          obj.id.location, obj.id.type, dir_.status, 
                          dir_.length, dir_.startid))
            print('{0}-       version={1:#x} store_candidacy={2} check={3:#x} '
                  'setsize={4}'
                  .format(pad, dir_.version.versionvalue,
                          dir_.version.storecandidacy, dir_.check,
                          obj.setsize))

            pad.indent()

        # Get a segment. If it's None then we just finished up an imbedded
        # object so time to outdent.
        segment = segment_list.pop(0)
        if segment is None:
            pad.outdent()
            continue

        line += 1
        print('{0:04} {1}{2}   st={3:#x} sl={4:#x}({4})'
              .format(line, pad(prefix=False), segment.__class__.__name__,
                      segment.get_seg_type(), segment.get_seg_length()))

        # Interrupt with a new object?
        if isinstance(segment, segments.ImbeddedObjectSegment):
            obj = segment.object
            segment_list = (list(segment_factory.parse_segments(obj)) +
                            [None] + segment_list)

            line += 1
            print('{0:04} {1}- {2} {3} {4:#x}   length={6:#x}({6}) '
                  'version={5:#x}'
                  .format(line, pad(prefix=False), 
                          obj.id.get_name(delim=True, nonascii=True),
                          obj.id.location, obj.id.type,
                          obj.version.versionvalue, obj.length))
            print('{0}-        store_candidacy={1} setsize={2}'
                  .format(pad, obj.version.storecandidacy, obj.setsize))
            pad.indent()
            continue

        # Present the data. Exceptions are shown first. Unknown segments
        # have to be done separately.
        pad.indent()
        for exception in segment.get_exceptions():
            print('{}{}: {}'.format(pad, exception.__class__.__name__,
                                    exception))

        # Is this an unknown/invalid segment?
        if segment._segment_type is None:
            k = 'data'
            v = segment.get_data()
            if len(v) > short_dump_len:
                print('{0}{1:16}: ({2} bytes) '.format(pad, k, len(v)))
                print(dump(v))
            else:
                print('{0}{1:16}:   {2}'.format(pad, k, short_dump(v)))
        else:
            for k, v in sorted(segment.__dict__.items()):
                if k.startswith('_'):
                    continue
                if isinstance(v, bytes):
                    if len(v) > short_dump_len:
                        print('{0}{1:16}: ({2} bytes) '.format(pad, k, len(v)))
                        print(dump(v))
                    else:
                        print('{0}{1:16}:   {2}'.format(pad, k, short_dump(v)))
                elif isinstance(v, int):
                    print('{0}{1:16}: {2:<#8x}({2})'.format(pad, k, v))
                else:
                    print('{0}{1:16}: {2}'.format(pad, k, v))
        pad.outdent()


def extract(args):
    class LineNumber:

        def __init__(self):
            self.object = self.segment = self.line = 0

        def bump(self):
            self.line += 1
            return self.line

        def bump_object(self):
            self.object = self.bump()
            return self.object

        def bump_segment(self):
            self.segment = self.bump()
            return self.segment

        def __str__(self):
            return str(self.line)

    class OutputData:

        def __init__(self, fmt_, dir_, force):
            # Our stuff should start with an underscore
            # in order to avoid potential name collisions.
            self._format = fmt_
            self._directory = dir_
            # open()'s 'wb' is for writing binary and will clobber. 'xb' is
            # the same but raises an exception if the file already exists.
            self._mode = force and 'wb' or 'xb'

        def make_name(self):
            return '{}/{}'.format(self._directory,
                                  self._format.format(**self.__dict__))

        def __call__(self, data):
            with open(self.make_name(), self._mode) as f:
                f.write(data)

    stage_obj = load_stage_file(args.stagefile)
    segment_factory = segments.SegmentFactory()

    # We'll keep the last 10 objects around
    # (more than enough history to handle deeply nested imbedded objects)
    skip_object = collections.deque([], 10)

    if args.name_format is not None:
        fmt = args.name_format
    elif args.object:
        fmt = '{obj_name}_{id}'
    elif args.segment:
        fmt = '{obj_name}_{id}_{segment_name}'
    else:
        fmt = '{obj_name}_{id}_{segment_type}_{attribute}'
    output_data = OutputData(fmt, args.output_dir, args.force)

    dir_entry = obj = segment = None
    obj_idx = 0
    segment_list = []
    line = LineNumber()
    while True:

        # Interrupt with a new object?
        if isinstance(segment, segments.ImbeddedObjectSegment):

            # Prepend the new segments to the segment list for processing.
            # Separate the new and the old with a tuple that remembers where
            # we were.
            segment_list = (
                list(segment_factory.parse_segments(segment.object)) +
                [(obj, dir_entry, line.object)] + segment_list
            )

            obj = segment.object
            # create a fake directory entry
            dir_entry = structures.DirectoryEntry()
            dir_entry.set_from_object(obj)

            line.bump_object()

        # Time to get another object?
        elif not segment_list:

            if obj_idx >= stage_obj.dir.inuse:
                break
            dir_entry = stage_obj.dir.get_entry(obj_idx)
            obj = stage_obj.get_object(obj_idx)
            obj_idx += 1
            segment_list = list(segment_factory.parse_segments(obj))

            line.bump_object()

        # Pop off a segment for processing. If it's a tuple then we just
        # finished with the last segment of an imbedded object; restore the
        # previous object/directory entry/line ID so we can continue with it.
        segment = segment_list.pop(0)
        if isinstance(segment, tuple):
            obj, dir_entry, line.object = segment
            continue

        line.bump_segment()
        # Are we done with this object?
        if obj in skip_object:
            continue

        ###### conditions

        # line number
        if (args.line and
                line.object not in args.line and
                line.segment not in args.line):
            continue

        if not conditions.Objects.check(args, dir_entry):
            continue
        if not conditions.Segments.check(args, segment):
            continue
        if not conditions.Attributes.check(args, segment):
            continue

        ###### output section

        output_data.id = args.object and line.object or line.segment

        output_data.obj_name = obj.id.get_name(delim=True)
        output_data.obj_name_nodelim = obj.id.get_name(delim=False)
        output_data.obj_loc = obj.id.location
        output_data.obj_type = obj.id.type
        output_data.obj_status = dir_entry.status
        output_data.obj_version = obj.version.versionvalue
        output_data.obj_store = obj.version.storecandidacy

        output_data.segment_type = segment.get_seg_type()
        output_data.segment_name = segment.__class__.__name__
        output_data.segment_len = segment.get_seg_length()

        # set below when applicable
        output_data.attribute = None

        if args.object is True:
            skip_object.append(obj)
            if args.no_header:
                output_data(obj.get_data())
            else:
                output_data(obj.get_data(with_header=True))

        elif args.segment is True:
            if args.no_header:
                output_data(segment.get_data())
            else:
                output_data(segment.get_data(with_header=True))

        elif args.attribute:

            # TODO: test
            if '*' in args.attribute:
                attributes = [attr for attr in segment.__dict__.keys()
                              if not attr.startswith('_')]
            else:
                attributes = [attr for attr in args.attribute
                              if hasattr(segment, attr)]

            for attr in attributes:
                output_data.attribute = attr
                output_data(getattr(segment, attr))


def main():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.convert_arg_line_to_args = arghelpers.convert_arg_line_to_args
    parser.add_argument('--version', action='version', version='%(prog)s ' +
                                                               VERSION)

    subparsers = parser.add_subparsers(
        dest='subparser_name',
        title='subcommands',
        description='valid subcommands',
        help='SUBCOMMAND --help for more options'
    )

    ######
    view_subparser = subparsers.add_parser('view')
    view_subparser.set_defaults(func=view)
    view_subparser.add_argument('stagefile', type=argparse.FileType('rb'))

    ######
    dir_subparser = subparsers.add_parser(
        'dir',
        parents=[conditions.Objects.get_parser()]
    )
    dir_subparser.set_defaults(func=directory)
    dir_subparser.add_argument('--no-header', action='store_true',
                               help='suppress column header')
    dir_subparser.add_argument('--skip-imbedded', action='store_true',
                               help="don't process imbedded objects")
    dir_subparser.add_argument('stagefile', type=argparse.FileType('rb'))

    ######
    extract_subparser = subparsers.add_parser(
        'extract',
        parents=[conditions.Objects.get_parser(),
                 conditions.Segments.get_parser(),
                 conditions.Attributes.get_parser()]
    )
    extract_subparser.set_defaults(func=extract)
    extract_subparser.add_argument('--line', typecode='H', metavar='RANGE',
                                   action=arghelpers.ArrayRangeAction,
                                   help='line number')
    extract_subparser.add_argument('--output-dir', required=True,
                                   metavar='DIR', help='output directory')
    extract_subparser.add_argument('--name-format', default=None,
                                   help='output file name format',
                                   metavar='FORMAT')
    extract_subparser.add_argument('--object', action='store_true',
                                   help='output objects')
    extract_subparser.add_argument('--segment', action='store_true',
                                   help='output segments')
    extract_subparser.add_argument('--attribute', help='output attributes',
                                   action=arghelpers.ListAction,
                                   metavar='LIST')
    extract_subparser.add_argument('--force', action='store_true',
                                   help='clobber existing output files')
    extract_subparser.add_argument('--no-header', action='store_true',
                                   help='suppress object/segment headers')
    extract_subparser.add_argument('--skip-imbedded', action='store_true',
                                   help="don't process imbedded objects")
    extract_subparser.add_argument('stagefile', type=argparse.FileType('rb'))

    ######
    seg_types_subparser = subparsers.add_parser('list-segment-types')
    seg_types_subparser.set_defaults(func=list_segment_types)

    ######
    show_fat_subparser = subparsers.add_parser('show-aum')
    show_fat_subparser.set_defaults(func=show_aum)
    show_fat_subparser.add_argument('--no-symbols', action='store_true',
                                    help='show raw values')
    show_fat_subparser.add_argument('stagefile', type=argparse.FileType('rb'))

    # Do it!
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
