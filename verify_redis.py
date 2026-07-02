import redis
r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
keys = r.keys('patient:*')
print(f'Total keys found: {len(keys)}')
if keys:
    print('Sample keys:', keys[:5])
else:
    print('Still empty!')
