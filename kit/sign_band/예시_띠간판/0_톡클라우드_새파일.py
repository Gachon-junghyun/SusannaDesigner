import sys, json, time, os, datetime; sys.path.insert(0, os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent')))
from module_browser import _fast as F
c = F.CDP(match='talkcloud.kakao.com')
JS = r'''(async()=>{const H={credentials:"include",headers:{Accept:"application/json+javascript"}};
const ch=await (await fetch("https://drawer-api.kakao.com/chat/list?verticalType=FILE",H)).json();
const F=await (await fetch("https://drawer-api.kakao.com/v2/mediaFile/list?verticalType=FILE&direction=DESC&fetchCount=10",H)).json();
const M=await (await fetch("https://drawer-api.kakao.com/v2/mediaFile/list?verticalType=MEDIA&direction=DESC&fetchCount=10",H)).json();
return JSON.stringify({ch,F,M});})()'''
r = json.loads(c.eval(JS))
t = {x.get('hashedChatId'): x.get('title') for x in r['ch']['items']}
new = []
for k in ('F', 'M'):
    for i in r[k]['items']:
        d = datetime.datetime.fromtimestamp(int(i['createdAt']) / 1000)
        print(k, d.strftime('%m/%d %H:%M'), t.get(i['hashedChatId']), i['contentType'], i['size'], i.get('name') or i.get('originalFileName') or '', i['url'][-28:])
        if d.date() == datetime.date(2026, 10, 11) and d.hour >= 16 and t.get(i['hashedChatId'], '').startswith('수산나디자인'):
            new.append(i)
json.dump(new, open(sys.argv[0].replace('.py', '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(json.dumps(r['F']['items'][0], ensure_ascii=False)[:800])
