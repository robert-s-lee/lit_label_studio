import socket, errno
import shlex
import os

def args_to_dict(script_args:str) -> dict:
  """convert str to dict A=1 B=2 to {'A':1, 'B':2}"""
  script_args_dict = {}
  for x in shlex.split(script_args, posix=False):
    try:
      k,v = x.split("=",1)
    except:
      k=x
      v=None
    script_args_dict[k] = v
  return(script_args_dict) 

def add_to_system_env(env_key='env', **kwargs) -> dict:
  """add env to the current system env"""
  new_env = None
  if env_key in kwargs: 
    env = kwargs[env_key]
    if isinstance(env,str):
      env = args_to_dict(env)  
    if not(env is None) and not(env == {}):
      new_env = os.environ.copy()
      new_env.update(env)
  return(new_env)

def is_port_in_use(host:str, port: int) -> bool:
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
      s.bind((host, port))
      in_use = False
  except socket.error as e:
      in_use = True
      if e.errno == errno.EADDRINUSE:
          print("Port is already in use")
      else:
          # something else raised the socket.error exception
          print(e)

  s.close()
  return(in_use)
