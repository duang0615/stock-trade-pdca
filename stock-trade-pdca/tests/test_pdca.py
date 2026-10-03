"""Synthetic fixtures only: not real trading statements."""
import unittest,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('pdca',Path(__file__).parents[1]/'scripts/pdca.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fill(i,side,q,p,instrument='cb',fee='10'):
 return dict(fill_id=str(i),time=f'2026-01-0{i}T13:30:00+08:00',symbol='TEST01',instrument=instrument,side=side,price=str(p),quantity=str(q),fee=fee,tax='0')
class Checks(unittest.TestCase):
 def test_symbol_only_pending(self):self.assertEqual(m.plan('2330')['status'],'pending')
 def test_false_confirm_downgraded(self):
  snap=dict(strategy='test',plan_version='v1',checks={k:dict(status='confirmed') for k in m.CHECKS})
  self.assertEqual(m.plan('2330',snap)['status'],'pending')
 def test_missing_stop_not_zero_risk(self):self.assertEqual(m.scenario({})['status'],'unknown')
 def test_budget_not_max_guarantee(self):
  s=dict(instrument='cb',entry=120,stop=118,risk_budget_ntd=5000,fee_buy_ntd=10,fee_sell_ntd=10,tax_exit_ntd=0,slippage_ntd=0)
  self.assertEqual(m.scenario(s)['risk_budget_unit_cap'],2)
 def test_cb_fee(self):
  r=m.reconcile([fill(1,'BUY',1,120),fill(2,'SELL',1,120.05)],True)
  self.assertEqual(r['realized_pnl_ntd'],'30.00')
 def test_flat_loses_fee(self):self.assertEqual(m.reconcile([fill(1,'BUY',1,120),fill(2,'SELL',1,120)],True)['realized_pnl_ntd'],'-20')
 def test_partial_fifo(self):
  r=m.reconcile([fill(1,'BUY',2,120),fill(2,'SELL',1,121)],True)
  self.assertEqual(r['realized_pnl_ntd'],'985');self.assertEqual(r['open_positions'][0]['cost_ntd'],'120005')
 def test_unknown_opening_no_pnl(self):self.assertIsNone(m.reconcile([fill(1,'SELL',1,120)])['realized_pnl_ntd'])
 def test_inventory_gap(self):
  with self.assertRaises(ValueError):m.reconcile([fill(1,'SELL',1,120)],True)
 def test_duplicate(self):
  with self.assertRaises(ValueError):m.reconcile([fill(1,'BUY',1,120)]*2,True)
 def test_stock_units(self):self.assertEqual(m.reconcile([fill(1,'BUY',1000,100,'stock'),fill(2,'SELL',1000,101,'stock')],True)['realized_pnl_ntd'],'980.00')
if __name__=='__main__':unittest.main()
