# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An HSPICE transistor-level design of a **synchronous buck DC-DC converter with automatic PWM/PFM mode switching** (3.3 V in → 1.8 V out, ~2.22 MHz switching, 1.7 µH / 20 µF output filter). It uses the TSMC 0.18 µm 3.3 V device models (`PCH3`, `NCH3`, `pnp10`). There's no build system or git repo. Besides the HSPICE deck, the only code is the Python diagram scripts in `diagram/`.

- [hspice/sub_system.net](hspice/sub_system.net): the whole circuit, meaning the top-level `SUB` subckt and every leaf subckt.
- [hspice/sub_system_tb.sp](hspice/sub_system_tb.sp): testbench with supply, load step, `.IC`s, probes and `.MEAS` checks.
- `hspice/archive/vN/`: archived decks for v11–v14. Each folder holds `sub_system.net` and `sub_system_tb.sp` under their original names, because every tb does `.INCLUDE 'sub_system.net'`. That lets you rerun an archived revision from inside its folder. The working deck is currently byte-identical to `archive/v11/`.
- `hspice/result/vN/`: simulator output per revision (`.lis` log plus measure printout, `.mt0` measure table, `.tr0` waveforms, `.st0` run stats, `.pa0` subckt path map). These are generated files. Nothing sits directly in `result/`, so copy each run into its `vN/` folder.
- `hspice/sxcmd.log`: WaveView GUI replay log. It's noise, so ignore it.
- `diagram/`: top-level `SUB` architecture diagrams drawn with Python + `schemdraw`. Net names follow `hspice/archive/v11/sub_system.net`.
  - `diagram/v11/draw_sub_v11.py` writes `sub_arch_v11.svg`/`.png`. This is the detailed version, with the device sizes, component values and driver-chain labels.
  - `diagram/teacher/draw_sub_teacher.py` writes `sub_arch_teacher.svg`/`.png`. It's a simplified copy of the v11 script for presentation, with no component values, the driver chain shown as "Driver", and slightly different spacing.
  - Run either one from the project root (`python diagram/<dir>/<script>.py`). The output goes next to the script. If the netlist changes, update both scripts.

## Running simulations

Simulation does **not** run on this Windows machine. It runs on the school's Linux CAD server (`cad04`, user `114B01`) with PrimeSim HSPICE W-2024.09-1. Run it from the `hspice/` directory:

```
hspice -i sub_system_tb.sp -o result/
```

The model library is loaded by absolute server path (`/home/114B01/Desktop/TECH/models/hspice/toplevel.l`, corner `t18_tt`), so the deck can't run locally. Edits made here have to be copied to the server, and results copied back into `result/vN/`, where N matches `PFM_REV`. To check a run:
- Measurement values are in `result/vN/sub_system_tb.mt0`, and in readable form near the end of `result/vN/sub_system_tb.lis`.
- Grep the `.lis` for `error` and `warning`. Two warnings are known and harmless: the `gnd` pin in the subckt pin list, and the `.PROBE` of `X_SYS.TRIANGO_HZ.RAMP_RST` on tb line 52, which is a wrong path (the node is `X_SYS.RAMP_RST`, and that one is probed correctly on line 69).
- Waveforms (`.tr0`) are viewed in WaveView.

## Circuit architecture (inside `SUB`)

Signal flow, from reference to power stage:

1. **Bias**: eight separate `BIAS_BLOCK_2V_LOWI` instances, one per consumer (`VBIAS_BGR`, `_CMP01`, `_TRI`, `_EA`, `_PWMOSC`, `_PWMCMP`, `_PG`, `_MODE`).
2. **Reference**: `BANDGAP_SOFT_START` gives `VREF_FIX` (the raw bandgap, used by the PG comparator and the mode threshold) and `VREF` (the soft-started reference).
3. **Two feedback dividers on VOUT**:
   - `VOUTR` (3K / 7.365K, with `CFF`) feeds the PWM error amp.
   - `VOUTR2` (3K / 7.52K) feeds the PFM comparator and the power-good comparator.
   The two bottom resistors are tuned separately so that PWM and PFM both regulate to 1.800 V.
4. **PWM path**: `EA` (VOUTR vs VREF) gives `VCOMP`, which has lead-lag compensation (`RZ_PWM`/`CZ_PWM`/`CP_PWM`). `PWM_OSC` produces the `RAMP`, and `XPWM_CMP` compares it with `VCOMP` to give `PWM_QB`.
5. **PFM path**: `VREF` is filtered to `VREF_PFM` by a 200k/47p RC, which `PFM_REF_START` bypasses with a fast 22k branch until `PG` plus a delay asserts `REF_READY`. `XCMP01` (VOUTR2 vs VREF_PFM) gives `S1`, which sets the `RS` latch (`XRS2`). The latch is reset by `TRIANGO_HZ`, a one-shot on-time generator whose C1 sets the PFM frequency. Its output is `PFM_Q`/`PFM_QB`.
6. **Mode detect** (`MODE_DET`): detects zero-crossing on `SW` while the low side is on and PG is high, or `PFM_IDLE`. It discharges a timer cap `N_TMR`, and if no ZCD is seen the timer charges past `VREF_FIX`, which gives `MODE=1` (PWM). `MODE=0` means PFM.
7. **`MUX2`** picks `PFM_QB` (MODE=0) or `PWM_QB` (MODE=1) and outputs `VDUTY_SEL`. This feeds `DEAD_ZONE` (non-overlap), which gives `VP_RAW_DEAD`/`VN_RAW_DEAD`. These go through 4-stage tapered driver chains (`INV`, then `INV_DRV1`, `INV_DRV2`, `INV_DRV3`) to `MPC`/`MNC`.
8. **PFM low-side stop**: `CMP_ZCD` senses `SW_PFM_ZCD`, which is `SW` through 100 Ω and deliberately biased up by `RZCD_LEAD` from VDD so the stop fires early to cover comparator delay. `PFM_DIODE_GATE` latches `PFM_IDLE` and drops `PFM_LS_ALLOW` into `DEAD_ZONE`, which turns the low-side FET off (diode emulation). In PWM, `MODE=1` bypasses this.
9. **`BUCK`**: the power FETs, L1, C1 with 20 mΩ ESR, and an RC snubber on `SW`.

### Netlist gotchas

- **Comparator pin orders differ**. `CMP01` is `(VIN+ VIN-)`, but `CMP01_BG` is `(VIN- VIN+)`. Check the `.SUBCKT` line before you rewire any comparator.
- Every subckt has a pin named `GND`. HSPICE treats this as a local pin (hence the warning), so ground has to be passed down explicitly.
- `CMP_ZCD` is instantiated with `GND` on `VIN_P` and the sensed switch node on `VIN_N`.

## Testbench conventions

- **Load profile**: 50 mA, stepping to 500 mA at 32 µs for ~20 µs, then back to 50 mA. The run is `.TRAN 1n 80u UIC`, so there's only one step. The measurement windows depend on this timing:
  - startup: 0–32 µs
  - heavy load / PWM: 42–51 µs
  - light load / PFM: 62–71 µs and 70–79 µs, plus the long window 62–79 µs

  If you change `ILOAD_STEP` or `.TRAN`, update every `FROM=`/`TO=`/`TD=` to match.
- **Logic thresholds**: 1.65 V for edge crossings, and `VLOGIC_H=2.31` / `VLOGIC_L=0.99` for high/low checks.
- **`.IC` and `.PROBE` use hierarchical node names** (`X_SYS.XMODE_DET.N_TMR`, etc.). If you rename an instance or internal node in the netlist, update the testbench to match. Otherwise HSPICE just warns and drops the line.
- The initial conditions pre-set the latches (RS states, `ARMED`/`ARMEDB`, `PFM_Q`/`PFM_QB`, `IDLE_B`) to a consistent state. Keep complementary pairs consistent if you edit them.
- **Revision tracking**: design iterations are tagged `PFM vN` in netlist comments next to each tuned component. The tb title line (line 1) summarizes the current tuned values. `.MEAS PFM_REV PARAM='N'` is a version marker that should match, so bump it with each revision to confirm that the returned `.mt0` comes from the current deck. The current (final) revision is v11, and its title is still marked "UNVALIDATED". Decks are archived as `archive/vN/sub_system.net` + `sub_system_tb.sp`, with results in `result/vN/`. To archive a new revision, copy both working files into `archive/vN/` and keep the original filenames. v12–v14 tried removing the `VREF_PFM` filter and `PFM_REF_START` and were rejected: without the startup-fast / steady-slow switching, the PFM period jitters (v12 348–567 ns, v14 426–488 ns, vs v11 443–452 ns), and a cap on `VREF` itself (v13) broke soft-start and the PWM handover.
