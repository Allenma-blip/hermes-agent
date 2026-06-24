#!/usr/bin/env python3
import os, json, hashlib
from datetime import datetime

# Use hermes_tools for memory
from hermes_tools import read_file, write_file, memory, fact_store

vault_root = os.path.expanduser('~/Documents/HermesVault')
history_path = os.path.expanduser('~/.hermes/obsidian_zenbrain_history.json')
skip_prefixes = ['.obsidian', '.trash', '.git', '.claude', '.claudian']

if not os.path.exists(history_path):
    history = {}
else:
    with open(history_path, 'r') as f:
        history = json.load(f)

current_files = []
for dirpath, dirnames, filenames in os.walk(vault_root):
    dirnames[:] = [d for d in dirnames if not any(d.startswith(s) for s in skip_prefixes)]
    for fname in filenames:
        if fname.endswith('.md'):
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, vault_root)
            if os.path.getsize(full_path) > 500*1024:
                continue
            current_files.append(rel_path)

new_or_changed = []
for rel_path in current_files:
    full_path = os.path.join(vault_root, rel_path)
    with open(full_path, 'rb') as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()
    if rel_path not in history:
        new_or_changed.append((rel_path, content_hash, 'new'))
    elif history[rel_path].get('hash') != content_hash:
        new_or_changed.append((rel_path, content_hash, 'changed'))

print(f"Total current .md files: {len(current_files)}")
print(f"History entries: {len(history)}")
print(f"New/changed files: {len(new_or_changed)}")

to_process = new_or_changed[:10]
print(f"Processing top {len(to_process)} files")

added = updated = skipped = 0

def extract_fact(content):
    lines = content.split('\n')
    start = 0
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                start = i + 1
                break
    body = '\n'.join(lines[start:])
    paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
    for p in paragraphs:
        if p.startswith('#'):
            continue
        if len(p) > 20:
            return p[:200]
    return None

for rel_path, content_hash, change_type in to_process:
    full_path = os.path.join(vault_root, rel_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read(5000)
        fact = extract_fact(content)
        if not fact:
            print(f"SKIP {rel_path}: no fact extracted")
            skipped += 1
            continue
        
        fact_text = f"{rel_path}: {fact}"
        memory(action='add', target='memory', content=fact_text)
        fact_store(action='add', content=fact_text)
        print(f"ADDED {rel_path}: {fact[:60]}...")
        added += 1
        
        history[rel_path] = {
            "hash": content_hash,
            "fact_id": None,
            "pending": True,
            "size": os.path.getsize(full_path),
            "mtime": os.path.getmtime(full_path),
            "updated_at": datetime.now().strftime('%Y-%m-%d')
        }
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR {rel_path}: {e}")
        skipped += 1

print(f"\nadded={added}, updated={updated}, skipped={skipped}")
