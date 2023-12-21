import os
import subprocess
import sys
from apscheduler.schedulers.blocking import BlockingScheduler

def kill_pyre():
  try:
    # The os.setsid() is passed in the argument preexec_fn so
    # it's run after the fork() and before  exec() to run the shell.
    proc = subprocess.Popen("pkill -c pyre.bin".split(" "), stdout=subprocess.PIPE, preexec_fn=os.setsid)
    out = proc.communicate(timeout=180)[0]
    out = out.decode(sys.stdout.encoding)
    print(out)
  except Exception as e:
      print(e)

scheduler = BlockingScheduler()
scheduler.add_job(kill_pyre, 'interval', minutes=30)
scheduler.start()
