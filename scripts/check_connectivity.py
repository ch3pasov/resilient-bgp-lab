#!/usr/bin/env python3

import subprocess
import sys


CLIENT_CONTAINER = "clab-routed-lab-client"
SERVER_IP = "10.0.2.2"


def check_connectivity() -> bool:
    command = [
        "docker",
        "exec",
        CLIENT_CONTAINER,
        "ping",
        "-c",
        "1",
        "-W",
        "1",
        SERVER_IP,
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    return result.returncode == 0


def main() -> int:
    if check_connectivity():
        print(f"OK: {CLIENT_CONTAINER} can reach {SERVER_IP}")
        return 0

    print(f"FAIL: {CLIENT_CONTAINER} cannot reach {SERVER_IP}")
    return 1


if __name__ == "__main__":
    sys.exit(main())