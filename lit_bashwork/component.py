import lightning.app as la
from lightning.app.storage.path import Path
from lightning.app.storage.drive import Drive
from lightning.app.structures import Dict, List
from lightning.app.utilities.app_helpers import _collect_child_process_pids
from lit_bashwork.lit_bashwork_utils import add_to_system_env, args_to_dict
from lit_bashwork.lit_work_utils import work_is_free, work_calls_len

import os
import subprocess 
import threading
import shlex
from string import Template
import signal
import time
from functools import partial

class LitBashWork(la.LightningWork):
  def __init__(self, *args, 
      wait_seconds_after_run = 10,
      wait_seconds_after_kill = 10,
      drive_name = "lit://lpa",
      **kwargs):
    super().__init__(*args, **kwargs)
    self.wait_seconds_after_run = wait_seconds_after_run
    self.wait_seconds_after_kill = wait_seconds_after_kill
    self.drive_lpa = Drive(drive_name)

    self.pid = None
    self.exit_code = None
    self.stdout = None
    self.inputs = None
    self.outputs = None
    self.args = ""

    self._wait_proc = None

  def reset_last_args(self) -> str:
    self.args = ""

  def reset_last_stdout(self) -> str:
    self.stdout = None

  def last_args(self) -> str:
    return(self.args)

  def last_stdout(self):
    return(self.stdout)

  def on_before_run(self):
    """Called before the python script is executed."""

  def on_after_run(self):
      """Called after the python script is executed. Wrap outputs in Path so they will be available"""

  # statistics on this work
  def work_is_free(self) -> bool:
      return(work_is_free(self))
  def work_calls_len(self) -> int:
      return(work_calls_len(self))

  # drive
  def get_from_drive(self,inputs):
    for i in inputs:
      # print(f"drive get {i}")
      try:                     # file may not be ready 
        self.drive_lpa.get(i)  # Transfer the file from this drive to the local filesystem.
      except:
        pass  
      #os.system(f"find {i} -print")

  def put_to_drive(self,outputs):
    for o in outputs:
      # print(f"drive put {o}")
      # make sure dir end with / so that put works correctly
      if os.path.isdir(o):
        o = os.path.join(o,"")
      # os.system(f"find {o} -print")
      self.drive_lpa.put(o)  

  def popen_wait(self, cmd, save_stdout, exception_on_error, **kwargs):
    """empty the stdout, do not set pid"""
    with subprocess.Popen(
      cmd, 
      stdout=subprocess.PIPE, 
      stderr=subprocess.STDOUT, 
      bufsize=0, 
      close_fds=True, 
      shell=True, 
      executable='/bin/bash',
      **kwargs
    ) as self._wait_proc:
        if self._wait_proc.stdout:
            with self._wait_proc.stdout:
                for line in iter(self._wait_proc.stdout.readline, b""):
                    #logger.info("%s", line.decode().rstrip())
                    line = line.decode().rstrip() 
                    print(line)
                    if save_stdout:
                      if self.stdout is None: 
                        self.stdout = []
                      self.stdout.append(line)

    if exception_on_error and self.exit_code != 0:
      raise Exception(self.exit_code)  

  def popen_nowait(self, cmd, **kwargs):
    proc = subprocess.Popen(
      cmd, 
      shell=True, 
      executable='/bin/bash',
      close_fds=True,
      **kwargs
    )
    self.pid = proc.pid

  def subprocess_call(self, cmd, 
    save_stdout=True, 
    exception_on_error=False, 
    venv_name = "", 
    wait_for_exit=True, 
    timeout=0,
    **kwargs):
    """run the command"""
    cmd = Template(cmd).substitute({'host':self.host,'port':self.port}) # replace host and port
    cmd = ' '.join(shlex.split(cmd))                # convert multiline to a single line
    print(cmd, kwargs)
    kwargs['env'] = add_to_system_env(**kwargs)
    pwd = os.path.abspath(os.getcwd())
    if venv_name:
      cmd = f"source ~/{venv_name}/bin/activate; which python; {cmd}; deactivate"
      
    if wait_for_exit:
      print("wait popen")
      # start the thread
      target = partial(self.popen_wait, cmd, save_stdout=save_stdout, exception_on_error=exception_on_error, **kwargs)
      thread = threading.Thread(target=target)
      thread.start()
      # tr 
      thread.join(timeout)
      if thread.is_alive() and timeout > 0:
        print(f"terminating after waiting {timeout}")
        self._wait_proc.terminate()
      # should either wait, process is already done, or kill
      thread.join()
      print(self._wait_proc.returncode)
      print("wait completed",cmd)
    else:
      print("no wait popen")
      self.popen_nowait(cmd, **kwargs)
      print("no wait completed",cmd)

  def run(self, args, 
    venv_name="",
    save_stdout=False,
    wait_for_exit=True, 
    input_output_only = False, 
    kill_pid=False,
    inputs=[], outputs=[], 
    run_after_run=[],
    timeout=0,
    **kwargs):

    print(f"args={args} \n venv_name={venv_name} \n save_stdout={save_stdout} \n wait_for_exit={wait_for_exit} \n input_output_only={input_output_only} \n kill_pid={kill_pid} \n inputs={inputs} \n outputs={outputs} \n run_after_run={run_after_run} timeout={timeout} kwargs={kwargs}")
    
    # pre processing
    self.on_before_run()    
    self.get_from_drive(inputs)
    # set args stdout
    self.args = args
    self.stdout = None

    # run the command
    if not(input_output_only):
      # kill previous process
      if self.pid and kill_pid:
        print(f"***killing {self.pid}")
        os.kill(self.pid, signal.SIGTERM)
        info = os.waitpid(self.pid, 0)
        while is_port_in_use(self.host, self.port):
          print(f"***killed. pid {self.pid} waiting to free port")
          time.sleep(self.wait_seconds_after_kill)

      # start a new process
      self.subprocess_call(
        cmd=args, venv_name = venv_name, save_stdout=save_stdout, wait_for_exit=wait_for_exit, timeout=timeout, **kwargs)

    # Hack to get info after the run that can be passed to Flow 
    for cmd in run_after_run:
      self.popen_wait(cmd, save_stdout=True, exception_on_error=False, **kwargs)

    # post processing
    self.put_to_drive(outputs) 
    # give time for REDIS to catch up and propagate self.stdout back to flow
    if save_stdout or run_after_run:
      print(f"waiting work to flow message sleeping {self.wait_seconds_after_run}")
      time.sleep(self.wait_seconds_after_run) 
    # regular hook  
    self.on_after_run()

  def on_exit(self):
      for child_pid in _collect_child_process_pids(os.getpid()):
          os.kill(child_pid, signal.SIGTERM)
