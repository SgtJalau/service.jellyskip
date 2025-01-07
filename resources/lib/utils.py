import sys
import traceback
import logging
import xbmc

def get_player_speed():
    try:
        return float(xbmc.getInfoLabel("Player.PlaySpeed"))
    except (ValueError, TypeError):
        return None

def calc_wait_time(end_time=None, start_time=0, rate=None):
    # https://github.com/MoojMidge/service.upnext
    if not end_time or not rate or rate < 1:
        return None

    return max(0, (end_time - start_time) // rate)

def log(msg: str, level: int = xbmc.LOGINFO) -> None:
    if msg:
        xbmc.log(f"Jellyskip: {msg}", level)

def log_exception():
    exc_type, exc_value, exc_traceback = sys.exc_info()

    try:
        stack_summary = traceback.extract_stack(limit=10+2)[:-2]
        if exc_traceback:
            stack_summary.extend(traceback.extract_tb(exc_traceback))
        formatted_traceback = "".join(traceback.format_list(stack_summary))
    except Exception:
        formatted_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
 
    try:
        final_exc_line = traceback.format_exception_only(exc_type, exc_value)[0]
    except Exception:
        final_exc_line = ""

    ex_msg = (
        "EXCEPTION Thrown in Python callback/script (execution continues):\n"
        f"Error Type: {exc_type}\n"
        f"Error Contents: {exc_value}\n"
        "Traceback (most recent call last):\n"
        f"{formatted_traceback.rstrip()}\n"
        f"{final_exc_line}"
    )
    logging.error(ex_msg.rstrip())
