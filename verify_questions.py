import sys
sys.stdout.reconfigure(encoding='utf-8')
import pokeapi_trivia as p

errors = 0
for i in range(30):
    q = p.generate_daily_trivia()
    if q['correct'] not in q['options']:
        print(f'ERROR: {q["question"]}')
        print(f'  Correct: {q["correct"]}')
        print(f'  Options: {q["options"]}')
        errors += 1
    else:
        print(f'OK: {q["question"]} -> {q["correct"]}')

print(f'\nTotal errors: {errors}/30')
