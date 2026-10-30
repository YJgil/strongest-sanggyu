import unittest,json,runpy
from unittest.mock import Mock,patch
from core import Game,price,RESEARCH_PRICES
class Hunting(unittest.TestCase):
 def test_income_and_lock(self):
  g=Game();g.cards={1:20,2:19};g.work(1);before=g.cash
  self.assertEqual(g.hunt_tick(3600),int(price(20)*.02));self.assertEqual(g.cash-before,int(price(20)*.02))
  with self.assertRaises(ValueError):g.sell(1)
  with self.assertRaises(ValueError):g.upgrade(1,2)
  g.work(1);g.work(2)
  with self.assertRaises(ValueError):g.upgrade(1,2)
 def test_fraction_and_save(self):
  g=Game();g.work(1)
  for _ in range(3600):g.hunt_tick(1)
  self.assertAlmostEqual(g.cash-50000+g.hunt_remainder,3)
  h=Game.load(json.loads(json.dumps(g.dump())));self.assertEqual(h.dump(),g.dump())
 def test_one_worker_and_return(self):
  g=Game();i=g.buy();g.work(1)
  with self.assertRaises(ValueError):g.work(i)
  g.work(1);self.assertEqual(g.hunt_tick(100),0);g.sell(1)
 def test_crit_cap_and_unlock_skipped_stage(self):
  for level,expected in [(9,11),(19,21),(29,30)]:
   g=Game();g.cash=10**15;g.cards={1:level,2:level-1};g.research['crit']=5
   g.upgrade(1,2,roll=0,crit_roll=0);self.assertEqual(g.cards[1],expected);self.assertIn(level+1,g.found)
 def test_batch_price(self):self.assertEqual(RESEARCH_PRICES['batch'][0],price(30)*5//2)
class Batch(unittest.TestCase):
 def app(self,level):
  App=runpy.run_path('main.pyw')['App'];a=App.__new__(App);a.g=Game();a.g.cards={1:level};a.g.cash=10**15;a.g.research['batch']=1;a.selected=1;a.busy=False;a.protect_var=Mock();a.protect_var.get.return_value=False
  for k in ['upbtn','sellbtn','batchbtn','protect_check','result','balance','save','draw','log','refresh']:setattr(a,k,Mock())
  a.queue=[];a.delays=[];a.root=Mock()
  def schedule(ms,fn):a.queue.append(fn);a.delays.append(ms)
  a.root.after.side_effect=schedule
  a.batch_upgrade=App.batch_upgrade.__get__(a)
  return a
 def drain(self,a):
  while a.queue:a.queue.pop(0)()
 def test_ten_in_2500ms(self):
  a=self.app(1)
  with patch('core.random.random',return_value=0):a.batch_upgrade();self.drain(a)
  self.assertEqual(a.g.attempts,10);self.assertEqual(sum(a.delays),2500);self.assertEqual(a.g.cards[1],11);self.assertFalse(a.busy)
 def test_destroy_stops_not_other_card(self):
  a=self.app(16);a.g.cards[2]=1
  with patch('core.random.random',return_value=.999):a.batch_upgrade();self.drain(a)
  self.assertEqual(a.g.attempts,1);self.assertEqual(a.g.cards,{2:1})
 def test_missing_material_no_charge(self):
  a=self.app(20);before=a.g.cash;a.batch_upgrade();self.drain(a)
  self.assertEqual(a.g.attempts,0);self.assertEqual(a.g.cash,before)
