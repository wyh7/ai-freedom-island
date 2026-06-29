import json, re, os
from collections import Counter, defaultdict

worlds = ['claude_world', 'qwen_world', 'gpt_world', 'gemini_world']
results = {}

for world in worlds:
    log_path = f'logs/{world}_stdout.txt'
    awi_path = f'results/{world}/awi.json'
    crime_path = f'results/{world}/crimes.json'

    awi = json.load(open(awi_path, encoding='utf-8'))
    crimes = json.load(open(crime_path, encoding='utf-8')) if os.path.exists(crime_path) else []
    last = awi[-1]

    log = ''
    if os.path.exists(log_path):
        with open(log_path, encoding='utf-8', errors='ignore') as f:
            log = f.read()

    # diary quotes (content between ' after write_diary(content=)
    diary_matches = re.findall(r"write_diary\(content='([^']+)'", log)
    # billboard posts
    bb_matches = re.findall(r"post_to_billboard\((?:content|message)='([^']+)'", log)
    # agent dialogue
    say_matches = re.findall(r"say_to_agent\(target='(\w+)', message='([^']+)'", log)
    # think_aloud
    think_matches = re.findall(r"think_aloud\(thought='([^']+)'", log)
    # proposals
    proposal_matches = re.findall(r"submit_proposal\(title='([^']+)', body='([^']+)'", log)

    # crimes per day
    by_day = defaultdict(int)
    for c in crimes:
        by_day[c['day']] += 1
    first_crime_day = min((c['day'] for c in crimes), default=None)

    results[world] = {
        'last': last,
        'crimes': crimes,
        'crime_types': dict(Counter(c['type'] for c in crimes)),
        'top_criminals': Counter(c['actor'] for c in crimes).most_common(3),
        'first_crime_day': first_crime_day,
        'crimes_by_day': dict(by_day),
        'diary_quotes': diary_matches[:5],
        'bb_quotes': bb_matches[:5],
        'say_samples': say_matches[:5],
        'think_samples': think_matches[:3],
        'proposals': proposal_matches[:3],
        'awi': awi,
    }
    print(f'{world}: {len(diary_matches)} diary, {len(bb_matches)} BB, {len(crimes)} crimes, {len(proposal_matches)} proposals')
    if diary_matches:
        print(f'  Diary[0]: {diary_matches[0][:100]}')
    if bb_matches:
        print(f'  BB[0]: {bb_matches[0][:100]}')
    if think_matches:
        print(f'  Think[0]: {think_matches[0][:100]}')
    print()
