# Snapshot格式

JSON：symbol、as_of、strategy、plan_version、checks、scenario。checks必須包含 strategy、chips、technical、instrument、risk、execution 六項，各項值含 status、evidence、source、as_of。status僅 confirmed / failed / unknown。腳本確認的是欄位完整，不能替代AI對來源真假及規則的判讀。

scenario可填 instrument（stock / cb）、entry、stop、risk_budget_ntd、fee_buy_ntd、fee_sell_ntd、tax_exit_ntd、slippage_ntd；皆為本次情境的明確值。預計一單位損失=(entry−stop)×multiplier+費用稅滑價，multiplier現股1000（一張）、CB1000（面額10萬元）。只適用明確價格停損情境，不設停損時不要填假的stop。按風險預算與情境估算整張上限，再另外檢查可用資金與總曝險。數字是假設，不是保證成交。

Snapshot缺項時腳本標待確認。任何failed表示該版本條件不合；unknown不等於不合也不等於通過。所有confirmed也只表示可交人工複核，非自動交易。

CSV標準欄位：fill_id,time,symbol,instrument,side,price,quantity,fee,tax。side為BUY或SELL；quantity現股為股、CB為面額10萬元交易單位；price現股為每股元、CB為百元報價。所有費用稅為本筆實收新臺幣；CSV請按完整成交明細整理，不重複加入日彙總列。時間使用含時區ISO8601，日期範圍及期初持倉另核對。示例資料只在tests為虛構核算，不是真實交易。
