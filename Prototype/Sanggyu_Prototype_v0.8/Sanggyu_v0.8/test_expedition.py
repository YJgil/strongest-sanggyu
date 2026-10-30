import json
import unittest
from core import Game
from expedition import Expedition, BOSSES, reward_for


class BossExpedition(unittest.TestCase):
    def win(self, expedition):
        # React to telegraphed attacks instead of relying on random rolls.
        for _ in range(100):
            b = expedition.battle
            action = 'guard' if b['turn'] % 3 == 0 else 'burst' if b['energy'] >= 3 else 'attack'
            status, reward, _ = expedition.act(action)
            if status != 'ongoing':
                self.assertEqual(status, 'won')
                return reward
        self.fail('Battle did not finish')

    def test_all_bosses_beatable_at_minimum_level(self):
        e = Expedition()
        for stage, (_, minimum, _) in enumerate(BOSSES):
            e.start(minimum)
            self.assertEqual(self.win(e), reward_for(stage))
            self.assertEqual(e.cleared, stage + 1)
        with self.assertRaises(ValueError):
            e.start(30)

    def test_unlock_and_invalid_actions_are_atomic(self):
        e = Expedition()
        with self.assertRaises(ValueError):
            e.start(1)
        e.start(3)
        before = e.dump()
        for action in ['burst', 'invalid']:
            with self.assertRaises(ValueError):
                e.act(action)
            self.assertEqual(e.dump(), before)
        with self.assertRaises(ValueError):
            e.start(30)
        self.assertEqual(e.dump(), before)

    def test_guard_reduces_telegraphed_heavy_attack(self):
        a = Expedition(); a.start(3)
        b = Expedition(); b.start(3)
        a.battle['turn'] = b.battle['turn'] = 3
        a.act('attack'); b.act('guard')
        self.assertGreater(b.battle['hp'], a.battle['hp'])
        self.assertEqual(b.battle['energy'], 1)

    def test_heal_once_and_burst_cost(self):
        e = Expedition(); e.start(3)
        e.act('attack'); e.act('attack'); e.act('guard')
        e.act('burst')
        self.assertEqual(e.battle['energy'], 0)
        e.act('heal')
        before = e.dump()
        with self.assertRaises(ValueError):
            e.act('heal')
        self.assertEqual(e.dump(), before)

    def test_defeat_does_not_change_inventory_or_cash(self):
        g = Game(); g.expedition.start(3)
        before = (g.cash, g.cards.copy(), g.found.copy())
        for _ in range(100):
            status, reward, _ = g.expedition.act('guard')
            self.assertEqual(reward, 0)
            if status == 'lost':break
        self.assertEqual(status, 'lost')
        self.assertEqual((g.cash, g.cards, g.found), before)
        self.assertEqual(g.expedition.cleared, 0)
        g.expedition.start(3)

    def test_roundtrip_mid_battle_and_completed_progress(self):
        g = Game(); g.expedition.start(3); g.expedition.act('attack')
        h = Game.load(json.loads(json.dumps(g.dump())))
        self.assertEqual(h.dump(), g.dump())
        reward = self.win(h.expedition); h.cash += reward
        h.expedition.claim(h, 'boss_1')
        loaded = Game.load(json.loads(json.dumps(h.dump())))
        self.assertEqual(loaded.dump(), h.dump())
        with self.assertRaises(ValueError):loaded.expedition.act('attack')

    def test_v6_save_migrates_without_changing_gameplay(self):
        g = Game(); data = g.dump(); del data['expedition']
        loaded = Game.load(json.loads(json.dumps(data)))
        actual = loaded.dump(); del actual['expedition']
        self.assertEqual(actual, data)
        self.assertEqual(loaded.expedition.cleared, 0)

    def test_claim_is_once_and_conditions_enforced(self):
        g = Game(); before = g.dump()
        for key in ['first_upgrade', 'unknown']:
            with self.assertRaises(ValueError):g.expedition.claim(g, key)
            self.assertEqual(g.dump(), before)
        g.upgrade(1, roll=0); cash = g.cash
        self.assertEqual(g.expedition.claim(g, 'first_upgrade'), 1000)
        self.assertEqual(g.cash, cash + 1000)
        before = g.dump()
        with self.assertRaises(ValueError):g.expedition.claim(g, 'first_upgrade')
        self.assertEqual(g.dump(), before)

    def test_reject_corrupt_campaign(self):
        e = Expedition(); e.start(3)
        for key, value in [('level', 31), ('energy', 4), ('hp', -1), ('boss_hp', 0), ('heal', 2), ('turn', 0)]:
            data = e.dump(); data['battle'][key] = value
            with self.assertRaises(ValueError):Expedition.load(data)
        for data in [{'cleared': 8}, {'cleared': -1}, {'claimed': ['fake']}, {'cleared': 7, 'battle': e.battle}]:
            with self.assertRaises(ValueError):Expedition.load(data)

    def test_dump_does_not_share_mutable_battle(self):
        e = Expedition(); e.start(3); data = e.dump(); data['battle']['hp'] = 1
        self.assertNotEqual(e.battle['hp'], 1)

    def test_game_awards_boss_reward_exactly_once(self):
        g = Game(); g.cards[1] = 3; g.start_expedition(1); before = g.cash
        while g.expedition.battle:
            b = g.expedition.battle
            action = 'guard' if b['turn'] % 3 == 0 else 'burst' if b['energy'] >= 3 else 'attack'
            status, reward, _ = g.expedition_action(action)
        self.assertEqual(status, 'won')
        self.assertEqual(g.cash, before + reward_for(0))
        with self.assertRaises(ValueError):g.expedition_action('attack')
        self.assertEqual(g.cash, before + reward_for(0))

    def test_game_rejects_missing_or_hunting_card(self):
        g = Game(); g.cards[1] = 3; g.work(1); before = g.dump()
        for uid in (1, 99):
            with self.assertRaises(ValueError):g.start_expedition(uid)
            self.assertEqual(g.dump(), before)
