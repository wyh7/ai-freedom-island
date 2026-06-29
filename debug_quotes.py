import json, re, os

worlds = ['claude_world', 'qwen_world', 'gpt_world', 'gemini_world']
for world in worlds:
    log = f'logs/{world}_stdout.txt'
    if not os.path.exists(log):
        continue
    with open(log, encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # extract tool call lines from stdout
    bb_lines    = [l for l in content.split('\n') if 'post_to_billboard' in l and '->' in l and 'ok' in l.lower()]
    diary_lines = [l for l in content.split('\n') if 'write_diary' in l and '->' in l]
    crime_lines = [l for l in content.split('\n') if any(t in l for t in ['steal_from','commit_arson','assault_agent','intimidate_agent']) and '-> ok' in l]
    proposal_lines = [l for l in content.split('\n') if 'submit_proposal' in l and '-> ok' in l]

    print(f'=== {world} ===')
    print(f'  Billboard posts found in log: {len(bb_lines)}')
    for l in bb_lines[:3]:
        print(f'    {l.strip()[:120]}')
    print(f'  Crimes in log: {len(crime_lines)}')
    for l in crime_lines[:3]:
        print(f'    {l.strip()[:120]}')
    print(f'  Proposals in log: {len(proposal_lines)}')
    for l in proposal_lines[:2]:
        print(f'    {l.strip()[:120]}')
    print()
