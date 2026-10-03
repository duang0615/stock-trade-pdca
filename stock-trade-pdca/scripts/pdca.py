"""Local planning artifacts and FIFO statement arithmetic; no market/order access."""
import argparse,csv,json,hashlib,html,re
from pathlib import Path
from decimal import Decimal,ROUND_FLOOR
from datetime import datetime
CHECKS=['strategy','chips','technical','instrument','risk','execution']
LABELS=['策略與選股','籌碼確認','技術型態','現股／CB選擇','損失預算與部位','進出場劇本']
def number(v):
 d=Decimal(str(v))
 if not d.is_finite():raise ValueError('數值不可為NaN或Infinity')
 return d
def scenario(s):
 required=['instrument','entry','stop','risk_budget_ntd','fee_buy_ntd','fee_sell_ntd','tax_exit_ntd','slippage_ntd']
 if not all(k in s and s[k] is not None for k in required):return {'status':'unknown','reason':'價格停損情境欄位不完整，或此策略不設價格停損'}
 if s['instrument'] not in ['stock','cb']:raise ValueError('只支援stock/cb情境；CBAS須按契約另核算')
 vals={k:number(s[k]) for k in required if k!='instrument'}
 if any(v<0 for v in vals.values()) or vals['entry']<=vals['stop']:raise ValueError('只計多頭有效價格停損情境，費用不可為負')
 loss=(vals['entry']-vals['stop'])*1000+sum(vals[k] for k in ['fee_buy_ntd','fee_sell_ntd','tax_exit_ntd','slippage_ntd'])
 return {'status':'scenario_only','planned_loss_per_unit_ntd':str(loss),'risk_budget_unit_cap':int((vals['risk_budget_ntd']/loss).to_integral_value(rounding=ROUND_FLOOR)),'warning':'預算整張上限非最終部位；另核對資金、曝險與成交。跳空或停損無法成交可超出此額，並非保證最大損失。'}
def plan(symbol,snapshot=None):
 if not re.fullmatch(r'[0-9A-Za-z]{4,8}',symbol):raise ValueError('股號格式錯誤')
 data=dict(snapshot or {})
 if data.get('symbol',symbol)!=symbol:raise ValueError('snapshot股號與輸入不一致')
 if data.get('as_of'):
  datetime.fromisoformat(data['as_of'])
 checks={}
 for key in CHECKS:
  c=dict(data.get('checks',{}).get(key,{}) or {})
  if c.get('status','unknown') not in ['confirmed','failed','unknown']:raise ValueError('不支援的關卡狀態')
  if c.get('status')=='confirmed' and (not all(c.get(k) for k in ['evidence','source','as_of']) or not data.get('as_of')):
   c.update(status='unknown',reason='缺證據、來源或資料時點，不能標確認')
  c.setdefault('status','unknown');checks[key]=c
 if not data.get('strategy') or not data.get('plan_version'):
  checks['strategy'].update(status='unknown',reason='尚未指定策略及版本')
 state='abandon' if any(c['status']=='failed' for c in checks.values()) else 'manual_review' if all(c['status']=='confirmed' for c in checks.values()) else 'pending'
 return {'symbol':symbol,'as_of':data.get('as_of'),'strategy':data.get('strategy'),'plan_version':data.get('plan_version'),'status':state,'checks':checks,'scenario':scenario(data.get('scenario',{})),'market_fetched_by_script':False,'order_authorized':False}
def artifacts(p,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 # Never silently overwrite a frozen plan or a reconciliation.
 for name in ['plan.json','plan.md','flow.mmd','flow.svg','flow.html']:
  if (out/name).exists():raise FileExistsError('請使用新的交易／版本目錄，不覆寫原計畫')
 (out/'plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
 lines=[f"# {p['symbol']} 交易前PDCA",'',f"狀態：{p['status']}；資料時點：{p['as_of'] or '待確認'}；策略：{p['strategy'] or '待確認'}。",'','| 關卡 | 狀態 | 證據／缺口 |','|---|---|---|']
 for key,label in zip(CHECKS,LABELS):
  c=p['checks'][key];lines.append(f"| {label} | {c['status']} | {str(c.get('evidence') or c.get('reason') or '尚未取得資料').replace('|','／')} |")
 lines+=['','預計損失情境：'+json.dumps(p['scenario'],ensure_ascii=False),'','Do：保存真實成交；Check：對帳與劇本偏差；Act：一次改一個條件並保存新版本。','腳本未取即時行情，未下單；紅／綠是輸入欄位狀態，不是自動投資判斷。']
 (out/'plan.md').write_text('\n'.join(lines),encoding='utf-8')
 m=['flowchart TD',f'  S["股號 {p["symbol"]}：策略開始"]']
 for i,(key,label) in enumerate(zip(CHECKS,LABELS)):
  m.append(f'  G{i}["{label}：{p["checks"][key]["status"]}"]');m.append(f'  {"S" if i==0 else "G"+str(i-1)} --> G{i}')
 m+=['  G5 --> Q{"必要確認是否完整？"}','  Q -->|否| W["待確認／放棄；不進場"]','  Q -->|是| H["人工複核劇本與部位"]','  H --> D["Do：使用者執行，AI保存真實成交"]','  D --> C["Check：核對對帳與執行偏差"]','  C --> A["Act：一項改善，保存版本"]','  A --> S']
 (out/'flow.mmd').write_text('\n'.join(m),encoding='utf-8')
 colors={'unknown':'#fff3d9','confirmed':'#e1f1e8','failed':'#f9dede'}
 svg=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="880" viewBox="0 0 900 880"><style>text{font-family:sans-serif;fill:#193b39;font-size:19px}</style><rect width="900" height="880" fill="#f3f6f3"/>',f'<text x="35" y="42">{p["symbol"]}｜交易前確認 → 交易後PDCA</text>']
 for i,(key,label) in enumerate(zip(CHECKS,LABELS)):
  y=70+i*86;status=p['checks'][key]['status'];svg.append(f'<rect x="45" y="{y}" width="570" height="62" rx="9" fill="{colors[status]}" stroke="#89a197"/><text x="64" y="{y+38}">{html.escape(label)}：{status}</text>')
  if i<5:svg.append(f'<path d="M330 {y+62}v18m-5-5 5 5 5-5" fill="none" stroke="#32735e"/>')
 svg+=['<text x="650" y="118">unknown：先補資料</text>','<text x="650" y="150">failed：此版放棄</text>','<text x="650" y="182">confirmed：人工複核</text>','<rect x="45" y="602" width="570" height="53" fill="#d8e7ef"/><text x="65" y="635">Do：使用者交易，保留原計畫與真實成交</text>','<path d="M330 655v25m-5-5 5 5 5-5" fill="none" stroke="#32735e"/>','<rect x="45" y="682" width="570" height="53" fill="#d8e7ef"/><text x="65" y="715">Check：AI核對對帳單與執行偏差</text>','<path d="M330 735v25m-5-5 5 5 5-5" fill="none" stroke="#32735e"/>','<rect x="45" y="762" width="570" height="53" fill="#d8e7ef"/><text x="65" y="795">Act：保存一項改善，下一輪重新Plan</text>','<path d="M615 788h210V100H615" fill="none" stroke="#32735e"/><text x="650" y="840">回到下一版交易計畫</text></svg>']
 sv=''.join(svg);(out/'flow.svg').write_text(sv,encoding='utf-8');(out/'flow.html').write_text('<!doctype html><meta charset="utf-8"><title>交易PDCA流程</title>'+sv,encoding='utf-8')
def reconcile(rows,from_flat=False):
 ids=set();clean=[]
 for r in rows:
  if not r.get('fill_id') or r['fill_id'] in ids:raise ValueError('缺成交ID或重複成交ID，不重複計帳')
  ids.add(r['fill_id']);r=dict(r)
  if r.get('instrument') not in ['stock','cb'] or r.get('side') not in ['BUY','SELL']:raise ValueError('商品或買賣方向錯誤')
  dt=datetime.fromisoformat(r['time'])
  if dt.tzinfo is None:raise ValueError('時間須含時區')
  r['_dt']=dt
  for k in ['price','quantity','fee','tax']:r[k]=number(r[k])
  if r['price']<=0 or r['quantity']<=0 or r['quantity']!=int(r['quantity']) or r['fee']<0 or r['tax']<0:raise ValueError('成交價格、數量、費用錯誤')
  if not r.get('symbol'):raise ValueError('缺商品代號')
  clean.append(r)
 if not clean:raise ValueError('無成交列')
 clean.sort(key=lambda r:r['_dt']);lots={};cash=Decimal(0);realized=Decimal(0)
 for r in clean:
  key=(r['instrument'],r['symbol']);mult=Decimal(1000 if r['instrument']=='cb' else 1);q=r['quantity'];value=r['price']*mult*q;fees=r['fee']+r['tax']
  cash+=-value-fees if r['side']=='BUY' else value-fees
  if not from_flat:continue
  book=lots.setdefault(key,[])
  if r['side']=='BUY':book.append([q,r['price']*mult+fees/q]);continue
  if sum(v[0] for v in book)<q:raise ValueError('賣出超過可配對庫存；期初持倉或資料範圍須核對')
  sell_per=r['price']*mult-fees/q
  while q:
   take=min(q,book[0][0]);realized+=take*(sell_per-book[0][1]);q-=take;book[0][0]-=take
   if book[0][0]==0:book.pop(0)
 return {'fills':len(clean),'from_flat_confirmed':from_flat,'net_cashflow_ntd':str(cash),'realized_pnl_ntd':str(realized) if from_flat else None,'status':'arithmetic_checked' if from_flat else 'opening_holdings_unknown','open_positions':[{'instrument':k[0],'symbol':k[1],'quantity':str(sum(v[0] for v in book)),'cost_ntd':str(sum(v[0]*v[1] for v in book))} for k,book in lots.items() if book],'unrealized_pnl':None,'limitations':['FIFO非券商必然採用成本法','公司行動、利息股利與轉股未自動調節','劇本遵守情況須AI另核對；此為數學核對，不是完整券商驗收']}
def main():
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
 p=sub.add_parser('plan');p.add_argument('--symbol',required=True);p.add_argument('--snapshot');p.add_argument('--out',required=True)
 p=sub.add_parser('reconcile');p.add_argument('--csv',required=True);p.add_argument('--from-flat',action='store_true');p.add_argument('--out',required=True)
 a=parser.parse_args()
 if a.command=='plan':
  snapshot=json.loads(Path(a.snapshot).read_text(encoding='utf-8')) if a.snapshot else None
  result=plan(a.symbol,snapshot);artifacts(result,a.out)
 else:
  with Path(a.csv).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
  result=reconcile(rows,a.from_flat);result['source_sha256']=hashlib.sha256(Path(a.csv).read_bytes()).hexdigest();out=Path(a.out);out.mkdir(parents=True,exist_ok=True);target=out/'reconciliation.json'
  if target.exists():raise FileExistsError('請使用新的核對版本目錄')
  target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
