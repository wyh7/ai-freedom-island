"""
Example: Run a single-world experiment with Qwen Plus for 5 days.
This is the quickest way to verify your setup works.
"""

import subprocess
import sys

result = subprocess.run([
    sys.executable, "run_with_env.py",
    "--world", "example_qwen",
    "--model", "qwen-turbo",   # turbo is cheaper; use qwen-plus for full quality
    "--days", "5",
], capture_output=False)

print("\nExperiment complete. Check results/example_qwen/")
print("Run audit: python audit.py --world example_qwen --full")
