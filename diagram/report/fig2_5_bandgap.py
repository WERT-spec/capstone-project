"""圖2.5 能隙參考電壓電路（依 hspice/sub_system.net 的 .SUBCKT BANDGAP 繪製）。
Run: python diagram/report/fig2_5_bandgap.py -> fig2_5_bandgap.png / .svg
"""
from pathlib import Path
import schemdraw
import schemdraw.elements as elm

schemdraw.use('matplotlib')
OUT = Path(__file__).resolve().parent
BLUE = '#1f3fbf'
d = schemdraw.Drawing(show=False)
d.config(unit=2.0, fontsize=15, lw=1.4)
A = d.add
P = lambda e, n: e.absanchors[n]


def wire(*pts):
    for a, b in zip(pts, pts[1:]):
        A(elm.Line().at(a).to(b))


def dot(p):
    A(elm.Dot(radius=0.07).at(p))


def lab(p, s, ha='left'):
    A(elm.Label().at(p).label(s, color=BLUE, halign=ha, fontsize=15))


X0, X1, X2 = 0.0, 5.0, 11.0      # columns: MQ4/MQ2/Q1 | MQ3/MQ1/R1/Q2,Q3 | MQ5/R2/Q4
YV = 12.0                         # VDD rail
YN = 9.6                          # NBIAS / NGATE / VREF node row
YND = 8.8                         # NMOS drains
YG = 3.3                          # ground rail

# ---- VDD rail and PMOS mirror
wire((X0, YV), (X2, YV))
A(elm.Vdd().at(((X0 + X2) / 2, YV)).label('VDD', fontsize=15))
mq4 = A(elm.PFet(bulk=False).right().anchor('source').at((X0, YV)))          # gate right
mq3 = A(elm.PFet(bulk=False).right().reverse().anchor('source').at((X1, YV)))  # gate left
mq5 = A(elm.PFet(bulk=False).right().reverse().anchor('source').at((X2, YV)))  # gate left
wire(P(mq4, 'gate'), P(mq3, 'gate'))
xm = (P(mq4, 'gate')[0] + P(mq3, 'gate')[0]) / 2
dot((xm, P(mq3, 'gate')[1]))
wire((xm, P(mq3, 'gate')[1]), (xm, YN + 0.3), (X1, YN + 0.3))   # MQ3 diode connection (NBIAS)
dot((X1, YN + 0.3))
wire(P(mq5, 'gate'), (P(mq5, 'gate')[0] - 0.9, P(mq5, 'gate')[1]), (P(mq5, 'gate')[0] - 0.9, YN + 0.3), (X1, YN + 0.3))
lab((P(mq4, 'source')[0] - 0.35, P(mq4, 'gate')[1]), 'MQ4', 'right')
lab((X1 + 0.3, P(mq3, 'gate')[1]), 'MQ3')
lab((X2 + 0.3, P(mq5, 'gate')[1]), 'MQ5')
for m, x in ((mq4, X0), (mq3, X1)):
    wire(P(m, 'drain'), (x, YND))

# ---- NMOS pair
mq2 = A(elm.NFet(bulk=False).right().anchor('drain').at((X0, YND)))          # gate right (diode)
mq1 = A(elm.NFet(bulk=False).right().reverse().anchor('drain').at((X1, YND)))  # gate left
wire(P(mq2, 'gate'), P(mq1, 'gate'))
xg = (P(mq2, 'gate')[0] + P(mq1, 'gate')[0]) / 2
dot((xg, P(mq2, 'gate')[1]))
wire((xg, P(mq2, 'gate')[1]), (xg, YND + 0.35), (X0, YND + 0.35))   # MQ2 diode connection (NGATE)
dot((X0, YND + 0.35))
lab((X0 - 0.35, P(mq2, 'gate')[1]), 'MQ2', 'right')
lab((X1 + 0.3, P(mq1, 'gate')[1]), 'MQ1')

# ---- bipolar side
YE = 5.0   # PNP emitter row
def pnp(xe, name):
    q = A(elm.BjtPnp().theta(0).anchor('emitter').at((xe, YE)))
    wire(P(q, 'collector'), (P(q, 'collector')[0], YG))
    wire(P(q, 'base'), (P(q, 'base')[0], YG))
    lab((P(q, 'emitter')[0] + 0.2, P(q, 'base')[1]), name)
    return q
wire(P(mq2, 'source'), (X0, YE))
pnp(X0, 'Q1')
r1 = A(elm.Resistor().at(P(mq1, 'source')).down().to((X1, YE + 0.9)))
lab((X1 + 0.35, (P(mq1, 'source')[1] + YE + 0.9) / 2), 'R1')
wire((X1, YE + 0.9), (X1, YE)); dot((X1, YE + 0.4))
wire((X1, YE + 0.4), (X1 + 3.0, YE + 0.4), (X1 + 3.0, YE))
pnp(X1, 'Q2')
pnp(X1 + 3.0, 'Q3')

wire(P(mq5, 'drain'), (X2, YN + 0.3))
dot((X2, YN + 0.3))
wire((X2, YN + 0.3), (X2 + 1.6, YN + 0.3))
A(elm.Dot(open=True).at((X2 + 1.6, YN + 0.3)))
lab((X2 + 1.85, YN + 0.3), 'VOUT')
A(elm.Resistor().at((X2, YN + 0.3)).down().to((X2, YE)).label('', loc='bot'))
lab((X2 + 0.35, (YN + YE) / 2), 'R2')
pnp(X2, 'Q4')

# ---- ground rail
xl = P(d.elements[0], 'start')[0]
wire((X0 - 0.75, YG), (X2 + 0.75, YG))
A(elm.Ground().at(((X0 + X2) / 2, YG)).label('GND', loc='bottom', fontsize=15))

d.save(str(OUT / 'fig2_5_bandgap.svg'))
d.save(str(OUT / 'fig2_5_bandgap.png'), dpi=300)
print('saved')
