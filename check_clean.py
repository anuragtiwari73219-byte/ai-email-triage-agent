import csv

total = 0
u_correct = 0
t_correct = 0
both = 0
failed = 0

with open('eval_results.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if 'Failed:' in row['model_reason']:
            failed += 1
            continue
        total += 1
        if row['urgency_match'] == 'True':
            u_correct += 1
        if row['topic_match'] == 'True':
            t_correct += 1
        if row['both_match'] == 'True':
            both += 1

print(f'Excluded (rate-limited): {failed}')
print(f'Clean total: {total}')
print(f'Urgency accuracy: {u_correct}/{total} ({100*u_correct/total:.1f}%)')
print(f'Topic accuracy: {t_correct}/{total} ({100*t_correct/total:.1f}%)')
print(f'Both-correct: {both}/{total} ({100*both/total:.1f}%)')