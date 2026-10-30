import unittest, runpy
from unittest.mock import Mock, patch
from pathlib import Path
from core import Game, NAMES
from PIL import Image
App=runpy.run_path(str(Path(__file__).with_name('main.pyw')))['App']
class Controls(unittest.TestCase):
 def make_app(self):
  a=App.__new__(App);a.g=Game();a.busy=False;a.buy_ready_at=0;a.root=Mock();a.buybtn=Mock();a.result=Mock();a.log=Mock();a.refresh=Mock();return a
 def test_purchase_cooldown(self):
  a=self.make_app()
  with patch('time.monotonic',return_value=100):
   a.buy();a.buy();self.assertEqual(len(a.g.cards),2);self.assertEqual(a.g.cash,49800)
  with patch('time.monotonic',return_value=100.499):a.buy();self.assertEqual(len(a.g.cards),2)
  with patch('time.monotonic',return_value=100.5):a.buy();self.assertEqual(len(a.g.cards),3)
 def test_busy_blocks_purchase(self):
  a=self.make_app();a.busy=True;a.buy();self.assertEqual(len(a.g.cards),1)
 def test_hotkeys(self):
  a=self.make_app();a.upgrade=Mock();a.buy=Mock();e=Mock();e.widget.winfo_toplevel.return_value=a.root;e.state=0
  for key,fn in [('space',a.upgrade),('b',a.buy),('B',a.buy)]:
   fn.reset_mock();e.keysym=key;self.assertEqual(a.hotkey(e),'break');fn.assert_called_once()
  a.buy.reset_mock();e.widget.winfo_toplevel.return_value=object();a.hotkey(e);a.buy.assert_not_called()
 def test_images_and_names(self):
  import json
  root=Path(__file__).parent/'assets';sources=json.loads((root/'sources.json').read_text())
  for n in range(1,31):
   self.assertEqual(sources[str(n)].split('_',1)[1][:-4].replace(' ',''),NAMES[n-1].replace(' ',''))
   with Image.open(root/f'{n:02}.png') as im:im.load();self.assertLessEqual(im.height,300);self.assertEqual(im.mode,'RGBA')

class FocusRegression(Controls):
 def test_readonly_controls_allow_keys(self):
  import tkinter as tk
  from tkinter import ttk
  for kind in (tk.Text,ttk.Combobox):
   a=self.make_app();a.upgrade=Mock()
   widget=Mock(spec=kind);widget.winfo_toplevel.return_value=a.root;widget.cget.return_value='disabled' if kind==tk.Text else 'readonly'
   e=Mock(widget=widget,keysym='space',state=0)
   a.hotkey(e);a.upgrade.assert_called_once()
 def test_korean_b_key(self):
  a=self.make_app();a.buy=Mock();e=Mock(keysym='Hangul_YU',char='ㅠ',state=0);e.widget.winfo_toplevel.return_value=a.root
  a.hotkey(e);a.buy.assert_called_once()
