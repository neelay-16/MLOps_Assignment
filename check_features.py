import redis
r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# Check specific key
key = 'patient:5:features'
data = r.get(key)
print(f'Key patient:5:features exists: {data is not None}')

# Check a few other keys
print('Checking patient:0, patient:1, patient:10...')
for pid in ['0', '1', '5', '10', '50']:
    k = f'patient:{pid}:features'
    exists = r.exists(k)
    print(f'{k} → exists: {bool(exists)}')