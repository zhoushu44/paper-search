# -*- coding: utf-8 -*-
"""Quick test script"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
import time
import re
from datetime import datetime

# Config
OPENAI_KEY = 'sk-rniPHXm3rCD1M4LIyFFw0zhXsJIdmfXIRRZLEsSpBoLk56n2'
OPENAI_BASE = 'https://api.nofx.online/v1'
OPENAI_MODEL = 'gpt-5.4'
SERPAPI_KEY = 'a65089c62fdfa94600f13300d3684e2051b4efe95d160d28d32a6f799a823571'

TOP_VENUES = {'NeurIPS', 'ICML', 'ICLR', 'ACL', 'EMNLP', 'CVPR', 'ICCV', 'KDD', 'SIGIR'}

def search_serpapi(keyword, n=5):
    print('  [SerpAPI] Searching...')
    url = 'https://serpapi.com/search'
    params = {'engine': 'google_scholar', 'q': f'{keyword} after:2021', 'api_key': SERPAPI_KEY, 'num': n}
    r = requests.get(url, params=params, timeout=30)
    papers = []
    for p in r.json().get('organic_results', []):
        papers.append({
            'title': p.get('title', ''),
            'year': 2023,
            'venue': '',
            'abstract': p.get('snippet', ''),
            'citations': 0
        })
    print(f'  Found {len(papers)}')
    return papers

def analyze(title, abstract, keyword):
    prompt = f'''Analyze paper:
Title: {title}
Abstract: {abstract[:400]}
Keyword: {keyword}
Return JSON: {{"summary": "summary", "chinese": "Chinese explanation", "apps": "applications", "suggs": "suggestions"}}'''
    try:
        r = requests.post(f'{OPENAI_BASE}/chat/completions',
            headers={'Authorization': f'Bearer {OPENAI_KEY}', 'Content-Type': 'application/json'},
            json={'model': OPENAI_MODEL, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0.3, 'max_tokens': 500},
            timeout=60)
        m = re.search(r'\{[\s\S]*\}', r.json()['choices'][0]['message']['content'])
        if m: return json.loads(m.group())
    except Exception as e:
        print(f'Error: {e}')
    return {}

def is_top(venue):
    for t in TOP_VENUES:
        if t in venue.upper(): return True, t
    return False, ''

def main():
    keyword = 'attention mechanism'
    print(f'\n{"="*50}\nSearching: {keyword}\n{"="*50}\n')

    papers = search_serpapi(keyword, 3)
    results = []

    for i, p in enumerate(papers):
        print(f'\n[{i+1}] {p["title"][:45]}...')

        print('  Analyzing...', end=' ')
        analysis = analyze(p['title'], p.get('abstract', ''), keyword)

        if analysis:
            p['summary'] = analysis.get('summary', '')
            p['chinese'] = analysis.get('chinese', '')
            p['apps'] = analysis.get('apps', '')
            p['suggs'] = analysis.get('suggs', '')
            results.append(p)
            print('Done')
        else:
            print('Failed')
        time.sleep(1)

    # Generate MD
    md = f'''# Paper Search: {keyword}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

| # | Paper | Summary | Chinese | Applications |
|---|-------|---------|---------|--------------|
'''
    for i, p in enumerate(results, 1):
        md += f"| {i} | [[{p['title'][:40]}]] | {p.get('summary', '')[:30]} | {p.get('chinese', '')[:30]} | {p.get('apps', '')[:25]} |\n"

    fn = f'papers_{keyword.replace(" ", "_")}.md'
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(md)

    print(f'\n{"="*50}\nSaved: {fn}\nTotal: {len(results)} papers\n{"="*50}')

if __name__ == '__main__':
    main()
