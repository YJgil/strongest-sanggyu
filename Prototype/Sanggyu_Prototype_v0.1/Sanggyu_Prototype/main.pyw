import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import json, os, time, random
from core import Game,NAMES,RATE,cost,price,required,failure,era
BG='#10141e';PANEL='#192030';TEXT='#eef1f8';MUTED='#97a2b8';GOLD='#f4cc74';TEAL='#8fe3c0'
SAVE=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'StrongestSanggyu'/'save.json'
class App:
 def __init__(self,root):
  self.root=root;self.g=Game();self.lab=False;self.busy=False;self.selected=1;self.material=None;self.last_job=0;self.logs=[];self.save_failed=False
  if SAVE.exists():
   try:self.g=Game.load(json.loads(SAVE.read_text(encoding='utf-8')))
   except Exception as e:
    messagebox.showwarning('저장 파일 확인',f'저장 파일을 읽지 못했습니다. 기존 파일을 보존하고 새로 시작합니다.\n{e}')
    try:SAVE.rename(SAVE.with_name(f'save-corrupt-{int(time.time())}.json'))
    except OSError:self.save_failed=True
  root.title('최강상규만들기 · Prototype 0.1');root.geometry('1180x820');root.minsize(1040,760);root.configure(bg=BG)
  style=ttk.Style();style.theme_use('clam');style.configure('Treeview',background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=31,font=('Malgun Gothic',10));style.configure('Treeview.Heading',background='#263149',foreground=TEXT,font=('Malgun Gothic',10,'bold'));style.map('Treeview',background=[('selected','#435279')]);style.configure('TCombobox',fieldbackground='#263149',foreground=TEXT)
  top=tk.Frame(root,bg=BG);top.pack(fill='x',padx=28,pady=(20,12));self.label(top,'SANGGYU LAB / 001',GOLD,10).pack(anchor='w');self.label(top,'최강상규만들기',TEXT,26,True).pack(side='left');self.balance=self.label(top,'',GOLD,20,True);self.balance.pack(side='right')
  tools=tk.Frame(root,bg=BG);tools.pack(fill='x',padx=28,pady=(0,15))
  for text,fn in [('발견 도감',self.codex),('확률·비용표',self.table),('실험실 전환',self.toggle_lab),('새 게임',self.reset)]:self.button(tools,text,fn).pack(side='left',padx=(0,8))
  self.mode=self.label(tools,'',MUTED,10);self.mode.pack(side='right')
  body=tk.Frame(root,bg=BG);body.pack(fill='both',expand=True,padx=28)
  left=tk.Frame(body,bg=PANEL);left.pack(side='left',fill='both',expand=True,padx=(0,18));self.era_label=self.label(left,'',GOLD,11);self.era_label.pack(pady=(16,0));self.canvas=tk.Canvas(left,height=215,bg=PANEL,highlightthickness=0);self.canvas.pack(fill='x',padx=12)
  self.level_label=self.label(left,'',TEAL,26,True);self.level_label.pack();self.name_label=self.label(left,'',TEXT,18,True);self.name_label.configure(wraplength=550);self.name_label.pack(padx=16,pady=8)
  self.info=self.label(left,'',MUTED,11);self.info.configure(justify='center');self.info.pack(pady=8)
  self.matbox=ttk.Combobox(left,state='readonly',width=44);self.matbox.pack(pady=6);self.matbox.bind('<<ComboboxSelected>>',self.choose_material)
  self.upbtn=self.button(left,'강화하기',self.upgrade,TEAL,'#10241e');self.upbtn.configure(font=('Malgun Gothic',15,'bold'),height=2);self.upbtn.pack(fill='x',padx=28,pady=8)
  self.sellbtn=self.button(left,'판매하기',self.sell);self.sellbtn.pack(fill='x',padx=28,pady=(0,10));self.result=self.label(left,'상규는 아직 당신을 믿고 있습니다.',GOLD,11);self.result.configure(wraplength=560);self.result.pack(padx=18,pady=(5,18))
  right=tk.Frame(body,bg=BG,width=420);right.pack(side='right',fill='both');right.pack_propagate(False)
  self.label(right,'보유 상규  /  강화할 카드를 선택하세요',TEXT,12,True).pack(anchor='w',pady=(0,10));self.tree=ttk.Treeview(right,columns=('level','name'),show='headings',height=9,selectmode='browse');self.tree.heading('level',text='강화');self.tree.heading('name',text='상규');self.tree.column('level',width=55,stretch=False);self.tree.column('name',width=330);self.tree.pack(fill='both',expand=True);self.tree.bind('<<TreeviewSelect>>',self.select)
  row=tk.Frame(right,bg=BG);row.pack(fill='x',pady=10);self.button(row,'+1 상규 구매 · 200 G',self.buy).pack(side='left');self.button(row,'긴급 지원',self.rescue).pack(side='right')
  self.labrow=tk.Frame(right,bg=BG);self.lab_level=tk.Spinbox(self.labrow,from_=1,to=29,width=5,font=('Malgun Gothic',12));self.lab_level.pack(side='left');self.button(self.labrow,'실험용 상규 생성',self.lab_buy).pack(side='left',padx=8)
  self.label(right,'강화의 역사',GOLD,11).pack(anchor='w',pady=(12,6));self.logbox=tk.Text(right,height=8,bg=PANEL,fg=MUTED,wrap='word',font=('Malgun Gothic',10),relief='flat',state='disabled');self.logbox.pack(fill='x')
  self.footer=self.label(root,'자동 저장 · 재료는 성공/실패와 관계없이 소모 · 실험실 기록은 일반 도감에 반영되지 않습니다',MUTED,9);self.footer.pack(pady=14)
  root.protocol('WM_DELETE_WINDOW',self.quit);self.refresh();self.log('상규 연구소에 오신 것을 환영합니다.');root.after(100,self.resize)
 def label(self,parent,text,color=TEXT,size=11,bold=False):return tk.Label(parent,text=text,bg=parent['bg'],fg=color,font=('Malgun Gothic',size,'bold' if bold else 'normal'))
 def button(self,parent,text,fn,bg='#29334a',fg=TEXT):return tk.Button(parent,text=text,command=fn,bg=bg,fg=fg,activebackground='#425275',activeforeground=TEXT,relief='flat',bd=0,padx=14,pady=9,cursor='hand2',font=('Malgun Gothic',10))
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
  n=self.g.cards.get(self.selected);self.material=None;self.material_ids=[]
  if n is None:
   self.level_label.config(text='—');self.name_label.config(text='상규가 기다리고 있습니다');self.info.config(text='상규를 구매하거나, 목록에서 선택하세요.');self.era_label.config(text='EMPTY');self.upbtn.config(state='disabled');self.sellbtn.config(state='disabled');self.matbox.config(values=[]);self.matbox.set('재료 필요 없음');self.draw(0);return
  self.level_label.config(text=f'+{n:02d}');self.name_label.config(text=NAMES[n-1]);self.era_label.config(text=era(n).upper());self.draw(n)
  self.sellbtn.config(text=f'판매하기 · {price(n):,} G',state='normal');self.upbtn.config(state='normal' if n<30 else 'disabled',text=f'+{n+1} 강화하기' if n<30 else '상규가 완성되었습니다')
  self.info.config(text=f'성공 {RATE[n-1]}%  ·  비용 {cost(n):,} G\n실패: {failure(n)}' if n<30 else '당신이 상규를 키운 것이 아닙니다.\n상규가 당신에게 시간을 준 것입니다.')
  req=required(n)
  if req:
   self.material_ids=[i for i,v in self.g.cards.items() if v==req and i!=self.selected];self.matbox.config(values=[f'#{i}  +{req} {NAMES[req-1]}' for i in self.material_ids]);self.matbox.set(f'+{req} 재료 선택 · 실패해도 소모됩니다')
   if self.material_ids:self.matbox.current(0);self.material=self.material_ids[0]
  else:self.matbox.config(values=[]);self.matbox.set('재료 필요 없음')
 def refresh(self):
  self.balance.config(text=f'{self.g.cash:,} G');self.mode.config(text='실험실 · 저장 안 함' if self.lab else '일반 모드 · 자동 저장');existing=set(self.tree.get_children());wanted={str(i) for i in self.g.cards}
  for i in existing-wanted:self.tree.delete(i)
  for i,n in sorted(self.g.cards.items(),key=lambda p:(-p[1],p[0])):
   if str(i) in existing:self.tree.item(str(i),values=(f'+{n}',NAMES[n-1]))
   else:self.tree.insert('','end',iid=str(i),values=(f'+{n}',NAMES[n-1]))
  if self.selected not in self.g.cards:self.selected=next(iter(self.g.cards),None)
  if self.selected is not None:self.tree.selection_set(str(self.selected))
  self.card();self.save()
 def draw(self,n):
  c=self.canvas;c.delete('all');w=max(c.winfo_width(),560);x=w/2;y=112;accent=['#96ddb9','#fac779','#91c7ff','#c1a1ff','#ff91a3','#faf0bd'][min(5,max(0,n-1)//5)]
  for r in [86,103]:c.create_oval(x-r,y-r,x+r,y+r,outline='#35405b',width=1)
  if n>=16:
   for k in range(16):
    import math
    a=k*math.pi/8;c.create_text(x+96*math.cos(a),y+96*math.sin(a),text='✦',fill=accent,font=('Arial',10))
  c.create_oval(x-65,y+66,x+65,y+80,fill='#10141e',outline='')
  if n==0:c.create_text(x,y,text='?',fill=MUTED,font=('Arial',60));return
  if n==30:c.create_text(x,y,text='상규',fill=GOLD,font=('Malgun Gothic',38,'bold'));return
  width=28+min(n,15)*2;c.create_polygon(x-width,y+65,x-width+8,y+5,x+width-8,y+5,x+width,y+65,fill=accent,outline='')
  c.create_oval(x-32,y-52,x+32,y+12,fill='#f2cfb1',outline='');c.create_arc(x-34,y-58,x+34,y+5,start=0,extent=180,fill='#343146',outline='')
  for dx in [-12,12]:c.create_rectangle(x+dx-2,y-24,x+dx+2,y-18,fill='#222435',outline='')
  c.create_line(x-8,y-5,x+8,y-5,fill='#ab736a',width=2)
  if n>=8:c.create_line(x-100,y+35,x+100,y+35,fill='#b2bdcf',width=7);c.create_rectangle(x-104,y+9,x-85,y+60,fill=accent,outline='');c.create_rectangle(x+85,y+9,x+104,y+60,fill=accent,outline='')
  if n>=21:c.create_text(x,y-80,text='SYSTEM OWNER',fill=accent,font=('Arial',9,'bold'))
 def resize(self):self.card()
 def buy(self):
  if self.busy:return
  try:self.selected=self.g.buy();self.log('+1 애기 상규 입장. 아직 세상 물정을 모릅니다.');self.refresh()
  except ValueError as e:messagebox.showinfo('구매',str(e))
 def sell(self):
  if self.busy or self.selected not in self.g.cards:return
  n=self.g.cards[self.selected]
  if n>=10 and not messagebox.askyesno('판매 확인',f'+{n} {NAMES[n-1]}\n{price(n):,} G에 판매할까요?'):return
  value=self.g.sell(self.selected);self.log(f'+{n} 상규 판매 · +{value:,} G');self.refresh()
 def upgrade(self):
  if self.busy:return
  try:result=self.g.upgrade(self.selected,self.material)
  except ValueError as e:messagebox.showinfo('강화 조건',str(e));return
  self.busy=True;self.upbtn.config(state='disabled');self.sellbtn.config(state='disabled');self.save();self.result.config(text='상규가 인과관계와 협의 중입니다…',fg=GOLD);self.root.after(650,lambda:self.reveal(result))
 def reveal(self,result):
  self.busy=False;ok,old,new=result
  if ok:text=f'성공! +{old} → +{new} · {NAMES[new-1]}';color=TEAL
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
  w=self.window('상규 도감');self.label(w,f'발견 도감  {len(self.g.found)} / 30',GOLD,22,True).pack(pady=16);self.label(w,'최고 강화만 남는 게 아닙니다. 사라진 상규도 기억합니다.',MUTED).pack();t=self.listing(w,('단계','이름','시대'),(70,520,210))
  for n in range(1,31):t.insert('','end',values=(f'+{n}',NAMES[n-1] if n in self.g.found else '??? 미발견 상규',era(n) if n in self.g.found else '???'))
  self.label(w,f'강화 {self.g.attempts}회 · 성공 {self.g.successes}회 · 파괴 {self.g.destroyed}명',MUTED).pack(pady=12)
 def table(self):
  w=self.window('강화 확률표 · 고정 확률');self.label(w,'강화 확률 · 비용 · 재료',GOLD,22,True).pack(pady=15);self.label(w,'각 시도는 독립 추첨 · 천장 없음 · 재료는 성공/실패와 관계없이 소모',MUTED).pack();t=self.listing(w,('시도','성공률','비용 G','실패','재료'),(100,80,130,260,100))
  for n,p in enumerate(RATE,1):t.insert('','end',values=(f'+{n} → +{n+1}',f'{p}%',f'{cost(n):,}',failure(n),f'+{required(n)} 1명' if required(n) else '없음'))
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
  if messagebox.askyesno('새 게임','자금과 보유 상규를 초기화합니다. 도감 기록은 유지됩니다.\n시작할까요?'):
   found=self.g.found.copy();self.g=Game();self.g.found|=found;self.selected=1;self.logs=[];self.refresh();self.log('새로운 상규의 시대가 시작됩니다.')
 def quit(self):self.save();self.root.destroy()
if __name__=='__main__':
 root=tk.Tk();app=App(root);root.mainloop()
