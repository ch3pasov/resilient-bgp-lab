#!/usr/bin/env python3

import subprocess
import time

CLIENT = "clab-redundant-lab-client"
SERVER_IP = "192.168.0.2"

TIMEOUT_SECONDS = 15
POLL_INTERVAL_SECONDS = 1


def has_connectivity() -> bool:
    result = subprocess.run(
        [
            "docker",
            "exec",
            CLIENT,
            "ping",
            "-c",
            "1",
            "-W",
            "1",
            SERVER_IP,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    print(f"Checking connectivity to {SERVER_IP}")

    deadline = time.monotonic() + TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        if has_connectivity():
            print("PASS: server is reachable over the BGP fabric")
            return 0

        time.sleep(POLL_INTERVAL_SECONDS)

    print("FAIL: server did not become reachable")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
