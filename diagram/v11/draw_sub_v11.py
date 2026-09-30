"""Draw the top-level architecture of subckt SUB, PFM v11 (hspice/archive/v11/sub_system.net) with schemdraw.

Run:  python diagram/v11/draw_sub_v11.py
Out:  diagram/v11/sub_arch_v11.svg, diagram/v11/sub_arch_v11.png

Net names follow archive/v11/sub_system.net. Long feedback nets (VOUTR, VOUTR2, SW, MNC,
PG, MODE, ...) are drawn as net-label tags instead of routed wires.

Portrait layout, top to bottom:
  Bias / Reference / Power-good
  Dead time + gate drivers | BUCK power stage + feedback dividers
  PFM zero-cross / diode emulation
  Mode detect + select | PWM loop (upper) / PFM loop (lower)
The PWM/PFM loops flow right-to-left into MUX2; VDUTY_SEL loops back up the
left edge into DEAD_ZONE.
"""
from pathlib import Path

import schemdraw
import schemdraw.elements as elm

OUT = Path(__file__).resolve().parent
TAG_FS = 9
VAL_FS = 9

d = schemdraw.Drawing(show=False)
d.config(unit=2.0, fontsize=10, lw=1.1)
A = d.add


def P(e, name):
    return e.absanchors[name]


def poly(*pts):
    for a, b in zip(pts, pts[1:]):
        A(elm.Line().at(a).to(b))


def dot(p):
    A(elm.Dot(radius=0.08).at(p))


def mktag(name, fs=TAG_FS):
    return elm.Tag(width=0.12 * len(name) * fs / 9 + 0.55).label(name, fontsize=fs)


def tag(p, name, side='left', lead=0.6):
    """Net-label tag attached to point p, extending towards `side`."""
    dx = {'left': -lead, 'right': lead}[side]
    end = (p[0] + dx, p[1])
    A(elm.Line().at(p).to(end))
    t = mktag(name).at(end)
    A(t.left() if side == 'left' else t.right())


def vtag(p, name, dy, side='right'):
    """Vertical stub of length dy from p, then a horizontal tag."""
    end = (p[0], p[1] + dy)
    A(elm.Line().at(p).to(end))
    tag(end, name, side, lead=0.3)


def block(xy, w, h, name, left=(), right=(), top=(), bot=(), fs=10):
    """Ic box centred at xy. Pin lists are given top->bottom / left->right."""
    pins = []
    for side, names in (('left', left), ('right', right)):
        n = len(names)
        for i, nm in enumerate(names):  # slots count bottom->top on sides
            pins.append(elm.IcPin(name=nm, side=side, slot=f'{n - i}/{n}',
                                  anchorname=nm, lblsize=7))
    for side, names in (('top', top), ('bottom', bot)):
        n = len(names)
        for i, nm in enumerate(names):
            pins.append(elm.IcPin(name=nm, side=side, slot=f'{i + 1}/{n}',
                                  anchorname=nm, lblsize=7))
    ic = elm.Ic(size=(w, h), pins=pins).right().at(xy).anchor('center')
    ic.label(name, loc='center', fontsize=fs)
    return A(ic)


def comp(out_xy, name, plus_on_top=False):
    """Right-facing comparator. '+' is anchor in2."""
    op = elm.Opamp(sign=True, leads=True).right().at(out_xy).anchor('out')
    if plus_on_top:
        op.flip()
    op.label(name, loc='center', ofst=(-0.35, 0), fontsize=8)
    return A(op)


def comp_l(out_xy, name):
    """Left-facing comparator, '+' (anchor in2) on top."""
    op = elm.Opamp(sign=True, leads=True).left().at(out_xy).anchor('out')
    op.label(name, loc='center', fontsize=8)
    return A(op)


# ---------------------------------------------------------------- bias / reference
# Top row: bias/bandgap/PG on the left, PFM zero-cross block on the right.
YC = 21.5       # centre line of the PFM zero-cross block
RY = YC + 2.5   # bias / bandgap line; XPG_CMP sits below the bandgap
bias = block((3.2, RY), 4.2, 2.6, 'BIAS ×8\nBIAS_BLOCK\n_2V_LOWI', right=('VB',), fs=9)
A(elm.Label().at((3.2, RY - 2.0)).label(
    'VBIAS_BGR / _CMP01 / _TRI / _EA\n_PWMOSC / _PWMCMP / _PG / _MODE', fontsize=7))
bgr = block((10.8, RY), 3.6, 2.6, 'BANDGAP\n+ SOFT_START',
            left=('VB1', 'VB_COMP'), right=('VSOFT', 'VREF_FIX'), fs=9)
vb = P(bias, 'VB')
poly(vb, (vb[0] + 0.5, vb[1]), (vb[0] + 0.5, P(bgr, 'VB1')[1]), P(bgr, 'VB1'))
poly((vb[0] + 0.5, vb[1]), (vb[0] + 0.5, P(bgr, 'VB_COMP')[1]), P(bgr, 'VB_COMP'))
dot((vb[0] + 0.5, vb[1]))
tag(P(bgr, 'VSOFT'), 'VREF', 'right')
tag(P(bgr, 'VREF_FIX'), 'VREF_FIX', 'right')

pg = comp((15.0, YC - 0.2), 'XPG_CMP', plus_on_top=True)
tag(P(pg, 'in2'), 'VREF_FIX', 'left')
tag(P(pg, 'in1'), 'VOUTR2', 'left')
tag(P(pg, 'out'), 'PG', 'right')

# ---------------------------------------------------------------- dead time + drivers
# Height 2.5 puts VP/VN at ±0.75, level with the MP/MN gates: VP→driver→MPC is one straight line.
dz = block((1.0, 16), 3.0, 2.5, 'DEAD\nZONE', left=('VDUTY',), right=('VP', 'VN'),
           bot=('LS_ALLOW',), fs=9)
vtag(P(dz, 'LS_ALLOW'), 'PFM_LS_ALLOW', -0.5)

drv_lbl = 'INV → DRV1 → DRV2 → DRV3'
drvp = block((7.7, P(dz, 'VP')[1]), 4.6, 1.0, drv_lbl, left=('in',), right=('out',), fs=8)
drvn = block((7.7, P(dz, 'VN')[1]), 4.6, 1.0, drv_lbl, left=('in',), right=('out',), fs=8)
poly(P(dz, 'VP'), (4.1, P(dz, 'VP')[1]), (4.1, P(drvp, 'in')[1]), P(drvp, 'in'))
poly(P(dz, 'VN'), (4.1, P(dz, 'VN')[1]), (4.1, P(drvn, 'in')[1]), P(drvn, 'in'))
A(elm.Label().at((7.7, P(drvp, 'in')[1] + 1.0)).label('4-stage tapered driver', fontsize=7))

# ---------------------------------------------------------------- power stage (BUCK)
sw = (15.0, 16.0)
mp = A(elm.PFet(bulk=False).right().reverse().anchor('drain').at(sw))
mn = A(elm.NFet(bulk=False).right().reverse().anchor('drain').at(sw))
A(elm.Vdd().at(P(mp, 'source')).label('VDD', fontsize=9))
A(elm.Ground().at(P(mn, 'source')))
A(elm.Label().at((sw[0] + 0.3, sw[1] + 1.0)).label('MP\n700×30u/0.35u', halign='left', fontsize=7))
A(elm.Label().at((sw[0] + 0.3, sw[1] - 1.0)).label('MN\n350×30u/0.35u', halign='left', fontsize=7))
po, no = P(drvp, 'out'), P(drvn, 'out')
gx = 11.7
poly(po, (gx, po[1]), (gx, P(mp, 'gate')[1]), P(mp, 'gate'))
poly(no, (gx, no[1]), (gx, P(mn, 'gate')[1]), P(mn, 'gate'))
A(elm.Label().at((gx + 0.7, P(mp, 'gate')[1] + 0.3)).label('MPC', fontsize=8))
A(elm.Label().at((gx + 0.7, P(mn, 'gate')[1] - 0.3)).label('MNC', fontsize=8))
dot((gx, no[1]))
vtag((gx, no[1]), 'MNC', -2.2, 'left')

dot(sw)
snub = (sw[0] + 2.6, sw[1])
poly(sw, snub)
dot(snub)
A(elm.Label().at((sw[0] + 1.6, sw[1] + 0.35)).label('SW', fontsize=9))
A(elm.Resistor().at(snub).down().length(1.6).label('220', loc='bottom', fontsize=VAL_FS))
A(elm.Capacitor().down().length(1.4).label('100p', loc='bottom', fontsize=VAL_FS))
A(elm.Ground())
A(elm.Label().at((snub[0] + 1.0, sw[1] - 3.6)).label('snubber', fontsize=7))
vout = (snub[0] + 4.0, sw[1])
A(elm.Inductor2(loops=3).at(snub).to(vout).label('L1 1.7µH', fontsize=VAL_FS))
dot(vout)
A(elm.Capacitor(polar=True).at(vout).down().length(1.6).label('C1 20µ', loc='bottom', fontsize=VAL_FS))
A(elm.Resistor().down().length(1.4).label('ESR 20m', loc='bottom', fontsize=VAL_FS))
A(elm.Ground())
vtag(snub, 'SW', 2.0)

# feedback dividers
fb1 = vout[0] + 2.4
fb2 = fb1 + 3.4
poly(vout, (fb2, vout[1]))
dot((fb1, vout[1]))
A(elm.Dot(open=True).at((fb2, vout[1])).label('VOUT', loc='right', fontsize=10))
A(elm.Resistor().at((fb1, vout[1])).down().length(2.2).label('RFB_TOP 3k', loc='bottom', fontsize=VAL_FS))
n1 = (fb1, vout[1] - 2.2)
dot(n1)
A(elm.Resistor().at(n1).down().length(2.2).label('RFB_BOT\n7.365k', loc='top', fontsize=VAL_FS))
A(elm.Ground())
cff_x = fb1 - 1.0
poly((fb1, vout[1] - 0.2), (cff_x, vout[1] - 0.2))
A(elm.Capacitor().at((cff_x, vout[1] - 0.2)).down().length(2.0).label('CFF\n4.7p', loc='top', fontsize=8))
poly((cff_x, n1[1]), n1)
dot((fb1, vout[1] - 0.2))
A(elm.Label().at((n1[0] + 0.5, n1[1] + 0.3)).label('VOUTR', halign='left', fontsize=8))
dot((fb2, vout[1]))
A(elm.Resistor().at((fb2, vout[1])).down().length(2.2).label('RFB2_TOP 3k', loc='bottom', fontsize=VAL_FS))
n2 = (fb2, vout[1] - 2.2)
dot(n2)
A(elm.Resistor().at(n2).down().length(2.2).label('RFB2_BOT\n7.52k', loc='bottom', fontsize=VAL_FS))
A(elm.Ground())
A(elm.Label().at((n2[0] + 0.3, n2[1] + 0.3)).label('VOUTR2', halign='left', fontsize=8))

# ---------------------------------------------------------------- PFM ZCD / diode emulation
# Placed right-to-left from PFM_DIODE_GATE so ZCD_PFM and SW_PFM_ZCD are straight wires.
dg = block((27.8, YC), 3.6, 3.4, 'PFM_DIODE\n_GATE',
           left=('ZCD', 'MODE', 'DUTY', 'LS_GATE'), right=('IDLE', 'LS_ALLOW'), fs=9)
for pin, net in (('MODE', 'MODE'), ('DUTY', 'VDUTY_SEL'), ('LS_GATE', 'MNC')):
    tag(P(dg, pin), net, 'left', lead=0.3)
tag(P(dg, 'IDLE'), 'PFM_IDLE', 'right', lead=0.3)
tag(P(dg, 'LS_ALLOW'), 'PFM_LS_ALLOW', 'right', lead=0.3)
zcd = comp((P(dg, 'ZCD')[0] - 0.9, P(dg, 'ZCD')[1]), 'XPFM_ZCD\nCMP_ZCD')
poly(P(zcd, 'out'), P(dg, 'ZCD'))
A(elm.Label().at((P(zcd, 'out')[0] + 0.45, P(zcd, 'out')[1] + 0.3)).label('ZCD_PFM', fontsize=7))
A(elm.Ground().at(P(zcd, 'in2')))
zy = P(zcd, 'in1')[1]
zn = (P(zcd, 'in1')[0] - 1.2, zy)
poly(zn, P(zcd, 'in1'))
dot(zn)
A(elm.Label().at((zn[0] + 0.75, zy + 0.3)).label('SW_PFM_ZCD', fontsize=7))
A(elm.Resistor().at(zn).left().length(1.8).label('RZCD_SENSE 100', loc='bottom', fontsize=VAL_FS))
tag((zn[0] - 1.8, zy), 'SW', 'left', lead=0.01)
A(elm.Resistor().at(zn).up().length(1.6).label('RZCD_LEAD\n45k', loc='top', fontsize=VAL_FS))
A(elm.Vdd().label('VDD', fontsize=9))

# ---------------------------------------------------------------- lower half
# Mode detect + select on the left; PWM loop (upper) and PFM loop (lower) flow
# right-to-left into MUX2. Pins are aligned so the main signal paths are straight.

# PWM loop
LY = 7.8  # lower-half offset: its top edge sits right under the dead-time / BUCK row
vy = LY  # VCOMP line
pwmc = comp_l((10.0, vy + 0.63), 'XPWM_CMP')  # '-' (in1) lands on the VCOMP line
osc = block((16.3, P(pwmc, 'in2')[1]), 3.2, 1.8, 'PWM_OSC',
            left=('RAMP',), right=('VBIAS', 'VTH'), fs=9)
poly(P(pwmc, 'in2'), P(osc, 'RAMP'))
A(elm.Label().at((P(pwmc, 'in2')[0] + 0.4, P(pwmc, 'in2')[1] + 0.3)).label('RAMP', fontsize=8))
tag(P(osc, 'VBIAS'), 'VBIAS_PWMOSC', 'right')
tag(P(osc, 'VTH'), 'VREF', 'right')

ea = comp_l((25.5, vy), 'EA')
tag(P(ea, 'in1'), 'VREF', 'right')
poly(P(pwmc, 'in1'), P(ea, 'out'))
A(elm.Label().at((24.75, vy + 0.3)).label('VCOMP', fontsize=8))
# lead-lag compensation
cp_x, rz_x = 21.6, 23.4
dot((cp_x, vy))
A(elm.Capacitor().at((cp_x, vy)).down().length(1.4).label('CP 2.2p', loc='top', fontsize=VAL_FS))
A(elm.Ground())
dot((rz_x, vy))
A(elm.Resistor().at((rz_x, vy)).down().length(1.4).label('RZ 160k', loc='bottom', fontsize=VAL_FS))
A(elm.Capacitor().down().length(1.4).label('CZ 20p', loc='bottom', fontsize=VAL_FS))
A(elm.Ground())

# MUX2: input 1 level with XPWM_CMP output
pwm_out = P(pwmc, 'out')
mux = A(elm.Multiplexer(size=(2, 3.4), slant=-25, pins=[
    elm.IcPin(name='1', side='right', slot='2/2', anchorname='in1'),
    elm.IcPin(name='0', side='right', slot='1/2', anchorname='in0'),
    elm.IcPin(name='SEL', side='bottom', slot='1/1', anchorname='sel'),
    elm.IcPin(name='', side='left', slot='1/1', anchorname='y'),
]).right().at((5.0, pwm_out[1] - 1.2)).anchor('center').label('MUX2', loc='center', fontsize=9))
poly(pwm_out, P(mux, 'in1'))
A(elm.Label().at((8.2, pwm_out[1] + 0.3)).label('PWM_QB', fontsize=8))

# MODE_DET straight under SEL
sel = P(mux, 'sel')
mode = block((sel[0], sel[1] - 1.4 - 0.5 - 1.8), 3.6, 3.6, 'MODE\nDET',
             left=('SW', 'MNC_GATE', 'VTH_MODE', 'PG', 'PFM_IDLE'), top=('MODE',), fs=9)
for pin, net in (('SW', 'SW'), ('MNC_GATE', 'MNC'), ('VTH_MODE', 'VREF_FIX'),
                 ('PG', 'PG'), ('PFM_IDLE', 'PFM_IDLE')):
    tag(P(mode, pin), net, 'left', lead=0.4)
poly(sel, P(mode, 'MODE'))
mtap = (sel[0], sel[1] - 0.7)
dot(mtap)
tag(mtap, 'MODE', 'left', lead=0.8)
A(elm.Label().at((sel[0] + 0.9, mtap[1])).label('1=PWM\n0=PFM', fontsize=7))

# VDUTY_SEL: MUX2 output loops back up the left edge into DEAD_ZONE
ym = P(mux, 'y')
bx = -1.8
poly(ym, (bx, ym[1]), (bx, P(dz, 'VDUTY')[1]), P(dz, 'VDUTY'))
A(elm.Label().at((ym[0] - 1.9, ym[1] + 0.3)).label('VDUTY_SEL', fontsize=8))

# PFM loop
# Tall RS (pins at ±1.3) drops R below the 47p ground so RAMP_RST runs straight to TRIANGO_HZ.
rs = block((12.5, LY - 8.27), 2.4, 3.6, 'RS\n(XRS2)',
           right=('S', 'R'), left=('QB',), top=('Q',), fs=9)
cmp01 = comp_l((15.2, P(rs, 'S')[1]), 'XCMP01')
vp = P(cmp01, 'in1')[1]  # VREF_PFM line, level with XCMP01 '-'
poly(P(cmp01, 'out'), P(rs, 'S'))
A(elm.Label().at((14.7, P(cmp01, 'out')[1] + 0.3)).label('S1', fontsize=8))

node = (21.5, vp)
poly(P(cmp01, 'in1'), node)
dot(node)
A(elm.Label().at((20.2, vp + 0.3)).label('VREF_PFM', fontsize=8))
A(elm.Capacitor().at(node).down().length(1.2).label('47p', loc='top', fontsize=VAL_FS))
A(elm.Ground())
vin = (node[0] + 2.4, vp)
A(elm.Resistor().at(node).to(vin).label('RPFM_REF 200k', loc='top', fontsize=VAL_FS))
dot(vin)
tag(vin, 'VREF', 'right', lead=0.5)

# PFM_REF_START sits over the 200k: its pins drop straight onto both ends
refst = A(elm.Ic(size=(4.0, 1.6), pins=[
    elm.IcPin(name='VFILTER', side='bottom', pos=0.1, anchorname='VFILTER', lblsize=7),
    elm.IcPin(name='VIN', side='bottom', pos=0.9, anchorname='VIN', lblsize=7),
    elm.IcPin(name='PG', side='right', slot='1/1', anchorname='PG', lblsize=7),
]).right().at((node[0] + 1.2, vp + 1.8 + 0.8)).anchor('center')  # clear of the VOUTR2 wire
    .label('PFM_REF_START\n22k bypass until REF_READY', loc='center', ofst=(-0.35, 0), fontsize=7))
poly(P(refst, 'VFILTER'), node)
poly(P(refst, 'VIN'), vin)
tag(P(refst, 'PG'), 'PG', 'right', lead=0.3)

# TRIANGO_HZ: VOUT level with RS R (h=2.2 -> pins at ±0.6)
tri = block((25.0, P(rs, 'R')[1] - 0.6), 3.6, 2.2, 'TRIANGO_HZ\n(on-time one-shot)',
            right=('VIN+', 'VBIAS'), left=('VOUT', 'PFM_QB'), fs=8)
tag(P(tri, 'VIN+'), 'VREF', 'right')
tag(P(tri, 'VBIAS'), 'VBIAS_TRI', 'right')
poly(P(rs, 'R'), P(tri, 'VOUT'))
A(elm.Label().at((P(rs, 'R')[0] + 1.2, P(rs, 'R')[1] + 0.3)).label('RAMP_RST', fontsize=8))

qb = P(rs, 'QB')
qb_x = qb[0] - 0.8
in0 = P(mux, 'in0')
poly(in0, (qb_x, in0[1]), (qb_x, P(tri, 'PFM_QB')[1]), P(tri, 'PFM_QB'))
poly(qb, (qb_x, qb[1]))
dot((qb_x, qb[1]))
A(elm.Label().at((qb_x - 0.7, in0[1] - 1.2)).label('PFM_QB', fontsize=8))
vtag(P(rs, 'Q'), 'PFM_Q', 0.3, 'right')

# ---------------------------------------------------------------- feedback wires down the right edge
# VOUTR: divider tap -> under the divider grounds -> right edge -> EA '+'
# (VOUTR and VOUTR2 taps share a height, so VOUTR ducks below the ground symbols first.)
xr1, xr2, yb = 33.0, 33.6, 10.7
ea_p = P(ea, 'in2')
poly(n1, (n1[0] + 0.8, n1[1]), (n1[0] + 0.8, yb), (xr1, yb), (xr1, ea_p[1]), ea_p)
# VOUTR2: divider tap -> right edge -> XCMP01 '+'
c_p = P(cmp01, 'in2')
poly(n2, (xr2, n2[1]), (xr2, c_p[1]), c_p)
A(elm.Label().at((c_p[0] + 0.3, c_p[1] + 0.3)).label('VOUTR2', halign='left', fontsize=8))
A(elm.Label().at((ea_p[0] + 0.3, ea_p[1] + 0.3)).label('VOUTR', halign='left', fontsize=8))

# ---------------------------------------------------------------- group frames
def frame(x0, y0, x1, y1, title):
    # theta(0): otherwise Rect inherits the direction of the last drawn line
    A(elm.Rect(corner1=(x0, y0), corner2=(x1, y1), ls='--', lw=0.8, color='#6b7280').at((0, 0)).theta(0))
    A(elm.Label().at((x0 + 0.2, y1 - 0.35)).label(title, halign='left', fontsize=9, color='#374151'))


top = YC + 4.6
frame(-0.3, 19.5, 16.7, top, 'Bias / Reference / Power-good')
frame(16.9, 19.5, 32.5, top, 'PFM zero-cross / diode emulation')
frame(-0.3, 10.4, 12.5, 19.3, 'Dead time + gate drivers')
frame(12.7, 10.4, 32.5, 19.3, 'BUCK power stage + feedback dividers')
low = P(tri, 'PFM_QB')[1] - 0.8
split = vy - 3.6
frame(-0.3, low, 7.6, LY + 2.4, 'Mode detect + select')
frame(7.8, split, 32.5, LY + 2.4, 'PWM loop')
frame(7.8, low, 32.5, split - 0.2, 'PFM loop')

A(elm.Label().at((0, top + 0.7)).label(
    'SUB [PFM v11]  —  Synchronous buck with automatic PWM/PFM  (VDD 3.3 V → VOUT 1.8 V, ~2.22 MHz, 1.7 µH / 20 µF)',
    halign='left', fontsize=13))

d.save(str(OUT / 'sub_arch_v11.svg'))
d.save(str(OUT / 'sub_arch_v11.png'), dpi=160)
print('saved', OUT / 'sub_arch_v11.png')

