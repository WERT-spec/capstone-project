"""圖 多工器電路（依 hspice/sub_system.net 的 .SUBCKT MUX2：INV + 2 x AND2 + OR2）。
Run: python diagram/report/fig2_14_mux2.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import Sch, elm, lg

OUT = Path(__file__).resolve().parent
s = Sch(); A, P, W = s.A, s.P, s.wire
XA = 6.0
anda = A(lg.And().right().anchor('in1').at((XA, 4.25)))
andb = A(lg.And().right().anchor('in1').at((XA, 1.25)))
X0 = 0.0
# PFM_QB -> AND_A.in2 ; PWM_QB -> AND_B.in1
yi = P(anda, 'in1')[1] + 0.7
W((X0, yi), (XA - 0.5, yi), (XA - 0.5, P(anda, 'in1')[1]), P(anda, 'in1')); s.port((X0, yi), 'PFM_QB (INA)', 'left')
W((X0, P(andb, 'in2')[1]), P(andb, 'in2')); s.port((X0, P(andb, 'in2')[1]), 'PWM_QB (INB)', 'left')
# MODE -> INV -> AND_A.in1 ; MODE -> AND_B.in2
YS = (P(anda, 'in2')[1] + P(andb, 'in1')[1]) / 2
XS = 1.2
W((X0, YS), (XS, YS)); s.port((X0, YS), 'MODE (SEL)', 'left'); s.dot((XS, YS))
W((XS, YS), (XS, P(anda, 'in2')[1]))
inv = A(lg.Not().right().anchor('in1').at((XS + 0.6, P(anda, 'in2')[1])))
W((XS, P(anda, 'in2')[1]), P(inv, 'in1'))
W(P(inv, 'out'), P(anda, 'in2'))
s.lab(((P(inv, 'out')[0] + XA) / 2, P(anda, 'in2')[1] - 0.3), 'SELB', 'center', color='black', fs=12)
W((XS, YS), (XS, P(andb, 'in1')[1]), P(andb, 'in1'))
# OR
XO = P(anda, 'out')[0] + 1.6
orr = A(lg.Or().right().anchor('in1').at((XO, YS + 0.25)))
XJ = XO - 0.7
W(P(anda, 'out'), (XJ, P(anda, 'out')[1]), (XJ, P(orr, 'in1')[1]), P(orr, 'in1'))
W(P(andb, 'out'), (XJ + 0.35, P(andb, 'out')[1]), (XJ + 0.35, P(orr, 'in2')[1]), P(orr, 'in2'))
s.lab((P(anda, 'out')[0] + 0.2, P(anda, 'out')[1] + 0.3), 'PA', color='black', fs=12)
s.lab((P(andb, 'out')[0] + 0.2, P(andb, 'out')[1] - 0.3), 'PB', color='black', fs=12)
o = P(orr, 'out'); W(o, (o[0] + 1.2, o[1])); s.port((o[0] + 1.2, o[1]), 'VDUTY_SEL', 'right')
s.save(OUT / 'fig2_14_mux2')
