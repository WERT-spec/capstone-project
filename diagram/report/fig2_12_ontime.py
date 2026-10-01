"""圖 導通時間產生器（依 hspice/sub_system.net 的 .SUBCKT TRIANGO_HZ 繪製；比較器 CMP01 以符號表示）。
Run: python diagram/report/fig2_12_ontime.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import Sch, elm

OUT = Path(__file__).resolve().parent
s = Sch(); A, P, W = s.A, s.P, s.wire
YB, YG, XM = 5.0, 1.0, 3.0
YV = YB + 2.0

m1 = A(elm.PFet(bulk=False).right().reverse().anchor('source').at((XM, YV)))
W(P(m1, 'drain'), (XM, YB)); s.vdd((XM, YV))
s.lab((XM + 0.3, P(m1, 'gate')[1]), 'M1')
g1 = P(m1, 'gate'); W(g1, (g1[0] - 0.8, g1[1])); s.port((g1[0] - 0.8, g1[1]), 'VBIAS', 'left')
m2 = A(elm.NFet(bulk=False).right().reverse().anchor('drain').at((XM, YB)))
W(P(m2, 'source'), (XM, YG))
s.lab((XM + 0.3, P(m2, 'gate')[1]), 'M2')
g2 = P(m2, 'gate'); W(g2, (g2[0] - 0.8, g2[1])); s.port((g2[0] - 0.8, g2[1]), 'PFM_QB', 'left')

XC1 = XM + 2.0
W((XM, YB), (XC1 + 3.4, YB)); s.dot((XM, YB)); s.dot((XC1, YB))
A(elm.Capacitor().at((XC1, YB)).down().to((XC1, YG))); s.lab((XC1 + 0.45, (YB + YG) / 2), 'C1')
s.lab((XM + 0.9, YB + 0.3), 'N_C1', color='black', fs=12)

cmp_ = A(elm.Opamp(sign=True, leads=True).right().anchor('in1').at((XC1 + 3.4, YB)))
ip = P(cmp_, 'in2'); W(ip, (ip[0] - 0.8, ip[1])); s.port((ip[0] - 0.8, ip[1]), 'VREF', 'left')
o = P(cmp_, 'out'); W(o, (o[0] + 1.2, o[1])); s.port((o[0] + 1.2, o[1]), 'RAMP_RST', 'right')
s.lab((XC1 + 5.6, o[1] - 1.25), 'CMP', 'center', fs=13)

W((XM - 0.6, YG), (XC1 + 0.6, YG)); s.gnd(((XM + XC1) / 2, YG), True)
s.save(OUT / 'fig2_12_ontime')
