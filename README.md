# Resilient BGP Network Lab

A reproducible Containerlab and FRRouting lab demonstrating redundant
eBGP paths, automatic failover, stable loopback addressing, and
automated resilience testing.

## Architecture

```text
                    router-a (AS 65010)
                   /                   \
client (AS 65001)                         server (AS 65002)
192.168.0.1/32     \                   /  192.168.0.2/32
                    router-b (AS 65020)
```

Link networks:

| Link | Subnet |
| --- | --- |
| client ↔ router-a | `10.0.1.0/30` |
| router-a ↔ server | `10.0.2.0/30` |
| client ↔ router-b | `10.0.3.0/30` |
| router-b ↔ server | `10.0.4.0/30` |

The client normally reaches the server through `router-a`. If the
primary path fails, BGP converges on the path through `router-b`.

## Requirements

- Docker
- Containerlab
- GNU Make
- Python 3

## Quick start

Deploy the lab and run all checks:

```bash
make demo
```

Run individual operations:

```bash
make deploy
make check
make test
make destroy
```

## Automated failure test

The test validates every primary and backup path combination:

| Primary | Backup | Expected result |
| --- | --- |
| Up | Up | Reachable through primary |
| Down | Up | Reachable through backup |
| Down | Down | Unreachable |
| Up | Down | Reachable through primary |

After testing all four combinations, the script restores both paths and
verifies the final healthy state.

The test checks both end-to-end connectivity and the actual next hop
installed in the Linux routing table after BGP convergence.

## Key concepts demonstrated

- eBGP neighbor establishment
- BGP route advertisement
- AS-path propagation
- Primary and backup path selection
- Stable `/32` loopback addresses
- Preferred source addresses
- Linux routing table integration through FRR Zebra
- Automated fault injection
- BGP convergence and recovery validation

## Repository structure

```text
.
├── configs/
│   ├── client.conf
│   ├── daemons
│   ├── router-a.conf
│   ├── router-b.conf
│   ├── server.conf
│   └── vtysh.conf
├── scripts/
│   ├── check_connectivity.py
│   └── test_link_failure.py
├── lab.clab.yml
├── Makefile
└── README.md
```

## Inspecting BGP

Show the BGP neighbor summary on the client:

```bash
docker exec clab-redundant-lab-client \
  vtysh -c "show ip bgp summary"
```

Show all BGP paths learned by the client:

```bash
docker exec clab-redundant-lab-client \
  vtysh -c "show ip bgp"
```

Inspect the selected route to the server loopback:

```bash
docker exec clab-redundant-lab-client \
  ip route show 192.168.0.2
```

Inspect detailed BGP information for the server loopback:

```bash
docker exec clab-redundant-lab-client \
  vtysh -c "show ip bgp 192.168.0.2/32"
```

## Manual failover demonstration

Check the current route:

```bash
docker exec clab-redundant-lab-client \
  ip route show 192.168.0.2
```

Disable the primary path:

```bash
docker exec clab-redundant-lab-router-a \
  ip link set eth2 down
```

Verify that connectivity remains available:

```bash
docker exec clab-redundant-lab-client \
  ping -c 3 192.168.0.2
```

Inspect the new route through the backup router:

```bash
docker exec clab-redundant-lab-client \
  ip route show 192.168.0.2
```

Restore the primary path:

```bash
docker exec clab-redundant-lab-router-a \
  ip link set eth2 up
```

For the complete automated scenario, run:

```bash
make test
```

## Cleanup

```bash
make destroy
```
