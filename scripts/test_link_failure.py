#!/usr/bin/env python3

import subprocess
import sys
import time


CLIENT_CONTAINER = "clab-routed-lab-client"
ROUTER_CONTAINER = "clab-routed-lab-router"
SERVER_IP = "10.0.2.2"
ROUTER_INTERFACE = "eth2"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )


def can_reach_server() -> bool:
    result = run(
        [
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
    )
    return result.returncode == 0


def set_link_state(state: str) -> None:
    result = run(
        [
            "docker",
            "exec",
            ROUTER_CONTAINER,
            "ip",
            "link",
            "set",
            ROUTER_INTERFACE,
            state,
        ]
    )

    if result.returncode != 0:
        print(f"ERROR: could not set {ROUTER_INTERFACE} {state}")
        print(result.stderr.strip())
        sys.exit(1)


def main() -> int:
    print("1. Checking initial connectivity")

    if not can_reach_server():
        print("FAIL: server is unreachable before the test")
        return 1

    print("OK: initial connectivity works")

    try:
        print(f"2. Disabling {ROUTER_CONTAINER}:{ROUTER_INTERFACE}")
        set_link_state("down")
        time.sleep(1)

        if can_reach_server():
            print("FAIL: connectivity still works after link failure")
            return 1

        print("OK: link failure was detected")

    finally:
        print(f"3. Restoring {ROUTER_CONTAINER}:{ROUTER_INTERFACE}")
        set_link_state("up")
        time.sleep(1)

    if not can_reach_server():
        print("FAIL: connectivity did not recover")
        return 1

    print("OK: connectivity recovered")
    print("PASS: link failure scenario completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
