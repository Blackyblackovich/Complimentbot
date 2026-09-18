import os, json, random, urllib.request, urllib.parse, subprocess, datetime

TOKEN = os.environ['BOT_TOKEN']
API = f'https://api.telegram.org/bot{TOKEN}'

def call(method, **kw):
    data = urllib.parse.urlencode(kw).encode() if kw else None
    req = urllib.request.Request(f'{API}/{method}', data=data)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except Exception as e:
        print('err', method, e)
        return None

# 1) кто подписан
users_file = 'users.json'
try:
    users = json.load(open(users_file))
except Exception:
    users = []

# 2) новые /start
res = call('getUpdates', timeout=30)
new_users = 0
if res and res.get('ok'):
    for upd in res['result']:
        msg = upd.get('message') or {}
        if msg.get('text') == '/start':
            chat_id = msg['chat']['id']
            name = msg['chat'].get('first_name', '')
            if not any(u['id'] == chat_id for u in users):
                users.append({'id': chat_id, 'name': name, 'added': str(datetime.date.today())})
                new_users += 1
                call('sendMessage', chat_id=chat_id,
                     text=f'Привет, {name}! 💖 Я твой персональный бот-комплиментатор. Буду присылать тёплые слова четыре раза в день — и всегда разные.')

# 3) сохраняем список
if new_users > 0:
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    subprocess.run(['git', 'config', 'user.email', 'bot@example.com'], check=False)
    subprocess.run(['git', 'config', 'user.name', 'compliments-bot'], check=False)
    subprocess.run(['git', 'add', users_file], check=False)
    subprocess.run(['git', 'commit', '-m', 'update users'], check=False)
    subprocess.run(['git', 'push'], check=False)

# 4) отправляем
if not users:
    print('Пока никто не подписался')
    raise SystemExit

lines = [l.strip() for l in open('compliments.txt', encoding='utf-8') if l.strip()]
n = len(lines)

now = datetime.datetime.now(datetime.timezone.utc)
epoch = (now.date() - datetime.date(1970, 1, 1)).days
event = os.environ.get('GITHUB_EVENT_NAME', 'schedule')
SLOT_HOURS_UTC = [9, 13, 18, 24]   # наши четыре будильника по UTC
slot = next((i for i, h in enumerate(SLOT_HOURS_UTC) if now.hour < h), 3)

emoji = random.choice(['💖', '💌', '🌸', '☀️', '🪽', '🌙'])

for u in users:
    if event == 'workflow_dispatch':
        idx = random.randrange(n)        # ручной запуск — случайный комплимент
    else:
        idx = (epoch * 4 + slot) % n     # плановый — у каждого будильника свой
    call('sendMessage', chat_id=u['id'],
         text=f'{emoji} {lines[idx]}\n\nЦелую. Твой любимый 💫')
    print('sent', u['id'], 'idx', idx, 'slot', slot, 'event', event)
