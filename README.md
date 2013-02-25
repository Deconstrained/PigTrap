# PigTrap

Logs whenever any processes get resource-hungry.

## Usage:
In config.py:

* Set maxDays to the total number of log files to keep.
* Set gzipDays to the number of "days" after which to begin zipping old logfiles
* Set sleep to the number of seconds between calls to ps for gathering information on running processes
* Set strikes to the number of intervals (calls to ps) after which averages are reset. This is to prevent short-term average resource consumption from being diluted by longer periods of inactivity in the case of long-running processes that only get greedy on occasion.
* Set memThresh to the minimum percentage of memory usage above which a process will be counted as a "resource hog"
* Set cpuThresh to the minimum "..." cpu usage "..."
* set logInterval to the number of seconds to wait before rotating logfiles (i.e. 86400 for 24 hours)