# CLAUDE.md

本檔案提供 Claude Code（claude.ai/code）在此專案中工作時的指引。

## 核心任務

本專題的主要工作是撰寫**「以 HSPICE 做積體電路設計的同步降壓（buck）DC-DC 轉換器」專題報告**。電路設計已大致定案（v11），目前的重點在於把設計、模擬結果整理成報告。

### 報告撰寫規範（必須遵守）

撰寫或規劃報告章節時，**必須嚴格參考 [report/學長的專題.pdf](report/學長的專題.pdf)**，模仿它的章節結構、排版邏輯、專業用詞與論述方式。學長報告的重點如下：

- **前置頁**：封面（校系、實務專題、英文題目＋中文題目、指導教授、專題學生與學號、中華民國年月）→ 審定書 → 授權同意書 → 目錄 → 圖目錄 → 表目錄 → 中文摘要 → Abstract → 致謝。
- **章節結構**：
  - 第一章 緒論：1-1 研究動機、1-2 研究目的（條列）、1-3 研究方法、1-4 研究流程（附流程圖）。
  - 第二章 原理與各子電路：先寫切換式轉換器概念、本次設計架構、CCM/DCM 工作模式，再**一個子電路一節**（放大器、比較器、鋸齒波產生器、RS 栓鎖器、死區電路、PWM 架構、ZCD……），最後是效能指標（線性調節率、負載調節率）。
  - 第三章 電路模擬結果（學長還包含佈局圖）：暫態響應（undershoot/overshoot）、模擬數據表、與預期規格或文獻的 Performance Comparison 表。
  - 第四章 結論與未來展望。
  - 參考文獻（IEEE 格式，編號 [1]、[2]…）。
- **子電路小節的寫法**：標題用「中文名稱（English Name）」→ 先放電路圖「圖2.X …[n]」→ 說明「如圖2.X 所示」，逐一交代各電晶體（M1～Mn）的功能 → 必要時列公式並編號 (2.1)、(2.2) → 放模擬波形圖，並寫出關鍵數值（如延遲時間、DC Gain、Phase Margin）。
- **用詞與格式**：專有名詞第一次出現時寫成「中文（English, 縮寫）」，例如「零電流檢測電路（Zero Current Detector, ZCD）」；圖表依章節編號（圖2.1、表3.1），圖說放在圖下方；引用文獻放在句中或圖說後面。
- 我們的電路比學長多了 **PFM 模式與 PWM/PFM 自動切換**（模式偵測、PFM 迴路、diode emulation 等），這些在第二章要比照同樣格式另外寫小節。

## 專案簡介

這是一個以 HSPICE 做電晶體層級設計的**具 PWM/PFM 自動模式切換的同步降壓 DC-DC 轉換器**（輸入 3.3 V → 輸出 1.8 V，切換頻率約 2.22 MHz，輸出濾波 1.7 µH / 20 µF）。使用 TSMC 0.18 µm 3.3 V 元件模型（`PCH3`、`NCH3`、`pnp10`），沒有建置系統。除了 HSPICE deck 之外，唯一的程式碼是 `diagram/` 裡的 Python 繪圖腳本。

## 目錄結構

- `hspice/`：目前的電路與測試平台。
  - [hspice/sub_system.net](hspice/sub_system.net)：整個電路，包含頂層 `SUB` 子電路與所有底層子電路。
  - [hspice/sub_system_tb.sp](hspice/sub_system_tb.sp)：測試平台（testbench），包含電源、負載步階、`.IC`、探針與 `.MEAS` 量測。
- `hspice/result/`：最新一次的模擬輸出，直接放在這一層，不另外分版本資料夾（`.lis` 日誌與量測輸出、`.mt0` 量測表、`.tr0` 波形、`.st0` 執行統計、`.pa0` 子電路路徑對照）。每次重新模擬都直接覆蓋。
- `diagram/`：以 Python + `schemdraw` 繪製的架構圖與繪圖腳本。節點名稱依照 `hspice/sub_system.net`。
  - `diagram/teacher/`：簡報及報告用的參考架構圖。`draw_sub_teacher.py` 會產生 `sub_arch_teacher.svg`/`.png`（頂層，區塊 1–3 收合），以及 `blk1_mode_detect`、`blk2_pwm_loop`、`blk3_pfm_loop` 三張子區塊圖。圖上不標元件數值，驅動鏈只標示為「Driver」。
  - `diagram/v11/`：目前版本（v11）的詳細架構圖。`draw_sub_v11.py` 會產生 `sub_arch_v11.svg`/`.png`，圖上標有元件尺寸、元件數值與驅動鏈標籤。
  - 所有腳本都從專案根目錄執行（`python diagram/<dir>/<script>.py`），輸出檔會放在腳本旁邊。如果網表有變動，`v11` 和 `teacher` 都要同步更新。
- `report/`：專題報告相關檔案。
  - `報告書_前模擬.docx`/`.pdf`：我們的報告草稿（前模擬）。
  - `報告書_截圖清單.md`：報告中還缺的截圖清單。
  - `學長的專題.pdf`：**報告範本**，章節、排版、用詞都以它為準（見上方「報告撰寫規範」）。

## 執行模擬

模擬**無法**在這台 Windows 電腦上執行，而是在學校的 Linux CAD 伺服器（`cad04`，帳號 `114B01`）上用 PrimeSim HSPICE W-2024.09-1 執行。請在 `hspice/` 目錄下執行：

```
hspice -i sub_system_tb.sp -o result/
```

模型庫是用伺服器上的絕對路徑載入（`/home/114B01/Desktop/TECH/models/hspice/toplevel.l`，corner 為 `t18_tt`），所以 deck 無法在本機執行。在這裡做的修改必須先複製到伺服器，跑完後再把結果複製回 `hspice/result/`。檢查執行結果的方式：
- 量測值在 `result/sub_system_tb.mt0`，比較好讀的版本在 `result/sub_system_tb.lis` 的結尾附近。
- 在 `.lis` 中搜尋 `error` 與 `warning`。有兩個已知且無害的警告：一是子電路腳位列表中的 `gnd` 腳位；二是 tb 對 `X_SYS.TRIANGO_HZ.RAMP_RST` 的 `.PROBE`，這是錯誤路徑（實際節點是 `X_SYS.RAMP_RST`，另一行已經正確探測）。
- 波形（`.tr0`）用 WaveView 檢視，報告用的波形截圖也從這裡擷取。

## 電路架構（`SUB` 內部）

訊號流程，從參考電壓到功率級：

1. **偏壓**：八個獨立的 `BIAS_BLOCK_2V_LOWI` 實例，每個使用端各一個（`VBIAS_BGR`、`_CMP01`、`_TRI`、`_EA`、`_PWMOSC`、`_PWMCMP`、`_PG`、`_MODE`）。
2. **參考電壓**：`BANDGAP_SOFT_START` 輸出 `VREF_FIX`（原始 bandgap 電壓，供 PG 比較器與模式判斷門檻使用）與 `VREF`（經軟啟動的參考電壓）。
3. **VOUT 上的兩組回授分壓**：
   - `VOUTR`（3K / 7.365K，含 `CFF`）接到 PWM 誤差放大器。
   - `VOUTR2`（3K / 7.52K）接到 PFM 比較器與 power-good 比較器。
   兩個下方電阻分別調整，讓 PWM 與 PFM 都穩壓在 1.800 V。
4. **PWM 路徑**：`EA`（VOUTR 對 VREF）輸出 `VCOMP`，具有 lead-lag 補償（`RZ_PWM`/`CZ_PWM`/`CP_PWM`）。`PWM_OSC` 產生 `RAMP`，`XPWM_CMP` 將它與 `VCOMP` 比較後輸出 `PWM_QB`。
5. **PFM 路徑**：`VREF` 經 200k/47p 的 RC 濾波成 `VREF_PFM`。在 `PG` 加上延遲讓 `REF_READY` 成立之前，`PFM_REF_START` 會用快速的 22k 支路旁路這個濾波。`XCMP01`（VOUTR2 對 VREF_PFM）輸出 `S1`，用來 set `RS` 栓鎖器（`XRS2`）。栓鎖器由 `TRIANGO_HZ` 重置，這是一個單擊（one-shot）導通時間產生器，它的 C1 決定 PFM 頻率。輸出為 `PFM_Q`/`PFM_QB`。
6. **模式偵測**（`MODE_DET`）：在下管導通且 PG 為高時偵測 `SW` 的過零點，或偵測 `PFM_IDLE`。偵測到時會讓計時電容 `N_TMR` 放電；如果一直沒偵測到 ZCD，計時電容會充電到超過 `VREF_FIX`，輸出 `MODE=1`（PWM）。`MODE=0` 表示 PFM。
7. **`MUX2`** 選擇 `PFM_QB`（MODE=0）或 `PWM_QB`（MODE=1），輸出 `VDUTY_SEL`，送進 `DEAD_ZONE`（非重疊產生）得到 `VP_RAW_DEAD`/`VN_RAW_DEAD`，再經過 4 級漸增尺寸的驅動鏈（`INV` → `INV_DRV1` → `INV_DRV2` → `INV_DRV3`）驅動 `MPC`/`MNC`。
8. **PFM 下管關斷**：`CMP_ZCD` 感測 `SW_PFM_ZCD`，也就是 `SW` 經 100 Ω 後的節點，並刻意用 `RZCD_LEAD` 從 VDD 往上偏壓，讓關斷提早觸發，以補償比較器延遲。`PFM_DIODE_GATE` 栓鎖 `PFM_IDLE`，並把 `PFM_LS_ALLOW` 拉低送進 `DEAD_ZONE`，關閉下管 FET（二極體模擬）。在 PWM 模式下，`MODE=1` 會旁路這個功能。
9. **`BUCK`**：功率 FET、L1、C1（含 20 mΩ ESR），以及 `SW` 上的 RC 緩衝電路（snubber）。

### 網表注意事項

- **比較器的腳位順序不一致**。`CMP01` 是 `(VIN+ VIN-)`，但 `CMP01_BG` 是 `(VIN- VIN+)`。重新接線任何比較器之前，先確認它的 `.SUBCKT` 定義行。
- 每個子電路都有名為 `GND` 的腳位。HSPICE 會把它當成區域腳位（所以會出現警告），因此接地必須明確地一層一層傳下去。
- `CMP_ZCD` 實例化時，`VIN_P` 接 `GND`，`VIN_N` 接被感測的切換節點。

## 測試平台慣例

- **負載波形**：50 mA，在 32 µs 時步階到 500 mA 約 20 µs，之後回到 50 mA。模擬為 `.TRAN 1n 80u UIC`，所以只有一次步階。量測視窗依照這個時序設定：
  - 啟動：0–32 µs
  - 重載 / PWM：42–51 µs
  - 輕載 / PFM：62–71 µs 與 70–79 µs，以及長視窗 62–79 µs

  如果修改 `ILOAD_STEP` 或 `.TRAN`，所有 `FROM=`/`TO=`/`TD=` 都要跟著更新。
- **邏輯門檻**：邊緣跨越用 1.65 V；高/低準位判斷用 `VLOGIC_H=2.31` / `VLOGIC_L=0.99`。
- **`.IC` 與 `.PROBE` 使用階層式節點名稱**（例如 `X_SYS.XMODE_DET.N_TMR`）。如果在網表中改了實例名稱或內部節點名稱，測試平台也要同步修改，否則 HSPICE 只會發出警告並忽略那一行。
- 初始條件會把各栓鎖器（RS 狀態、`ARMED`/`ARMEDB`、`PFM_Q`/`PFM_QB`、`IDLE_B`）預設成一致的狀態。修改時，互補的訊號對必須保持一致。
- **版本標記**：網表中各個調整過的元件旁有 `PFM vN` 註解，tb 第 1 行的標題摘要目前的調整數值。`.MEAS PFM_REV PARAM='N'` 是版本標記，改版時要遞增，用來確認拿回來的 `.mt0` 確實是目前 deck 跑出來的。目前（最終）版本為 v11。
- **設計歷程（可寫進報告的改良討論）**：v12–v14 曾嘗試移除 `VREF_PFM` 濾波與 `PFM_REF_START`，但都被否決。少了「啟動時快、穩態時慢」的切換，PFM 週期會抖動（v12 為 348–567 ns，v14 為 426–488 ns，v11 則為 443–452 ns）；直接在 `VREF` 上加電容（v13）則會破壞軟啟動與 PWM 的交接。
