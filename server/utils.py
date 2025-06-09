import subprocess
import psutil
import time
import socket

def is_mediamtx_running() -> bool:
    """Check if a mediamtx process is running."""
    for process in psutil.process_iter(['name']):
        if process.info['name'] == 'mediamtx':
            return True
    return False


def start_mediamtx_if_needed(exec_path: str, config_path: str = None) -> subprocess.Popen:
    """Start MediaMTX server if not already running. Returns the process if started, else None."""
    if is_mediamtx_running():
        print("MediaMTX is already running.")
        return None

    cmd = [exec_path]
    if config_path:
        cmd += ["-config", config_path]

    print("Starting MediaMTX server...")
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)



def is_port_open(host: str, port: int) -> bool:
    """Check if the given host:port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def wait_for_rtmp_server(host: str, port: int, timeout: int = 60):
    """Wait until RTMP server is reachable on host:port."""
    print(f"Waiting for RTMP server at {host}:{port}...")
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open(host, port):
            print("RTMP server is ready!")
            return True
        time.sleep(1)
    raise TimeoutError("RTMP server did not become ready in time.")


