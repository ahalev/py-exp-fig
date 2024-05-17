import sys
from io import StringIO, TextIOBase, TextIOWrapper
from contextlib import ContextDecorator


class TapeRecorder(ContextDecorator):
    _dest: 'TextIOWrapper' = None
    _string: 'StringIO' = None
    _stdout: '_IOList' = None
    _stderr: '_IOList' = None

    def __init__(self, dest=None):
        super().__init__()
        self._initialized = False

        if dest is not None:
            self._init(dest)

    def _init(self, dest=None):
        self._string = StringIO()

        if dest is not None:
            self.add_file(dest)

        self._stdout = _IOList(sys.stdout, self.destination)
        self._stderr = _IOList(sys.stderr, self.destination)
        self._initialized = True

    def add_file(self, file_like, copy_history=True):
        if not isinstance(file_like, TextIOBase):
            file_like = open(file_like, 'w+')

        if self._initialized:
            if copy_history:
                file_like.write(self._string.getvalue())

            if not self._string.closed:
                self._string.close()

        self.set_dest(file_like)

    def set_dest(self, dest):
        if self._stdout is not None:
            self._stdout.add(dest)
            self._stdout.remove(self.destination)

        if self._stderr is not None:
            self._stderr.add(dest)
            self._stderr.remove(self.destination)

        self._dest = dest

    def read_tape(self):
        if not self._initialized:
            raise RuntimeError('Attempting to read never-initialized tape.')

        if self._dest is None:
            return self._string.getvalue()

        if self._dest.closed:
            with open(self._dest.name, 'r') as f:
                return f.read()

        return self._dest.read()

    @property
    def destination(self):
        return self._dest or self._string

    @destination.setter
    def destination(self, value):
        self.set_dest(value)

    def record(self):
        self.__enter__()

    def end_record(self):
        self.__exit__(None, None, None)

    def __del__(self):
        self.__exit__(None, None, None)

    def __enter__(self, dest=None, copy_history=True):
        if not self._initialized:
            self._init(dest)
        elif dest is not None:
            self.add_file(dest, copy_history=copy_history)

        for cm in (self._stdout, self._stderr):
            cm.__enter__()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for cm in (self._stdout, self._stderr):
            cm.__exit__(exc_type, exc_val, exc_tb)


class _IOList(TextIOBase):
    def __init__(self, original_stream, *io_streams):
        self._original_stream = original_stream
        self._io_streams = set(io_streams)

        self._original_write = self._original_stream.write
        self._original_flush = self._original_stream.flush

    def write(self, line):
        o = [self._original_write(line)] + [s.write(line) for s in self._io_streams]
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

    def __enter__(self):
        self._original_stream.write = self.write
        self._original_stream.flush = self.flush
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._original_stream.write = self._original_write
        self._original_stream.flush = self._original_flush
        self.close()
