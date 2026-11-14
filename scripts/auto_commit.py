#!/usr/bin/env python3
"""Делает 3-5 коммитов в день в случайное время. Каждый коммит реально меняет файлы."""
import datetime as dt
import os
import random
import subprocess
import sys
import uuid
from pathlib import Path

# ---------- НАСТРОЙКИ ----------
UTC_OFFSET = 5            # твой часовой пояс (Ташкент = +5)
START_HOUR = 9            # окно активности: с 09:00
END_HOUR = 23             # ... до 23:00 (по твоему времени)
MIN_COMMITS, MAX_COMMITS = 3, 5
# -------------------------------

TZ = dt.timezone(dt.timedelta(hours=UTC_OFFSET))
now = dt.datetime.now(TZ)
today = now.date().isoformat()

ROOT = Path(__file__).resolve().parent.parent
ACT = ROOT / "activity"
ACT.mkdir(exist_ok=True)
LOG = ACT / "log.txt"
STATS = ACT / "stats.md"
SNIPPETS = ACT / "snippets"
SNIPPETS.mkdir(exist_ok=True)

# --- План дня (одинаковый при каждом запуске в течение дня) ---
rng = random.Random(f"plan-{today}")
n_commits = rng.randint(MIN_COMMITS, MAX_COMMITS)
window = (END_HOUR - START_HOUR) * 60
seg = window // n_commits
# окно делится на n частей, в каждой выбирается случайная минута -> время разное каждый день
plan = [START_HOUR * 60 + i * seg + rng.randint(0, seg - 1) for i in range(n_commits)]

# --- Сколько уже сделано сегодня ---
lines = LOG.read_text().splitlines() if LOG.exists() else []
done = sum(1 for l in lines if l.startswith(today))

now_min = now.hour * 60 + now.minute
force = os.environ.get("FORCE") == "1"

print(f"[{today}] план: {n_commits} коммитов в "
      f"{[f'{m//60:02d}:{m%60:02d}' for m in plan]}, сделано: {done}, сейчас {now:%H:%M}")

if not force:
    if done >= n_commits:
        print("План на сегодня выполнен.")
        sys.exit(0)
    if now_min < plan[done]:
        print("Ещё не время.")
        sys.exit(0)

# --- Реальные изменения файлов ---
token = uuid.uuid4().hex[:8]
rnd = random.Random()
value = rnd.randint(1000, 9999)

# 1) лог
with LOG.open("a") as f:
    f.write(f"{today} {now:%H:%M:%S} commit#{done + 1} id={token} value={value}\n")

# 2) статистика (меняются числа и дата)
total = len(LOG.read_text().splitlines())
STATS.write_text(
    f"# Activity stats\n\n"
    f"- Last update: {now:%Y-%m-%d %H:%M:%S} (UTC{UTC_OFFSET:+d})\n"
    f"- Total updates: {total}\n"
    f"- Random metric: {rnd.randint(0, 100000)}\n"
)

# 3) небольшой файл-сниппет
topics = ["note", "idea", "todo", "snippet", "tip"]
(SNIPPETS / f"{today}-{done + 1}-{token}.txt").write_text(
    f"{rnd.choice(topics)}: {uuid.uuid4()}\nvalue={value}\n"
)

messages = [
    "Update activity log", "Refresh stats", "Add daily note", "Minor update",
    "Update metrics", "Sync notes", "Add snippet", "Tweak data", "Routine update",
]
msg = f"{rnd.choice(messages)} ({today})"

def git(*args):
    subprocess.run(["git", *args], cwd=ROOT, check=True)

git("add", "-A")
# защита от пустого коммита
if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
    print("Нет изменений - коммит пропущен.")
    sys.exit(0)
git("commit", "-m", msg)
print("Коммит создан:", msg)
