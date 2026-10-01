"""Draw subckt SUB, PFM v11 (hspice/archive/v11/sub_system.net) with schemdraw: a top-level
diagram with three sub-blocks collapsed to boxes, plus one detailed diagram per sub-block.

Run:  python diagram/teacher/draw_sub_teacher.py
Out (next to this script):
  sub_arch_teacher.svg/.png   top level: dead time + drivers, BUCK + dividers, MUX2, blocks 1-3
  blk1_mode_detect.svg/.png   block 1: PFM zero-cross / diode emulation + mode detect + power-good
  blk2_pwm_loop.svg/.png      block 2: PWM loop + reference
  blk3_pfm_loop.svg/.png      block 3: PFM loop

Net names follow archive/v11/sub_system.net. In the block diagrams, every net that leaves the
block is a net-label tag carrying the same name as the matching pin of the block's box in the
top-level diagram. The previous single-page version is kept in diagram/teacher/final/.
"""
from pathlib import Path

import schemdraw
import schemdraw.elements as elm

schemdraw.use('matplotlib')

OUT = Path(__file__).resolve().parent
TAG_FS = 9
LBL_DX, LBL_DY = 0.1, 0.1  # schemdraw draws Label text this far right/up of its anchor; centred names compensate

BLK1 = 'PWM/PFM detect'
BLK2 = 'PWM'
BLK3 = 'PFM'

d = A = None


def new_drawing():
    global d, A
    d = schemdraw.Drawing(show=False)
    d.config(unit=2.0, fontsize=10, lw=1.1)
    A = d.add


def save(stem):
    d.save(str(OUT / f'{stem}.svg'))
    d.save(str(OUT / f'{stem}.png'), dpi=160)
    print('saved', OUT / f'{stem}.png')


def P(e, name):
    return e.absanchors[name]


def poly(*pts):
    for a, b in zip(pts, pts[1:]):
        A(elm.Line().at(a).to(b))


def dot(p):
    A(elm.Dot(radius=0.08).at(p))


def text(p, s, fs=9, halign='center', color=None):
    """Text centred (vertically) on p; theta(0) + zero offset keep schemdraw from nudging it."""
    kw = {'color': color} if color else {}
    A(elm.Label().at((p[0] - LBL_DX, p[1] - LBL_DY)).theta(0).label(
        s, loc='center', ofst=(0, 0), halign=halign, valign='center', fontsize=fs, **kw))


def mktag(name, fs=TAG_FS, width=None):
    """width=<other name>: size the tag for that name instead, so stacked tags match."""
    n = len(width or name)
    return elm.Tag(width=0.12 * n * fs / 9 + 0.55).label(name, fontsize=fs)


def tag(p, name, side='left', lead=0.6, width=None, out=False):
    """Net-label tag attached to point p, extending towards `side`.
    The tip points at the wire (input) or, with out=True, away from it (output)."""
    dx = {'left': -lead, 'right': lead}[side]
    end = (p[0] + dx, p[1])
    A(elm.Line().at(p).to(end))
    t = mktag(name, width=width)
    if out:  # tip on the far end
        w = t.params['width']
        tip = (end[0] + w, end[1]) if side == 'right' else (end[0] - w, end[1])
        A(t.at(tip).left() if side == 'right' else t.at(tip).right())
    else:
        A(t.at(end).left() if side == 'left' else t.at(end).right())


def vtag(p, name, dy, side='right', out=False, width=None):
    """Vertical stub of length dy from p, then a horizontal tag."""
    end = (p[0], p[1] + dy)
    A(elm.Line().at(p).to(end))
    tag(end, name, side, lead=0.3, out=out, width=width)


def block(xy, w, h, name, left=(), right=(), top=(), bot=(), fs=10):
    """Ic box centred at xy. Pin lists are given top->bottom / left->right; ' ' = empty slot."""
    pins = []
    for side, names in (('left', left), ('right', right)):
        n = len(names)
        for i, nm in enumerate(names):  # slots count bottom->top on sides
            if not nm.strip():
                continue
            pins.append(elm.IcPin(name=nm, side=side, slot=f'{n - i}/{n}',
                                  anchorname=nm, lblsize=7))
    for side, names in (('top', top), ('bottom', bot)):
        n = len(names)
        for i, nm in enumerate(names):
            if isinstance(nm, tuple):  # (name, pos): pin at fraction pos along the edge
                pins.append(elm.IcPin(name=nm[0], side=side, pos=nm[1],
                                      anchorname=nm[0], lblsize=7))
                continue
            pins.append(elm.IcPin(name=nm, side=side, slot=f'{i + 1}/{n}',
                                  anchorname=nm, lblsize=7))
    ic = A(elm.Ic(size=(w, h), pins=pins).right().at(xy).anchor('center'))
    text(xy, name, fs)
    return ic


def comp_name(op, name):
    """Name inside a comparator, at 40% of the way from the triangle's base to its tip."""
    out, base_in = P(op, 'out'), P(op, 'xy')
    sgn = 1 if out[0] > base_in[0] else -1
    tip, base = out[0] - sgn * 0.625, base_in[0] + sgn * 0.625
    text((base + 0.4 * (tip - base), out[1]), name, 8)


def comp_l(out_xy, name, minus_on_top=False):
    """Left-facing comparator, '+' (anchor in2) on top unless minus_on_top."""
    op = elm.Opamp(sign=True, leads=True).left().at(out_xy).anchor('out')
    if minus_on_top:
        op.flip()
    op = A(op)
    comp_name(op, name)
    return op


def frame(x0, y0, x1, y1, title, tx=None):
    # theta(0): otherwise Rect inherits the direction of the last drawn line
    A(elm.Rect(corner1=(x0, y0), corner2=(x1, y1), ls='--', lw=0.8, color='#6b7280').at((0, 0)).theta(0))
    text((x0 + 0.2 if tx is None else tx, y1 - 0.35), title, 9, halign='left', color='#374151')


def title(x, y, s):
    A(elm.Label().at((x, y)).label(s, halign='left', fontsize=13))


# ================================================================ top level
def draw_top():
    new_drawing()

    # ------------------------------------------------ dead time + drivers
    # Height 2.5 puts VP/VN at ±0.75, level with the MP/MN gates: VP→driver→MPC is one straight line.
    dz = block((5.0, 13.6), 4.0, 2.5, 'DEAD_ZONE', left=('VDUTY', 'LS_ALLOW'), right=('VP', 'VN'), fs=9)
    drvp = block((10.0, P(dz, 'VP')[1]), 3.0, 1.0, 'Driver', left=('in',), right=('out',), fs=8)
    drvn = block((10.0, P(dz, 'VN')[1]), 3.0, 1.0, 'Driver', left=('in',), right=('out',), fs=8)
    poly(P(dz, 'VP'), (7.7, P(dz, 'VP')[1]), (7.7, P(drvp, 'in')[1]), P(drvp, 'in'))
    poly(P(dz, 'VN'), (7.7, P(dz, 'VN')[1]), (7.7, P(drvn, 'in')[1]), P(drvn, 'in'))

    # ------------------------------------------------ power stage (BUCK)
    sw = (15.0, 13.6)
    mp = A(elm.PFet(bulk=False).right().reverse().anchor('drain').at(sw))
    mn = A(elm.NFet(bulk=False).right().reverse().anchor('drain').at(sw))
    A(elm.Vdd().at(P(mp, 'source')).label('VDD', fontsize=9))
    ygnd = sw[1] - 3.2  # every ground in the power stage sits on this line
    ms = P(mn, 'source')
    poly(ms, (ms[0], ygnd))
    A(elm.Ground().at((ms[0], ygnd)))
    po, no = P(drvp, 'out'), P(drvn, 'out')
    poly(po, P(mp, 'gate'))
    poly(no, P(mn, 'gate'))

    dot(sw)
    snub = (sw[0] + 2.6, sw[1])
    poly(sw, snub)
    dot(snub)
    A(elm.Resistor().at(snub).down().length(1.6))
    A(elm.Capacitor().down().length(1.6))
    A(elm.Ground())
    vout = (snub[0] + 4.0, sw[1])
    A(elm.Inductor2(loops=3).at(snub).to(vout))
    dot(vout)
    A(elm.Capacitor().at(vout).down().length(1.6))
    A(elm.Resistor().down().length(1.6))
    A(elm.Ground())

    # feedback dividers
    fb1 = vout[0] + 3.2
    fb2 = fb1 + 3.4
    poly(vout, (fb2, vout[1]))
    dot((fb1, vout[1]))
    # output port of SUB: tag tip points away from the circuit
    pend = (fb2 + 1.0, vout[1])
    poly((fb2, vout[1]), pend)
    port = mktag('VOUT', 10)
    A(port.left().at((pend[0] + port.params['width'], pend[1])))
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

    # ------------------------------------------------ blocks 1-3, stacked under the BUCK stage
    # Block 1 keeps its detail-diagram convention: inputs on the right, outputs on the left.
    # Other pins sit on the side their wire comes from, ordered so the right-edge risers cross as
    # little as possible. MNC enters block 1 from the top, straight down from the low-side gate.
    bw = 5.0
    bx0 = 20.0 - bw  # right edge of blocks 2/3 stays at 20
    bcx = bx0 + bw / 2
    # block 1 sits up-left of blocks 2/3 (overlapping them by ~1 unit); MUX2 sits left of block 1
    b1w = 6.4
    b1x0 = 13.0 - b1w  # right edge of block 1 stays at 13
    b1_y = 8.7  # PG / VDUTY_SEL runs below clear MUX2; SW pin stays under the low-side ground
    b1 = block((b1x0 + b1w / 2, b1_y), b1w, 3.8, BLK1, left=('PFM_LS_ALLOW', 'MODE', 'PG'),
               right=('VDUTY_SEL', 'MNC', 'SW', 'VOUTR2', 'VREF_FIX'), fs=9)
    b1_bot = b1_y - 3.8 / 2
    b2 = block((bcx, 4.6), bw, 2.0, BLK2, left=('PWM_QB',), right=('VOUTR', 'VREF'), fs=9)
    # MUX2 left of blocks 2/3; PFM sits level with its 0 input so PFM_QB is a straight wire
    in1_y = P(b2, 'PWM_QB')[1]
    mux = A(elm.Multiplexer(size=(2, 3.4), slant=-25, pins=[
        elm.IcPin(name='1', side='right', slot='2/2', anchorname='in1'),
        elm.IcPin(name='0', side='right', slot='1/2', anchorname='in0'),
        elm.IcPin(name='SEL', side='top', slot='1/1', anchorname='sel'),
        elm.IcPin(name='', side='left', slot='1/1', anchorname='y'),
    ]).right().at((b1x0 - 1.9, in1_y - 1.2)).anchor('center').label('MUX2', loc='center', fontsize=9))
    b3 = block((bcx, P(mux, 'in0')[1]), bw, 2.0, BLK3, left=('PFM_QB',), right=('PG', 'VREF', 'VOUTR2'), fs=9)

    # MNC (input, under VDUTY_SEL): low-side gate straight down, then left into the pin.
    # Its riser sits outside the VDUTY_SEL riser so the two never cross.
    xg = P(b1, 'MNC')[0] + 0.3
    dot((xg, no[1]))
    poly((xg, no[1]), (xg, P(b1, 'MNC')[1]), P(b1, 'MNC'))
    # SW: switch node straight down, then left into the pin
    xs = sw[0] + 1.1
    dot((xs, sw[1]))
    poly((xs, sw[1]), (xs, P(b1, 'SW')[1]), P(b1, 'SW'))

    # right-edge risers (x grows outward): PG, VREF bus, VOUTR, VOUTR2, SW
    # PG leaves block 1 on the left, drops below it and runs right under it to the PG riser
    xb = P(b2, 'VOUTR')[0] + 0.6  # right of blocks 2/3
    p1 = P(b1, 'PG')
    xpg, ypg = p1[0] - 0.5, b1_bot - 0.4
    poly(p1, (xpg, p1[1]), (xpg, ypg), (xb, ypg), (xb, P(b3, 'PG')[1]), P(b3, 'PG'))

    # reference right of blocks 2/3: SOFT_START <- BANDGAP; VREF feeds blocks 2 and 3,
    # VREF_FIX (tapped between them) runs straight up into block 1
    yref = P(b2, 'VREF')[1]  # PWM VREF runs straight into SOFT_START
    ss_l, ss_r, bg_l, bg_r = 22.4, 24.6, 25.4, 27.6
    block(((ss_l + ss_r) / 2, yref), ss_r - ss_l, 1.2, 'SOFT_START', fs=9)
    block(((bg_l + bg_r) / 2, yref), bg_r - bg_l, 1.2, 'BANDGAP', fs=9)
    xv = ss_l - 0.5
    poly(P(b2, 'VREF'), (xv, P(b2, 'VREF')[1]), (xv, P(b3, 'VREF')[1]), P(b3, 'VREF'))
    dot((xv, yref))
    poly((xv, yref), (ss_l, yref))
    poly((ss_r, yref), (bg_l, yref))
    ftap = ((ss_r + bg_l) / 2, yref)
    dot(ftap)
    poly(ftap, (ftap[0], P(b1, 'VREF_FIX')[1]), P(b1, 'VREF_FIX'))
    xr = n1[0] + 0.8  # VOUTR: divider tap straight down into block 2
    poly(n1, (xr, n1[1]), (xr, P(b2, 'VOUTR')[1]), P(b2, 'VOUTR'))
    xr2 = n2[0] + 0.8  # VOUTR2: divider tap down the right edge into blocks 1 and 3
    poly(n2, (xr2, n2[1]), (xr2, P(b3, 'VOUTR2')[1]), P(b3, 'VOUTR2'))
    dot((xr2, P(b1, 'VOUTR2')[1]))
    poly((xr2, P(b1, 'VOUTR2')[1]), P(b1, 'VOUTR2'))

    # ------------------------------------------------ MUX2 and the mode-select wiring
    poly(P(b2, 'PWM_QB'), P(mux, 'in1'))
    poly(P(b3, 'PFM_QB'), P(mux, 'in0'))
    sel = P(mux, 'sel')
    poly(sel, (sel[0], P(b1, 'MODE')[1]), P(b1, 'MODE'))

    # VDUTY_SEL: MUX2 output up the left edge into DEAD_ZONE, branching over the top of block 1
    # and down into its top-right pin. Its only crossing is the PFM_LS_ALLOW riser.
    ym = P(mux, 'y')
    bx = 1.8
    poly(ym, (bx, ym[1]), (bx, P(dz, 'VDUTY')[1]), P(dz, 'VDUTY'))
    vd = P(b1, 'VDUTY_SEL')
    yvd, xvd = b1_y + 3.8 / 2 + 0.4, vd[0]
    dot((bx, yvd))
    poly((bx, yvd), (xvd, yvd), (xvd, vd[1]), vd)
    # PFM_LS_ALLOW: block 1 back up into DEAD_ZONE LS_ALLOW (left pin, below VDUTY).
    # Its riser sits inside the VDUTY_SEL riser.
    dls = P(dz, 'LS_ALLOW')
    xls = dls[0] - 0.4
    poly(dls, (xls, dls[1]), (xls, P(b1, 'PFM_LS_ALLOW')[1]), P(b1, 'PFM_LS_ALLOW'))


    title(0, 16.9, 'SUB [PFM v11]  —  Synchronous buck with automatic PWM/PFM  '
                   '(VDD 3.3 V → VOUT 1.8 V, ~2.22 MHz, 1.7 µH / 20 µF)')
    save('sub_arch_teacher')


# ================================================================ block 1
def draw_blk1():
    """PFM zero-cross / diode emulation + mode detect + power-good; signal flows right-to-left."""
    new_drawing()
    # Names describe function (netlist subckt in brackets): Mode Detect (MODE_DET), PG CMP (CMP01),
    # Diode Emulation (PFM_DIODE_GATE), ZCD CMP (CMP_ZCD)
    YC = 0.0
    # PFM_DIODE_GATE: inputs on the right, outputs on the left
    dg = block((20.7, YC), 4.4, 3.4, 'Diode Emulation', right=('LS_GATE', 'DUTY', 'ZCD', 'MODE'),
               left=('IDLE', 'LS_ALLOW'), fs=9)
    zcd = comp_l((P(dg, 'ZCD')[0] + 1.8, P(dg, 'ZCD')[1]), 'ZCD CMP', minus_on_top=True)
    poly(P(zcd, 'out'), P(dg, 'ZCD'))
    A(elm.Ground().at(P(zcd, 'in2')))
    zy = P(zcd, 'in1')[1]
    zn = (P(zcd, 'in1')[0] + 0.3, zy)  # SW_PFM_ZCD: 100 Ω from SW, pulled up to VDD
    poly(zn, P(zcd, 'in1'))
    dot(zn)
    rlen = 1.6
    A(elm.Resistor().at(zn).right().length(rlen))
    sw_in = (zn[0] + rlen, zy)
    A(elm.Resistor().at(zn).up().length(1.6))
    A(elm.Vdd().label('VDD', fontsize=9))

    # MODE_DET: output (MODE) on the left, inputs on the right; PFM_IDLE level with IDLE
    idle = P(dg, 'IDLE')
    mode = block((10.3, idle[1] + 1.5), 3.6, 6.4, 'Mode Detect',
                 right=('SW', 'VTH_MODE', ' ', ' ', 'PG', ' ', ' ', 'PFM_IDLE', ' ', 'MNC_GATE'),
                 left=('MODE',), fs=9)
    poly(idle, P(mode, 'PFM_IDLE'))

    # power-good comparator drives MODE_DET PG; PG also leaves the block (to PFM_REF_START)
    mpg = P(mode, 'PG')
    pg = comp_l((mpg[0] + 3.6, mpg[1]), 'PG CMP')
    poly(P(pg, 'out'), mpg)
    pgj = (mpg[0] + 2.8, mpg[1])  # PG tap: down, then a left-pointing output tag
    dot(pgj)
    # PG and PFM_LS_ALLOW output tags share one column and one width
    ow = 'PFM_LS_ALLOW'
    xo = pgj[0] - 0.3  # flat (right) end of both output tags
    vtag(pgj, 'PG', -0.8, side='left', out=True, width=ow)
    p_in, m_in = P(pg, 'in2'), P(pg, 'in1')
    # VREF_FIX: VTH_MODE straight over CMP01, down into its '+', and out of the block
    vth = P(mode, 'VTH_MODE')
    xvf = p_in[0] + 0.6
    poly(vth, (xvf, vth[1]), (xvf, p_in[1]), p_in)
    dot((xvf, vth[1]))
    # right-hand input tags (VREF_FIX, VOUTR2, MNC, VDUTY_SEL) share one column and one width
    xt = max(xvf + 1.0, P(dg, 'LS_GATE')[0] + 0.4)
    tw = 'VDUTY_SEL'
    tag((xvf, vth[1]), 'VREF_FIX', 'right', lead=xt - xvf, width=tw)
    tag(m_in, 'VOUTR2', 'right', lead=xt - m_in[0], width=tw)

    # SW: MODE_DET SW pin across, down into the ZCD pull-up network, and out of the block
    st = P(mode, 'SW')
    poly(st, (sw_in[0], st[1]), sw_in)
    dot((sw_in[0], st[1]))
    tag((sw_in[0], st[1]), 'SW', 'right', lead=0.4)

    # MODE: MODE_DET output leaves the block, branching under the bottom into PFM_DIODE_GATE
    mt, dgm = P(mode, 'MODE'), P(dg, 'MODE')
    xm, ymo = mt[0] - 0.5, min(YC - 3.4 / 2, P(mode, 'center')[1] - 6.4 / 2) - 0.7
    poly(mt, (xm, mt[1]))
    dot((xm, mt[1]))
    tag((xm, mt[1]), 'MODE', 'left', lead=0.3, out=True)
    poly((xm, mt[1]), (xm, ymo), (dgm[0] + 0.3, ymo), (dgm[0] + 0.3, dgm[1]), dgm)

    # MNC (low-side gate), PFM_LS_ALLOW and VDUTY_SEL connect outside the block
    tag(P(mode, 'MNC_GATE'), 'MNC', 'right', lead=0.4)
    tag(P(dg, 'LS_GATE'), 'MNC', 'right', lead=xt - P(dg, 'LS_GATE')[0], width=tw)
    tag(P(dg, 'LS_ALLOW'), 'PFM_LS_ALLOW', 'left', lead=P(dg, 'LS_ALLOW')[0] - xo, out=True, width=ow)
    tag(P(dg, 'DUTY'), 'VDUTY_SEL', 'right', lead=xt - P(dg, 'DUTY')[0], width=tw)

    title(5.0, P(mode, 'SW')[1] + 1.2, 'Block 1  —  ' + BLK1)
    save('blk1_mode_detect')


# ================================================================ block 2
def draw_blk2():
    """PWM loop + reference: EA (VOUTR vs VREF) -> VCOMP vs RAMP -> PWM_QB."""
    new_drawing()
    vy = 0.0  # VCOMP line
    # Names describe function (netlist subckt in brackets): PWM CMP (CMP01), Ramp Gen (PWM_OSC),
    # Error Amp (EA)
    pwmc = comp_l((10.0, vy - 0.63), 'PWM CMP', minus_on_top=True)  # '-' (in1) on the VCOMP line
    tag(P(pwmc, 'out'), 'PWM_QB', 'left', lead=0.4, out=True)
    # ramp generator right of the comparator, RAMP level with '+' so it is one straight wire
    p_pl = P(pwmc, 'in2')
    ow = 3.6
    osc = block((p_pl[0] + 0.6 + ow / 2, p_pl[1]), ow, 1.4, 'Ramp Gen', left=('RAMP',), right=('VTH',), fs=9)
    poly(p_pl, P(osc, 'RAMP'))
    ybus = vy - 3.4  # VTH return runs under the compensation network

    ea = comp_l((23.0, vy), 'Error Amp')
    ea_m = P(ea, 'in1')
    tag(P(ea, 'in2'), 'VOUTR', 'right', lead=0.8)  # same end x as the VREF tag below
    poly(P(pwmc, 'in1'), P(ea, 'out'))
    # lead-lag compensation
    cp_x, rz_x = 19.6, 21.0
    dot((cp_x, vy))
    A(elm.Capacitor().at((cp_x, vy)).down().length(1.1))
    A(elm.Ground())
    dot((rz_x, vy))
    A(elm.Resistor().at((rz_x, vy)).down().length(1.1))
    A(elm.Capacitor().down().length(1.1))
    A(elm.Ground())

    # VREF (from SOFT_START, outside the block): into EA '-' and down to PWM_OSC VTH
    xv = ea_m[0] + 0.4
    poly(ea_m, (xv, ea_m[1]))
    dot((xv, ea_m[1]))
    tag((xv, ea_m[1]), 'VREF', 'right', lead=0.4, width='VOUTR')
    vth_o = P(osc, 'VTH')
    xj = vth_o[0] + 0.6
    poly((xv, ea_m[1]), (xv, ybus), (xj, ybus), (xj, vth_o[1]), vth_o)

    title(8.0, vy + 2.2, 'Block 2  —  ' + BLK2)
    save('blk2_pwm_loop')


# ================================================================ block 3
def draw_blk3():
    """PFM loop: VOUTR2 vs filtered VREF sets RS; TRIANGO_HZ one-shot resets it -> PFM_QB."""
    new_drawing()
    # Names describe function (netlist subckt in brackets): SR Latch (RS), PFM CMP (CMP01),
    # On-Time Gen (TRIANGO_HZ), Ref Fast-Start (PFM_REF_START)
    rs = block((12.5, 0.0), 2.4, 3.6, 'SR Latch', right=('S', 'R'), left=('Q', 'QB'), fs=9)
    cmp01 = comp_l((15.2, P(rs, 'S')[1]), 'PFM CMP')
    poly(P(cmp01, 'out'), P(rs, 'S'))
    # TRIANGO_HZ under CMP01: its right edge sits level with the CMP01 inputs
    cin = P(cmp01, 'in1')[0]
    tl = P(rs, 'R')[0] + 0.9
    tri = block(((tl + cin) / 2, P(rs, 'R')[1] - 0.6), cin - tl, 2.2, 'On-Time Gen',
                right=('VIN+', 'PFM_QB'), left=('VOUT', ' '), fs=8)
    poly(P(rs, 'R'), P(tri, 'VOUT'))

    # VREF_PFM: RC filter (CPFM_REF to ground, RPFM_REF vertical) from VREF into CMP01 '-'
    vp = P(cmp01, 'in1')[1]
    yv = P(tri, 'VIN+')[1]      # VREF line
    xend = cin + 11.0           # tags on the right edge start here
    fc = (cin + 1.6, vp)        # capacitor tap, right of TRIANGO_HZ
    fn = (cin + 3.4, vp)        # VREF_PFM node: top of the resistor (PFM_REF_START VFILTER)
    fv = (fn[0], vp - 1.4)      # VREF end of the resistor (PFM_REF_START VIN)
    poly(P(cmp01, 'in1'), fn)
    dot(fc)
    A(elm.Capacitor().at(fc).down().length(1.0))
    A(elm.Ground())
    dot(fn)
    A(elm.Resistor().at(fn).to(fv))
    dot(fv)

    # PFM_REF_START right of the resistor: VFILTER / VIN on its left, PG out on its right
    # (pins drawn by hand so VFILTER / VIN sit exactly level with the resistor ends)
    bh, bw3 = 2.2, 4.8
    bl = fn[0] + 1.5
    bcy = (fn[1] + fv[1]) / 2
    A(elm.Ic(size=(bw3, bh)).right().at((bl + bw3 / 2, bcy)).anchor('center'))
    text((bl + bw3 / 2 - 0.1, bcy), 'Ref Fast-Start', 8)
    poly(fn, (bl, fn[1]))
    poly(fv, (bl, fv[1]))
    text((bl + 0.15, fn[1]), 'VFILTER', 7, halign='left')
    text((bl + 0.15, fv[1]), 'VIN', 7, halign='left')
    pg = (bl + bw3, bcy)
    text((pg[0] - 0.15, bcy), 'PG', 7, halign='right')
    tag(pg, 'PG', 'right', lead=xend - pg[0], width='VOUTR2')

    # VREF: resistor bottom down to the VREF line, which feeds TRIANGO_HZ VIN+ and leaves the block
    poly(fv, (fv[0], yv))
    dot((fv[0], yv))
    poly(P(tri, 'VIN+'), (fv[0], yv))
    tag((fv[0], yv), 'VREF', 'right', lead=xend - fv[0], width='VOUTR2')
    tag(P(cmp01, 'in2'), 'VOUTR2', 'right', lead=xend - P(cmp01, 'in2')[0])

    # PFM_QB: TRIANGO_HZ PFM_QB out the right, back under everything into RS QB, out of the block
    qb = P(rs, 'QB')
    qb_x = qb[0] - 1.0
    tq = P(tri, 'PFM_QB')
    ybot = P(tri, 'center')[1] - 2.2 / 2 - 0.8
    xq = fn[0] - 0.3  # loop riser just left of the resistor
    poly(tq, (xq, tq[1]), (xq, ybot), (qb_x, ybot), (qb_x, qb[1]), qb)
    dot((qb_x, qb[1]))
    tag((qb_x, qb[1]), 'PFM_QB', 'left', lead=0.3, out=True)

    title(8.0, P(cmp01, 'in2')[1] + 1.6, 'Block 3  —  ' + BLK3)
    save('blk3_pfm_loop')


if __name__ == '__main__':
    draw_top()
    draw_blk1()
    draw_blk2()
    draw_blk3()
