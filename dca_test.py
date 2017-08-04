from subprocess import call

for i in range(10):
	call(['./dca', 'transaction', 'reservebudget', '-p', 'p1', '-e', '5', '-m'])

import time
time.sleep(5)

for i in range(10):
	call(['./dca', 'transaction', 'charge', '-p', 'p1', '-e', '5', '-j', '5', '-s', '2017-08-04 10:10:00', '-m'])
