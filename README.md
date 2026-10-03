# 台股交易 PDCA Skill

把波段全壘打四堂內容串成一筆完整交易：策略→選股→籌碼／技術→現股或CB→風險與部位→劇本→真實成交→對帳→PDCA。

學生安裝：把本repo的 `stock-trade-pdca` 資料夾放入AI支援的skills目錄；Codex使用 `~/.codex/skills/stock-trade-pdca`。其他AI需支援SKILL.md或將Skill入口及references加入其自訂指令；只給GitHub連結不等於AI已安裝。

使用：`使用 $stock-trade-pdca，股號2330，請依我的設定產出交易計畫、待確認事項與流程圖。` 沒有即時資料連線時先列缺口，不能生成真實即時行情。

Python3標準庫即可執行：
```
python stock-trade-pdca/scripts/pdca.py plan --symbol 2330 --out ./output/2330
python stock-trade-pdca/scripts/pdca.py reconcile --csv 我的標準成交.csv --out ./private/review
python -m unittest discover -s stock-trade-pdca/tests
```
第一個指令輸出股號計畫、Mermaid及離線SVG流程圖；完整資料由使用者AI依權限取數。第二個僅本機核對，不連券商、不下單，預設期初持倉未知。

費用按學生個人設定；第四堂CB案例採講師每邊10元、交易稅0元。套件沒有真實對帳單、個人紀錄與金鑰；紀錄要存到個人目錄。公開儲存庫：https://github.com/duang0615/stock-trade-pdca 。
