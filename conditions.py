import argparse
import fnmatch
import codecs

from prodigyclassic.stage import segments
from prodigyclassic.stage import structures
import arghelpers


class Objects:
    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--obj-delim',
                            type=arghelpers.true_false_other_type,
                            default='.', metavar='CHAR',
                            help='delimiter to use in object names')
        parser.add_argument('--obj-nonascii',
                            type=arghelpers.true_false_other_type, 
                            default='_', metavar='CHAR',
                            help='character to use for non-printable '
                                 'characters in object names')

        parser.add_argument('--obj-name', action=arghelpers.ListAction,
                            help='object name', metavar='LIST')
        parser.add_argument('--obj-type', action=arghelpers.ArrayRangeAction,
                            typecode='B', help='object type',
                            metavar='RANGE')
        parser.add_argument('--obj-loc', action=arghelpers.ArrayRangeAction,
                            typecode='B', help='object location in set',
                            metavar='RANGE')
        parser.add_argument('--obj-status', action=arghelpers.ArrayRangeAction,
                            typecode='H', help='object status',
                            metavar='RANGE')
        parser.add_argument('--obj-version', typecode='B',
                            help='object version', metavar='RANGE',
                            action=arghelpers.ArrayRangeAction)
        parser.add_argument('--obj-store', action=arghelpers.ArrayRangeAction,
                            typecode='H', help='object storage candidacy',
                            metavar='RANGE')
        parser.add_argument('--obj-min-size', type=arghelpers.integer_type,
                            help='minimum size of object', metavar='INT')
        parser.add_argument('--obj-max-size', type=arghelpers.integer_type,
                            help='maximum size of object', metavar='INT')
        return parser

    @staticmethod
    def check(args, dir_entry):

        # If we were given an object then make a fake directory entry
        if isinstance(dir_entry, structures.Object):
            obj = dir_entry
            dir_entry = structures.DirectoryEntry()
            dir_entry.set_from_object(obj)

        # We allow globbing object names. It's case-insensitive so we convert
        # all names to their natural upper-case versions.
        if args.obj_name:
            n = dir_entry.id.get_name(delim=args.obj_delim).upper()
            match = False
            for name in args.obj_name:
                if fnmatch.fnmatchcase(n, name.upper()):
                    match = True
                    break
            if match is False:
                return False

        if args.obj_loc and dir_entry.id.location not in args.obj_loc:
            return False

        if args.obj_type and dir_entry.id.type not in args.obj_type:
            return False

        if args.obj_status and dir_entry.status not in args.obj_status:
            return False

        if (args.obj_version and
                dir_entry.version_id.versionvalue not in args.obj_version):
            return False

        if (args.obj_store and
                dir_entry.version_id.storecandidacy not in args.obj_store):
            return False

        if args.obj_min_size and dir_entry.length < args.obj_min_size:
            return False

        if args.obj_max_size and dir_entry.length > args.obj_max_size:
            return False

        # Good match
        return True


class Segments:
    @staticmethod
    def get_parser():

        def segment_type(arg_string):

            factory = segments.SegmentFactory()
            name_list = {cls.__name__.lower(): cls.__name__
                         for cls in factory.segment_subclasses.values()}
            # Get the class that's handling unknown segments
            unknown = factory.segment_subclasses[None]
            name_list[unknown.__name__.lower()] = unknown.__name__

            segment_list = []
            for arg in arg_string.lower().split(','):
                if arg[0].isdigit():
                    segment_list.append(int(arg, 0))
                elif arg in name_list:
                    segment_list.append(name_list[arg])
                else:
                    raise argparse.ArgumentTypeError(
                        "'{0}' unknown segment type".format(arg))
            return segment_list

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--seg-type', type=segment_type, metavar='LIST',
                            action=arghelpers.ListAction, help='segment type')
        parser.add_argument('--seg-min-size', type=arghelpers.integer_type,
                            help='minimum size of segment', metavar='INT')
        parser.add_argument('--seg-max-size', type=arghelpers.integer_type,
                            help='maximum size of segment', metavar='INT')

        return parser

    @staticmethod
    def check(args, segment):
        if (args.seg_type and
                segment.__class__.__name__ not in args.seg_type and
                segment._st not in args.seg_type):
            return False

        if args.seg_min_size and segment._sl < args.seg_min_size:
            return False

        if args.seg_max_size and segment._sl > args.seg_max_size:
            return False

        return True


class Attributes:
    @staticmethod
    def get_parser():
        def _attr_type(arg_string):

            # trying to convert strings to integers here can help speed
            # things up

            # TODO: test
            name, sep, val_str = arg_string.partition('=')
            if sep:
                try:
                    val_int = int(val_str, 0)
                except ValueError:
                    val_int = None
                # covert \x65\x66\x67 type encodings
                # TODO: implement elsewhere?
                val_str = codecs.decode(val_str, 'unicode-escape')
            else:
                name = arg_string
                val_str = val_int = None

            return name, val_str, val_int

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--attr', action='append', metavar='STR',
                            type=_attr_type,
                            help='attribute key[=[value]]')
        return parser

    @staticmethod
    def check(args, segment):
        if args.attr:
            for name, val_str, val_int in args.attr:
                if not hasattr(segment, name):
                    return False
                # Are we just checking for the presence of the attribute?
                if val_str is None:
                    continue
                seg_val = getattr(segment, name)
                if isinstance(seg_val, int):
                    if seg_val != val_int:
                        return False
                elif str(seg_val) != val_str:
                    return False
        return True
