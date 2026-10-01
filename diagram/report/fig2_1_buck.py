"""圖2.1 同步降壓轉換器基本架構（報告用）。
以 diagram/teacher/sub_arch_teacher 為基礎：上排為功率級，下排為控制（訊號由右往左）。
Run:  python diagram/report/fig2_1_buck.py   ->  fig2_1_buck.svg / .png（輸出在本腳本旁）
"""
from pathlib import Path
import schemdraw
import schemdraw.elements as elm

schemdraw.use('matplotlib')
OUT = Path(__file__).resolve().parent
LBL_DX, LBL_DY = 0.1, 0.1

d = schemdraw.Drawing(show=False)
d.config(unit=2.0, fontsize=10, lw=1.2)
A = d.add
P = lambda e, n: e.absanchors[n]


def poly(*pts):
    for a, b in zip(pts, pts[1:]):
        A(elm.Line().at(a).to(b))


def dot(p):
    A(elm.Dot(radius=0.08).at(p))


def text(p, s, fs=10, halign='center'):
    A(elm.Label().at((p[0] - LBL_DX, p[1] - LBL_DY)).theta(0).label(
        s, loc='center', ofst=(0, 0), halign=halign, valign='center', fontsize=fs))


def box(cx, cy, w, h, name, pins, fs=10, tdx=0.0):
    """pins: list of (name, side, pos) ; slot = 'k/n' (counted bottom->top / left->right)."""
    ic = A(elm.Ic(size=(w, h), pins=[
        elm.IcPin(name=n, side=s, slot=p, anchorname=n, lblsize=8) for n, s, p in pins
    ]).right().at((cx, cy)).anchor('center'))
    text((cx + tdx, cy), name, fs)
    return ic


# ---------------- geometry
Y = 8.0            # power rail
YG = 5.4           # every ground sits here
X_SW = 5.0
X_L2 = X_SW + 3.8  # inductor right end = VOUT node
X_C = X_L2 + 1.0
X_FB = X_C + 2.2
YC = 3.0           # control row centre
H = 2.4            # control box height

# ---------------- power stage
vdd = (0.0, Y)
A(elm.Dot(open=True).at(vdd))
text((vdd[0] - 0.25, Y), 'VDD', 10, halign='right')
mp = A(elm.PFet(bulk=False).up().reverse().anchor('source').at((0.8, Y)))
poly(vdd, P(mp, 'source'))
poly(P(mp, 'drain'), (X_SW, Y))
dot((X_SW, Y))

mn = A(elm.NFet(bulk=False).right().reverse().anchor('drain').at((X_SW, Y)))
poly(P(mn, 'source'), (X_SW, YG))
A(elm.Ground().at((X_SW, YG)))

XL_MID = (X_SW + X_C) / 2           # inductor centred between SW and the output node
poly((X_SW, Y), (XL_MID - 1.0, Y))
A(elm.Inductor2(loops=3).at((XL_MID - 1.0, Y)).right().length(2.0))
poly((XL_MID + 1.0, Y), (X_C, Y))
dot((X_C, Y))
A(elm.Capacitor().at((X_C, Y)).down().to((X_C, YG)))
A(elm.Ground().at((X_C, YG)))

poly((X_C, Y), (X_FB, Y))
dot((X_FB, Y))
YM = (Y + YG) / 2
A(elm.Resistor().at((X_FB, Y)).down().to((X_FB, YM)))
dot((X_FB, YM))
A(elm.Resistor().at((X_FB, YM)).down().to((X_FB, YG)))
A(elm.Ground().at((X_FB, YG)))

TW = 1.3
pend = (X_FB + 2.2, Y)
poly((X_FB, Y), pend)
A(elm.Tag(width=TW).label('VOUT', fontsize=10).left().at((pend[0] + TW, Y)))

# ---------------- control row (right -> left)
X_CTL = X_FB + 2.0
ctl = box(X_CTL, YC, 3.4, H, 'Controller', tdx=0.35, pins=
          [('FB', 'top', '1/1'), ('VDUTY', 'left', '1/1')])
poly((X_FB, YM), (P(ctl, 'FB')[0], YM), P(ctl, 'FB'))

X_DZ = X_CTL - 4.8
dz = box(X_DZ, YC, 3.4, H, 'DEAD_ZONE', tdx=-0.3, pins=
         [('VDUTY', 'right', '1/1'), ('VN', 'left', '2/2'), ('VP', 'left', '1/2')])
poly(P(ctl, 'VDUTY'), P(dz, 'VDUTY'))

gn, gp = P(mn, 'gate'), P(mp, 'gate')
X_DRV = X_DZ - 4.4


def driver(y):
    ic = box(X_DRV, y, 2.2, 0.9, 'Driver', [('in', 'right', '1/1'), ('out', 'left', '1/1')], fs=9)
    return ic


drvn, drvp = driver(P(dz, 'VN')[1]), driver(P(dz, 'VP')[1])
poly(P(dz, 'VN'), P(drvn, 'in'))
poly(P(dz, 'VP'), P(drvp, 'in'))
xgn = gn[0] - 0.9
poly(P(drvn, 'out'), (xgn, P(drvn, 'out')[1]), (xgn, gn[1]), gn)
poly(P(drvp, 'out'), (gp[0], P(drvp, 'out')[1]), gp)

d.save(str(OUT / 'fig2_1_buck.svg'))
d.save(str(OUT / 'fig2_1_buck.png'), dpi=300)
print('saved', OUT / 'fig2_1_buck.png', P(dz,'VN'), P(dz,'VP'), P(drvn, 'out'), xgn)
