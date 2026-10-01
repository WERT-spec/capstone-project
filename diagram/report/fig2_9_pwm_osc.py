"""圖2.9 鋸齒波產生器（依 hspice/sub_system.net 的 .SUBCKT PWM_OSC 繪製；比較器 CMP01 以符號表示）。
Run: python diagram/report/fig2_9_pwm_osc.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import Sch, elm

OUT = Path(__file__).resolve().parent
s = Sch(); A, P, W = s.A, s.P, s.wire
YB, XM = 5.0, 3.0              # RAMP bus, M1/M2 column
YV = YB + 2.0

m1 = A(elm.PFet(bulk=False).right().reverse().anchor('source').at((XM, YV)))
W(P(m1, 'drain'), (XM, YB)); s.vdd((XM, YV))
s.lab((XM + 0.3, P(m1, 'gate')[1]), 'M1')
g1 = P(m1, 'gate'); W(g1, (g1[0] - 0.8, g1[1])); s.port((g1[0] - 0.8, g1[1]), 'VBIAS', 'left')

m2 = A(elm.NFet(bulk=False).right().reverse().anchor('drain').at((XM, YB)))   # gate on the left
s.lab((XM + 0.3, P(m2, 'gate')[1]), 'M2')

XC2, XRA = XM + 1.9, XM + 3.0
W((XM - 2.2, YB), (XRA, YB)); s.port((XM - 2.2, YB), 'RAMP', 'left')
s.dot((XM, YB)); s.dot((XC2, YB))
ra = A(elm.Resistor().at((XRA, YB)).right().length(2.0))
s.lab((XRA + 1.0, YB + 0.6), 'RHYS_A', 'center')
XN = XRA + 2.0; s.dot((XN, YB))
cmp_ = A(elm.Opamp(sign=True, leads=True).right().anchor('in1').at((XN + 0.6, YB)))
W((XN, YB), (XN + 0.6, YB))
ip = P(cmp_, 'in2'); W(ip, (ip[0] - 0.6, ip[1])); s.port((ip[0] - 0.6, ip[1]), 'VREF', 'left')
o = P(cmp_, 'out'); XK = o[0] + 0.8
W(o, (XK, o[1])); s.dot((XK, o[1]))
s.lab((XN + 2.2, o[1] - 1.25), 'CMP', 'center', fs=13)
YTOP = YB + 1.5
W((XN, YB), (XN, YTOP))
A(elm.Resistor().at((XN, YTOP)).right().to((XK, YTOP)))
s.lab(((XN + XK) / 2, YTOP + 0.6), 'RHYS_B', 'center')
W((XK, YTOP), (XK, o[1]))
W((XK, o[1]), (XK + 1.0, o[1])); s.port((XK + 1.0, o[1]), 'CLK', 'right')

# CLK back to the M2 gate along a line under the comparator
YR = P(m2, 'source')[1] - 0.7
g2 = P(m2, 'gate'); xg = g2[0] - 0.4
W((XK, o[1]), (XK, YR), (xg, YR), (xg, g2[1]), g2)

# ground: M2 source and C2
YG = YR - 1.4
W(P(m2, 'source'), (XM, YG))
A(elm.Capacitor().at((XC2, YB)).down().to((XC2, YR + 0.35))); W((XC2, YR + 0.35), (XC2, YG)); s.lab((XC2 + 0.45, (YB + YR) / 2 + 0.15), 'C2')
W((XM, YG), (XC2, YG)); s.gnd((XM, YG), True)
s.save(OUT / 'fig2_9_pwm_osc')
