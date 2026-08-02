#!/usr/bin/env python3

import subprocess
import time

CLIENT = "clab-redundant-lab-client"
ROUTER_A = "clab-redundant-lab-router-a"
ROUTER_B = "clab-redundant-lab-router-b"

SERVER_IP = "192.168.0.2"

PRIMARY_INTERFACE = "eth2"
BACKUP_INTERFACE = "eth3"

PRIMARY_NEXT_HOP = "10.0.1.1"
BACKUP_NEXT_HOP = "10.0.3.1"

TIMEOUT_SECONDS = 15
POLL_INTERVAL_SECONDS = 1


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
    )


def set_link(container: str, interface: str, state: str) -> None:
    result = run_command(
        "docker",
        "exec",
        container,
        "ip",
        "link",
        "set",
        interface,
        state,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"Failed to set {container}:{interface} {state}: {message}"
        )


def has_connectivity() -> bool:
    result = run_command(
        "docker",
        "exec",
        CLIENT,
        "ping",
        "-c",
        "1",
        "-W",
        "1",
        SERVER_IP,
    )
    return result.returncode == 0


def get_route() -> str:
    result = run_command(
        "docker",
        "exec",
        CLIENT,
        "ip",
        "route",
        "show",
        SERVER_IP,
    )

    if result.returncode != 0:
        return ""

    return result.stdout.strip()


def wait_for_connectivity(expected: bool) -> bool:
    deadline = time.monotonic() + TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        if has_connectivity() is expected:
            return True
        time.sleep(POLL_INTERVAL_SECONDS)

    return False


def wait_for_next_hop(expected_next_hop: str) -> bool:
    deadline = time.monotonic() + TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        if f"via {expected_next_hop}" in get_route():
            return True
        time.sleep(POLL_INTERVAL_SECONDS)

    return False


def verify_state(
    *,
    description: str,
    connectivity_expected: bool,
    next_hop_expected: str | None,
) -> bool:
    print(description)

    if not wait_for_connectivity(connectivity_expected):
        actual = "available" if has_connectivity() else "unavailable"
        expected = "available" if connectivity_expected else "unavailable"
        print(
            f"FAIL: connectivity is {actual}, "
            f"but expected it to be {expected}"
        )
        print(f"   Current route: {get_route() or '<no route>'}")
        return False

    if next_hop_expected is not None:
        if not wait_for_next_hop(next_hop_expected):
            print(
                "FAIL: route did not converge to expected next hop "
                f"{next_hop_expected}"
            )
            print(f"   Current route: {get_route() or '<no route>'}")
            return False

        print(f"   Route: {get_route()}")
        print(f"   PASS: connectivity uses {next_hop_expected}")
        return True

    print(f"   Route: {get_route() or '<no route>'}")
    print("   PASS: connectivity is unavailable as expected")
    return True


def restore_all_paths() -> None:
    set_link(ROUTER_A, PRIMARY_INTERFACE, "up")
    set_link(ROUTER_B, BACKUP_INTERFACE, "up")


def main() -> int:
    print("Preparing test: enabling primary and backup paths")
    restore_all_paths()

    try:
        if not verify_state(
            description="1. Primary UP, backup UP",
            connectivity_expected=True,
            next_hop_expected=PRIMARY_NEXT_HOP,
        ):
            return 1

        print("   Disabling primary path")
        set_link(ROUTER_A, PRIMARY_INTERFACE, "down")

        if not verify_state(
            description="2. Primary DOWN, backup UP",
            connectivity_expected=True,
            next_hop_expected=BACKUP_NEXT_HOP,
        ):
            return 1

        print("   Disabling backup path")
        set_link(ROUTER_B, BACKUP_INTERFACE, "down")

        if not verify_state(
            description="3. Primary DOWN, backup DOWN",
            connectivity_expected=False,
            next_hop_expected=None,
        ):
            return 1

        print("   Enabling primary path")
        set_link(ROUTER_A, PRIMARY_INTERFACE, "up")

        if not verify_state(
            description="4. Primary UP, backup DOWN",
            connectivity_expected=True,
            next_hop_expected=PRIMARY_NEXT_HOP,
        ):
            return 1

        print("   Enabling backup path")
        set_link(ROUTER_B, BACKUP_INTERFACE, "up")

        if not verify_state(
            description="5. Primary UP, backup UP — final state",
            connectivity_expected=True,
            next_hop_expected=PRIMARY_NEXT_HOP,
        ):
            return 1

    finally:
        print("Restoring both paths")
        restore_all_paths()

    print("PASS: all BGP path combinations behaved as expected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())