#!/usr/bin/env python

## pigtrap.py 
# Python script for system monitoring, which logs processes that run the biggest and longest
# License: http://www.gnu.org/licenses/gpl.html

import gzip,os,re,subprocess,sys,time
from config import *

now = time.time()
today = time.time()
logfile = None
countPigs = 0
processes = {}
ignoreProc = re.compile(ignorePat)

class process:
	def __init__(self,user,pid,line):
		"""How to init:
		1. Take a line in the output of 'ps aux'
		2. Split it.
		3. Take the first field and pass it in as user, the second as PID
		4. For "line", send in the full array."""
		# USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
		self.user = user
		self.pid = pid
		self.cpuTot = float(line[2])
		self.memTot = float(line[3])
		self.vsz = line[4]
		self.rss = line[5]
		self.tty = line[6]
		self.stat = line[7]
		self.start = line[8]
		self.time = line[9]
		self.command = ' '.join(line[10:])
		self.count = 1

	def add(self,line):
		self.cpuTot += float(line[2])
		self.memTot += float(line[3])
		self.count += 1

	@property
	def cpu(self):
		return self.cpuTot / self.count
	
	@property
	def mem(self):
		return self.memTot / self.count

	def __str__(self):
		return '%s (c%f,m%f): %s'%(self.user,self.cpu,self.mem,self.command)

def getPs():
	return subprocess.check_output(['ps','aux']).split('\n')[1:]

def openLog():
	global logfile
	logfile = open(logFilename(),'a+')

def writeLog(pid):
	"""Record that a PID is being a resource hog"""
	global processes,logfile,strikes,sleep
	proc = processes[pid]
	logfile.write('[%s] %d %s %f%%cpu %f%%mem (over %d s): %s\n'%(time.strftime('%b %d %H:%M:%S'),pid,proc.user,proc.cpu,proc.mem,proc.count*sleep,proc.command))

def logFilename(ind=''):
	global gzipDays
	day = int(ind) if ind != '' else 0
	return 'trap.log%s%s'%('.%s'%ind if ind !='' else '','.gz' if day>=gzipDays else '')
	
def logRotate():
	global processes,maxDays,gzipDays,logfile
	if os.path.exists(logFilename(maxDays)):
		os.remove(logFilename(maxDays))
	for i in range(maxDays)[-2::-1]:
		if os.path.exists(logFilename(i)):
			if i != gzipDays-1: # Move old file to older file of same type
				os.rename(logFilename(i),logFilename(i+1))
			else: # Create new zip file
				f = open(logFilename(i),'rb')
				zf = gzip.open(logFilename(i+1),'wb')
				zf.writelines(f)
				f.close()
				zf.close()
				os.remove(logFilename(i))
	# New day, new logfile, new processes
	logfile.close()
	os.rename(logFilename(),logFilename(1))
	openLog()
	processes = {}
			
def refresh(concurrent):
	global processes,strikes
	# Clear out old PIDs that came and went quietly:
	processes = dict(map(lambda pid:(pid,processes[pid]),concurrent))
	# Clear out old PIDs that are sticking around:
	processes = dict(filter(lambda (pid,proc):proc.count <= strikes,processes.items()))

def pigs():
	global processes,cpuThresh,memThresh,countPigs
	for (pid,proc) in processes.items():
		if proc.cpu > cpuThresh or proc.mem > memThresh:
			countPigs += 1
			yield pid

while True:
	try:
		now = time.time()
		if now-today >= logInterval:
			today = now
			logRotate()
		concurrent = []
		for line in getPs():
			llist = line.split()
			if len(llist):
				if not ignoreProc.match(llist[10]):
					uid = llist[0]
					pid = int(llist[1])
					concurrent.append(pid)
					if pid in processes:
						processes[pid].add(llist)
					else:
						processes[pid] = process(uid,pid,llist)
		# Record which processes are being pigs:
		openLog()
		countPigs = 0
		for pigPID in pigs():
			if processes[pid].cpu > 10:
				print pid,processes[pid].cpu
			writeLog(pigPID)
		if countPigs > 0:
			print "Recorded that %d processes were being resource hogs."%countPigs
		logfile.close()
		refresh(concurrent)
		# Wait a moment before repeating the process
		time.sleep(sleep)
	except KeyboardInterrupt:
		sys.exit(0)
