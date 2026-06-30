"""
Example: Run all 4 model worlds in parallel (Season 1 replication).
Requires: BAILIAN_API_KEY, YUNHE_API_KEY, JINGZHE_API_KEY, JD_API_KEY
"""

import subprocess
import sys
import os

EXPERIMENTS = [
    ("season1_qwen",   "qwen-plus"),
    ("season1_gpt",    "gpt-4.1"),
    ("season1_gemini", "gemini-2.5-flash"),
    ("season1_claude", "claude-sonnet-4-6"),
]

DAYS = 15
procs = []

for world, model in EXPERIMENTS:
    print(f"Starting {world} with {model}...")
    log_file = open(f"logs/{world}.txt", "w")
    p = subprocess.Popen(
        [sys.executable, "run_with_env.py", "--world", world, "--model", model, "--days", str(DAYS)],
        stdout=log_file, stderr=log_file
    )
    procs.append((world, model, p, log_file))

print(f"\n{len(procs)} experiments running in parallel.")
print("Monitor with: python -c \"import os,re; [print(w, open(f'logs/{w}.txt').read().count('-> ok'), 'calls') for w in ['season1_qwen','season1_gpt','season1_gemini','season1_claude'] if os.path.exists(f'logs/{w}.txt')]\"")

for world, model, p, log_file in procs:
    p.wait()
    log_file.close()
    print(f"  {world}: done (exit {p.returncode})")

print("\nAll done. Run audit:")
for world, _, _, _ in procs:
    print(f"  python audit.py --world {world} --full")
