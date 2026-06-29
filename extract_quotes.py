import json, re

worlds = ['qwen_world', 'gemini_world', 'claude_world', 'gpt_world']
for world in worlds:
    log = f'logs/{world}_stdout.txt'
    print(f'=== {world} ===')
    try:
        with open(log, encoding='utf-8', errors='ignore') as f:
            content = f.read()
        bb = re.findall(r"post_to_billboard\((?:content|message)='([^']{30,120})'", content)
        for line in bb[:4]:
            print(f'  BB: {line}')
        diary = re.findall(r"write_diary\(content='([^']{40,120})'", content)
        for line in diary[:3]:
            print(f'  Diary: {line}')
    except Exception as e:
        print(f'  Error: {e}')
    print()
