import os, json
base = 'seo_audit/auditor/rules'
total = 0
by_cat = {}
for fn in sorted(os.listdir(base)):
    if not fn.endswith('.json'): continue
    with open(os.path.join(base, fn), 'r', encoding='utf-8') as f:
        rules = json.load(f)
    for r in rules:
        cat = r.get('category', 'unknown')
        by_cat[cat] = by_cat.get(cat, 0) + 1
    print(f'{fn}: {len(rules)}')
    total += len(rules)
print(f'TOTAL: {total}')
print('BY_CATEGORY:', json.dumps(by_cat, ensure_ascii=False, indent=2))
