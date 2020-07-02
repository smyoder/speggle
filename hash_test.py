from datetime import datetime
tuple = {}
nested = {}

number = 1
for x in range(10000):
  nested[x] = {}
  for y in range(10000):
    tuple[(x, y)] = 1
    nested[x][y] = 1

sum = 0
print("Tuple:")
start = datetime.now()
for x in range(10000):
  for y in range(10000):
    sum += tuple[(x, y)]

print(sum)
print(datetime.now() - start)

sum = 0
print("Nested:")
start = datetime.now()
for x in range(1000):
  for y in range(1000):
    sum += nested[x][y]

print(sum)
print(datetime.now() - start)
