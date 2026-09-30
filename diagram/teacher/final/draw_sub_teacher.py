"""Draw the top-level architecture of subckt SUB, PFM v11 (hspice/archive/v11/sub_system.net) with schemdraw.

Run:  python diagram/teacher/final/draw_sub_teacher.py
Out:  diagram/teacher/final/sub_arch_teacher.svg, diagram/teacher/final/sub_arch_teacher.png

Net names follow archive/v11/sub_system.net. Long feedback nets (VOUTR, VOUTR2, SW, MNC,
PG, MODE, ...) are drawn as net-label tags instead of routed wires.

Portrait layout, top to bottom:
  Dead time + gate drivers | BUCK power stage + feedback dividers
  Mode select (full-height left column) | PFM zero-cross / diode emulation + mode detect + power-good
                                        | PWM loop + reference
                                        | PFM loop
"""
from pathlib import Path

import schemdraw
import schemdraw.elements as elm

schemdraw.use('matplotlib')

OUT = Path(__file__).resolve().parent
TAG_FS = 9
LBL_DX, LBL_DY = 0.1, 0.1  # schemdraw draws Label text this far right/up of its anchor; centred names compensate
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
        for i, nm in enumerate(names):  # slots count bottom->top on sides; ' ' = empty slot
            if not nm.strip():
                continue
            pins.append(elm.IcPin(name=nm, side=side, slot=f'{n - i}/{n}',
                                  anchorname=nm, lblsize=7))
    for side, names in (('top', top), ('bottom', bot)):
        n = len(names)
        for i, nm in enumerate(names):
            pins.append(elm.IcPin(name=nm, side=side, slot=f'{i + 1}/{n}',
                                  anchorname=nm, lblsize=7))
    ic = A(elm.Ic(size=(w, h), pins=pins).right().at(xy).anchor('center'))
    A(elm.Label().at((xy[0] - LBL_DX, xy[1] - LBL_DY)).theta(0).label(name, loc='center', ofst=(0, 0), halign='center', valign='center', fontsize=fs))
    return ic


def comp_name(op, name):
    """Name inside a comparator, at 40% of the way from the triangle's base to its tip."""
    out, base_in = P(op, 'out'), P(op, 'xy')
    sgn = 1 if out[0] > base_in[0] else -1
    tip, base = out[0] - sgn * 0.625, base_in[0] + sgn * 0.625
    # theta(0) + zero offset: otherwise the label is nudged along whatever direction was drawn last
    A(elm.Label().at((base + 0.4 * (tip - base) - LBL_DX, out[1] - LBL_DY)).theta(0)
      .label(name, loc='center', ofst=(0, 0), halign='center', valign='center', fontsize=8))


def comp(out_xy, name, plus_on_top=False):
    """Right-facing comparator. '+' is anchor in2."""
    op = elm.Opamp(sign=True, leads=True).right().at(out_xy).anchor('out')
    if plus_on_top:
        op.flip()
    op = A(op)
    comp_name(op, name)
    return op


def comp_l(out_xy, name, minus_on_top=False):
    """Left-facing comparator, '+' (anchor in2) on top unless minus_on_top."""
    op = elm.Opamp(sign=True, leads=True).left().at(out_xy).anchor('out')
    if minus_on_top:
        op.flip()
    op = A(op)
    comp_name(op, name)
    return op


# Bottom row (mirrored): MODE_DET <- XPG_CMP / PFM_DIODE_GATE <- ZCD, flowing right-to-left.
# The bandgap / soft-start reference is drawn next to the EA (PWM loop).
PD = 2.0       # extra PFM-loop height: room for PFM_REF_START above the VOUTR2 wire
YC = 4.3        # centre line of the PFM zero-cross row (second row, right under the dead-time / BUCK row)
DX = 1.4        # horizontal shift of PFM_DIODE_GATE / ZCD, clear of XPG_CMP and its input wires

# ---------------------------------------------------------------- dead time + drivers
# Height 2.5 puts VP/VN at ±0.75, level with the MP/MN gates: VP→driver→MPC is one straight line.
dz = block((1.0, 16), 4.0, 2.5, 'DEAD_ZONE', left=('VDUTY',), right=('VP', 'VN'),
           bot=('LS_ALLOW',), fs=9)

drv_lbl = 'Driver'
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
po, no = P(drvp, 'out'), P(drvn, 'out')
gx = 11.7
poly(po, (gx, po[1]), (gx, P(mp, 'gate')[1]), P(mp, 'gate'))
poly(no, (gx, no[1]), (gx, P(mn, 'gate')[1]), P(mn, 'gate'))

dot(sw)
snub = (sw[0] + 2.6, sw[1])
poly(sw, snub)
dot(snub)
A(elm.Resistor().at(snub).down().length(1.6))
A(elm.Capacitor().down().length(1.4))
A(elm.Ground())
A(elm.Label().at((snub[0] + 1.0, sw[1] - 3.6)).label('snubber', fontsize=7))
vout = (snub[0] + 4.0, sw[1])
A(elm.Inductor2(loops=3).at(snub).to(vout))
dot(vout)
A(elm.Capacitor().at(vout).down().length(1.6))
A(elm.Resistor().down().length(1.4))
A(elm.Ground())

# feedback dividers
fb1 = vout[0] + 3.2
fb2 = fb1 + 3.4
poly(vout, (fb2, vout[1]))
dot((fb1, vout[1]))
A(elm.Dot(open=True).at((fb2, vout[1])).label('VOUT', loc='right', fontsize=10))
A(elm.Resistor().at((fb1, vout[1])).down().length(1.6))
n1 = (fb1, vout[1] - 1.6)
dot(n1)
A(elm.Resistor().at(n1).down().length(1.6))
A(elm.Ground())
dot((fb2, vout[1]))
A(elm.Resistor().at((fb2, vout[1])).down().length(1.6))
n2 = (fb2, vout[1] - 1.6)
dot(n2)
A(elm.Resistor().at(n2).down().length(1.6))
A(elm.Ground())

# ---------------------------------------------------------------- PFM ZCD / diode emulation + MODE_DET
# Bottom row, mirrored: signal flows right-to-left (SW -> ZCD -> PFM_DIODE_GATE -> MODE_DET).
# Blocks take inputs on the right and drive outputs on the left.
# PFM_DIODE_GATE right pins: MODE (from above), ZCD, LS_GATE (MNC tag) and DUTY (from below).
dg = block((19.3 + DX, YC), 4.4, 3.4, 'PFM_DIODE_GATE', right=('MODE', 'ZCD', 'LS_GATE', 'DUTY'),
           left=('IDLE', 'LS_ALLOW'), fs=9)
zcd = comp_l((P(dg, 'ZCD')[0] + 1.8,  # tip right of the VOUTR riser
 P(dg, 'ZCD')[1]), 'CMP_ZCD', minus_on_top=True)
poly(P(zcd, 'out'), P(dg, 'ZCD'))
A(elm.Ground().at(P(zcd, 'in2')))
zy = P(zcd, 'in1')[1]
zn = (P(zcd, 'in1')[0] + 1.05, zy)  # pull-up node right of the VREF_FIX riser
poly(zn, P(zcd, 'in1'))
dot(zn)
A(elm.Resistor().at(zn).right().length(1.0))
sw_in = (zn[0] + 1.0, zy)
A(elm.Resistor().at(zn).up().length(1.6))
A(elm.Vdd().label('VDD', fontsize=9))

# MODE_DET left of PFM_DIODE_GATE, just right of the MUX2 SEL wire; PFM_IDLE is level with IDLE.
# Inputs on the right, output (MODE) on the left. Right pins 0.6 apart; empty slots leave room
# for XPG_CMP between PG and PFM_IDLE, and put MNC_GATE level with LS_GATE.
idle = P(dg, 'IDLE')
mode = block((10.3, idle[1] + 1.5), 3.6, 6.4, 'MODE_DET',
             right=('SW', 'VTH_MODE', ' ', ' ', 'PG', ' ', ' ', 'PFM_IDLE', ' ', 'MNC_GATE'),
             left=('MODE',), fs=9)
poly(idle, P(mode, 'PFM_IDLE'))
# power-good comparator drives MODE_DET PG directly
mpg = P(mode, 'PG')
pg = comp_l((mpg[0] + 0.4, mpg[1]), 'CMP01')
poly(P(pg, 'out'), mpg)
p_in, m_in = P(pg, 'in2'), P(pg, 'in1')
# VREF_FIX: MODE_DET VTH_MODE over the top of XPG_CMP into its '+' input
vth = P(mode, 'VTH_MODE')
yv = vth[1]  # VTH_MODE sits above XPG_CMP, so VREF_FIX runs to it in one straight line
xvf = p_in[0] + 0.6
poly(vth, (xvf, yv), (xvf, p_in[1]), p_in)
dot((xvf, yv))
# SW: over the top of the whole row into MODE_DET
ysw = YC + 6.5
st = P(mode, 'SW')
# MNC: tag (from the driver) into PFM_DIODE_GATE LS_GATE; the same net runs under
# PFM_DIODE_GATE back to MODE_DET MNC_GATE.
lg, mg = P(dg, 'LS_GATE'), P(mode, 'MNC_GATE')
ymn = YC - 2.15  # between PFM_DIODE_GATE's bottom edge and the VDUTY_SEL wire
xmn = mg[0] + 3.0
mj = (lg[0] + 0.9, lg[1])
poly(mg, (xmn, mg[1]), (xmn, ymn), (mj[0], ymn), mj, lg)

# ---------------------------------------------------------------- lower half
# Mode detect + select on the left; PWM loop (upper) and PFM loop (lower) flow
# right-to-left into MUX2. Pins are aligned so the main signal paths are straight.

# PWM loop
LY = YC - 5.6  # PWM loop offset: its frame top sits right under the PFM zero-cross row
vy = LY + 0.8  # VCOMP line, raised to trim the white space at the top of the PWM loop
pwmc = comp_l((10.0, vy - 0.63), 'CMP01', minus_on_top=True)  # '-' (in1) on the VCOMP line
# PWM_OSC under the compensation network; its VTH wire runs straight under EA to the VREF bus
yc = vy - 3.0
osc = block((17.3, yc), 3.2, 1.4, 'PWM_OSC', left=('RAMP',), right=('VTH',), fs=9)
p_pl = P(pwmc, 'in2')
poly(p_pl, (p_pl[0] + 1.4, p_pl[1]), (p_pl[0] + 1.4, yc), P(osc, 'RAMP'))

ea = comp_l((22.0, vy), 'EA')
# EA '-' <- SOFT_START <- BANDGAP, between EA and the VOUTR/VOUTR2 return wires
ea_m = P(ea, 'in1')
ss = block((ea_m[0] + 1.9, ea_m[1]), 2.2, 1.4, 'SOFT_START', fs=9)
bg = block((ea_m[0] + 5.2, ea_m[1]), 2.4, 1.4, 'BANDGAP', fs=9)
poly(ea_m, (ea_m[0] + 0.8, ea_m[1]))
poly((ea_m[0] + 3.0, ea_m[1]), (ea_m[0] + 4.0, ea_m[1]))
ftap = (ea_m[0] + 3.8, ea_m[1])  # VREF_FIX riser, clear of the CMP_ZCD ground and pull-up
dot(ftap)
poly(P(pwmc, 'in1'), P(ea, 'out'))
# lead-lag compensation (short legs so it ends above the PWM_OSC VTH wire)
cp_x, rz_x = 18.6, 20.0
dot((cp_x, vy))
A(elm.Capacitor().at((cp_x, vy)).down().length(1.1))
A(elm.Ground())
dot((rz_x, vy))
A(elm.Resistor().at((rz_x, vy)).down().length(1.1))
A(elm.Capacitor().down().length(1.1))
A(elm.Ground())

# MUX2: input 1 level with XPWM_CMP output
pwm_out = P(pwmc, 'out')
mux = A(elm.Multiplexer(size=(2, 3.4), slant=-25, pins=[
    elm.IcPin(name='1', side='right', slot='2/2', anchorname='in1'),
    elm.IcPin(name='0', side='right', slot='1/2', anchorname='in0'),
    elm.IcPin(name='SEL', side='top', slot='1/1', anchorname='sel'),
    elm.IcPin(name='', side='left', slot='1/1', anchorname='y'),
]).right().at((5.0, pwm_out[1] - 1.2)).anchor('center').label('MUX2', loc='center', fontsize=9))
poly(pwm_out, P(mux, 'in1'))

# MODE: MUX2 SEL straight up past MODE_DET's MODE pin, then over the top into PFM_DIODE_GATE
sel = P(mux, 'sel')
mt, dgm = P(mode, 'MODE'), P(dg, 'MODE')
ym = YC + 6.2  # above MODE_DET, below the frame top
poly(sel, (sel[0], ym))
poly((sel[0], mt[1]), mt)
dot((sel[0], mt[1]))
poly((sel[0], ym), (dgm[0] + 0.3, ym), (dgm[0] + 0.3, dgm[1]), dgm)

# VDUTY_SEL: MUX2 output loops back up the left edge into DEAD_ZONE
ym = P(mux, 'y')
bx = -1.8
poly(ym, (bx, ym[1]), (bx, P(dz, 'VDUTY')[1]), P(dz, 'VDUTY'))
# ... and also runs down the left edge, under PFM_DIODE_GATE, into its DUTY pin
duty = P(dg, 'DUTY')
yd = YC - 2.6
dot((bx, yd))
poly((bx, yd), (duty[0] + 0.3, yd), (duty[0] + 0.3, duty[1]), duty)

# PFM_LS_ALLOW: PFM_DIODE_GATE LS_ALLOW back up into DEAD_ZONE LS_ALLOW
dls, gls = P(dz, 'LS_ALLOW'), P(dg, 'LS_ALLOW')
poly(dls, (dls[0], gls[1]), gls)

# PFM loop
# Tall RS (pins at ±1.3) drops R below the 47p ground so RAMP_RST runs straight to TRIANGO_HZ.
rs = block((12.5, LY - 6.77 - PD), 2.4, 3.6, 'RS',
           right=('S', 'R'), left=('Q', 'QB'), fs=9)
cmp01 = comp_l((15.2, P(rs, 'S')[1]), 'CMP01')
poly(P(cmp01, 'out'), P(rs, 'S'))

# TRIANGO_HZ: VOUT level with RS R (h=2.2 -> pins at ±0.6)
tri = block((20.5, P(rs, 'R')[1] - 0.6), 3.6, 2.2, 'TRIANGO_HZ',
            right=('VIN+', ' '), left=('VOUT', 'PFM_QB'), fs=8)
# VREF bus: drops from the EA '-' node to TRIANGO_HZ VIN+, branching to the VREF_PFM filter
xv = ea_m[0] + 0.4
dot((xv, ea_m[1]))
# PWM_OSC VTH: straight from the VREF bus, under EA and the compensation network
vth_o = P(osc, 'VTH')
poly(vth_o, (xv, vth_o[1]))
dot((xv, vth_o[1]))
poly((xv, ea_m[1]), (xv, P(tri, 'VIN+')[1]), P(tri, 'VIN+'))
# VREF_PFM: RC filter (RPFM_REF / CPFM_REF) from VREF into XCMP01 '-'; the cap sits right of TRIANGO_HZ
vp = P(cmp01, 'in1')[1]
fv = (xv - 0.6, vp)         # VREF end of the resistor (PFM_REF_START VIN)
fn = (fv[0] - 2.2, vp)      # VREF_PFM node (PFM_REF_START VFILTER)
poly(P(cmp01, 'in1'), fn)
dot(fn)
A(elm.Capacitor().at(fn).down().length(1.0))
A(elm.Ground())
A(elm.Resistor().at(fn).to(fv))
dot(fv)
poly(fv, (xv, vp))
# PFM_REF_START sits over the resistor, above the VOUTR2 wire; its VFILTER / VIN legs drop onto both ends
rc = ((fn[0] + fv[0]) / 2, vp + 2.5)
rh = 1.8
refst = A(elm.Ic(size=(2.8, rh), pins=[
    elm.IcPin(name='', side='top', pos=0.15, anchorname='PG'),
]).right().at(rc).anchor('center'))
A(elm.Label().at((P(refst, 'center')[0] - LBL_DX, rc[1] - LBL_DY)).theta(0)
  .label('PFM_REF_START', loc='center', ofst=(0, 0), halign='center', valign='center', fontsize=8))
rb = rc[1] - rh / 2
poly((fn[0], rb), fn)
poly((fv[0], rb), fv)
A(elm.Label().at((fn[0] + 0.1, rb + 0.2)).label('VFILTER', halign='left', fontsize=6))
A(elm.Label().at((fv[0] - 0.1, rb + 0.2)).label('VIN', halign='right', fontsize=6))
vtag(P(refst, 'PG'), 'PG', 0.2, 'right')
dot((xv, vp))
poly(P(rs, 'R'), P(tri, 'VOUT'))

qb = P(rs, 'QB')
qb_x = qb[0] - 1.6  # clear of the PFM_Q tag on the left and of the 'PFM loop' title
in0 = P(mux, 'in0')
poly(in0, (qb_x, in0[1]), (qb_x, P(tri, 'PFM_QB')[1]), P(tri, 'PFM_QB'))
poly(qb, (qb_x, qb[1]))
dot((qb_x, qb[1]))

# ---------------------------------------------------------------- feedback wires down the right edge
# VOUTR: divider tap -> straight down into EA '+'
xr1, xr2, yb = 32.5, 32.0, 12.0  # inside the frames' right edge (33.3)
# SW: switch node up over the BUCK stage, down the far right edge into the ZCD pull-up network
xsw, ysw_top = 32.95, snub[1] + 2.0
poly(snub, (snub[0], ysw_top), (xsw, ysw_top), (xsw, sw_in[1]), sw_in)
# MODE_DET SW pin: straight across to the SW riser on the right edge
poly(st, (xsw, st[1]))
dot((xsw, st[1]))
# MNC: low-side gate wire straight down into MODE_DET MNC_GATE (which continues on to LS_GATE)
xg = 13.2
dot((xg, no[1]))
dot((xg, mg[1]))
poly((xg, no[1]), (xg, mg[1]))
ea_p = P(ea, 'in2')
poly(n1, (n1[0] + 0.8, n1[1]), (n1[0] + 0.8, ea_p[1]), ea_p)  # straight down, left of the CMP_ZCD tip
# VOUTR2: divider tap -> right edge -> XCMP01 '+'
c_p = P(cmp01, 'in2')
poly(n2, (xr2, n2[1]), (xr2, c_p[1]), c_p)

# ---------------------------------------------------------------- wires down into the bottom row
# VREF_FIX runs level with VTH_MODE; VOUTR2 drops down the right edge, then straight into XPG_CMP '-'
# (crossing over the SW pull-up resistor).
y_f = yv
y_o = m_in[1]
# VOUTR2: continues down the right edge past XCMP01 into XPG_CMP '-'
dot((xr2, y_o))
poly((xr2, y_o), m_in)
# VREF_FIX: from the BANDGAP / SOFT_START node straight down, then over to the VTH_MODE / XPG_CMP '+' net
poly(ftap, (ftap[0], y_f), (xvf, y_f))

# ---------------------------------------------------------------- group frames
def frame(x0, y0, x1, y1, title, tx=None):
    # theta(0): otherwise Rect inherits the direction of the last drawn line
    A(elm.Rect(corner1=(x0, y0), corner2=(x1, y1), ls='--', lw=0.8, color='#6b7280').at((0, 0)).theta(0))
    tx = x0 + 0.2 if tx is None else tx
    A(elm.Label().at((tx - LBL_DX, y1 - 0.35 - LBL_DY)).theta(0).label(
        title, loc='center', ofst=(0, 0), halign='left', valign='center', fontsize=9, color='#374151'))


top = 19.3  # top edge of the dead-time / BUCK row (now the first row)
fx0 = bx - 0.6  # left edge: keeps the VDUTY_SEL return wire and DEAD_ZONE inside the frames
frame(7.8, YC - 3.0, 33.3, YC + 7.2, 'PFM zero-cross / diode emulation + mode detect + power-good', tx=xg + 0.3)  # right of the MNC riser
frame(fx0, 11.7, 12.5, 19.3, 'Dead time + gate drivers')
frame(12.7, 11.7, 33.3, 19.3, 'BUCK power stage + feedback dividers')
low = P(tri, 'PFM_QB')[1] - 0.8
split = vy - 4.0
frame(fx0, low, 7.6, YC + 7.2, 'Mode select', tx=bx + 0.2)  # title right of the VDUTY_SEL wire
frame(7.8, split, 33.3, LY + 2.4, 'PWM loop + reference')
frame(7.8, low, 33.3, split - 0.2, 'PFM loop')

A(elm.Label().at((0, top + 0.7)).label(
    'SUB [PFM v11]  —  Synchronous buck with automatic PWM/PFM  (VDD 3.3 V → VOUT 1.8 V, ~2.22 MHz, 1.7 µH / 20 µF)',
    halign='left', fontsize=13))

d.save(str(OUT / 'sub_arch_teacher.svg'))
d.save(str(OUT / 'sub_arch_teacher.png'), dpi=160)
print('saved', OUT / 'sub_arch_teacher.png')

