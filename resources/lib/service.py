import logging
from monitor import JellySkipMonitor
from utils import log

if __name__ == "__main__":
    logging.getLogger().name = "Jellyskip"
    log("Loading service.py")
    monitor = JellySkipMonitor()
    monitor.run()

    del monitor
