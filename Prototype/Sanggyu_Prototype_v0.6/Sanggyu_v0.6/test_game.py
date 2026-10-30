import unittest
from core import Game, RATE
class Rules(unittest.TestCase):
 def test_rates(self): self.assertEqual(len(RATE),29)
 def test_failure_boundaries(self):
  for level,expected in [(1,1),(15,14),(16,None)]:
   g=Game();g.cards={1:level};g.cash=10**9;g.upgrade(1,roll=1,break_roll=0);self.assertEqual(g.cards.get(1),expected)
 def test_material_consumed_on_failure(self):
  g=Game();g.cards={1:20,2:19};g.cash=10**9;g.upgrade(1,2,roll=1,break_roll=0);self.assertEqual(g.cards,{})
 def test_missing_material_no_charge(self):
  g=Game();g.cards={1:20};before=g.cash
  with self.assertRaises(ValueError):g.upgrade(1)
  self.assertEqual(g.cash,before)
 def test_success_and_archive(self):
  g=Game();g.cards={1:29,2:28};g.cash=10**15;g.upgrade(1,2,roll=0);self.assertEqual(g.cards,{1:30});self.assertIn(30,g.found)
 def test_rescue(self):
  g=Game();g.cash=0;g.cards={};g.rescue();self.assertEqual(g.cash,2000)
if __name__=='__main__':unittest.main()

class Persistence(unittest.TestCase):
 def test_roundtrip(self):
  import json
  g=Game();g.buy();g.upgrade(1,roll=0);h=Game.load(json.loads(json.dumps(g.dump())));self.assertEqual(h.dump(),g.dump())
 def test_reject_bad_level(self):
  d=Game().dump();d['cards']={1:100}
  with self.assertRaises(ValueError):Game.load(d)
