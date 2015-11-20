import argparse
import array


class ArrayRangeAction(argparse.Action):
    def __init__(self, *args, typecode='I', **kwargs):
        super().__init__(*args, **kwargs)
        assert typecode.isupper(), 'no unsigned types allowed'
        self.typecode = typecode

    def __call__(self, parser, namespace, arg_value, option_string=None):
        dest = getattr(namespace, self.dest)
        if not dest:
            dest = array.array(self.typecode)
        for arg in arg_value.split(','):
            low, sep, high = arg.partition('-')
            try:
                if not sep:
                    dest.append(int(arg, 0))
                else:
                    # range is inclusive
                    dest.extend(range(int(low, 0), int(high, 0) + 1))
            except OverflowError:
                raise argparse.ArgumentError(self,
                                             'value(s) must be >= 0 and <= {}'
                                             .format
                                             ((1 << dest.itemsize * 8) - 1))
            except ValueError:
                raise argparse.ArgumentError(self, 'invalid range')
        setattr(namespace, self.dest, dest)


class ListAction(argparse.Action):
    def __call__(self, parser, namespace, arg_value, option_string=None):

        dest = getattr(namespace, self.dest)
        if not dest:
            dest = []
        if isinstance(arg_value, list):
            dest.extend(arg_value)
        else:
            dest.extend(arg_value.split(','))
        setattr(namespace, self.dest, dest)


def integer_type(s):
    try:
        return int(s, 0)
    except ValueError:
        raise argparse.ArgumentTypeError('{} cannot be converted to an integer'
                                         .format(s))


def true_false_other_type(s):
    b = s.lower()
    if b == 'true':
        return True
    elif b == 'false':
        return False
    else:
        return s


def convert_arg_line_to_args(arg_line):
    for arg in arg_line.split():
        if not arg.strip():
            continue
        yield arg
