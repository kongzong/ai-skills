#!/usr/bin/env python3
"""Find glyph codepoints in a TTF by name substring — pure Python, no deps.

Parses cmap (format 12 or 4) + post (format 2.0) tables to map codepoints to
glyph names. Needed because memorized nerd-font/MDI codepoints are unreliable
(e.g. U+F1954 is md-sphere, not alarm).

Usage:
  python3 find_glyph.py /path/to/Font.ttf <substring> [substring2 ...]
  python3 find_glyph.py /usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf alarm

Output lines: "U+XXXXX  <glyph-name>", plus a QML surrogate-escape hint for
codepoints >= U+10000.
"""
import struct
import sys


def read_name_tables(path):
    data = open(path, "rb").read()
    num_tables = struct.unpack(">H", data[4:6])[0]
    tables = {}
    for i in range(num_tables):
        off = 12 + i * 16
        tag, _, toff, tlen = struct.unpack(">4sIII", data[off:off + 16])
        tables[tag.decode()] = (toff, tlen)
    return data, tables


def build_cp2gid(data, tables):
    cmap_off = tables["cmap"][0]
    n = struct.unpack(">H", data[cmap_off + 2:cmap_off + 4])[0]
    sub = None
    fallback = None
    for i in range(n):
        _, _, so = struct.unpack(">HHI", data[cmap_off + 4 + i * 8:cmap_off + 12 + i * 8])
        fmt = struct.unpack(">H", data[cmap_off + so:cmap_off + so + 2])[0]
        if fmt == 12:
            sub = cmap_off + so
            break
        if fmt == 4:
            fallback = cmap_off + so
    cp2gid = {}
    if sub is not None:
        ngroups = struct.unpack(">I", data[sub + 12:sub + 16])[0]
        for i in range(ngroups):
            s, e, g = struct.unpack(">III", data[sub + 16 + i * 12:sub + 28 + i * 12])
            if e - s > 50000:
                continue
            for cp in range(s, e + 1):
                cp2gid[cp] = g + (cp - s)
    elif fallback is not None:
        b = fallback
        seg_x2 = struct.unpack(">H", data[b + 6:b + 8])[0]
        segs = seg_x2 // 2
        ends = struct.unpack(f">{segs}H", data[b + 14:b + 14 + seg_x2])
        starts = struct.unpack(f">{segs}H", data[b + 16 + seg_x2:b + 16 + seg_x2 * 2])
        deltas = struct.unpack(f">{segs}h", data[b + 16 + seg_x2 * 2:b + 16 + seg_x2 * 3])
        rng_base = b + 16 + seg_x2 * 3
        rngs = struct.unpack(f">{segs}H", data[rng_base:rng_base + seg_x2])
        for i in range(segs):
            for cp in range(starts[i], min(ends[i], 0xFFFF) + 1):
                if rngs[i] == 0:
                    g = (cp + deltas[i]) & 0xFFFF
                else:
                    gi = rng_base + i * 2 + rngs[i] + (cp - starts[i]) * 2
                    g = struct.unpack(">H", data[gi:gi + 2])[0]
                    if g:
                        g = (g + deltas[i]) & 0xFFFF
                if g:
                    cp2gid[cp] = g
    return cp2gid


def build_gid2name(data, tables, nglyphs_hint=None):
    post_off, post_len = tables["post"]
    ver = struct.unpack(">I", data[post_off:post_off + 4])[0]
    gid2name = {}
    if ver != 0x00020000:
        return gid2name  # post v3 has no names
    nglyphs = struct.unpack(">H", data[post_off + 32:post_off + 34])[0]
    idx = struct.unpack(f">{nglyphs}H", data[post_off + 34:post_off + 34 + nglyphs * 2])
    # Standard Macintosh order (first 258) — abbreviated set suffices for matching;
    # custom pool covers everything beyond.
    std = [".notdef"]
    q = post_off + 34 + nglyphs * 2
    end = post_off + post_len
    pool = {}
    si = 258
    while q < end:
        ln = data[q]
        if ln == 0:
            break
        pool[si] = data[q + 1:q + 1 + ln].decode("latin1")
        si += 1
        q += 1 + ln

    def name_of(gid):
        if gid >= len(idx):
            return None
        ni = idx[gid]
        if ni < 258:
            return None if ni >= len(std) else std[ni]
        return pool.get(ni)

    for gid in range(nglyphs):
        nm = name_of(gid)
        if nm:
            gid2name[gid] = nm
    return gid2name


def surrogate_escape(cp):
    v = cp - 0x10000
    hi = 0xD800 + (v >> 10)
    lo = 0xDC00 + (v & 0x3FF)
    return f'"\\u{hi:04X}\\u{lo:04X}"'


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    path, needles = sys.argv[1], [s.lower() for s in sys.argv[2:]]
    data, tables = read_name_tables(path)
    cp2gid = build_cp2gid(data, tables)
    gid2name = build_gid2name(data, tables)
    hits = []
    for cp, g in sorted(cp2gid.items()):
        nm = gid2name.get(g)
        if nm and any(t in nm.lower() for t in needles):
            hits.append((cp, nm))
    print(f"# mapped codepoints: {len(cp2gid)}, named glyphs: {len(gid2name)}, hits: {len(hits)}")
    for cp, nm in hits:
        hint = f"  QML: {surrogate_escape(cp)}" if cp >= 0x10000 else "  QML: literal char ok"
        print(f"U+{cp:05X}  {nm}{hint}")


if __name__ == "__main__":
    main()
