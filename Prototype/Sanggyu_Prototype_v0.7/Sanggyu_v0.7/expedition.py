"""Deterministic boss battles and one-time progression rewards, independent of Tk."""
from copy import deepcopy
from core import price

BOSSES = (
    ('급식실의 지배자', 3, '오늘의 반찬은 네 근손실이다.'),
    ('헬스장 문지기', 6, '회원님, 마지막 한 세트 더.'),
    ('단백질 골렘', 10, '흡수당할 준비는 되었나.'),
    ('중력 집행관', 15, '스쿼트 깊이가 우주의 법이다.'),
    ('블랙홀 관장', 20, '탈출 속도보다 빠르게 들어라.'),
    ('인과율 감사관', 25, '이 근육은 규정 위반입니다.'),
    ('밸런스 패치의 신', 30, '너프를 거부한 자, 앞으로.'),
)
# key, title, metric, goal, reward
ACHIEVEMENTS = (
    ('first_upgrade', '첫 세트 완료', 'successes', 1, 1000),
    ('attempt_25', '꺾이지 않는 상규', 'attempts', 25, 5000),
    ('attempt_100', '강화는 유산소다', 'attempts', 100, 30000),
    ('discover_10', '동네의 전설', 'found', 10, 50000),
    ('discover_20', '우주의 회원권', 'found', 20, 2000000),
    ('boss_1', '원정의 시작', 'cleared', 1, 5000),
    ('boss_4', '중력도 근손실', 'cleared', 4, 1000000),
    ('boss_7', '패치 거부권', 'cleared', 7, price(30)),
)


def reward_for(stage):
    return max(3000, price(BOSSES[stage][1]) * 2)


class Expedition:
    def __init__(self):
        self.cleared = 0
        self.claimed = set()
        self.battle = None

    def start(self, level):
        if self.battle is not None:
            raise ValueError('진행 중인 원정을 먼저 끝내거나 포기하세요.')
        if self.cleared == len(BOSSES):
            raise ValueError('모든 보스를 격파했습니다. 상규가 패치를 반려했습니다.')
        name, minimum, _ = BOSSES[self.cleared]
        if not minimum <= level <= 30:
            raise ValueError(f'{name} 도전에는 +{minimum} 이상 상규가 필요합니다.')
        hp, attack = 100 + level * 12, 16 + level * 3
        self.battle = dict(level=level, hp=hp, boss_hp=(16 + minimum * 3) * 7,
                           energy=0, heal=1, turn=1)

    def intent(self):
        return '강공격 · 피해 2배' if self.battle and self.battle['turn'] % 3 == 0 else '일반 공격'

    def act(self, action):
        b = self.battle
        if b is None:
            raise ValueError('먼저 원정을 시작하세요.')
        if action not in ('attack', 'guard', 'burst', 'heal'):
            raise ValueError('알 수 없는 행동입니다.')
        if action == 'burst' and b['energy'] < 3:
            raise ValueError('필살기는 기력 3이 필요합니다.')
        if action == 'heal' and not b['heal']:
            raise ValueError('이번 원정의 회복을 이미 사용했습니다.')
        max_hp = 100 + b['level'] * 12
        attack = 16 + b['level'] * 3
        messages = []
        if action in ('attack', 'burst'):
            damage = attack * (3 if action == 'burst' else 1)
            b['boss_hp'] = max(0, b['boss_hp'] - damage)
            b['energy'] = b['energy'] - 3 if action == 'burst' else min(3, b['energy'] + 1)
            messages.append(f'{"필살기!" if action == "burst" else "공격"} 보스에게 {damage} 피해.')
        elif action == 'guard':
            b['energy'] = min(3, b['energy'] + 1)
            messages.append('방어! 이번 피해 80% 감소 · 기력 +1.')
        else:
            amount = min(max_hp - b['hp'], max_hp // 2)
            b['hp'] += amount
            b['heal'] = 0
            messages.append(f'단백질 셰이크! 체력 {amount} 회복.')
        if not b['boss_hp']:
            reward = reward_for(self.cleared)
            self.cleared += 1
            self.battle = None
            messages.append(f'격파! 첫 클리어 보상 {reward:,} G.')
            return 'won', reward, messages
        minimum = BOSSES[self.cleared][1]
        damage = (100 + minimum * 12) // 7
        heavy = b['turn'] % 3 == 0
        damage *= 2 if heavy else 1
        if action == 'guard':
            damage = max(1, damage // 5)
        b['hp'] = max(0, b['hp'] - damage)
        messages.append(f'{"강공격" if heavy else "보스 공격"} · {damage} 피해를 받았습니다.')
        b['turn'] += 1
        if not b['hp']:
            self.battle = None
            messages.append('원정 종료. 보유 상규와 자금은 잃지 않습니다. 다시 도전하세요!')
            return 'lost', 0, messages
        return 'ongoing', 0, messages

    def progress(self, game, metric):
        return len(game.found) if metric == 'found' else self.cleared if metric == 'cleared' else getattr(game, metric)

    def claim(self, game, key):
        achievement = next((a for a in ACHIEVEMENTS if a[0] == key), None)
        if achievement is None:
            raise ValueError('알 수 없는 업적입니다.')
        _, _, metric, goal, reward = achievement
        if key in self.claimed:
            raise ValueError('이미 보상을 받은 업적입니다.')
        if self.progress(game, metric) < goal:
            raise ValueError('아직 업적 조건을 달성하지 못했습니다.')
        self.claimed.add(key)
        game.cash += reward
        return reward

    def dump(self):
        return dict(cleared=self.cleared, claimed=sorted(self.claimed), battle=deepcopy(self.battle))

    @classmethod
    def load(cls, data):
        result = cls()
        result.cleared = data.get('cleared', 0)
        result.claimed = set(data.get('claimed', []))
        if type(result.cleared) is not int or not 0 <= result.cleared <= len(BOSSES):
            raise ValueError('잘못된 원정 진행 데이터')
        if not result.claimed <= {a[0] for a in ACHIEVEMENTS}:
            raise ValueError('잘못된 업적 데이터')
        b = deepcopy(data.get('battle'))
        if b is not None:
            if result.cleared == len(BOSSES) or not isinstance(b, dict):
                raise ValueError('잘못된 전투 데이터')
            fields = {'level', 'hp', 'boss_hp', 'energy', 'heal', 'turn'}
            if set(b) != fields or any(type(v) is not int for v in b.values()):
                raise ValueError('잘못된 전투 데이터')
            minimum = BOSSES[result.cleared][1]
            if not (minimum <= b['level'] <= 30 and 0 < b['hp'] <= 100 + b['level'] * 12
                    and 0 < b['boss_hp'] <= (16 + minimum * 3) * 7
                    and 0 <= b['energy'] <= 3 and b['heal'] in (0, 1) and b['turn'] >= 1):
                raise ValueError('잘못된 전투 데이터')
        result.battle = b
        return result
