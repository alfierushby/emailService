import threading

# Event to signal threads to stop
from app import stop_event

def worker_exit(server, worker):
    """
    Gunicorn hook: Called just before a worker exits.
    """
    server.log.info("Worker exiting. Signaling background threads to stop.")
    stop_event.set()

    active_threads = threading.enumerate()
    server.log.info(f"Total active threads: {len(active_threads)}")
    # Join to make sure the process doesnt get killed until the background threads are done
    for thread in active_threads:
        if thread is threading.current_thread():
            continue
        thread.join()
   