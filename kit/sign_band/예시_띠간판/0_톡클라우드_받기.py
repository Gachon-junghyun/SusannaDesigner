import sys, json, time, os; sys.path.insert(0, os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent')))
from module_browser import _fast as F
dst = os.path.abspath(os.path.join(os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent')), 'users', os.environ.get('DEGAJA_USER', 'user'), 'domains', 'susanna', '시안', '2026-10_부대찌개', 'src', '1011'))
items = [i for i in json.load(open(sys.argv[0].replace('dl.py', 'tcnew.json'), encoding='utf-8')) if i['contentType'] == 'FILE']
c = F.CDP(match='talkcloud.kakao.com')
c.call('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': dst})
for i in items:
    c.eval('(()=>{const a=document.createElement("a");a.href="%s?attach";document.body.appendChild(a);a.click();a.remove();return 1})()' % i['url'])
    for _ in range(30):
        time.sleep(1)
        fs = [f for f in os.listdir(dst) if os.path.getsize(os.path.join(dst, f)) == int(i['size']) and not f.endswith('.crdownload')]
        if fs: print('OK', fs, i['size']); break
    else: print('timeout', i['originalFileName'])
print(os.listdir(dst))
