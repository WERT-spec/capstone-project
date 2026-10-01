"""圖2.6 軟啟動電路（依 hspice/sub_system.net 的 .SUBCKT SOFT_START 繪製；比較器與緩衝器 CMP01_BG 以符號表示）。
Run: python diagram/report/fig2_6_softstart.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import Sch, elm, lg

OUT = Path(__file__).resolve().parent
s = Sch(); A, P, W = s.A, s.P, s.wire

YV, YB, YG = 10.0, 6.0, 0.6      # VDD, VC1 bus, ground rail
X1 = 0.6                         # M1 / C1 column
XT = 6.0                         # tap feeding BUF '+' and CMP '+'

# M1 : PMOS current source (gate VB1) charging C1
m1 = A(elm.PFet(bulk=False).right().reverse().anchor('source').at((X1, YV)))
s.vdd((X1, YV))
s.lab((X1 + 0.3, P(m1, 'gate')[1]), 'M1')
g = P(m1, 'gate'); W(g, (g[0] - 0.8, g[1])); s.port((g[0] - 0.8, g[1]), 'VB1', 'left')
W(P(m1, 'drain'), (X1, YB)); s.dot((X1, YB))
A(elm.Capacitor().at((X1, YB)).down().to((X1, YG))); s.lab((X1 + 0.45, (YB + YG) / 2), 'C1')

# BUF (unity gain) on top: '+' from the VC1 bus, '-' tied to its output
buf = A(elm.Opamp(sign=True, leads=True).right().anchor('in2').at((XT + 0.6, YB + 1.6)))
ip, im, o = P(buf, 'in2'), P(buf, 'in1'), P(buf, 'out')
W((XT, YB), (XT, ip[1]), ip); s.dot((XT, YB))
W(im, (im[0] - 0.5, im[1]), (im[0] - 0.5, im[1] + 0.8), (o[0] + 0.5, im[1] + 0.8), (o[0] + 0.5, o[1]))
W(o, (o[0] + 0.5, o[1])); s.dot((o[0] + 0.5, o[1]))
s.lab((ip[0] + 1.25, o[1]), 'BUF', 'center', fs=12)

# CMP below: '+' = VC1, '-' = VREF_FIX ; output -> INV -> M2 gate
cmpo = A(elm.Opamp(sign=True, leads=True).right().flip().anchor('in2').at((XT + 0.6, YB - 2.4)))
cp, cm, co = P(cmpo, 'in2'), P(cmpo, 'in1'), P(cmpo, 'out')
W((XT, YB), (XT, cp[1]), cp)
W(cm, (cm[0] - 2.2, cm[1])); s.port((cm[0] - 2.2, cm[1]), 'VREF_FIX', 'left')
s.lab((cp[0] + 1.25, co[1]), 'CMP', 'center', fs=12)
inv = A(lg.Not().right().anchor('in1').at((co[0] + 0.4, co[1])))
W(co, P(inv, 'in1'))
X2 = P(inv, 'out')[0] + 0.25 + 1.37
m2 = A(elm.NFet(bulk=False).right().reverse().anchor('gate').at((P(inv, 'out')[0] + 0.25, co[1])))
W(P(inv, 'out'), P(m2, 'gate'))
s.lab((P(m2, 'drain')[0] + 0.3, co[1]), 'M2')
W(P(m2, 'drain'), (P(m2, 'drain')[0], YB))
W(P(m2, 'source'), (P(m2, 'source')[0], YG))
X2 = P(m2, 'drain')[0]
W((X1, YB), (X2, YB))                       # VC1 bus

# RA + C2 -> VREF
XV = X2 + 1.8
ra = A(elm.Resistor().at((o[0] + 0.5, o[1])).right().to((XV, o[1])))
s.lab(((o[0] + 0.5 + XV) / 2, o[1] + 0.6), 'RA', 'center')
s.dot((XV, o[1]))
A(elm.Capacitor().at((XV, o[1])).down().to((XV, YG))); s.lab((XV + 0.45, (o[1] + YG) / 2), 'C2')
W((XV, o[1]), (XV + 1.0, o[1])); s.port((XV + 1.0, o[1]), 'VREF', 'right')

W((X1, YG), (XV, YG)); s.gnd(((X1 + XV) / 2, YG), True)
s.save(OUT / 'fig2_6_softstart')
