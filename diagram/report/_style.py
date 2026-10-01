"""報告用電路圖的共用樣式（與 fig2_5_bandgap.py 相同：黑線、藍色元件標籤、空心圓端點）。"""
import schemdraw
import schemdraw.elements as elm
import schemdraw.logic as lg

schemdraw.use('matplotlib')
BLUE = '#1f3fbf'
FS = 15


class Sch:
    def __init__(self):
        self.d = schemdraw.Drawing(show=False)
        self.d.config(unit=2.0, fontsize=FS, lw=1.4)
        self.A = self.d.add

    @staticmethod
    def P(e, n):
        return e.absanchors[n]

    def wire(self, *pts):
        for a, b in zip(pts, pts[1:]):
            self.A(elm.Line().at(a).to(b))

    def dot(self, p):
        self.A(elm.Dot(radius=0.07).at(p))

    def lab(self, p, s, ha='left', color=BLUE, fs=FS, va='center'):
        self.A(elm.Label().at(p).label(s, color=color, halign=ha, valign=va, fontsize=fs))

    def port(self, p, name, side='right', lead=0.0):
        """Open-circle terminal at p with a black name beside it."""
        x, y = p
        self.A(elm.Dot(open=True).at(p))
        if side == 'right':
            self.lab((x + 0.25, y), name, 'left', color='black')
        elif side == 'left':
            self.lab((x - 0.25, y), name, 'right', color='black')
        elif side == 'top':
            self.lab((x, y + 0.3), name, 'center', color='black', va='bottom')
        else:
            self.lab((x, y - 0.3), name, 'center', color='black', va='top')

    def vdd(self, p):
        self.A(elm.Vdd().at(p).label('VDD', fontsize=FS))

    def gnd(self, p, label=False):
        g = elm.Ground().at(p)
        if label:
            g = g.label('GND', loc='bottom', fontsize=FS)
        self.A(g)

    def save(self, path_stem):
        self.d.save(str(path_stem) + '.svg')
        self.d.save(str(path_stem) + '.png', dpi=300)
        print('saved', path_stem)
