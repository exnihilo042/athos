"""Génère les icônes PWA ATHOS — PNG minimal sans dépendance externe"""
import struct, zlib, math

def make_png(size):
    img = []
    cx = cy = size // 2
    r1 = size * 0.42  # cercle principal
    r2 = size * 0.18  # point central

    for y in range(size):
        row = []
        for x in range(size):
            dx, dy = x - cx, y - cy
            dist = math.sqrt(dx*dx + dy*dy)

            if dist > r1:
                row += [8, 8, 8, 0]       # transparent extérieur
            elif dist > r1 - 2:
                t = (dist - (r1-2)) / 2
                a = int(255 * (1-t) * 0.4)
                row += [74, 158, 255, a]   # bordure bleue
            elif dist < r2:
                # Étoile centrale
                row += [74, 158, 255, 200]
            else:
                # Fond sombre avec léger gradient
                factor = 1 - (dist / r1) * 0.3
                v = int(14 * factor)
                row += [v, v, int(v*1.15), 255]
        img.append(row)

    def pack_row(row_data):
        raw = b'\x00' + bytes(row_data)
        return zlib.compress(raw)

    # PNG header
    sig  = b'\x89PNG\r\n\x1a\n'
    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    # IDAT — on compresse toutes les lignes ensemble
    raw = b''
    for row in img:
        raw += b'\x00' + bytes(row)
    idat_data = zlib.compress(raw)

    def chunk(name, data):
        c = struct.pack('>I', len(data)) + name + data
        crc = zlib.crc32(name + data) & 0xffffffff
        return c + struct.pack('>I', crc)

    # IHDR avec color_type=6 (RGBA)
    ihdr_data = struct.pack('>II', size, size) + bytes([8, 6, 0, 0, 0])
    png  = sig
    png += chunk(b'IHDR', ihdr_data)
    png += chunk(b'IDAT', idat_data)
    png += chunk(b'IEND', b'')
    return png

import os
out = os.path.dirname(os.path.abspath(__file__))
for size in [192, 512]:
    with open(f"{out}/icon-{size}.png", "wb") as f:
        f.write(make_png(size))
    print(f"§icon:{size}x{size}:ok")
