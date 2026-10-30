import json
import unittest
from core import Game, price
from expedition import BOSSES, Expedition, reward_for


class IntuitiveDungeon(unittest.TestCase):
    def auto_finish(self, g):
        for _ in range(50):
            result = g.expedition_action(g.expedition.recommended_action())
            if result[0] != 'ongoing':return result
        self.fail('Automatic battle did not finish')

    def test_auto_wins_every_boss_at_minimum_level(self):
        g = Game()
        for stage, (_, level, _) in enumerate(BOSSES):
            g.cards[1] = level
            g.start_expedition(1)
            status, reward, _ = self.auto_finish(g)
            self.assertEqual(status, 'won')
            self.assertEqual(reward, reward_for(stage))

    def test_selling_fighter_keeps_saved_battle_and_sale_money(self):
        g = Game(); g.cards[1] = 3; g.start_expedition(1)
        g.expedition_action('attack'); cash = g.cash
        self.assertEqual(g.sell(1), price(3))
        self.assertEqual(g.cash, cash + price(3))
        g = Game.load(json.loads(json.dumps(g.dump())))
        self.assertFalse(g.cards)
        status, reward, _ = self.auto_finish(g)
        self.assertEqual(status, 'won')
        self.assertEqual(g.cash, cash + price(3) + reward)

    def test_resume_automatic_turns_matches_uninterrupted_battle(self):
        g = Game(); g.cards[1] = 6; g.start_expedition(1)
        expected = Game.load(json.loads(json.dumps(g.dump())))
        self.auto_finish(expected)
        while g.expedition.battle:
            g.expedition_action(g.expedition.recommended_action())
            g = Game.load(json.loads(json.dumps(g.dump())))
        self.assertEqual(g.dump(), expected.dump())

    def test_no_recommended_action_outside_battle(self):
        e = Expedition(); before = e.dump()
        with self.assertRaises(ValueError):e.recommended_action()
        self.assertEqual(e.dump(), before)
