"""圖2.6 能隙參考電壓 VREF_FIX 模擬波形（由 hspice/result/sub_system_tb.tr0 讀出）。
Run: python diagram/report/fig_bandgap_wave.py [path/to/sub_system_tb.tr0] -> fig2_6_bandgap_wave.png
"""
import struct, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
TR0 = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT.parents[1] / 'hspice' / 'result' / 'sub_system_tb.tr0'


def read_tr0(path):
    """HSPICE binary .tr0 (2013 format): TIME as float64, other signals float32."""
    b = path.read_bytes(); pos = 0; blocks = []
    while pos < len(b):
        n = struct.unpack('<i', b[pos + 12:pos + 16])[0]
        blocks.append(b[pos + 16:pos + 16 + n]); pos += 20 + n
    hdr = blocks[0].decode('latin1').split('$&%#')[0]
    names = ['TIME'] + hdr.split('TIME', 1)[1].split()
    dt = np.dtype([('TIME', '<f8')] + [(nm, '<f4') for nm in names[1:]])
    raw = b''.join(blocks[1:]); n = len(raw) // dt.itemsize
    a = np.frombuffer(raw[:n * dt.itemsize], dtype=dt)
    return a[a['TIME'] < 1.0]


a = read_tr0(TR0)
t = a['TIME'] * 1e6
v = a['v(x_sys.vref_fix'].astype(float)
avg = v[(t >= 26) & (t <= 31)].mean()

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12})
fig, ax = plt.subplots(figsize=(8.0, 2.4), dpi=250)
ax.plot(t, v, color='#1f4e9c', lw=0.8)
ax.axhline(avg, color='#c0392b', lw=1.0, ls='--')
ax.text(79, 1.206, f'avg = {avg:.4f} V', color='#c0392b', ha='right', va='bottom', fontsize=10)
ax.axvspan(32, 52, color='#999', alpha=0.12, lw=0)
ax.text(42, 1.206, 'ILOAD = 500 mA', ha='center', va='bottom', fontsize=10, color='#444')
ax.set_xlim(0, 80); ax.set_ylim(1.20, 1.29)
ax.set_xlabel('Time (μs)'); ax.set_ylabel('VREF_FIX (V)')
ax.grid(True, lw=0.4, alpha=0.5)
fig.tight_layout()
fig.savefig(OUT / 'fig2_6_bandgap_wave.png')
print('saved', OUT / 'fig2_6_bandgap_wave.png', avg)
