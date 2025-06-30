# ----------------------------------------------------------------------------
# udp_test_remote.py
#
# Copyright (c) 2023 [Peter Jacobi]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ----------------------------------------------------------------------------

""" udp_test_remote
  Author: Peter Jacobi
  Task: connect to a UDP-Client and deliver commandos to get an answer.
        This script can too run in loop and request the command multiple times.
        Another feature is to enter a docker network and do the former specified task.
        With this method it can enter any running network.
  Execute:
    This version has extended execution options to be as flexible as possible without exploding in features.
    To Simply connect to an udp-listener and ask a string command:
          python3 udp_test_remote.py -p <port> -q <query-command>
    ... same as before but request same command in loop for 10 times. If the -l 10 is missing the loop is endless.
        Terminate with ctrl-c:
           python3 udp_test_remote.py -p <port> -q <query-command> --loop -l 10
    ... same but enter a running docker network-environment using the compose-image-name and do the former specified task.
           python3 udp_test_remote.py <port> <commando> --loop -c <compose-docker-imagename>
    ... same but enter any network-environment usind the network-process-id and do the former specified task.
           python3 udp_test_remote.py <port> <commando> --loop -i <ns-pid>

        Arguments:
            -p <port>       The port number we listen, default 44440. The ip will be always 127.0.0.1 or localhost.
            -q <commando>   A commando the udp-listener understands. If no query is given the program sends "none"
            --loop          Give here the word "loop" if you want an endliess loop mode, break with ctrl-c
            -l <number of times>    Requires the --loop option to be set. Runs a number of times end ends.
            -i <ns-pid>     Give here the network pid of the container or participant of a running network.
                            This mode only runs with root-rights!
                            This mode has requirements you need to fullfill, read below.
            -c <compose-docker-imagename>   optional to -i you only enter the name of the container to enter the network
            --remote-ip <ip-address>    default 127.0.0.1
            --remote-port <port>    default 44444
            --logfile <logfile-name>    default udp_log.json
            --logformat <json | csv>        possible formats are "json" or "csv", default is json
            --log-on <all | success | fail> choose one of the three log options as argument, default is all
            --timestamp-format <iso | unix> choose one of the three timestamp formats as argument default is iso

    Entering to a network namespace as participant, this can be for example a running docker-network (mounting into a netowrk namespace)
        1.You need root rights! -> This version requests root rights

        2.For this the app uses nsenter a program you need to install:
            sudo apt update && sudo apt install util-linux -y

        3.Get the running docker image pid by:
            docker inspect -f '{{.State.Pid}}' <container-name>
            ---> This version includes the -c option that requires only the container-name and it auto-connects! The ID is auto-recognized!

        The third step gives you the running docker process-id, this app uses to connect to a docker network.

"""
import socket
import json
import sys
import time
import ctypes
import os
import argparse
import subprocess
from datetime import datetime

LIBC = ctypes.CDLL("libc.so.6", use_errno=True)

def setns(fd, nstype):
    if LIBC.setns(fd, nstype) != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))

def enter_netns(pid):
    if os.geteuid() != 0:
        print("Error: Must be root to enter a network namespace.")
        sys.exit(1)

    netns_path = f"/proc/{pid}/ns/net"
    try:
        fd = os.open(netns_path, os.O_RDONLY)
        setns(fd, 0)
        os.close(fd)
        print(f"Entered network namespace of PID {pid}")
    except Exception as e:
        print(f"Failed to enter network namespace: {e}")
        sys.exit(1)

def get_pid_from_compose_name(compose_name):
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Pid}}", compose_name],
            capture_output=True, text=True, check=True
        )
        pid = int(result.stdout.strip())
        print(f"Resolved container '{compose_name}' to PID {pid}")
        return pid
    except subprocess.CalledProcessError as e:
        print(f"Could not resolve container '{compose_name}': {e.stderr}")
        sys.exit(1)

def get_timestamp(fmt):
    now = datetime.now()
    if fmt == "unix":
        return int(now.timestamp())
    return now.isoformat()

def log_entry(logfile, logformat, query, response, timestamp_format):
    timestamp = get_timestamp(timestamp_format)
    if logformat == "csv":
        with open(logfile, "a") as f:
            line = f'"{timestamp}","{query}","{response}"\n'
            f.write(line)
    else:  # json
        with open(logfile, "a") as f:
            entry = {
                "timestamp": timestamp,
                "query": query,
                "response": response
            }
            f.write(json.dumps(entry) + "\n")

def send_and_receive(listen_port, command, remote_ip, remote_port, config):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", listen_port))
    sock.settimeout(2.0)

    try:
        sock.sendto(command.encode(), (remote_ip, remote_port))
        data, addr = sock.recvfrom(4096)
        print(f"Antwort von {addr[0]}:{addr[1]}")
        try:
            json_data = json.loads(data.decode())
            response_pretty = json.dumps(json_data, indent=2)
            print(response_pretty)
            if config.logfile and config.log_on in ["all", "success"]:
                log_entry(config.logfile, config.logformat, command, json_data, config.timestamp_format)
        except json.JSONDecodeError:
            print("Antwort ist kein gültiges JSON:")
            print(data.decode())
            if config.logfile and config.log_on in ["all", "fail"]:
                log_entry(config.logfile, config.logformat, command, data.decode(), config.timestamp_format)
    except socket.timeout:
        print("Keine Antwort empfangen (Timeout)")
        if config.logfile and config.log_on in ["all", "fail"]:
            log_entry(config.logfile, config.logformat, command, "Timeout", config.timestamp_format)
    finally:
        sock.close()

def main():
    parser = argparse.ArgumentParser(description="UDP Cyberbox Test Client")
    parser.add_argument("-p", "--port", type=int, default=44440)
    parser.add_argument("-q", "--query", default="none")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("-l", "--repeat", type=int)
    parser.add_argument("-i", "--ns-pid", type=int)
    parser.add_argument("-c", "--compose-name")
    parser.add_argument("--remote-ip", default="127.0.0.1")
    parser.add_argument("--remote-port", type=int, default=44444)

    parser.add_argument("--logfile", nargs="?", const="udp_log.json")
    parser.add_argument("--logformat", choices=["json", "csv"], default="json")
    parser.add_argument("--log-on", choices=["all", "success", "fail"], default="all")
    parser.add_argument("--timestamp-format", choices=["iso", "unix"], default="iso")

    args = parser.parse_args()

    if args.compose_name:
        args.ns_pid = get_pid_from_compose_name(args.compose_name)

    if args.ns_pid:
        enter_netns(args.ns_pid)

    def loop_handler():
        if args.repeat:
            print(f"Looping {args.repeat} times...")
            for i in range(args.repeat):
                print(f"▶ Request {i + 1}/{args.repeat}")
                send_and_receive(args.port, args.query, args.remote_ip, args.remote_port, args)
                time.sleep(5)
        else:
            print("Looping until interrupted (CTRL+C)")
            try:
                while True:
                    send_and_receive(args.port, args.query, args.remote_ip, args.remote_port, args)
                    time.sleep(5)
            except KeyboardInterrupt:
                print("\nLoop interrupted by user.")

    if args.loop:
        loop_handler()
    else:
        print(f"Sending '{args.query}' to {args.remote_ip}:{args.remote_port}, listening on {args.port}")
        send_and_receive(args.port, args.query, args.remote_ip, args.remote_port, args)

if __name__ == "__main__":
    main()
