import os

docs = os.listdir('data/')

processed, unprocessed = 0,0
for doc in docs:
    if '.md5' in doc:
        processed += 1
    else:
        unprocessed += 1

print(f'{processed} processed, {unprocessed - processed} to go')
