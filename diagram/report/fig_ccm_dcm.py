"""圖2.3 CCM / 圖2.4 DCM 電感電流示意圖（報告用）。
斜率依本專題條件：上升 (VIN-VOUT)/L = 1.5/L，下降 VOUT/L = 1.8/L，CCM 時 D = 1.8/3.3 ≈ 0.545。
Run: python diagram/report/fig_ccm_dcm.py -> fig2_3_ccm.png, fig2_4_dcm.png
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
plt.rcParams.update({'font.family': 'DejaVu Sans', 'mathtext.fontset': 'dejavusans', 'font.size': 15})
VIN, VOUT = 3.3, 1.8
D = VOUT / VIN
UP, DN = VIN - VOUT, VOUT          # slopes (per unit L)
TS, N = 1.0, 3


def axes():
    fig, ax = plt.subplots(figsize=(9.6, 3.6), dpi=250)
    ax.set_xlim(-0.08, N * TS + 0.75); ax.set_ylim(-0.62, 1.22)
    ax.axis('off')
    ax.annotate('', xy=(N * TS + 0.3, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='-|>', lw=1.6, color='k'))
    ax.annotate('', xy=(0, 1.2), xytext=(0, 0), arrowprops=dict(arrowstyle='-|>', lw=1.6, color='k'))
    ax.text(-0.04, 1.15, '$I_L$', ha='right', va='center')
    ax.text(N * TS + 0.3, -0.1, '$t$', ha='center', va='top')
    return fig, ax


def bracket(ax, x0, x1, y, label):
    ax.plot([x0, x1], [y, y], 'k', lw=1.1)
    for x in (x0, x1):
        ax.plot([x, x], [y - 0.05, y + 0.05], 'k', lw=1.1)
    ax.text((x0 + x1) / 2, y - 0.08, label, ha='center', va='top')


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    print('saved', OUT / name)


# ---------------- CCM
fig, ax = axes()
dI = 0.62
imin = 0.28
k_up, k_dn = dI / (D * TS), dI / ((1 - D) * TS)
xs, ys = [0], [imin]
for n in range(N):
    xs += [n * TS + D * TS, (n + 1) * TS]; ys += [imin + dI, imin]
ax.plot(xs, ys, 'k', lw=2.4)
iout = imin + dI / 2
ax.plot([0, N * TS], [iout, iout], color='#2563eb', lw=1.6, ls='--')
ax.text(N * TS + 0.03, iout - 0.1, '$I_{OUT}$', color='#2563eb', va='center')
xa = N * TS + 0.42
for y in (imin, imin + dI):
    ax.plot([N * TS - 0.25, xa + 0.05], [y, y], color='#777', lw=0.9, ls=':')
ax.annotate('', xy=(xa, imin + dI), xytext=(xa, imin), arrowprops=dict(arrowstyle='<->', lw=1.1, color='#333'))
ax.text(xa + 0.04, imin + dI / 2 + 0.17, r'$\Delta I_L$', color='#333', va='center')
bracket(ax, 0, D * TS, -0.2, '$t_{ON}$')
bracket(ax, 0, TS, -0.42, '$T_S$')
save(fig, 'fig2_3_ccm.png')

# ---------------- DCM
fig, ax = axes()
ipk = 0.62
t1 = 0.30 * TS                   # on time
t2 = t1 * UP / DN                # inductor current falls faster (VOUT > VIN-VOUT)
xs, ys = [0], [0]
for n in range(N):
    x0 = n * TS
    xs += [x0 + t1, x0 + t1 + t2, (n + 1) * TS]; ys += [ipk, 0, 0]
ax.plot(xs, ys, 'k', lw=2.4)
ax.text(t1 + t2 + (TS - t1 - t2) / 2, 0.06, '$I_L = 0$', color='#dc2626', ha='center', va='bottom')
bracket(ax, 0, t1, -0.2, '$t_{ON}$')
bracket(ax, 0, TS, -0.42, '$T_S$')
save(fig, 'fig2_4_dcm.png')
