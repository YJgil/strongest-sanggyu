"""Optional desktop integration check. Uses a temporary save, never player data."""
import os, sys, json, tempfile, runpy, time, tkinter as tk
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
base=Path(__file__).resolve().parent
sys.path.insert(0,str(base))
from core import Game, price
namespace=runpy.run_path(str(base/'main.pyw'));App=namespace['App']
tmp=tempfile.TemporaryDirectory();save=Path(tmp.name)/'save.json'
old=Game().dump();del old['expedition'];save.write_text(json.dumps(old))
App.__init__.__globals__['SAVE']=save
root=tk.Tk();a=App(root);root.update();a.enter_game();root.update()
assert save.with_name('save-pre-v0.7.json').exists()
assert json.loads(save.with_name('save-pre-v0.7.json').read_text())==json.loads(json.dumps(old))

def descendants(w):
 for c in w.winfo_children():
  yield c
  yield from descendants(c)
def press(w,text):
 button=next(c for c in descendants(w) if isinstance(c,(tk.Button,ttk.Button)) and c.cget('text')==text)
 button.invoke();root.update()
def modal():return next(c for c in root.winfo_children() if isinstance(c,tk.Toplevel))

a.g.upgrade(1,roll=0);a.g.upgrade(1,roll=0);a.refresh();a.expedition_window();root.update();w=modal()
press(w,'직접 조작으로 전환');press(w,'던전 입장 · 직접 전투');press(w,'공격 · 기력 +1');w.destroy();root.update()
assert Game.load(json.loads(save.read_text())).expedition.battle['turn']==2
a.expedition_window();root.update();w=modal();press(w,'직접 조작으로 전환')
for _ in range(20):
 if not a.g.expedition.battle:break
 b=a.g.expedition.battle
 press(w,'방어 · 피해 −80%' if b['turn']%3==0 else '필살기 · 기력 3' if b['energy']>=3 else '공격 · 기력 +1')
assert a.g.expedition.cleared==1
assert a.g.cash>50000
w.destroy();a.achievements_window();root.update();w=modal()
tree=next(c for c in descendants(w) if isinstance(c,ttk.Treeview));tree.selection_set('boss_1')
press(w,'선택한 업적 보상 받기');assert 'boss_1' in a.g.expedition.claimed;w.destroy()
with patch('tkinter.messagebox.askyesno',return_value=True):a.reset()
assert a.g.expedition.cleared==1 and 'boss_1' in a.g.expedition.claimed
normal=a.g
with patch('tkinter.messagebox.askyesno',return_value=True):a.toggle_lab()
assert a.g.expedition.cleared==0
a.toggle_lab();assert a.g is normal
# Check the macOS contrast regression and actual encyclopedia navigation.
a.codex();root.update();w=modal()
buttons=[c for c in descendants(w) if isinstance(c,ttk.Button)]
assert len(buttons)==8
style=ttk.Style(root)
for button in buttons:
 name=button.cget('style')
 assert style.lookup(name,'background')=='#29334a'
 assert style.lookup(name,'foreground')=='#eef1f8'
 assert style.lookup(name,'foreground',('disabled',))=='#b8c4d8'
press(w,'다음 페이지 →')
assert any(isinstance(c,tk.Label) and c.cget('text').startswith('+2 ') for c in descendants(w))
press(w,'← 이전 페이지')
assert any(isinstance(c,tk.Label) and c.cget('text')=='+1  애기 상규' for c in descendants(w))
w.destroy()
# Show a representative live battle after the assertions.
a.g.cards[1]=6;a.g.found.update(range(1,7));a.refresh();a.expedition_window();root.update();w=modal();press(w,'직접 조작으로 전환');press(w,'던전 입장 · 직접 전투');press(w,'공격 · 기력 +1');press(w,'공격 · 기력 +1')
press(w,'자동 전투로 전환');press(w,'자동 전투 이어하기')
deadline=time.monotonic()+15
while a.g.expedition.battle and time.monotonic()<deadline:
 root.update();time.sleep(.02)
assert a.g.expedition.cleared==2
assert any(isinstance(c,tk.Label) and '클리어!' in c.cget('text') for c in descendants(w))
press(w,'강화·판매로 돌아가기')
assert not any(isinstance(c,tk.Toplevel) for c in root.winfo_children())
root.geometry('1100x740');root.update()
assert a.sellbtn.winfo_viewable()
assert a.sellbtn.winfo_rooty()+a.sellbtn.winfo_height()<root.winfo_rooty()+root.winfo_height()
assert a.tree.set('1','value')==f'{price(6):,}'
assert '팔기' in a.sellbtn.cget('text')
cash=a.g.cash;a.sellbtn.invoke();root.update()
assert 1 not in a.g.cards and a.g.cash==cash+price(6)
print('UI SMOKE OK: automatic/manual dungeon, return and sale, visible sale at minimum window size, migration, rewards, resume, lab and codex. PID',os.getpid(),flush=True)
root.destroy()
tmp.cleanup()
