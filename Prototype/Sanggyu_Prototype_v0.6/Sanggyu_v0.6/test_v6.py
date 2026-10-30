import unittest,json
from core import Game,break_rate
class Changes(unittest.TestCase):
 def test_target_blocks_without_spending(self):
  g=Game();g.set_target(1);before=g.dump()
  with self.assertRaises(ValueError):g.upgrade(1)
  self.assertEqual(g.dump(),before)
 def test_critical_stops_exactly_at_target(self):
  g=Game();g.cards={1:9};g.cash=10**9;g.research['crit']=5;g.set_target(10)
  g.upgrade(1,roll=0,crit_roll=0);self.assertEqual(g.cards[1],10)
  self.assertEqual(Game.load(json.loads(json.dumps(g.dump()))).target,10)
 def test_failure_branches_all_high_levels(self):
  for n in range(16,30):
   for r,want in [(0,None),(.999,n-1)]:
    g=Game();g.cards={1:n,2:n-1};g.cash=10**15
    g.upgrade(1,2,roll=1,break_roll=r);self.assertEqual(g.cards.get(1),want)
    if n>=20:self.assertNotIn(2,g.cards)
 def test_rates_increasing_and_sum(self):
  self.assertEqual(break_rate(16),10);self.assertEqual(break_rate(29),75)
  for n in range(1,30):self.assertAlmostEqual(sum(Game().outcome_rates(n)),100)
 def test_minute_settlement(self):
  g=Game();g.cards={1:20};g.work(1);cash=g.cash
  self.assertEqual(g.hunt_tick(59),0);self.assertEqual(g.cash,cash)
  self.assertGreater(g.hunt_tick(1),0);self.assertEqual(g.hunt_seconds,0)
 def test_pending_survives_return_and_save(self):
  g=Game();g.work(1);g.hunt_tick(30);pending=g.hunt_pending;g.work(1);g.hunt_tick(60)
  self.assertEqual(g.hunt_pending,pending);self.assertEqual(g.hunt_seconds,30)
  h=Game.load(json.loads(json.dumps(g.dump())));h.work(1);h.hunt_tick(30);self.assertEqual(h.hunt_seconds,0)
