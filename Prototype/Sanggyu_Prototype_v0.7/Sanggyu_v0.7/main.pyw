import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import json, os, time, random
from core import Game,NAMES,RATE,cost,price,required,failure,era,shop_price,inventory_order,RESEARCH_NAMES,RESEARCH_PRICES
from lore import LORE
from expedition import BOSSES, ACHIEVEMENTS, reward_for
BG='#10141e';PANEL='#192030';TEXT='#eef1f8';MUTED='#c2ccde';GOLD='#f4cc74';TEAL='#8fe3c0'
SAVE=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'StrongestSanggyu'/'save.json'
class App:
 def __init__(self,root):
  self.root=root;self.g=Game();self.lab=False;self.busy=False;self.selected=1;self.material=None;self.last_job=0;self.logs=[];self.save_failed=False;self.buy_ready_at=0.0;self.images={};self.hunt_clock=time.monotonic();self.last_hunt_save=self.hunt_clock
  if SAVE.exists():
   try:
    raw=SAVE.read_text(encoding='utf-8');data=json.loads(raw);self.g=Game.load(data)
   except Exception as e:
    messagebox.showwarning('저장 파일 확인',f'저장 파일을 읽지 못했습니다. 기존 파일을 보존하고 새로 시작합니다.\n{e}')
    try:SAVE.rename(SAVE.with_name(f'save-corrupt-{int(time.time())}.json'))
    except OSError:self.save_failed=True
   else:
    if 'expedition' not in data:
     try:
      backup=SAVE.with_name('save-pre-v0.7.json')
      if not backup.exists():backup.write_text(raw,encoding='utf-8')
     except OSError as e:
      self.save_failed=True;messagebox.showwarning('저장 백업 실패',f'기존 저장을 읽었지만 백업에 실패하여 이번 실행은 저장하지 않습니다.\n{e}')
  root.title('최강상규만들기 · Prototype 0.7');root.geometry('1280x900');root.minsize(1100,740);root.configure(bg=BG)
  style=ttk.Style();style.theme_use('clam');style.configure('Treeview',background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=36,font=('Malgun Gothic',12));style.configure('Treeview.Heading',background='#263149',foreground=TEXT,font=('Malgun Gothic',10,'bold'));style.map('Treeview',background=[('selected','#435279')]);style.configure('TCombobox',fieldbackground='#263149',foreground=TEXT)
  top=tk.Frame(root,bg=BG);top.pack(fill='x',padx=28,pady=(20,12));self.label(top,'SANGGYU / EXPEDITION UPDATE 0.7',GOLD,10).pack(anchor='w');self.label(top,'최강상규만들기',TEXT,26,True).pack(side='left');self.balance=self.label(top,'',GOLD,20,True);self.balance.pack(side='right')
  tools=tk.Frame(root,bg=BG);tools.pack(fill='x',padx=28,pady=(0,15))
  for text,fn in [('상규 백과사전',self.codex),('상규 상점',self.shop),('영구 연구',self.research_window),('자동사냥',self.hunt_window),('확률·비용표',self.table),('실험실 전환',self.toggle_lab),('새 게임',self.reset)]:self.button(tools,text,fn).pack(side='left',padx=(0,8))
  self.mode=self.label(tools,'',MUTED,10);self.mode.pack(side='right')
  journey=tk.Frame(root,bg=PANEL);journey.pack(fill='x',padx=28,pady=(0,12))
  self.button(journey,'⚔ 보스 원정',self.expedition_window,TEAL,'#10241e').pack(side='left',padx=8,pady=6)
  self.button(journey,'★ 업적 · 보상',self.achievements_window,GOLD,'#201a0e').pack(side='left',padx=4)
  self.journey_status=self.label(journey,'',MUTED,12);self.journey_status.pack(side='right',padx=16)
  body=tk.Frame(root,bg=BG);body.pack(fill='both',expand=True,padx=28)
  left_outer=tk.Frame(body,bg=PANEL);left_outer.pack(side='left',fill='both',expand=True,padx=(0,18));scroll=tk.Canvas(left_outer,bg=PANEL,highlightthickness=0);bar=ttk.Scrollbar(left_outer,orient='vertical',command=scroll.yview);bar.pack(side='right',fill='y');scroll.pack(fill='both',expand=True);scroll.configure(yscrollcommand=bar.set);left=tk.Frame(scroll,bg=PANEL);item=scroll.create_window(0,0,window=left,anchor='nw');left.bind('<Configure>',lambda e:scroll.configure(scrollregion=scroll.bbox('all')));scroll.bind('<Configure>',lambda e:scroll.itemconfigure(item,width=e.width));self.era_label=self.label(left,'',GOLD,11);self.era_label.pack(pady=(16,0));self.canvas=tk.Canvas(left,height=300,bg=PANEL,highlightthickness=0);self.canvas.pack(fill='x',padx=12)
  self.level_label=self.label(left,'',TEAL,26,True);self.level_label.pack();self.name_label=self.label(left,'',TEXT,18,True);self.name_label.configure(wraplength=550);self.name_label.pack(padx=16,pady=8)
  self.info=self.label(left,'',MUTED,11);self.info.configure(justify='center');self.info.pack(pady=8)
  self.matbox=ttk.Combobox(left,state='readonly',width=44);self.matbox.pack(pady=6);self.matbox.bind('<<ComboboxSelected>>',self.choose_material)
  self.protect_var=tk.BooleanVar(value=False);self.protect_check=tk.Checkbutton(left,text='파괴 방지 · +20 달성 시 해금',variable=self.protect_var,command=self.card,bg=PANEL,fg=GOLD,selectcolor=BG,activebackground=PANEL,activeforeground=GOLD);self.protect_check.pack(pady=2)
  targetrow=tk.Frame(left,bg=PANEL);targetrow.pack(fill='x',padx=28,pady=6);self.label(targetrow,'목표 도달 시 강화 잠금',GOLD,12,True).pack(side='left');self.target_var=tk.StringVar(value=str(self.g.target));self.targetbox=ttk.Combobox(targetrow,textvariable=self.target_var,values=list(range(1,31)),state='readonly',width=5,font=('Malgun Gothic',13));self.targetbox.pack(side='right');self.targetbox.bind('<<ComboboxSelected>>',self.change_target)
  self.upbtn=self.button(left,'강화하기',self.upgrade,TEAL,'#10241e',large=True);self.upbtn.pack(fill='x',padx=28,pady=8)
  self.batchbtn=self.button(left,'10회 연속 강화 · 연구 필요',self.batch_upgrade,GOLD,'#201a0e');self.batchbtn.pack(fill='x',padx=28,pady=(0,4))
  self.sellbtn=self.button(left,'판매하기',self.sell);self.sellbtn.pack(fill='x',padx=28,pady=(0,10));self.result=self.label(left,'상규는 아직 당신을 믿고 있습니다.',GOLD,11);self.result.configure(wraplength=560);self.result.pack(padx=18,pady=(5,18))
  right=tk.Frame(body,bg=BG,width=420);right.pack(side='right',fill='both');right.pack_propagate(False)
  self.sort_mode=tk.StringVar(value='높은 등급순');sortbox=ttk.Combobox(right,textvariable=self.sort_mode,values=('높은 등급순','낮은 등급순','획득순'),state='readonly',width=16);sortbox.pack(anchor='e',pady=(0,8));sortbox.bind('<<ComboboxSelected>>',lambda e:self.refresh())
  self.label(right,'보유 상규  /  강화할 카드를 선택하세요',TEXT,12,True).pack(anchor='w',pady=(0,10));self.tree=ttk.Treeview(right,columns=('level','name'),show='headings',height=9,selectmode='browse');self.tree.heading('level',text='강화');self.tree.heading('name',text='상규');self.tree.column('level',width=55,stretch=False);self.tree.column('name',width=330);self.tree.pack(fill='both',expand=True);self.tree.bind('<<TreeviewSelect>>',self.select)
  row=tk.Frame(right,bg=BG);row.pack(fill='x',pady=10);self.buybtn=self.button(row,'[B] +1 구매 · 200 G',self.buy);self.buybtn.pack(side='left');self.button(row,'긴급 지원',self.rescue).pack(side='right')
  self.labrow=tk.Frame(right,bg=BG);self.lab_level=tk.Spinbox(self.labrow,from_=1,to=29,width=5,font=('Malgun Gothic',12));self.lab_level.pack(side='left');self.button(self.labrow,'실험용 상규 생성',self.lab_buy).pack(side='left',padx=8)
  self.label(right,'강화의 역사',GOLD,11).pack(anchor='w',pady=(12,6));self.logbox=tk.Text(right,height=8,bg=PANEL,fg=MUTED,wrap='word',font=('Malgun Gothic',12),relief='flat',state='disabled');self.logbox.pack(fill='x')
  self.footer=self.label(root,'Space 강화 · S 판매 · B 구매 (0.5초 대기) · 자동 저장 · 재료는 성공/실패와 관계없이 소모 · 실험실 기록은 일반 도감에 반영되지 않습니다',MUTED,9);self.footer.pack(pady=14)
  root.bind_class('GameKeys','<KeyPress>',self.hotkey);root.bind_class('GameKeys','<Button-1>',self.focus_game,add='+');root.after_idle(root.focus_set);self.install_keys(root);self.canvas.bind('<Configure>',lambda e:self.draw(self.g.cards.get(self.selected,0)));root.protocol('WM_DELETE_WINDOW',self.quit);self.refresh();self.log('상규 연구소에 오신 것을 환영합니다.');root.after(100,self.resize);self.show_title();self.root.after(1000,self.hunt_pulse)
 def label(self,parent,text,color=TEXT,size=12,bold=False):return tk.Label(parent,text=text,bg=parent['bg'],fg=color,font=('Malgun Gothic',max(12,size),'bold' if bold else 'normal'))
 def button(self,parent,text,fn,bg='#29334a',fg=TEXT,large=False):
  # Aqua's native tk.Button ignores background colors. Clam ttk elements
  # render the complete palette consistently on macOS and Windows.
  name=f'Sanggyu{bg.lstrip("#")}{fg.lstrip("#")}{int(large)}.TButton'
  style=ttk.Style(self.root)
  style.configure(name,background=bg,foreground=fg,anchor='center',
   font=('Malgun Gothic',15 if large else 12,'bold' if large else 'normal'),
   padding=(14,18 if large else 9),borderwidth=1,relief='flat',
   bordercolor=bg,lightcolor=bg,darkcolor=bg,focuscolor=GOLD)
  style.map(name,background=[('disabled','#263149'),('pressed',bg),('active',bg)],
   foreground=[('disabled','#b8c4d8'),('pressed',fg),('active',fg)],
   bordercolor=[('focus',GOLD),('active',GOLD)])
  return ttk.Button(parent,text=text,command=fn,style=name,cursor='hand2')
 def log(self,t):
  self.logs.append(t);self.logbox.configure(state='normal');self.logbox.delete('1.0','end');self.logbox.insert('end','\n\n'.join(self.logs[-30:]));self.logbox.see('end');self.logbox.configure(state='disabled')
 def save(self):
  if self.lab or self.save_failed:return
  try:
   SAVE.parent.mkdir(parents=True,exist_ok=True);temp=SAVE.with_suffix('.tmp');temp.write_text(json.dumps(self.g.dump(),ensure_ascii=False),encoding='utf-8');temp.replace(SAVE)
  except OSError as e:
   self.save_failed=True;messagebox.showwarning('자동 저장 실패',f'이번 실행의 진행이 저장되지 않습니다.\n{e}')
 def select(self,event=None):
  if self.busy:return
  ids=self.tree.selection()
  if ids:self.selected=int(ids[0]);self.card()
 def choose_material(self,event=None):
  idx=self.matbox.current();self.material=self.material_ids[idx] if idx>=0 else None
 def card(self):
  self.target_var.set(str(self.g.target));self.targetbox.config(state='disabled' if self.busy else 'readonly')
  n=self.g.cards.get(self.selected);self.material=None;self.material_ids=[]
  self.batchbtn.config(state='normal' if self.g.research['batch'] and n and n<self.g.target and self.selected not in self.g.workers and not self.busy else 'disabled',text='10회 연속 강화 · 2.5초' if self.g.research['batch'] else '10회 연속 강화 · 연구 필요')
  eligible=n is not None and 20<=n<30 and self.g.protection_unlocked()
  if not eligible:self.protect_var.set(False)
  self.protect_check.config(state='normal' if eligible and not self.busy else 'disabled',text=(f'파괴 방지 · 시도마다 {self.g.protection_cost(n):,} G 추가 (성공해도 소모)' if eligible else '파괴 방지 · +20 달성 후 +20~+29에 사용'))
  if n is None:
   self.level_label.config(text='—');self.name_label.config(text='상규가 기다리고 있습니다');self.info.config(text='상규를 구매하거나, 목록에서 선택하세요.');self.era_label.config(text='EMPTY');self.upbtn.config(state='disabled');self.sellbtn.config(state='disabled');self.matbox.config(values=[]);self.matbox.set('재료 필요 없음');self.draw(0);return
  self.level_label.config(text=f'+{n:02d}');self.name_label.config(text=NAMES[n-1]);self.era_label.config(text=era(n).upper());self.draw(n)
  self.sellbtn.config(text=f'[S] 판매하기 · {price(n):,} G',state='normal');self.upbtn.config(state='normal' if n<self.g.target else 'disabled',text=f'[Space] +{n+1} 강화하기' if n<self.g.target else f'목표 +{self.g.target} 도달 · 잠금')
  self.info.config(text=f'성공 {self.g.success_rate(n)}% (+{self.g.success_rate(n)-RATE[n-1]}%p)  ·  비용 {self.g.upgrade_cost(n):,} G  ·  {self.g.upgrade_ms()/1000:g}초\n실패: {"단계 유지 (재료 소모)" if self.protect_var.get() else failure(n)}' if n<30 else '당신이 상규를 키운 것이 아닙니다.\n상규가 당신에게 시간을 준 것입니다.')
  if n<30:
   success,down,broken=self.g.outcome_rates(n,self.protect_var.get());self.info.config(text=f'성공 {success:g}% (+{success-RATE[n-1]:g}%p)  |  비용 {self.g.upgrade_cost(n):,} G\n'+(f'보호 유지 {100-success:g}%' if self.protect_var.get() else f'하락 {down:g}%  |  파괴 {broken:g}%')+f'  |  {self.g.upgrade_ms()/1000:g}초')
  req=required(n)
  if req:
   self.material_ids=[i for i,v in self.g.cards.items() if v==req and i!=self.selected and i not in self.g.workers];self.matbox.config(values=[f'#{i}  +{req} {NAMES[req-1]}' for i in self.material_ids]);self.matbox.set(f'+{req} 재료 선택 · 실패해도 소모됩니다')
   if self.material_ids:self.matbox.current(0);self.material=self.material_ids[0]
  else:self.matbox.config(values=[]);self.matbox.set('재료 필요 없음')
  if self.selected in self.g.workers:self.upbtn.config(state='disabled');self.sellbtn.config(state='disabled');self.info.config(text='자동사냥 중 · 복귀 후 강화/판매 가능')
 def refresh(self):
  ready=sum(key not in self.g.expedition.claimed and self.g.expedition.progress(self.g,metric)>=goal for key,_,metric,goal,_ in ACHIEVEMENTS)
  self.journey_status.config(text=f'보스 {self.g.expedition.cleared}/7 격파  ·  도감 {len(self.g.found)}/30  ·  수령 가능 업적 {ready}')
  self.balance.config(text=f'{self.g.cash:,} G');self.mode.config(text='실험실 · 저장 안 함' if self.lab else '일반 모드 · 자동 저장');existing=set(self.tree.get_children());wanted={str(i) for i in self.g.cards}
  for i in existing-wanted:self.tree.delete(i)
  for position,i in enumerate(inventory_order(self.g.cards,self.sort_mode.get())):
   n=self.g.cards[i]
   if str(i) in existing:self.tree.item(str(i),values=(f'+{n}',('⚔ 사냥 중 · ' if i in self.g.workers else '')+NAMES[n-1]))
   else:self.tree.insert('','end',iid=str(i),values=(f'+{n}',('⚔ 사냥 중 · ' if i in self.g.workers else '')+NAMES[n-1]))
   self.tree.move(str(i),'',position)
  if self.selected not in self.g.cards:self.selected=next(iter(self.g.cards),None)
  if self.selected is not None:self.tree.selection_set(str(self.selected))
  self.card();self.save()
 def get_image(self,n):
  if n not in self.images:
   self.images[n]=tk.PhotoImage(master=self.root,file=str(Path(__file__).resolve().parent/'assets'/f'{n:02}.png'))
  return self.images[n]
 def draw(self,n):
  c=self.canvas;c.delete('all');x=max(c.winfo_width(),1)/2
  if not n:c.create_text(x,150,text='상규를 구매하세요',fill=MUTED,font=('Malgun Gothic',18));return
  c.create_image(x,150,image=self.get_image(n))
 def install_keys(self,widget):
  widget.bindtags(('GameKeys',)+widget.bindtags())
  for child in widget.winfo_children():self.install_keys(child)
 def focus_game(self,event):
  if event.widget.winfo_toplevel()==self.root and isinstance(event.widget,(tk.Canvas,tk.Frame,tk.Label)):
   self.root.focus_set()
 def hotkey(self,event):
  if getattr(self,'title_active',False):self.enter_game();return 'break'
  if time.monotonic()<getattr(self,'input_ready_at',0):return 'break'
  if event.widget.winfo_toplevel()!=self.root or self.root.grab_current() is not None:return
  if isinstance(event.widget,(tk.Entry,tk.Spinbox,ttk.Entry,ttk.Spinbox,ttk.Combobox,tk.Text)) and str(event.widget.cget('state')) not in ('readonly','disabled'):return
  system=self.root.tk.call('tk','windowingsystem')
  alt_mask=0x20000 if system=='win32' else (0x10 if system=='aqua' else 0x8)
  if event.state & (0x4 | alt_mask):return
  if event.keysym=='space':self.upgrade();return 'break'
  if event.keysym.lower() in ('s','hangul_nieun') or getattr(event,'char','')=='ㄴ':self.sell();return 'break'
  if event.keysym.lower() in ('b','hangul_yu') or getattr(event,'char','')=='ㅠ':self.buy();return 'break'
 def release_buy(self):
  remaining=self.buy_ready_at-time.monotonic()
  if remaining>0:self.root.after(max(1,int(remaining*1000)+1),self.release_buy);return
  self.buybtn.config(state='normal',text='[B] +1 구매 · 200 G')
 def resize(self):self.card()
 def change_target(self,event=None):
  if self.busy:self.target_var.set(str(self.g.target));return
  self.g.set_target(int(self.target_var.get()));self.card();self.save();self.result.config(text=f'목표 +{self.g.target} · 도달하면 강화가 잠깁니다.',fg=GOLD)
 def buy(self):
  if self.busy or time.monotonic()<self.buy_ready_at:return
  try:self.selected=self.g.buy()
  except ValueError as e:self.result.config(text=str(e),fg='#ffb17c');return
  self.buy_ready_at=time.monotonic()+0.5
  self.buybtn.config(state='disabled',text='구매 대기 · 0.5초')
  self.root.after(500,self.release_buy)
  self.log('+1 애기 상규 입장. 아직 세상 물정을 모릅니다.');self.refresh()
 def sell(self):
  if self.busy or time.monotonic()<getattr(self,'sell_ready_at',0) or self.selected not in self.g.cards:return
  n=self.g.cards[self.selected]
  if self.selected in self.g.workers:self.result.config(text='자동사냥에서 복귀한 뒤 판매하세요.');return
  if n>=10 and not messagebox.askyesno('판매 확인',f'+{n} {NAMES[n-1]}\n{price(n):,} G에 판매할까요?'):return
  self.sell_ready_at=time.monotonic()+0.5
  value=self.g.sell(self.selected);self.log(f'+{n} 상규 판매 · +{value:,} G');self.refresh()
 def upgrade(self):
  if self.busy:return
  try:result=self.g.upgrade(self.selected,self.material,protect=self.protect_var.get())
  except ValueError as e:self.result.config(text=str(e),fg='#ffb17c');return
  self.busy=True;self.upbtn.config(state='disabled');self.sellbtn.config(state='disabled');self.save();self.result.config(text='상규가 인과관계와 협의 중입니다…',fg=GOLD);self.targetbox.config(state='disabled');self.protect_check.config(state='disabled');self.root.after(self.g.upgrade_ms(),lambda:self.reveal(result))
 def reveal(self,result):
  self.busy=False;ok,old,new=result
  if ok:text=f'{"초월 강화!" if new-old==2 else "성공!"} +{old} → +{new} · {NAMES[new-1]}';color=TEAL
  elif old==new and old>=20:text=f'파괴 방지 발동 · +{old} 유지. 강화 비용·방지 비용·재료는 소모되었습니다.';color=GOLD
  elif new is None:text=f'+{old} 상규 소멸. “상규는 퇴사했습니다.”';color='#ff8b9b'
  else:text=f'실패 · +{old} → +{new}. “근손실입니다. 의학적으로.”';color='#ffb17c'
  self.refresh();self.result.config(text=text,fg=color);self.log(text)
  if new==30:messagebox.showinfo('상규','당신이 상규를 키운 것이 아닙니다.\n상규가 당신에게 시간을 준 것입니다.')
 def rescue(self):
  if self.busy:return
  try:self.g.rescue();self.log('상규 재기재단 지원금 +2,000 G');self.refresh()
  except ValueError as e:messagebox.showinfo('긴급 지원',str(e))
 def window(self,title):
  w=tk.Toplevel(self.root);w.title(title);w.geometry('900x690');w.configure(bg=BG);return w
 def listing(self,w,cols,widths):
  f=tk.Frame(w,bg=BG);f.pack(fill='both',expand=True,padx=20,pady=15);t=ttk.Treeview(f,columns=cols,show='headings');s=ttk.Scrollbar(f,orient='vertical',command=t.yview);t.configure(yscrollcommand=s.set);s.pack(side='right',fill='y');t.pack(fill='both',expand=True)
  for c,width in zip(cols,widths):t.heading(c,text=c);t.column(c,width=width)
  return t
 def codex(self):
  w=self.window('상규 백과사전');w.geometry('1040x760');w.minsize(900,700)
  self.label(w,'THE SANGGYU ENCYCLOPEDIA',GOLD,11,True).pack(pady=(20,4))
  self.label(w,f'상규 백과사전   ·   {len(self.g.found)} / 30 발견',TEXT,23,True).pack()
  book=tk.Frame(w,bg='#d8c6a5');book.pack(fill='both',expand=True,padx=26,pady=18)
  index=tk.Frame(book,bg='#202838',width=180);index.pack(side='left',fill='y');index.pack_propagate(False)
  self.label(index,'CHAPTER INDEX',GOLD,11,True).pack(pady=18)
  page=tk.Frame(book,bg='#eee5d3');page.pack(side='left',fill='both',expand=True,padx=3)
  number=tk.Label(page,bg='#eee5d3',fg='#8b6934',font=('Arial',12,'bold'));number.pack(pady=(18,5))
  portrait=tk.Canvas(page,height=300,bg='#eee5d3',highlightthickness=0);portrait.pack(fill='x')
  name=tk.Label(page,bg='#eee5d3',fg='#262b35',font=('Malgun Gothic',19,'bold'),wraplength=680);name.pack(pady=8)
  lore=tk.Label(page,bg='#eee5d3',fg='#655644',font=('Malgun Gothic',12),wraplength=650);lore.pack(padx=15,pady=8)
  facts=tk.Label(page,bg='#eee5d3',fg='#655644',font=('Malgun Gothic',12),justify='center');facts.pack(pady=8)
  selected=[1]
  def show(n):
   selected[0]=max(1,min(30,n));n=selected[0];known=n in self.g.found
   number.config(text=f'No. {n:03d}  /  {era(n) if known else "미발견"}');portrait.delete('all');x=max(portrait.winfo_width(),640)/2
   if known:portrait.create_image(x,150,image=self.get_image(n))
   else:portrait.create_text(x,150,text='?',font=('Arial',95),fill='#baab93')
   name.config(text=f'+{n}  {NAMES[n-1]}' if known else f'+{n}  아직 기록되지 않은 존재')
   lore.config(text=LORE[n-1] if known else '강화를 통해 이 상규를 발견하면 기록이 열립니다.')
   facts.config(text=(f'판매가 {price(n):,} G  ·  '+(f'상점가 {self.g.purchase_cost(n):,} G' if 10<=n<=20 else '상점 구매 불가')+'\n'+(f'다음 강화 성공률 {self.g.success_rate(n)}% (+{self.g.success_rate(n)-RATE[n-1]}%p)  ·  실패 시 {failure(n)}' if n<30 else '최종 단계')) if known else '???')
  for start in range(1,31,5):
   self.button(index,f'{start:02d} — {start+4:02d}\n{era(start)}',lambda n=start:show(n)).pack(fill='x',padx=10,pady=5)
  nav=tk.Frame(w,bg=BG);nav.pack(pady=(0,18));self.button(nav,'← 이전 페이지',lambda:show(selected[0]-1)).pack(side='left',padx=12);self.button(nav,'다음 페이지 →',lambda:show(selected[0]+1)).pack(side='left',padx=12)
  w.bind('<Left>',lambda e:show(selected[0]-1));w.bind('<Right>',lambda e:show(selected[0]+1));portrait.bind('<Configure>',lambda e:show(selected[0]));show(1)
 def hunt_pulse(self):
  now=time.monotonic();elapsed=now-self.hunt_clock;self.hunt_clock=now
  # Credit only while the program is running; ignore sleep/suspend gaps.
  if not getattr(self,'title_active',False):self.g.hunt_tick(min(elapsed,5))
  self.balance.config(text=f'{self.g.cash:,} G')
  if now-self.last_hunt_save>=10:self.save();self.last_hunt_save=now
  self.root.after(1000,self.hunt_pulse)
 def hunt_window(self):
  if self.busy:return
  w=self.window('자동사냥');w.transient(self.root);w.grab_set();w.focus_set()
  self.label(w,'SANGGYU / HUNTING GROUNDS',GOLD,12,True).pack(pady=20)
  self.label(w,'상규를 일하게 하라',TEXT,24,True).pack()
  self.label(w,'1명 배치 · 판매가의 0.1% / 분 · 60초마다 정산 · 게임 실행 중에만 수입 발생\n사냥 중인 상규는 판매·강화·재료 사용 불가. 복귀하면 즉시 해제.',MUTED,11).pack(pady=12)
  status=self.label(w,'',TEAL,13);status.pack()
  t=self.listing(w,('번호','등급','이름','분당 G','상태'),(70,60,360,160,100));t.configure(selectmode='browse')
  def redraw():
   for i in t.get_children():t.delete(i)
   for i in inventory_order(self.g.cards):
    n=self.g.cards[i];t.insert('','end',iid=str(i),values=(i,f'+{n}',NAMES[n-1],f'{price(n)*.001:,.2f}','사냥 중' if i in self.g.workers else '대기'))
  def toggle():
   if not t.selection():return
   try:active=self.g.work(int(t.selection()[0]))
   except ValueError as e:status.config(text=str(e));return
   self.hunt_clock=time.monotonic();self.refresh();redraw();status.config(text='사냥 시작' if active else '복귀 완료')
  self.button(w,'선택한 상규 배치 / 복귀',toggle,TEAL,'#10241e').pack(pady=15)
  def pulse():
   if not w.winfo_exists():return
   status.config(text=f'보유 {self.g.cash:,} G · 다음 정산 {60-int(self.g.hunt_seconds)}초 · 누적 {self.g.hunt_pending:,.2f} G');w.after(1000,pulse)
  redraw();pulse()
 def batch_upgrade(self):
  if self.busy or not self.g.research['batch']:return
  uid=self.selected
  if uid not in self.g.cards or uid in self.g.workers:return
  protection=self.protect_var.get();self.busy=True;self.upbtn.config(state='disabled');self.sellbtn.config(state='disabled');self.batchbtn.config(state='disabled');self.protect_check.config(state='disabled')
  self.targetbox.config(state='disabled');self.batch_count=0
  def finish(reason):
   self.busy=False;self.refresh();self.result.config(text=f'연속 강화 {self.batch_count}/10회 · {reason}',fg=GOLD)
  def step():
   n=self.g.cards.get(uid)
   if n is None:finish('상규 파괴로 중단');return
   if n>=self.g.target:finish(f'목표 +{self.g.target} 도달 · 잠금');return
   material=next((i for i,v in self.g.cards.items() if v==required(n) and i!=uid and i not in self.g.workers),None)
   try:ok,old,new=self.g.upgrade(uid,material,protect=protection and n>=20)
   except ValueError as e:finish(str(e));return
   self.batch_count+=1;self.save();self.balance.config(text=f'{self.g.cash:,} G');self.draw(new or 0)
   self.result.config(text=f'연속 강화 {self.batch_count}/10 · +{old} → '+(f'+{new}' if new else '파괴'),fg=TEAL if ok else GOLD)
   self.log(f'연속 {self.batch_count}/10 · +{old} → '+(f'+{new}' if new else '파괴'))
   if new is None:finish('상규 파괴로 중단')
   elif new>=self.g.target:finish(f'목표 +{self.g.target} 도달 · 잠금')
   elif self.batch_count>=10:finish('완료')
   else:self.root.after(250,step)
  self.root.after(250,step)
 def research_window(self):
  if self.busy:return
  w=self.window('상규 영구 연구');w.geometry('940x850');w.transient(self.root);w.grab_set();w.focus_set()
  self.label(w,'SANGGYU / PERMANENT RESEARCH',GOLD,12,True).pack(pady=(22,8))
  self.label(w,'상규의 한계를 연구하다',TEXT,24,True).pack()
  balance=self.label(w,'',TEAL,15);balance.pack(pady=12)
  notice=self.label(w,'연구는 자동 저장되며 새 게임에서도 유지됩니다. 실험실 연구는 임시입니다.',MUTED,10);notice.pack(pady=6)
  rows={}
  def effect(key,n):
   return {'speed':f'{3-0.5*n:g}초','cost':f'{5*n}% 감소','shop':f'{5*n}% 할인','luck':f'+{n}%p (최대 100%)','crit':f'성공 시 {n}% 확률로 +2','batch':'2.5초에 최대 10회' if n else '잠김'}[key]
  def redraw():
   balance.config(text=f'보유 자금 {self.g.cash:,} G')
   for key,(label,btn) in rows.items():
    n=self.g.research[key];cap=len(RESEARCH_PRICES[key]);label.config(text=f'{RESEARCH_NAMES[key]}  ({n}/{cap})\n{effect(key,n)}'+(f'  →  {effect(key,n+1)}' if n<cap else '  ·  연구 완료'))
    btn.config(text=f'{RESEARCH_PRICES[key][n]:,} G · 연구' if n<cap else 'MAX',state='normal' if n<cap and self.g.cash>=RESEARCH_PRICES[key][n] else 'disabled')
  def purchase(key):
   try:self.g.research_buy(key)
   except ValueError as e:notice.config(text=str(e));return
   self.refresh();redraw();self.log(f'{RESEARCH_NAMES[key]} 연구 {self.g.research[key]}/{len(RESEARCH_PRICES[key])} 완료')
  for key in RESEARCH_NAMES:
   row=tk.Frame(w,bg=PANEL);row.pack(fill='x',padx=28,pady=4)
   label=self.label(row,'',TEXT,13,True);label.config(justify='left');label.pack(side='left',padx=18,pady=9)
   btn=self.button(row,'',lambda k=key:purchase(k),TEAL,'#10241e');btn.pack(side='right',padx=18);rows[key]=(label,btn)
  self.label(w,'파괴 방지: +20 달성 시 강화 화면에서 해금\n현재 +20~+29 전용 · 최소 2,000만 G / 시도 · 단계가 높을수록 비싸집니다.\n선택 시 성공 여부와 무관하게 비용 지불 · 실패하면 대상 유지, 재료는 소모',GOLD,11).pack(pady=15)
  redraw()
 def shop(self):
  if self.busy:return
  if not self.g.shop_unlocked():messagebox.showinfo('상점 잠김','+10 상규 강화에 성공하면 상점이 해금됩니다.');return
  w=self.window('상규 상점');w.geometry('980x760');w.transient(self.root);w.grab_set();w.focus_set()
  self.label(w,'SANGGYU EXCHANGE',GOLD,12,True).pack(pady=(18,4));self.label(w,'다시 만나는 전설',TEXT,24,True).pack()
  wallet=self.label(w,'',TEAL,14);wallet.pack(pady=8)
  self.label(w,'도달한 +10~+20 구매 가능 · 영구 연구 할인 적용 · 구매 대기 0.5초',MUTED,10).pack()
  t=self.listing(w,('단계','이름','구매가 G','판매가 G','상태'),(60,370,150,150,100));t.configure(selectmode='browse')
  for n in range(10,21):t.insert('','end',iid=str(n),values=(f'+{n}',NAMES[n-1] if n in self.g.found else '미발견 상규',f'{self.g.purchase_cost(n):,}',f'{price(n):,}','해금' if n in self.g.found else '잠김'))
  note=self.label(w,'구매할 상규를 선택하세요.',GOLD,11);note.pack(pady=6)
  def update():
   if not w.winfo_exists():return
   wallet.config(text=f'보유 자금  {self.g.cash:,} G');ids=t.selection();n=int(ids[0]) if ids else 0
   ready=time.monotonic()>=self.buy_ready_at
   allowed=n in self.g.found and 10<=n<=20 and self.g.cash>=self.g.purchase_cost(n) and len(self.g.cards)<200 and not self.busy
   btn.config(state='normal' if ready and allowed else 'disabled',text='구매 대기 · 0.5초' if not ready else '선택한 상규 구매')
  def purchase():
   if self.busy or time.monotonic()<self.buy_ready_at or not t.selection():return
   n=int(t.selection()[0])
   try:self.selected=self.g.shop_buy(n)
   except ValueError as e:note.config(text=str(e));return
   self.buy_ready_at=time.monotonic()+0.5;self.buybtn.config(state='disabled',text='구매 대기 · 0.5초');self.root.after(500,self.release_buy)
   self.refresh();self.log(f'상점 구매 · +{n} {NAMES[n-1]} · {self.g.purchase_cost(n):,} G');note.config(text=f'+{n} {NAMES[n-1]} 구매 완료');update();w.after(510,update)
  btn=self.button(w,'선택한 상규 구매',purchase,TEAL,'#10241e');btn.pack(fill='x',padx=30,pady=(8,20));t.bind('<<TreeviewSelect>>',lambda e:update());update()
 def expedition_window(self):
  if self.busy:return
  w=self.window('보스 원정 · 상규의 다음 무대');w.geometry('960x820');w.minsize(900,780);w.transient(self.root);w.grab_set();w.focus_set()
  self.label(w,'S A N G G Y U   /   B O S S   R U S H',GOLD,12,True).pack(pady=(18,4))
  title=self.label(w,'',TEXT,24,True);title.pack()
  route=self.label(w,'',TEAL,12);route.pack(pady=6)
  arena=tk.Canvas(w,bg=PANEL,height=265,highlightthickness=0);arena.pack(fill='x',padx=28,pady=8)
  stats=self.label(w,'',TEXT,13,True);stats.pack(pady=5)
  intent=self.label(w,'',GOLD,14,True);intent.pack(pady=5)
  note=self.label(w,'',MUTED,12);note.config(wraplength=860,justify='center');note.pack(padx=20,pady=5)
  actions=tk.Frame(w,bg=BG);actions.pack(pady=8)
  buttons={}
  def redraw():
   e=self.g.expedition;b=e.battle;stage=e.cleared;done=stage==len(BOSSES)
   title.config(text='패치 거부권 획득 · 모든 보스 격파!' if done else BOSSES[stage][0])
   route.config(text='  /  '.join(f'{"✓" if i<stage else "◆" if i==stage else "·"} {i+1}' for i in range(7)))
   arena.delete('all');width=max(arena.winfo_width(),840);cx=width/2
   if done:
    arena.create_text(cx,110,text='SANGGYU WINS',fill=GOLD,font=('Arial',36,'bold'))
    arena.create_text(cx,165,text='밸런스 패치가 상규의 허락을 기다리고 있습니다.',fill=TEXT,font=('Malgun Gothic',14))
   else:
    level=b['level'] if b else self.g.cards.get(self.selected,1)
    # Keep the scaled PhotoImage alive for Tk.
    arena.player_image=self.get_image(level).subsample(2)
    arena.create_image(width*.23,110,image=arena.player_image)
    minimum=BOSSES[stage][1];arena.boss_image=self.get_image(minimum).subsample(2)
    arena.create_oval(width*.77-92,18,width*.77+92,202,outline='#ff8b9b',width=2)
    arena.create_image(width*.77,110,image=arena.boss_image)
    arena.create_text(cx,100,text='VS',fill=GOLD,font=('Arial',25,'bold'))
    arena.create_text(width*.23,203,text=f'+{level} 상규 · 원정 분신',fill=TEAL,font=('Malgun Gothic',12,'bold'))
    arena.create_text(width*.77,203,text=f'BOSS {stage+1:02} · {BOSSES[stage][0]}',fill='#ff8b9b',font=('Malgun Gothic',12,'bold'))
    hp=(b['hp']/(100+level*12)) if b else 1;bhp=b['boss_hp']/((16+minimum*3)*7) if b else 1
    for center,fraction,color in ((width*.23,hp,TEAL),(width*.77,bhp,'#ff8b9b')):
     arena.create_rectangle(center-120,228,center+120,240,fill=BG,outline='')
     arena.create_rectangle(center-120,228,center-120+240*fraction,240,fill=color,outline='')
   if b:
    stats.config(text=f'체력 {b["hp"]}/{100+b["level"]*12}    |    보스 체력 {b["boss_hp"]}    |    기력 {"●"*b["energy"]}{"○"*(3-b["energy"])}    |    {b["turn"]}턴')
    intent.config(text=f'다음 행동: {e.intent()}'+(' · 방어 타이밍!' if b['turn']%3==0 else ''))
   else:
    stats.config(text='7개의 세계, 7명의 보스. 상규의 한계를 증명하세요.' if done else f'입장 조건 +{BOSSES[stage][1]} 이상  ·  첫 격파 보상 {reward_for(stage):,} G')
    intent.config(text='업적 창에서 최종 보상도 수령하세요.' if done else f'“{BOSSES[stage][2]}”')
   for key,btn in buttons.items():
    allowed=b is not None and (key!='burst' or b['energy']>=3) and (key!='heal' or b['heal']>0)
    btn.config(state='normal' if allowed else 'disabled')
   start.config(text='진행 중 · 자동 저장됨' if b else '모든 원정 완료' if done else '선택한 상규로 도전',state='disabled' if b or done else 'normal')
   retreat.config(state='normal' if b else 'disabled')
  def begin():
   if self.selected not in self.g.cards:note.config(text='먼저 메인 화면에서 상규를 선택하세요.');return
   if self.selected in self.g.workers:note.config(text='자동사냥에서 복귀한 상규로 도전하세요.');return
   try:self.g.start_expedition(self.selected)
   except ValueError as ex:note.config(text=str(ex));return
   note.config(text='3턴마다 강공격! 방어로 피해를 줄이고 기력을 모아 필살기를 사용하세요.');self.refresh();redraw()
  def act(key):
   try:status,reward,lines=self.g.expedition_action(key)
   except ValueError as ex:note.config(text=str(ex));return
   note.config(text='\n'.join(lines));self.refresh();redraw()
   if status!='ongoing':self.log(' / '.join(lines))
  def abandon():
   if messagebox.askyesno('원정 포기','이번 전투를 종료할까요? 상규와 자금은 그대로 유지됩니다.',parent=w):
    self.g.expedition.battle=None;note.config(text='원정에서 복귀했습니다. 다시 도전할 수 있습니다.');self.refresh();redraw()
  for key,text in [('attack','공격 · 기력 +1'),('guard','방어 · 피해 −80%'),('burst','필살기 · 기력 3'),('heal','회복 50% · 1회')]:
   btn=self.button(actions,text,lambda k=key:act(k),TEAL if key=='burst' else '#29334a','#10241e' if key=='burst' else TEXT);btn.pack(side='left',padx=4);buttons[key]=btn
  start=self.button(w,'도전',begin,TEAL,'#10241e');start.pack(fill='x',padx=28,pady=5)
  retreat=self.button(w,'이번 원정 포기',abandon);retreat.pack(pady=3)
  self.label(w,'입장 무료 · 원정 분신으로 전투하여 보유 상규 손실 없음 · 첫 격파 보상은 각 보스 1회\n창을 닫아도 전투 유지 · 게임 재실행 시 이어하기 · 새 게임에도 격파/보상 기록 유지',MUTED,12).pack(padx=20,pady=8)
  arena.bind('<Configure>',lambda event:redraw());redraw()
 def achievements_window(self):
  if self.busy:return
  w=self.window('상규 업적 · 성장 보상');w.geometry('980x740');w.transient(self.root);w.grab_set();w.focus_set()
  self.label(w,'MILESTONES / 모든 도전은 기록된다',GOLD,20,True).pack(pady=18)
  t=self.listing(w,('업적','진행','보상 G','상태'),(290,160,190,150));t.configure(selectmode='browse')
  note=self.label(w,'달성한 업적을 선택하고 보상을 받으세요. 각 보상은 1회만 수령합니다.',MUTED,12);note.pack(pady=6)
  def redraw():
   for row in t.get_children():t.delete(row)
   for key,title,metric,goal,reward in ACHIEVEMENTS:
    progress=min(goal,self.g.expedition.progress(self.g,metric));claimed=key in self.g.expedition.claimed
    t.insert('','end',iid=key,values=(title,f'{progress} / {goal}',f'{reward:,}','수령 완료' if claimed else '수령 가능' if progress>=goal else '도전 중'))
  def claim():
   if not t.selection():note.config(text='업적을 먼저 선택하세요.');return
   try:reward=self.g.expedition.claim(self.g,t.selection()[0])
   except ValueError as ex:note.config(text=str(ex));return
   note.config(text=f'업적 보상 +{reward:,} G!');self.log(f'업적 보상 +{reward:,} G');self.refresh();redraw()
  self.button(w,'선택한 업적 보상 받기',claim,GOLD,'#201a0e').pack(fill='x',padx=28,pady=15);redraw()
 def show_title(self):
  self.title_active=True;self.title_frame=tk.Frame(self.root,bg='#090e18');self.title_frame.place(relx=0,rely=0,relwidth=1,relheight=1)
  c=tk.Canvas(self.title_frame,bg='#090e18',highlightthickness=0);c.pack(fill='both',expand=True)
  self.title_image=tk.PhotoImage(master=self.root,file=str(Path(__file__).resolve().parent/'assets/base.png'))
  def paint(event=None):
   c.delete('all');w=c.winfo_width();h=c.winfo_height();x=w/2
   for r in (205,240,280):c.create_oval(x-r,h*.50-r,x+r,h*.50+r,outline='#293340',width=1)
   c.create_line(w*.15,h*.075,w*.85,h*.075,fill=GOLD,width=2);c.create_text(x,h*.10,text='S A N G G Y U   /   O R I G I N',fill=GOLD,font=('Arial',13,'bold'))
   c.create_text(x,h*.19,text='최강상규만들기',fill=TEXT,font=('Malgun Gothic',40,'bold'))
   c.create_text(x,h*.26,text='한 번의 강화가, 세계의 법칙을 바꾼다.',fill=MUTED,font=('Malgun Gothic',12))
   c.create_image(x,h*.52,image=self.title_image)
   c.create_rectangle(x-235,h*.77,x+235,h*.85,fill='#202c40',outline=GOLD,width=2);c.create_text(x,h*.81,text='PRESS ANY KEY',fill=GOLD,font=('Arial',18,'bold'),tags='prompt')
   c.create_text(x,h*.88,text='아무 키나 클릭하여 시작  |  저장된 여정 이어하기',fill=MUTED,font=('Malgun Gothic',12))
   c.create_text(x,h*.95,text='PROTOTYPE 0.7    /    +01 → +30',fill=MUTED,font=('Arial',10))
  c.bind('<Configure>',paint);c.bind('<Button-1>',lambda e:self.enter_game());self.install_keys(self.title_frame)
  self.root.after_idle(self.root.focus_set)
  def blink(on=True):
   if not self.title_active:return
   c.itemconfig('prompt',fill=GOLD if on else '#685b40');self.root.after(700,lambda:blink(not on))
  blink()
 def enter_game(self):
  if not self.title_active:return
  self.title_active=False;self.input_ready_at=time.monotonic()+0.4;self.title_frame.destroy();self.root.focus_set()
 def table(self):
  w=self.window('강화 확률표 · 연구 반영');self.label(w,'강화 확률 · 비용 · 재료',GOLD,22,True).pack(pady=15);self.label(w,'연구 보너스 반영 · 각 시도 독립 추첨 · 재료는 성공/실패와 관계없이 소모',MUTED).pack();t=self.listing(w,('시도','성공률','비용 G','실패','재료'),(100,80,130,260,100))
  for n,p in enumerate(RATE,1):t.insert('','end',values=(f'+{n} → +{n+1}',f'{self.g.success_rate(n)}% (+{self.g.success_rate(n)-p}%p)',f'{self.g.upgrade_cost(n):,}',f'하락 {self.g.outcome_rates(n)[1]:g}% / 파괴 {self.g.outcome_rates(n)[2]:g}%',f'+{required(n)} 1명' if required(n) else '없음'))
 def toggle_lab(self):
  if self.busy:return
  if not self.lab:
   if not messagebox.askyesno('실험실','별도의 임시 게임으로 이동합니다.\n10억 G와 원하는 단계의 상규로 후반부를 테스트할 수 있습니다.\n일반 모드 진행은 보존됩니다.'):return
   self.save();self.normal=self.g;self.g=Game();self.g.cash=10**9;self.lab=True;self.labrow.pack(fill='x',pady=6)
  else:self.g=self.normal;self.lab=False;self.labrow.pack_forget()
  self.selected=next(iter(self.g.cards),None);self.logs=[];self.refresh();self.log('실험실에 입장했습니다.' if self.lab else '일반 모드로 돌아왔습니다.')
 def lab_buy(self):
  if self.busy or not self.lab:return
  try:self.selected=self.g.buy(int(self.lab_level.get()),lab=True);self.refresh()
  except ValueError as e:messagebox.showinfo('실험실',str(e))
 def reset(self):
  if self.busy:return
  if messagebox.askyesno('새 게임','자금과 보유 상규를 초기화합니다. 도감·영구 연구·보스 격파·수령한 업적은 유지됩니다. 진행 중인 전투는 종료됩니다.\n시작할까요?'):
   found=self.g.found.copy();research=self.g.research.copy();expedition=self.g.expedition;expedition.battle=None;self.g=Game();self.g.expedition=expedition;self.g.found|=found;self.g.research=research;self.selected=1;self.logs=[];self.refresh();self.log('새로운 상규의 시대가 시작됩니다.')
 def quit(self):self.save();self.root.destroy()
if __name__=='__main__':
 root=tk.Tk();app=App(root);root.mainloop()
