"""圖 死區控制電路（依 hspice/sub_system.net 的 .SUBCKT DEAD_ZONE 繪製；DLY_CELL 以方塊表示）。
Run: python diagram/report/fig2_15_deadzone.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import Sch, elm, lg, BLUE

OUT = Path(__file__).resolve().parent
s = Sch(); A, P, W = s.A, s.P, s.wire


def box(xr, y, w, h, name):
    """box whose RIGHT edge centre is (xr, y); returns (left_pt, right_pt)."""
    x0, x1, y0, y1 = xr - w, xr, y - h / 2, y + h / 2
    W((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))
    s.lab(((x0 + x1) / 2 - 0.1, y - 0.1), name, 'center', color=BLUE, fs=12)
    return (x0, y), (x1, y)


YT, YB = 4.0, 0.0
# ---------- top (P) path: NOR1 -> INV1 -> BUF -> VP
nor1 = A(lg.Nor().right().anchor('in1').at((4.0, YT + 0.25)))
inv1 = A(lg.Not().right().anchor('in1').at((7.6, P(nor1, 'out')[1])))
W(P(nor1, 'out'), P(inv1, 'in1'))
buf1 = A(lg.Buf().right().anchor('in1').at((11.4, P(nor1, 'out')[1])))
W(P(inv1, 'out'), P(buf1, 'in1'))
yP = P(buf1, 'out')[1]
XOUT = P(buf1, 'out')[0] + 1.4
W(P(buf1, 'out'), (XOUT, yP)); s.dot((XOUT, yP))
W((XOUT, yP), (XOUT + 1.0, yP)); s.port((XOUT + 1.0, yP), 'VP', 'right')

# ---------- bottom (N) path: INV3 -> NOR2 -> AND(LS_ALLOW) -> BUF -> VN
nor2 = A(lg.Nor().right().anchor('in2').at((5.0, YB - 0.25)))
inv3 = A(lg.Not().right().anchor('out').at((P(nor2, 'in2')[0] - 0.4, P(nor2, 'in2')[1])))
W(P(inv3, 'out'), P(nor2, 'in2'))
andn = A(lg.And().right().anchor('in1').at((8.6, P(nor2, 'out')[1] + 0.25)))
W(P(nor2, 'out'), (P(andn, 'in1')[0] - 0.6, P(nor2, 'out')[1]), (P(andn, 'in1')[0] - 0.6, P(andn, 'in1')[1]), P(andn, 'in1'))
yl = P(andn, 'in2')[1] - 1.1
W(P(andn, 'in2'), (P(andn, 'in2')[0] - 0.3, P(andn, 'in2')[1]), (P(andn, 'in2')[0] - 0.3, yl), (P(andn, 'in2')[0] - 1.6, yl))
s.port((P(andn, 'in2')[0] - 1.6, yl), 'LS_ALLOW', 'left')
buf2 = A(lg.Buf().right().anchor('in1').at((11.4, P(andn, 'out')[1])))
W(P(andn, 'out'), P(buf2, 'in1'))
yN = P(buf2, 'out')[1]
W(P(buf2, 'out'), (XOUT, yN)); s.dot((XOUT, yN))
W((XOUT, yN), (XOUT + 1.0, yN)); s.port((XOUT + 1.0, yN), 'VN', 'right')

# ---------- VDUTY to NOR1 and INV3
X0, XS = 0.0, 1.0
YM = (YT + YB) / 2
W((X0, YM), (XS, YM)); s.port((X0, YM), 'VDUTY', 'left'); s.dot((XS, YM))
W((XS, YM), (XS, P(nor1, 'in1')[1]), P(nor1, 'in1'))
W((XS, YM), (XS, P(inv3, 'in1')[1]), P(inv3, 'in1'))

# ---------- feedback: VP -> DLY_P -> INV2 -> NOR2.in1 ;  VN -> DLY_N -> NOR1.in2
yfp, yfn = YM + 0.6, YM - 0.6
W((XOUT, yP), (XOUT, yfp))
lp, rp = box(XOUT - 0.6, yfp, 2.0, 0.8, 'DLY')
W((XOUT, yfp), rp)
inv2 = A(lg.Not().left().anchor('in1').at((lp[0] - 0.4, yfp)))
W(lp, P(inv2, 'in1'))
xq = P(nor2, 'in1')[0] - 0.9
W(P(inv2, 'out'), (xq, yfp), (xq, P(nor2, 'in1')[1]), P(nor2, 'in1'))
W((XOUT, yN), (XOUT, yfn))
ln, rn = box(XOUT - 0.6, yfn, 2.0, 0.8, 'DLY')
W((XOUT, yfn), rn)
xr = P(nor1, 'in2')[0] - 0.5
W(ln, (xr, yfn), (xr, P(nor1, 'in2')[1]), P(nor1, 'in2'))
s.lab((P(nor1, 'out')[0] + 0.1, P(nor1, 'out')[1] + 0.35), 'A', color='black', fs=12)
s.lab((P(nor2, 'out')[0] + 0.3, P(nor2, 'out')[1] + 0.35), 'E', color='black', fs=12)
s.save(OUT / 'fig2_15_deadzone')
