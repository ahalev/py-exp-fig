import re
import sys
from io import StringIO, TextIOBase, TextIOWrapper
from contextlib import ContextDecorator
from enum import IntEnum
from typing import Union


class TapeRecorder(ContextDecorator):
    _dest: 'Union[TextIOWrapper, None]'
    _string: 'StringIO' = None
    _stdout: '_IOList' = None
    _stderr: '_IOList' = None

    def __init__(self, dest=None):
        super().__init__()
        self._dest = None
        self._status = TapeStatus.UNOPENED

        if dest is not None:
            self._init(dest)

    def _init(self, dest=None):
        self._dest = None
        self._string = StringIO()

        if dest is not None:
            self.add_file(dest)

        self._stdout = _IOList(sys.stdout, self.destination)
        self._stderr = _IOList(sys.stderr, self.destination)
        self._status = TapeStatus.INITIALIZED

    def reset(self, dest=None):
        if dest is not None:
            self.add_file(dest, copy_history=False)
        else:
            new_string = StringIO()
            self._replace_destination(new_string)

            self._dest = None
            self._string = new_string

        self._status = TapeStatus.INITIALIZED

    def add_file(self, file_like, copy_history=True):
        if not isinstance(file_like, TextIOBase):
            file_like = open(file_like, 'w')

        if self._status >= TapeStatus.INITIALIZED:
            if copy_history:
                file_like.write(self.read_tape())
                file_like.flush()

            if not self._string.closed:
                self._string.close()

        self.set_dest(file_like)

    def set_dest(self, dest):
        self._replace_destination(dest)
        self._dest = dest

    def _replace_destination(self, new_destination):
        if self._stdout is not None:
            self._stdout.replace(self.destination, new_destination)

        if self._stderr is not None:
            self._stderr.replace(self.destination, new_destination)

    def read_tape(self):
        if self._dest is None:
            try:
                return self._string.getvalue()
            except ValueError:
                raise ValueError('Attempting to read from never-entered tape.')

        with open(self._dest.name, 'r') as f:
            return f.read()

    @property
    def destination(self):
        return self._dest or self._string

    @destination.setter
    def destination(self, value):
        self.set_dest(value)

    @property
    def status(self):
        return self._status

    def record(self, dest=None, copy_history=True):
        self.__enter__(dest, copy_history)

    def end_record(self):
        self.__exit__(None, None, None)

    def __del__(self):
        self.__exit__(None, None, None)

    def __enter__(self, dest=None, copy_history=True):
        if self._status == TapeStatus.UNOPENED:
            self._init(dest)
        elif self._status == TapeStatus.CLOSED:
            self.reset(dest)
        elif dest is not None:
            self.add_file(dest, copy_history=copy_history)

        for cm in (self._stdout, self._stderr):
            cm.__enter__()

        self._status = TapeStatus.ACTIVE

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for cm in (self._stdout, self._stderr):
            cm.__exit__(exc_type, exc_val, exc_tb)

        self._status = TapeStatus.CLOSED


class _IOList(TextIOBase):
    def __init__(self, original_stream, *io_streams):
        self._original_stream = original_stream
        self._io_streams = set(io_streams)

        self._original_write = self._original_stream.write
        self._original_flush = self._original_stream.flush

    def write(self, line):
        o = [self._original_write(line)] + [s.write(escape_ansi(line)) for s in self._io_streams]
        return max(o)

    def flush(self):
        self._original_flush()

        for s in self._io_streams:
            s.flush()

    def close(self):
        for s in self._io_streams:
            s.close()

    def add(self, stream):
        self._io_streams.add(stream)

    def remove(self, stream):
        self._io_streams.remove(stream)

    def replace(self, old, new):
        self._io_streams.remove(old)
        self._io_streams.add(new)

    def __contains__(self, item):
        return self._io_streams.__contains__(item)

    def __enter__(self):
        self._original_stream.write = self.write
        self._original_stream.flush = self.flush
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._original_stream.write = self._original_write
        self._original_stream.flush = self._original_flush
        self.close()


class TapeStatus(IntEnum):
    UNOPENED = -2
    INITIALIZED = -1
    ACTIVE = 0
    CLOSED = 1


def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)
