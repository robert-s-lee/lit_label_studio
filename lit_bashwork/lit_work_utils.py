import lightning as L
import lightning.app.utilities.enum as LUE
import pprint

def print_status(lwork:L.LightningWork):
  """
  the statuses shows calls in at most one pending and all running status
  even if there are 100s in pending, only one pending is shown

  status and statuses before any calls:
  WorkStatus(stage='not_started', timestamp=1659039787.638122, reason=None, message=None, count=1)
  []
  status and statuses after any calls:
  WorkStatus(stage='pending', timestamp=1659039787.651226, reason=None, message=None, count=1)
  [WorkStatus(stage='pending', timestamp=1659039787.651226, reason=None, message=None, count=1)]
  """
  pprint.pprint(lwork.status)
  pprint.pprint(lwork.statuses)

def work_calls_len(lwork:L.LightningWork):
  """get the number of call in state dict. state dict has current and past calls to work."""
  # reduce by 1 to remove latest_call_hash entry
  return(len(lwork.state["calls"]) - 1)

def work_is_free(lwork:L.LightningWork):
  """work is free to accept new calls. 
  this is expensive when a lot of calls accumulate over time
  work is when there is there is no pending and running calls at the moment
  pending status is verified by examining each call history looking for anything call that is pending history
  status.stage is not reliable indicator as there is delay registering new calls
  status.stage shows SUCCEEDED even after 3 more calls are accepted in parallel mode 
  """
  status = lwork.status
  state = lwork.state
  # more than one work can started this way 
  # there is work assignment and status update
  # multiple works are queued but 
  # count run that are in pending state
  if (status.stage==LUE.WorkStageStatus.NOT_STARTED or 
    status.stage==LUE.WorkStageStatus.SUCCEEDED or
    status.stage==LUE.WorkStageStatus.FAILED):
    # do not run if jobs are in pending state
    # not counting to reduce CPU load as looping thru all of the calls can get expensive
    pending_count = 0
    for c in state["calls"]:
      if c == 'latest_call_hash': continue
      if len(state["calls"][c]['statuses']) == 1:
        return(False)
    return(True)
  # must in pending or running or stopped.     
  else:
    return(False)            


