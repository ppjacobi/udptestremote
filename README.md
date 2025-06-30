# README.md

# udp_test_remote

## Overview

`udp_test_remote.py` is a Python-based utility for interacting with a UDP client. The script provides various features, including the ability to send commands, retrieve responses, and optionally operate within a Docker network namespace. Additionally, it supports running in a loop to send commands repeatedly. The purpose of this tool is to enable flexible and configurable communication with UDP servers, making it suitable for debugging, testing, and monitoring tasks.

---

## Features

- **Send and Receive UDP Messages:** Allows sending commands to a UDP listener and receiving responses.
- **Loop Mode:** Execute the same command multiple times, either a defined number of times or indefinitely (until interrupted).
- **Docker Network Integration:** Enter a Docker container's network namespace and execute UDP communications.
- **Customizable Logging:** Supports logging responses in JSON or CSV format with configurable log levels (all, success, or fail) and timestamp formats (ISO or Unix).
- **Flexible Arguments:** Extensive argument support to customize the behavior based on execution requirements.

---

## Usage

### Basic Command Execution
To connect to a UDP server and send a command:
```shell script
python3 udp_test_remote.py -p <port> -q <query-command>
```

Example:
```shell script
python3 udp_test_remote.py -p 44440 -q "status"
```

---

### Loop Execution
Send the same command multiple times. You can either loop indefinitely or specify the number of repetitions using the `-l` flag:
```shell script
python3 udp_test_remote.py -p <port> -q <query-command> --loop -l <number-of-repeats>
```

Example:
```shell script
python3 udp_test_remote.py -p 44440 -q "status" --loop -l 10
```

Terminate an endless loop with `Ctrl+C`.

---

### Docker Network Mode
Perform UDP communications within the network namespace of a Docker container using the container's compose name:
```shell script
python3 udp_test_remote.py -p <port> -q <query-command> --loop -c <compose-docker-imagename>
```

You can also use the Docker container's process ID (PID) instead of its name:
```shell script
python3 udp_test_remote.py -p <port> -q <query-command> --loop -i <ns-pid>
```

**Note: Root privileges are required for this feature.**

---

### Additional Arguments
- `--remote-ip <ip>`: Specify the remote IP address (default: `127.0.0.1`).
- `--remote-port <port>`: Specify the remote port (default: `44444`).
- `--logfile <logfile-name>`: Specify a logfile to store results (default: `udp_log.json`).
- `--logformat <json|csv>`: Define the log format (default: `json`).
- `--log-on <all|success|fail>`: Log all responses, only successes, or only failed requests (default: `all`).
- `--timestamp-format <iso|unix>`: Specify the timestamp format in the logs (default: `iso`).

---

## Requirements

1. **`nsenter` package:** Install `nsenter` for entering network namespaces. For Debian/Ubuntu:
```shell script
sudo apt update && sudo apt install util-linux -y
```

2. **Root Access:** Required for entering a network namespace.

3. **Docker Setup:** If using Docker container integration, ensure the Docker CLI is available and the target container is running.

4. **Docker Container Process ID:** 
   To obtain the PID of a running container:
```shell script
docker inspect -f '{{.State.Pid}}' <container-name>
```
   Alternatively, use the `-c <compose-docker-imagename>` argument for automatic PID recognition.

---

## Examples

### Basic UDP Communication
```shell script
python3 udp_test_remote.py -p 44440 -q "ping"
```

### Loop Sending Command
Send "ping" 5 times:
```shell script
python3 udp_test_remote.py -p 44440 -q "ping" --loop -l 5
```

### Docker Network Namespace
Send "ping" to a container's network:
```shell script
python3 udp_test_remote.py -p 44440 -q "ping" --loop -c my_container
```

---

## License

This software is licensed under the GNU General Public License v2.0 or later. See the [LICENSE](https://www.gnu.org/licenses/gpl-2.0.html) file for more information.

---

## Author
- **Peter Jacobi**, 2023

