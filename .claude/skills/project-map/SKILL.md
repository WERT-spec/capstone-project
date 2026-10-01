---
name: project-map
description: 本專題資料夾（HSPICE 同步降壓 buck 轉換器、PWM/PFM 自動切換、專題報告）的導覽地圖：每個檔案是什麼、哪種問題該看哪個檔、哪些檔案不能直接讀、怎麼快速查子電路與量測值。只要使用者問到「某個東西在哪裡」「這個資料夾/檔案是做什麼的」「某個子電路/節點/量測值」「模擬結果數字」「報告要用哪張圖」，或要開始修改網表、testbench、繪圖腳本、報告之前需要先找到正確檔案時，都要先用這個 skill，即使使用者沒有說「資料夾」或「結構」。
---

# 專題資料夾地圖

CLAUDE.md 已經說明電路原理與撰寫規範；這個 skill 補上的是**操作層面**：檔案在哪、哪個檔能讀、怎麼不浪費 token 地取得資訊。

## 先跑一次即時掃描

檔案會變動（版本調整、重新模擬），所以不要憑記憶回答「某行在哪」或「某量測值多少」，先用腳本查目前的狀態（在專案根目錄執行）：

```
python .claude/skills/project-map/scripts/project_map.py tree            # 檔案樹＋大小
python .claude/skills/project-map/scripts/project_map.py subckt          # 所有 .SUBCKT：行號範圍＋腳位
python .claude/skills/project-map/scripts/project_map.py subckt CMP_ZCD  # 印出單一子電路全文
python .claude/skills/project-map/scripts/project_map.py meas [關鍵字]   # 把 .mt0 轉成 name = value
python .claude/skills/project-map/scripts/project_map.py check           # 版本一致性與過期路徑檢查
```

`meas` 很重要：`.mt0` 是「先列全部名稱、再列全部數值」的格式，肉眼對位很容易錯位，用腳本取值才可靠。

## 檔案地圖

| 路徑 | 內容 | 讀取方式 |
| --- | --- | --- |
| `CLAUDE.md` | 專案總說明、報告撰寫規範、電路訊號流程 | 已自動載入 |
| `hspice/sub_system.net` | 全部電路：頂層 `SUB` ＋所有子電路 | 用 `subckt` 找行號後局部讀 |
| `hspice/sub_system_tb.sp` | testbench：第 1 行版本摘要、`.lib`、電源/負載、`.IC`、`.PROBE`、`.TRAN`、`.MEAS` | 可整檔讀（約 230 行） |
| `hspice/result/sub_system_tb.mt0` | 量測結果（最新一次，會被覆蓋） | 用 `meas` |
| `hspice/result/sub_system_tb.lis` | 模擬日誌，結尾附近有易讀的量測輸出 | 用 Grep 搜 `error`/`warning`/量測名，**不要整檔讀**（約 110 KB） |
| `hspice/result/sub_system_tb.tr0` | 波形，二進位，約 18 MB | **不能讀**；只能在 cad04 用 WaveView 開 |
| `hspice/result/*.st0` / `*.pa0` | 執行統計／子電路路徑對照 | 偶爾需要時才讀 |
| `diagram/v11/draw_sub_v11.py` → `sub_arch_v11.*` | 詳細架構圖（含元件尺寸、數值） | 改網表後要重跑 |
| `diagram/teacher/draw_sub_teacher.py` → `sub_arch_teacher.*`、`blk1/2/3_*` | 簡報／報告用的簡化架構圖與三張子區塊圖 | 改網表後要重跑 |
| `report/報告書_前模擬.docx` / `.pdf` | 我們的報告草稿 | 讀 docx/pdf 用對應的 skill；pdf 用 `pages` 分段 |
| `report/報告書_截圖清單.md` | 報告缺的波形截圖（訊號＋時間區間）與待確認事項 | 可整檔讀 |
| `report/學長的專題.pdf` | **報告範本**（章節、用詞、排版的標準） | 2.3 MB，用 `pages` 分段讀，一次 ≤ 20 頁 |
| `.claude/settings.local.json` | 本機權限設定 | 與專題內容無關 |

這台 Windows 電腦**跑不了模擬**（模型庫路徑在 cad04 伺服器上）。凡是「改完要驗證」的工作，結論都是：交給使用者在 cad04 執行，再把 `result/` 拿回來。

## 依問題找檔案

- **某子電路怎麼接、某顆電晶體尺寸** → `subckt <名稱>`；頂層接線看 `subckt SUB`。比較器腳位順序不一致（見 CLAUDE.md），重新接線前先看 `.SUBCKT` 定義行。
- **某節點在 tb 的階層名稱**（例如 `X_SYS.XMODE_DET.N_TMR`）→ Grep `sub_system_tb.sp` 的 `.IC`／`.PROBE`；實例名稱在 `SUB` 內以 `X` 開頭。
- **某個規格數字（輸出電壓、漣波、負載調節率、頻率、效率、模式切換延遲）** → `meas <關鍵字>`，再到 tb Grep 同名 `.MEAS` 看它的量測視窗（`FROM=`/`TO=`/`TD=`），寫報告時要一起交代條件。
- **模擬有沒有錯** → Grep `.lis` 的 `error|warning`；CLAUDE.md 列的兩個警告是已知且無害的。
- **報告某章該怎麼寫** → 先看學長 PDF 對應章節，再看我們的草稿 PDF 同一章。
- **報告缺哪些圖、波形截哪段** → `report/報告書_截圖清單.md`。
- **架構圖要更新** → 兩支繪圖腳本都要從專案根目錄跑：`python diagram/v11/draw_sub_v11.py`、`python diagram/teacher/draw_sub_teacher.py`。
- **設計歷程（v12–v14 為何被否決）** → 只剩 CLAUDE.md 的文字紀錄；`hspice/archive/` 與舊版 `result/v1x/` 已刪除，要看舊檔只能用 `git show f8786e7:hspice/archive/v12/sub_system.net` 這類指令。

## 改檔案時的連動清單

改一處常常要同步改其他地方，漏掉的話 HSPICE 只會給警告、不會報錯，很容易沒發現：

- 改網表的**實例名稱或內部節點** → tb 的 `.IC`／`.PROBE`／`.MEAS` 階層名稱，以及兩支繪圖腳本。
- 改**元件數值** → 網表旁的 `PFM vN` 註解、tb 第 1 行標題、`.MEAS PFM_REV` 遞增、v11 架構圖（標有數值）。
- 改**負載時序或 `.TRAN`** → 所有量測視窗，以及截圖清單裡的時間區間。
- 拿回新的 `result/` 之後 → 跑 `check` 確認 `PFM_REV` 與 tb 一致，再用 `meas` 更新報告裡的數字。

## 已知的過期內容

`check` 會列出仍引用舊路徑（`result/v11/`、`archive/v11/`）的地方。目前已知的有：截圖清單第 10 行（實際檔案是 `hspice/result/sub_system_tb.tr0`），以及兩支繪圖腳本開頭的 docstring（只是註解，不影響執行）。回答時以實際路徑為準。
