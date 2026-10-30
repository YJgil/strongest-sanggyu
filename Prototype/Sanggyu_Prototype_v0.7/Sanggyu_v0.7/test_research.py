import unittest,json
from core import Game,price,shop_price,RESEARCH_PRICES
class Research(unittest.TestCase):
 def test_all_five_stacks_and_cap(self):
  g=Game();g.cash=10**12
  for key in g.research:
   for n,fee in enumerate(RESEARCH_PRICES[key]):
    cash=g.cash;g.research_buy(key);self.assertEqual(g.research[key],n+1);self.assertEqual(g.cash,cash-fee)
   before=g.dump()
   with self.assertRaises(ValueError):g.research_buy(key)
   self.assertEqual(before,g.dump())
  self.assertEqual(g.upgrade_ms(),500);self.assertEqual(g.success_rate(1),100);self.assertEqual(g.success_rate(20),75)
  for n in range(10,21):self.assertGreater(g.purchase_cost(n),price(n))
 def test_insufficient_research_atomic(self):
  g=Game();g.cash=0;before=g.dump()
  with self.assertRaises(ValueError):g.research_buy('luck')
  self.assertEqual(g.dump(),before)
 def test_old_save_and_roundtrip(self):
  g=Game();old=g.dump();old.pop('research');old.pop('protected');self.assertEqual(Game.load(old).research,g.research)
  g.research['speed']=5;self.assertEqual(Game.load(json.loads(json.dumps(g.dump()))).dump(),g.dump())
 def test_unlock_on_success(self):
  g=Game();g.cards={1:9};g.cash=10**9;self.assertFalse(g.shop_unlocked());g.upgrade(1,roll=0);self.assertTrue(g.shop_unlocked());self.assertIn(10,g.found)
  with self.assertRaises(ValueError):g.shop_buy(11)
 def test_discount_is_charged(self):
  g=Game();g.cash=10**12;g.research['cost']=5;g.research['shop']=5;g.found.add(10)
  before=g.cash;g.shop_buy(10);self.assertEqual(before-g.cash,g.purchase_cost(10))
  before=g.cash;g.upgrade(1,roll=0);self.assertEqual(before-g.cash,g.upgrade_cost(1))
 def test_bonus_changes_outcome(self):
  g=Game();g.cards={1:10};g.research['luck']=5;g.cash=10**9
  self.assertTrue(g.upgrade(1,roll=.68)[0])
 def test_protection_success_and_failure(self):
  for roll,expected,count in [(0,21,0),(1,20,1)]:
   g=Game();g.cards={1:20,2:19};g.found.add(20);g.cash=10**12;before=g.cash
   fee=g.upgrade_cost(20)+g.protection_cost(20)
   g.upgrade(1,2,roll=roll,protect=True)
   self.assertEqual(g.cards,{1:expected});self.assertEqual(g.protected,count);self.assertEqual(g.destroyed,0);self.assertEqual(before-g.cash,fee)
 def test_protection_invalid_no_charge(self):
  for level,unlocked,cash,material in [(19,True,10**12,None),(20,False,10**12,2),(20,True,0,2),(20,True,10**12,None)]:
   g=Game();g.cards={1:level,2:19};g.cash=cash
   if unlocked:g.found.add(20)
   before=g.dump()
   with self.assertRaises(ValueError):g.upgrade(1,material,roll=1,protect=True)
   self.assertEqual(g.dump(),before)
