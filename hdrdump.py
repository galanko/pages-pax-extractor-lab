#!/usr/bin/env python3
"""Dump the RAW 512-byte ustar header 'name' field (offset 0, len 100) of every
member block in a tar, and separately the name a real tar reader CONSUMES.
This is the whole PoC in one measurement: what a header-string validator sees
vs what the extractor writes."""
import sys, tarfile
p = sys.argv[1]
raw = open(p, "rb").read()
print("== RAW ustar header 'name' fields (what a byte-level validator reads) ==")
off = 0
while off + 512 <= len(raw):
    blk = raw[off:off+512]
    if blk == b"\0" * 512:
        break
    name = blk[0:100].rstrip(b"\0").decode("utf-8", "replace")
    typ = chr(blk[156]) if blk[156] else '0'
    size_field = blk[124:136].rstrip(b"\0 ").decode() or "0"
    try:
        size = int(size_field, 8)
    except ValueError:
        size = 0
    ok_prefix = name.startswith("./")
    no_dotdot = ".." not in name
    print("  off=%-7d type=%s  name=%-58r  starts_with_./=%-5s  no_'..'=%-5s"
          % (off, typ, name, ok_prefix, no_dotdot))
    off += 512 + ((size + 511) // 512) * 512
print("== names a real tar reader CONSUMES (python tarfile) ==")
with tarfile.open(p) as tf:
    for m in tf.getmembers():
        print("  consumed: %r" % m.name)
print("== names GNU tar reports ==")
