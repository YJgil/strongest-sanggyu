import unittest
from core import Game,price,shop_price,inventory_order
class Features(unittest.TestCase):
 def test_shop_locked_and_range(self):
  for n in (9,10,20,21):
   g=Game();before=g.dump()
   with self.assertRaises(ValueError):g.shop_buy(n)
   self.assertEqual(before,g.dump())
 def test_unlocked_purchase_and_resale(self):
  for n in range(10,21):
   g=Game();g.found.add(n);g.cash=shop_price(n);i=g.shop_buy(n)
   self.assertEqual(g.cash,0);self.assertEqual(g.cards[i],n);g.sell(i)
   self.assertLess(g.cash,shop_price(n));self.assertGreaterEqual(shop_price(n),price(n)*1.5)
 def test_failed_purchase_unchanged(self):
  for full in (False,True):
   g=Game();g.found.add(20)
   if full:g.cards={i:1 for i in range(1,201)};g.cash=10**12
   before=g.dump()
   with self.assertRaises(ValueError):g.shop_buy(20)
   self.assertEqual(g.dump(),before)
 def test_sort_after_upgrade(self):
  cards={1:10,2:20,3:10}
  self.assertEqual(inventory_order(cards),[2,1,3]);cards[1]=21
  self.assertEqual(inventory_order(cards),[1,2,3]);self.assertEqual(inventory_order(cards,'낮은 등급순'),[3,2,1]);self.assertEqual(inventory_order(cards,'획득순'),[1,2,3])

class IntroAndModal(unittest.TestCase):
 def test_intro_key_does_not_purchase(self):
  import runpy
  from unittest.mock import Mock
  App=runpy.run_path('main.pyw')['App'];a=App.__new__(App);a.title_active=True;a.enter_game=Mock();a.buy=Mock();a.upgrade=Mock()
  self.assertEqual(a.hotkey(Mock(keysym='b')),'break');a.enter_game.assert_called_once();a.buy.assert_not_called();a.upgrade.assert_not_called()
 def test_modal_blocks_game(self):
  import runpy
  from unittest.mock import Mock
  App=runpy.run_path('main.pyw')['App'];a=App.__new__(App);a.root=Mock();a.buy=Mock();e=Mock(keysym='b');e.widget.winfo_toplevel.return_value=a.root
  a.hotkey(e);a.buy.assert_not_called()
