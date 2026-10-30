"""Pure game rules; no UI, network, or external dependencies."""
import random
NAMES=['애기 상규','혼자 신발 신는 상규','엄마 몰래 콜라 마시는 상규','급식 두 번 받는 상규','반에서 팔씨름 좀 치는 상규','체육쌤이 눈여겨보는 상규','헬스장 첫날 기구 고장 낸 상규','3대 500치는 상규','근손실 무서워서 잠꼬대로 스쿼트하는 상규','단백질이 섭취하는 상규','헬스장 건물로 데드리프트하는 상규','산맥을 승모근으로 등록한 상규','지구 자전 반대로 러닝하는 상규','달을 원판으로 끼우는 상규','중력이 허락받고 당기는 상규','태양한테 웜업 시키는 상규','블랙홀에 보충제 타 먹는 상규','은하수 접어서 운동매트 까는 상규','빅뱅을 근육통으로 기억하는 상규','평행우주 상규들한테 회비 걷는 상규','시간 멈춰놓고 휴식시간 지키는 상규','인과관계한테 선후배 예절 가르친 상규','전지전능한테 자세 지적하는 상규','강화 실패를 불합격시킨 상규','시스템 메시지가 존댓말 쓰는 상규','마우스 커서를 잡아서 옮기는 상규','개발자한테 밸런스 패치 반려한 상규','다음 강화 재료로 개발자 요구하는 상규','당신을 +1로 구매한 상규','상규']
RATE=[95,92,90,87,84,80,76,72,68,64,60,56,52,48,45,65,62,59,56,70,68,66,64,62,60,58,56,54,50]
def cost(level):return round(100*1.38**(level-1)/10)*10
def price(level):return round(150*1.9**(level-1)/10)*10
def shop_price(level):return ((price(level)*3+199)//200)*100
def inventory_order(cards,mode='높은 등급순'):
 return sorted(cards,key=lambda i:(cards[i],i) if mode=='낮은 등급순' else ((i,) if mode=='획득순' else (-cards[i],i)))
def required(level):return level-1 if 20<=level<30 else None
def break_rate(level):return 0 if level<=15 else min(75,10+5*(level-16))
def failure(level):return '1단계 하락 (최저 +1)' if level<=15 else f'실패 중 하락 {100-break_rate(level)}% / 파괴 {break_rate(level)}%'
def era(level):
 return ['동네의 전설','근육의 시대','행성의 지배자','우주의 오류','시스템의 반역자','화면 너머의 존재'][min(5,(level-1)//5)]
RESEARCH_NAMES={'speed':'강화 속도','cost':'강화 비용 절감','shop':'상점 할인','luck':'강화 확률','crit':'초월 강화 (+2)','batch':'10회 연속 강화'}
RESEARCH_PRICES={
 'speed':[10000,50000,250000,1500000,10000000],
 'cost':[20000,100000,500000,3000000,20000000],
 'shop':[50000,250000,1500000,10000000,50000000],
 'luck':[100000,1000000,10000000,50000000,200000000],
 'crit':[5000000,25000000,100000000,500000000,2000000000],
 'batch':[price(30)*5//2]}
class Game:
 def __init__(self):
  from expedition import Expedition
  self.expedition=Expedition()
  self.cash=50000;self.cards={1:1};self.next_id=2;self.found={1};self.attempts=0;self.successes=0;self.destroyed=0;self.research={k:0 for k in RESEARCH_NAMES};self.protected=0;self.workers=set();self.hunt_remainder=0.0;self.hunt_seconds=0.0;self.hunt_pending=0.0;self.target=30
 def start_expedition(self,uid):
  if uid not in self.cards:raise ValueError('원정에 도전할 상규를 선택하세요.')
  if uid in self.workers:raise ValueError('자동사냥에서 복귀한 상규로 도전하세요.')
  self.expedition.start(self.cards[uid])
 def expedition_action(self,action):
  result=self.expedition.act(action);self.cash+=result[1];return result
 def hunt_rate(self):return sum(price(self.cards[i])/60000 for i in self.workers)
 def work(self,uid):
  if uid not in self.cards:raise ValueError('배치할 상규를 선택하세요.')
  if uid in self.workers:self.workers.remove(uid);return False
  if len(self.workers)>=1:raise ValueError('자동사냥은 1명까지 배치할 수 있습니다. 먼저 복귀시키세요.')
  self.workers.add(uid);return True
 def hunt_tick(self,seconds):
  if seconds<0:raise ValueError('잘못된 경과 시간')
  if not self.workers:return 0
  self.hunt_pending+=self.hunt_rate()*seconds;self.hunt_seconds+=seconds
  if self.hunt_seconds<60:return 0
  whole_minutes=int(self.hunt_seconds//60);fraction=whole_minutes*60/self.hunt_seconds
  amount=self.hunt_pending*fraction+self.hunt_remainder;whole=int(amount)
  self.hunt_pending*=1-fraction;self.hunt_seconds-=whole_minutes*60;self.hunt_remainder=amount-whole;self.cash+=whole;return whole
 def set_target(self,level):
  if not 1<=level<=30:raise ValueError('목표는 +1~+30입니다.')
  self.target=level
 def outcome_rates(self,level,protect=False):
  success=self.success_rate(level);broken=(100-success)*break_rate(level)/100
  return success,0 if protect else 100-success-broken,0 if protect else broken
 def shop_unlocked(self):return any(n>=10 for n in self.found)
 def protection_unlocked(self):return any(n>=20 for n in self.found)
 def upgrade_ms(self):return 3000-500*self.research['speed']
 def upgrade_cost(self,level):return max(1,(cost(level)*(100-5*self.research['cost'])+99)//100)
 def purchase_cost(self,level):return ((shop_price(level)*(100-5*self.research['shop'])+9999)//10000)*100
 def success_rate(self,level):return min(100,RATE[level-1]+self.research['luck'])
 def protection_cost(self,level):return max(20000000,((price(level)*3+399)//400)*100)
 def research_buy(self,key):
  if key not in RESEARCH_NAMES:raise ValueError('알 수 없는 연구입니다.')
  n=self.research[key]
  if n>=len(RESEARCH_PRICES[key]):raise ValueError('이미 최대 연구 단계입니다.')
  fee=RESEARCH_PRICES[key][n]
  if self.cash<fee:raise ValueError(f'연구 비용 {fee:,} G가 필요합니다.')
  self.cash-=fee;self.research[key]+=1
 def buy(self,level=1,lab=False):
  if not lab and level!=1:raise ValueError('일반 모드에서는 +1만 구매할 수 있습니다.')
  if not 1<=level<=30:raise ValueError('잘못된 강화 단계입니다.')
  if len(self.cards)>=200:raise ValueError('보유 한도 200명입니다. 판매 후 다시 시도하세요.')
  if not lab:
   if self.cash<200:raise ValueError('구매 자금 200 G가 필요합니다.')
   self.cash-=200
  uid=self.next_id;self.next_id+=1;self.cards[uid]=level;self.found.add(level);return uid
 def shop_buy(self,level):
  if not self.shop_unlocked():raise ValueError('+10 상규를 달성하면 상점이 열립니다.')
  if not 10<=level<=20:raise ValueError('상점에서는 +10~+20 상규만 구매할 수 있습니다.')
  if level not in self.found:raise ValueError('먼저 해당 단계의 상규를 발견해야 합니다.')
  if len(self.cards)>=200:raise ValueError('보유 한도 200명입니다.')
  fee=self.purchase_cost(level)
  if self.cash<fee:raise ValueError(f'구매 자금 {fee:,} G가 필요합니다.')
  self.cash-=fee;uid=self.next_id;self.next_id+=1;self.cards[uid]=level
  return uid
 def upgrade(self,uid,material=None,roll=None,protect=False,crit_roll=None,break_roll=None):
  if uid not in self.cards:raise ValueError('강화할 상규를 선택하세요.')
  if uid in self.workers:raise ValueError('자동사냥 중인 상규는 복귀 후 강화하세요.')
  level=self.cards[uid]
  if level>=self.target:raise ValueError(f'목표 +{self.target} 도달: 강화 잠금. 목표를 올려 해제하세요.')
  if level>=30:raise ValueError('상규는 이미 완성되었습니다.')
  need=required(level)
  if need and material in self.workers:raise ValueError('자동사냥 중인 상규는 재료로 사용할 수 없습니다.')
  if need and (material==uid or self.cards.get(material)!=need):raise ValueError(f'재료로 사용할 +{need} 상규를 선택하세요.')
  if protect and (not self.protection_unlocked() or level<20):raise ValueError('파괴 방지는 +20 달성 후 현재 +20 이상에 사용할 수 있습니다.')
  fee=self.upgrade_cost(level)+(self.protection_cost(level) if protect else 0)
  if self.cash<fee:raise ValueError(f'강화 비용 {fee:,} G가 부족합니다.')
  self.cash-=fee
  if need:del self.cards[material]
  self.attempts+=1
  success=(random.random() if roll is None else roll)<self.success_rate(level)/100
  if success:
   critical=self.research['crit']>0 and (random.random() if crit_roll is None else crit_roll)<self.research['crit']/100
   new=min(self.target,30,level+(2 if critical else 1));self.cards[uid]=new;self.found.update(range(level+1,new+1));self.successes+=1
  elif level<=15:self.cards[uid]=max(1,level-1)
  elif protect:self.protected+=1
  elif (random.random() if break_roll is None else break_roll)<break_rate(level)/100:del self.cards[uid];self.destroyed+=1
  else:self.cards[uid]=level-1
  return success,level,self.cards.get(uid)
 def sell(self,uid):
  if uid not in self.cards:raise ValueError('판매할 상규를 선택하세요.')
  if uid in self.workers:raise ValueError('자동사냥 중인 상규는 복귀 후 판매하세요.')
  value=price(self.cards.pop(uid));self.cash+=value;return value
 def rescue(self):
  if self.cards or self.cash>=200:raise ValueError('상규가 없고 자금이 200 G 미만일 때 지원됩니다.')
  self.cash+=2000
 def dump(self):return dict(expedition=self.expedition.dump(),cash=self.cash,cards=self.cards,next_id=self.next_id,found=sorted(self.found),attempts=self.attempts,successes=self.successes,destroyed=self.destroyed,research=self.research.copy(),protected=self.protected,workers=sorted(self.workers),hunt_remainder=self.hunt_remainder,hunt_pending=self.hunt_pending,hunt_seconds=self.hunt_seconds,target=self.target)
 @classmethod
 def load(cls,data):
  g=cls();g.cash=int(data['cash']);g.cards={int(k):int(v) for k,v in data['cards'].items()};g.found=set(map(int,data['found']));g.next_id=int(data['next_id'])
  if g.cash<0 or len(g.cards)>200 or any(k<1 or not 1<=v<=30 for k,v in g.cards.items()) or any(not 1<=v<=30 for v in g.found) or g.next_id<=max(g.cards,default=0):raise ValueError('잘못된 저장 데이터')
  for k in ['attempts','successes','destroyed']:setattr(g,k,max(0,int(data.get(k,0))))
  g.research={k:int(data.get('research',{}).get(k,0)) for k in RESEARCH_NAMES}
  if any(not 0<=v<=len(RESEARCH_PRICES[k]) for k,v in g.research.items()):raise ValueError('잘못된 연구 단계')
  g.protected=max(0,int(data.get('protected',0)))
  g.workers=set(map(int,data.get('workers',[])));g.hunt_remainder=float(data.get('hunt_remainder',0))
  if len(g.workers)>1 or not g.workers<=g.cards.keys() or not 0<=g.hunt_remainder<1:raise ValueError('잘못된 자동사냥 데이터')
  g.hunt_pending=float(data.get('hunt_pending',0));g.hunt_seconds=float(data.get('hunt_seconds',0));g.set_target(int(data.get('target',30)))
  import math
  if not math.isfinite(g.hunt_pending) or g.hunt_pending<0 or not 0<=g.hunt_seconds<60:raise ValueError('잘못된 정산 데이터')
  from expedition import Expedition
  g.expedition=Expedition.load(data.get('expedition',{}))
  return g
