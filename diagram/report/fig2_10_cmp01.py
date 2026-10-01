"""圖 比較器電路 CMP01（依 hspice/sub_system.net 的 .SUBCKT CMP01 繪製，元件名稱去掉 M_ 前綴）。
Run: python diagram/report/fig2_10_cmp01.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import Sch, elm

OUT = Path(__file__).resolve().parent
s = Sch(); A, P, W = s.A, s.P, s.wire
YV, YG = 12.0, 3.6
YT = 10.0            # N_TAIL
YNODE = 7.5          # N_LOAD_L / N_LOAD_R rows
YND = 6.6            # NMOS drains
PF = lambda x, y, gate_left=True: A((elm.PFet(bulk=False).right().reverse() if gate_left else elm.PFet(bulk=False).right()).anchor('source').at((x, y)))
NF = lambda x, y, gate_left=True: A((elm.NFet(bulk=False).right().reverse() if gate_left else elm.NFet(bulk=False).right()).anchor('drain').at((x, y)))

# ---- tail + input pair
XB, XP3, XP4 = 5.0, 2.5, 7.5
mb = PF(XB, YV); s.lab((XB + 0.3, P(mb, 'gate')[1]), 'MB')
g = P(mb, 'gate'); W(g, (g[0] - 0.8, g[1])); s.port((g[0] - 0.8, g[1]), 'VB', 'left')
W(P(mb, 'drain'), (XB, YT)); s.dot((XB, YT)); W((XP3, YT), (XP4, YT))
mp3 = PF(XP3, YT, True); mp4 = PF(XP4, YT, False)
g = P(mp3, 'gate'); W(g, (g[0] - 0.7, g[1])); s.port((g[0] - 0.7, g[1]), 'VIN+', 'left')
g = P(mp4, 'gate'); W(g, (g[0] + 0.7, g[1])); s.port((g[0] + 0.7, g[1]), 'VIN−', 'right')
s.lab((XP3 + 0.3, P(mp3, 'gate')[1]), 'MP3'); s.lab((XP4 - 0.3, P(mp4, 'gate')[1]), 'MP4', 'right')
W(P(mp3, 'drain'), (XP3, YNODE)); W(P(mp4, 'drain'), (XP4, YNODE))

# ---- loads: MN2 (diode) MN4 (cross) | MN3 (cross) MN5 (diode)
X2, X4, X3, X5 = 1.5, 3.5, 6.5, 8.5
W((X2, YNODE), (X4, YNODE)); W((X3, YNODE), (X5, YNODE))
s.dot((XP3, YNODE)); s.dot((XP4, YNODE))
mn2 = NF(X2, YND, False); mn4 = NF(X4, YND, False); mn3 = NF(X3, YND, True); mn5 = NF(X5, YND, True)
for x in (X2, X4, X3, X5):
    W((x, YNODE), (x, YND))
YX = 7.05
g = P(mn2, 'gate'); W(g, (g[0], YX), (X2, YX)); s.dot((X2, YX))                 # MN2 diode
g = P(mn5, 'gate'); W(g, (g[0], YX), (X5, YX)); s.dot((X5, YX))                 # MN5 diode
W(P(mn4, 'gate'), (X3, YX)); s.dot((X3, YX))                                     # MN4 gate -> N_LOAD_R
W(P(mn3, 'gate'), (X4, YX)); s.dot((X4, YX))                                     # MN3 gate -> N_LOAD_L
s.lab((X2 - 0.3, P(mn2, 'gate')[1]), 'MN2', 'right'); s.lab((X4 - 0.15, P(mn4, 'gate')[1] - 0.95), 'MN4', 'right')
s.lab((X3 + 0.15, P(mn3, 'gate')[1] - 0.95), 'MN3'); s.lab((X5 + 0.15, P(mn5, 'gate')[1] - 0.95), 'MN5')

# ---- output stage: MP2 / MN6 (gate R) -> N_COMP_OUT,  MP1 (diode) / MN1 (gate L) -> N_PGATE
XO1, XO2 = 11.4, 14.6          # XO1: MP2/MN6 column, XO2: MP1/MN1 column
mp2 = PF(XO1, YV, False); mp1 = PF(XO2, YV, True)
W(P(mp2, 'gate'), P(mp1, 'gate'))
xm = (P(mp2, 'gate')[0] + P(mp1, 'gate')[0]) / 2; s.dot((xm, P(mp1, 'gate')[1]))
yd = P(mp1, 'drain')[1] - 0.45
W((xm, P(mp1, 'gate')[1]), (xm, yd), (XO2, yd)); s.dot((XO2, yd))
mn6 = NF(XO1, YND, True); mn1 = NF(XO2, YND, True)
W(P(mp2, 'drain'), P(mn6, 'drain')); W(P(mp1, 'drain'), P(mn1, 'drain'))
s.lab((XO1 - 0.3, P(mp2, 'gate')[1]), 'MP2', 'right'); s.lab((XO2 + 0.3, P(mp1, 'gate')[1]), 'MP1')
s.lab((XO1 + 0.3, P(mn6, 'gate')[1] - 0.95), 'MN6'); s.lab((XO2 + 0.3, P(mn1, 'gate')[1] - 0.95), 'MN1')
YLR = 8.05
xa = P(mn1, 'gate')[0] - 0.35
W((XP3, YLR), (xa, YLR), (xa, P(mn1, 'gate')[1]), P(mn1, 'gate')); s.dot((XP3, YLR))          # N_LOAD_L -> MN1
xb = P(mn6, 'gate')[0] - 0.35
W((X5, YNODE), (xb, YNODE), (xb, P(mn6, 'gate')[1]), P(mn6, 'gate'))                         # N_LOAD_R -> MN6

# ---- two inverter buffers (input N_COMP_OUT taken from the MP2/MN6 column)
YM = 9.1
XI1, XI2 = 18.4, 21.8
prev = (XO1, YM); s.dot(prev)
invs = []
for xi, pn, nn in ((XI1, 'MP5', 'MN7'), (XI2, 'MP6', 'MN8')):
    mp = PF(xi, YV, True); mn = NF(xi, YND, True); invs.append((xi, mn))
    W(P(mp, 'drain'), P(mn, 'drain'))
    xg = P(mp, 'gate')[0] - 0.3
    W(P(mp, 'gate'), (xg, P(mp, 'gate')[1]), (xg, P(mn, 'gate')[1]), P(mn, 'gate'))
    W(prev, (xg, YM)); s.dot((xg, YM))
    s.lab((xi + 0.3, P(mp, 'gate')[1]), pn); s.lab((xi + 0.3, P(mn, 'gate')[1]), nn)
    prev = (xi, YM); s.dot(prev)
W(prev, (prev[0] + 1.2, YM)); s.port((prev[0] + 1.2, YM), 'VOUT', 'right')

# ---- rails
W((X2 - 0.5, YG), (XI2 + 0.5, YG))
for x, m in ((X2, mn2), (X4, mn4), (X3, mn3), (X5, mn5), (XO1, mn6), (XO2, mn1)) + tuple(invs):
    W(P(m, 'source'), (x, YG))
W((XB, YV), (XI2, YV))
s.vdd(((XB + XO1) / 2, YV)); s.gnd(((X2 + XI2) / 2, YG), True)
s.save(OUT / 'fig2_10_cmp01')
