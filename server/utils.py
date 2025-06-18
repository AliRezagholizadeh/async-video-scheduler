"""Functions used in this script have been inspired by ChatGPT or Google AI powered suggestions.  """
import asyncio
import subprocess
import psutil
import time
import socket
import requests
import signal
import platform


def kill_process_on_port(port):
    for proc in psutil.process_iter(['pid', 'connections']):
        try:
            for conn in proc.info['connections']:
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    print(f"Process found: {proc.info['pid']}")
                    print(f"Killing process with PID: {proc.info['pid']}")
                    proc.send_signal(signal.SIGTERM)  # Try SIGTERM first
                    proc.wait(timeout=5)  # Wait for process to terminate gracefully

                    if proc.is_running():
                        print("Process did not terminate gracefully. Using SIGKILL.")
                        proc.send_signal(signal.SIGKILL)  # Use SIGKILL if needed
                        proc.wait(timeout=5)
                    return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    print(f"No process found listening on port {port}")

def is_port_open(host:str, port:str) -> bool:
    """Check if the given host:port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def start_server_in_new_terminal(command):
    """Starts a server command in a new macOS terminal window."""
    osascript_command = f"""
        tell application "Terminal"
            activate
            do script "{command}"
        end tell
    """
    subprocess.run(["osascript", "-e", osascript_command], check=True)


class RTMP_Server:
    """It will handle running preinstalled Mediamtx RTMP on a host and port if needed."""
    def __init__(self, config):
        self.config = config
        self.host = config['RTMPServerAddress']['server_address']
        self.port = config['RTMPServerAddress']['server_port']
        self.stream_path = config['RTMPServerAddress']['tail']
        self.exec_path = config["MediaMTX"]["exec_path"]
        self.config_path = config["MediaMTX"]["config_path"]

    def is_mediamtx_running(self) -> bool:
        """Check if a mediamtx process is running."""
        for process in psutil.process_iter(['name']):
            if process.info['name'] == 'mediamtx':
                return True
        return False


    def start_mediamtx_if_needed(self) -> subprocess.Popen:
        """Start MediaMTX server if not already running. Returns the process if started, else None."""
        if self.is_mediamtx_running():
            print("MediaMTX is already running.")
            return None

        cmd = [self.exec_path]



        print("Starting MediaMTX server...")

        os_name = platform.system()

        if os_name == "Windows":
            if self.config_path:
                cmd += ["-config", self.config_path]
            return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True,
                                    creationflags=subprocess.CREATE_NEW_CONSOLE)

        elif os_name == "Linux":
            subprocess.Popen(["nohup", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif os_name == "Darwin":
            if self.config_path:
                cmd += [self.config_path]
            start_server_in_new_terminal(' '.join(cmd))


    def wait_for_rtmp_server(self, timeout: int = 60):
        """Wait until RTMP server is reachable on host:port."""

        print(f"Waiting for RTMP server at {self.host}:{self.port}...")

        start = time.time()
        while time.time() - start < timeout:
            if is_port_open(self.host, self.port):
                print("RTMP server is ready!")
                return True
            time.sleep(1)

        raise TimeoutError("RTMP server did not become ready in time.")


    def has_active_stream(self):
        """Check if the server is pushing the content to the url."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # Set a timeout for the connection attempt
            sock.connect((self.host, int(self.port)))
            sock.close()
            print("Server is active.")
            return True
        except (socket.error, socket.timeout) as e:
            print(f"Server is not active: {e}")

            return False


    # async def run(self, end_program_siganl: asyncio.Event):
    async def run(self):
        # check if MediaMTX RTMP Server is running
        message = "\nMediaMTX Server Handling --------- \n"
        print(message)
        message = ""
        check_time = [1 for t in range(60)]
        process = None
        while((not self.is_mediamtx_running() or not self.has_active_stream()) and len(check_time) > 0):
            # kill the port if a process has been listen on it and has been terminated improperly.
            if(self.has_active_stream()):
                message += f"A process has been listening on the port {self.port}. It needs to be killed. \n"
                kill_process_on_port(self.port)
                message += "The port is freed.\n"
                assert is_port_open(self.host, self.port), f"{self.host}:{self.port} is not open.."

            # try running MediaMTX server
            message += f"Run MediaMTX Server."
            try:
                process = self.start_mediamtx_if_needed()
            except Exception as e:
                print(message)
                raise Exception(f"There is problem in starting MediaMTX. \n{e}")
            print(f"\r{message}")
            message = ""
            t = check_time.pop()
            await asyncio.sleep(t)

        print("Server is running")

        # await end_program_siganl.wait()

        return process






