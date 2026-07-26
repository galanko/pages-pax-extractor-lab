"""Hand-built POSIX ustar headers. Needed for cell v, because the
'prefix' field (offset 345, 155 bytes) is the OTHER place the real member name
lives: POSIX says name = prefix + '/' + name when prefix is non-empty, and no
mainstream tar writer will put '..' there for you."""
import time

def hdr(name, size, typeflag=b'0', prefix=b'', mode=0o644, mtime=None):
    if mtime is None:
        mtime = int(time.time())
    b = bytearray(b'\0' * 512)
    def put(off, val, ln):
        v = val if isinstance(val, bytes) else val.encode()
        assert len(v) <= ln, (off, v)
        b[off:off + len(v)] = v
    put(0,   name,                        100)
    put(100, "%07o\0" % mode,               8)
    put(108, "%07o\0" % 0,                  8)
    put(116, "%07o\0" % 0,                  8)
    put(124, "%011o\0" % size,             12)
    put(136, "%011o\0" % mtime,            12)
    b[148:156] = b' ' * 8                       # checksum field = spaces while summing
    put(156, typeflag,                      1)
    put(257, b'ustar\0',                    6)
    put(263, b'00',                         2)
    put(345, prefix,                      155)
    chk = sum(b)
    b[148:156] = ("%06o\0 " % chk).encode()
    return bytes(b)

def pad(data):
    r = len(data) % 512
    return data + (b'\0' * (512 - r) if r else b'')
