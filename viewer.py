#!/usr/bin/env python3

# THIS ONLY WORKS FOR VERSIONS OF PRODIGY THAT RUN UNDER DOS.


import argparse
import mmap
import sys

from prodigyclassic.stage import stagefile
import arghelpers
import conditions


VERSION = '0.1.0'


class Batcher:
    def __init__(self, filename, config, prompt=False, expert=False,
                 quiet=False):
        self.filename = filename
        self.config = config
        self.prompt = prompt
        self.expert = expert
        self.quiet = quiet
        self.count = 0

        self.fd = open(self.filename, mode='w', newline='\r\n')

    def __enter__(self):
        self.write_header()
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Only write the trailer if there haven't been any problems
        if not exc_type:
            self.write_trailer()
        self.fd.close()

        # DON'T suppress exceptions
        return False

    def batch(self, line=''):
        return self.fd.write(line + '\n')

    def _write_config(self):

        # CONFIG.$$$ must exist, even when there are no options!
        # RS reads only to the first blank line!!!!

        batch = self.batch
        batch('REM  Build base configuration file')
        # Making an empty file that works in all DOSes can be tricky so we'll
        # write a harmless comment. Don't know if the RS considers semi-
        # colons to be comments but they, like invalid keys, are tolerated.
        batch('ECHO ; config file for use with {} > CONFIG.$$$'
              .format(self.filename))
        for k, v in self.config.options:
            if v is not None:
                batch('ECHO {}:{} >> CONFIG.$$$'.format(k, v))
            else:
                batch('ECHO {} >> CONFIG.$$$'.format(k))
        batch()

    def write_header(self):

        batch = self.batch
        batch('@ECHO OFF')
        batch()
        batch('REM  This file was automatically generated with: ')
        batch('REM    {0}'.format(' '.join(sys.argv)))
        batch()
        batch('REM  Make a feeble attempt to keep people from overwriting')
        batch('REM  their legitimate CONFIG.SM file.')
        batch('RENAME CONFIG.SM CONFIG.BCK > NUL')
        batch()
        batch('REM  Just in case you forgot to check it first ...')
        batch('COPY OBJECTS.LOG OBJECTS.OLD > NUL')
        batch('ECHO Objects shown: > OBJECTS.LOG')
        batch()

        self._write_config()

        batch('CLS')

        if self.prompt and not (self.expert or self.quiet):
            batch('ECHO Pressing Y at the Continue prompt will load the '
                  'object.')
            batch('ECHO Pressing N at the Continue prompt will exit.')
            batch('ECHO Pressing S at the Continue prompt will skip to the '
                  'next object.')
            batch('ECHO.')
            batch()

        # This allows jumping to a specific object
        batch('IF NOT "%1"=="" GOTO OBJ%1')
        batch()

        if not (self.expert or self.quiet):
            batch('ECHO If it hangs, OBJECTS.LOG contains a list of objects '
                  'viewed. Specify a ')
            batch('ECHO number on the command line to jump to that object or '
                  'one beyond it.')
            batch('ECHO.')
            # Don't pause here and then again at the Continue prompt.
            if not self.prompt:
                batch('PAUSE')
            batch()

    def add_object(self, obj_id):
        name = obj_id.get_name(delim='.')
        full_name = obj_id.get_id(True)

        # TODO: check source
        if len(name) < 12:
            name += '1'

        self.count += 1
        count = self.count

        batch = self.batch
        batch(':OBJ{}'.format(count))
        if not self.quiet:
            batch('ECHO {:4} - {}'.format(count, full_name))

        if self.prompt:
            batch('CHOICE /C:YNS Continue')
            batch('ECHO.')
            batch('IF ERRORLEVEL == 3 GOTO SKIP{}'.format(count))
            batch('IF ERRORLEVEL == 2 GOTO END')

        batch('COPY CONFIG.$$$ CONFIG.SM > NUL')
        batch('ECHO object:{} >> CONFIG.SM'.format(name))
        batch('ECHO {:4} - {} >> OBJECTS.LOG'.format(count, full_name))
        # Start the Reception System
        batch('RS')
        if not self.quiet:
            batch('ECHO ** That was {} - {}'.format(count, full_name))
        if self.prompt:
            batch(':SKIP{}'.format(count))
        if not self.quiet:
            batch('ECHO.')
        batch()

    def write_trailer(self):

        batch = self.batch
        batch()
        batch(':END')
        batch('DEL CONFIG.$$$ > NUL')
        batch('DEL CONFIG.SM > NUL')
        # Restore the backup
        batch('RENAME CONFIG.BCK CONFIG.SM > NUL')
        if not self.quiet:
            batch('ECHO DONE')
        batch()


class Config:
    def __init__(self):
        self.options = []

    def add_option(self, option, value=None):
        # we append a tuple
        self.options.append((option, value))

    def add_list(self, opt_list, sep=':'):
        for o in opt_list:
            k, s, v = o.partition(sep)
            if not s:
                v = None
            self.add_option(k, v)


def get_args():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                     parents=[conditions.Objects.get_parser()])
    parser.convert_arg_line_to_args = arghelpers.convert_arg_line_to_args
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + VERSION)
    parser.add_argument('--prompt', action='store_true',
                        help='enable prompting between objects')
    parser.add_argument('--quiet', action='store_true',
                        help='suppress most output')
    parser.add_argument('--expert', action='store_true',
                        help='suppress some help messages')
    parser.add_argument('--no-nohang', action='store_true',
                        help='wait for keypress before exiting RS')  # TODO: check
    parser.add_argument('--option', action='append', default=[],
                        help='add option to CONFIG.SM',
                        metavar='KEY[:[VALUE]]')
    parser.add_argument('--start-index', type=int, choices=[0, 1],
                        default=None, help='directory/AUM pair to use')

    parser.add_argument('stagefile', type=argparse.FileType('rb'),
                        help='STAGE.DAT file to use')
    parser.add_argument('batchfile', nargs='?', default='VIEW.BAT',
                        help='name of batch file to create')

    return parser.parse_args()


def load_stage_file(stage_fd):
    stage_map = mmap.mmap(stage_fd.fileno(), 0, access=mmap.ACCESS_READ)
    stage_obj = stagefile.StageFile(stage_map)
    stage_obj.load()
    return stage_obj


def build_config(args):
    config = Config()
    if not args.no_nohang:
        config.add_option('nohang')
    config.add_list(args.option, ':')
    return config


def main():
    args = get_args()
    config = build_config(args)
    stage_obj = load_stage_file(args.stagefile)
    stage_obj.change_index(args.start_index)

    with Batcher(args.batchfile, config, prompt=args.prompt,
                 expert=args.expert, quiet=args.quiet) as batch:
        for i in range(0, stage_obj.dir.inuse):
            dir_entry = stage_obj.dir.get_entry(i)
            if not conditions.Objects.check(args, dir_entry):
                continue
            batch.add_object(dir_entry.id)


if __name__ == '__main__':
    main()
