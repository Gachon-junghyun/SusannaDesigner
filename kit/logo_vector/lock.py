"""세 작업자가 크롬(그림 뽑기)·일러스트를 같이 쓰므로 한 번에 한 명만. mkdir 는 원자적이다.
usage: python lock.py <img|illu> -- <명령…>      잠금을 잡고 명령을 돌린 뒤 푼다(실패해도 푼다)"""
import os, sys, time, subprocess, tempfile
name = sys.argv[1]; cmd = sys.argv[sys.argv.index("--") + 1:]
d = os.path.join(tempfile.gettempdir(), f"aidesigner_{name}.lock")
t0 = time.time()
while True:
    try:
        os.mkdir(d); break
    except FileExistsError:
        # 30분 넘은 잠금은 죽은 작업이 남긴 것으로 본다
        if time.time() - os.path.getmtime(d) > 1800:
            os.rmdir(d); continue
        time.sleep(5)
print(f"[잠금 {name}] 잡음 ({time.time()-t0:.0f}초 기다림)", flush=True)
try:
    r = subprocess.run(cmd).returncode
finally:
    os.rmdir(d)
sys.exit(r)
