import redis
r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
keys = r.keys('patient:*:features')
print(f'Total keys in Redis: {len(keys)}')

if keys:
    ids = sorted([int(k.split(':')[1]) for k in keys])
    print('Available patient IDs (first 20):', ids[:20])
    print('Min ID:', min(ids), '| Max ID:', max(ids))
else:
    print('No data found!')