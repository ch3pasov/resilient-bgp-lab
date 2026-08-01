# Resilient Radio Network Lab

A small Containerlab-based networking lab for learning IP routing, connectivity checks, and failure injection.

## Current topology

```text
client                         router                         server

10.0.1.2/30          10.0.1.1/30   10.0.2.1/30          10.0.2.2/30
    eth1 ───────────────── eth1         eth2 ───────────────── eth1
```

The client and server are located in different IPv4 subnets:

- client network: `10.0.1.0/30`
- server network: `10.0.2.0/30`

The Linux router forwards packets between the two networks.

## Requirements

- Docker
- Containerlab
- Python 3

The repository includes a development container configuration suitable for GitHub Codespaces.

## Deploy the lab

```bash
sudo containerlab deploy -t lab.clab.yml
```

Verify that all three containers are running:

```bash
docker ps
```

Expected containers:

```text
clab-routed-lab-client
clab-routed-lab-router
clab-routed-lab-server
```

## Check connectivity

Run the health check:

```bash
./scripts/check_connectivity.py
```

Expected output:

```text
OK: clab-routed-lab-client can reach 10.0.2.2
```

The script exits with:

- `0` when the server is reachable;
- `1` when the connectivity check fails.

## Test a link failure

Run the automated failure scenario:

```bash
./scripts/test_link_failure.py
```

The test:

1. verifies initial connectivity;
2. disables `eth2` on the router;
3. verifies that connectivity is lost;
4. restores the interface;
5. verifies that connectivity recovers.

Expected final output:

```text
PASS: link failure scenario completed successfully
```

## Inspect routing

Client routing table:

```bash
docker exec clab-routed-lab-client ip route
```

Route selected for the server:

```bash
docker exec clab-routed-lab-client ip route get 10.0.2.2
```

Expected route:

```text
10.0.2.2 via 10.0.1.1 dev eth1 src 10.0.1.2
```

## Inspect L2 neighbors

After sending traffic:

```bash
docker exec clab-routed-lab-client ip neigh show dev eth1
docker exec clab-routed-lab-router ip neigh show
docker exec clab-routed-lab-server ip neigh show dev eth1
```

The client learns only the MAC address of the router, not the remote server. The router maintains separate neighbor entries for both directly connected networks.

## Destroy the lab

```bash
sudo containerlab destroy -t lab.clab.yml --cleanup
```

## What this lab demonstrates

- IPv4 subnetting with `/30` networks
- directly connected and static routes
- next-hop routing
- Linux IP forwarding
- ARP and neighbor discovery
- L2 versus L3 forwarding
- TTL reduction across a router
- automated connectivity checks
- controlled link-failure injection

## Planned next steps

- redundant network paths
- FRRouting
- dynamic route exchange with BGP
- automatic failover
- recovery-time measurement
- audio-stream availability checks