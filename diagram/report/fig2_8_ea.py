"""圖 誤差放大器與補償網路（依 hspice/sub_system.net 的 .SUBCKT EA 繪製）。
Run: python diagram/report/fig2_8_ea.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import Sch, elm

OUT = Path(__file__).resolve().parent
s = Sch(); A, P, W = s.A, s.P, s.wire
YV, YG = 10.0, 2.8
XL, XC, XR = 2.0, 4.0, 6.0

# tail current source MB (gate VB)
mb = A(elm.PFet(bulk=False).right().reverse().anchor('source').at((XC, YV)))
s.lab((XC + 0.3, P(mb, 'gate')[1]), 'MB')
gb = P(mb, 'gate'); W(gb, (gb[0] - 0.8, gb[1])); s.port((gb[0] - 0.8, gb[1]), 'VB', 'left')
YT = P(mb, 'drain')[1] - 0.5
W(P(mb, 'drain'), (XC, YT)); s.dot((XC, YT))
W((XL, YT), (XR, YT))
s.lab((XC + 0.15, YT + 0.3), 'N_TAIL', color='black', fs=12)

# PMOS input pair
mp3 = A(elm.PFet(bulk=False).right().reverse().anchor('source').at((XL, YT)))
mp4 = A(elm.PFet(bulk=False).right().anchor('source').at((XR, YT)))
g3, g4 = P(mp3, 'gate'), P(mp4, 'gate')
W(g3, (g3[0] - 0.8, g3[1])); s.port((g3[0] - 0.8, g3[1]), 'V+', 'left')
W(g4, (g4[0] + 0.8, g4[1])); s.port((g4[0] + 0.8, g4[1]), 'V−', 'right')
s.lab((XL + 0.3, g3[1]), 'MP3'); s.lab((XR - 0.3, g4[1]), 'MP4', 'right')

# NMOS current-mirror load
YN = P(mp3, 'drain')[1] - 1.4
W(P(mp3, 'drain'), (XL, YN)); W(P(mp4, 'drain'), (XR, YN))
mn2 = A(elm.NFet(bulk=False).right().anchor('drain').at((XL, YN)))      # gate right (diode)
mn1 = A(elm.NFet(bulk=False).right().reverse().anchor('drain').at((XR, YN)))
W(P(mn2, 'gate'), P(mn1, 'gate'))
xm = (P(mn2, 'gate')[0] + P(mn1, 'gate')[0]) / 2
s.dot((xm, P(mn2, 'gate')[1]))
W((xm, P(mn2, 'gate')[1]), (xm, YN + 0.45), (XL, YN + 0.45)); s.dot((XL, YN + 0.45))
s.lab((XL - 0.3, P(mn2, 'gate')[1]), 'MN2', 'right'); s.lab((XR + 0.3, P(mn1, 'gate')[1]), 'MN1')
W(P(mn2, 'source'), (XL, YG)); W(P(mn1, 'source'), (XR, YG))

# output node
YO = YN + 0.45
s.dot((XR, YO))
XO = XR + 1.6
W((XR, YO), (XO, YO)); s.port((XO, YO), 'VOUT', 'right')

s.vdd((XC, YV)); W((XC, YV), (XC, YV))
W((XL - 0.6, YG), (XR + 0.6, YG)); s.gnd(((XL + XR) / 2, YG), True)
s.save(OUT / 'fig2_8_ea')
