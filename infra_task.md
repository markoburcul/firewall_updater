# Description

This is a recruitment task for DevOps position which tests:

* Understanding of Linux firewalls
* Ability to research and design new solutions
* Automation using a scripting/programming language
* Knowledge of Consul catalog filtering

# Scenario

Infrastructure which consists of a set of fleets:
```
metrics.prod
metrics.test
logs.prod
logs.test
backups.prod
backups.test
app.prod
app.test
```
These fleets are all running Linux, are scaled up and down, and include one or more hosts. All hosts are part of an internal VPN([WireGuard](https://www.wireguard.com/)) using `10.10.0.0/16` network.

Assume that [Consul](https://www.consul.io/) is in place available on all hosts at `localhost:8500` with all metadata about hosts:
```sh
curl -sSf --get 'localhost:8500/v1/catalog/service/wireguard' \
   --data-urlencode filter="NodeMeta.env==metrics and NodeMeta.stage==prod" \
   | jq '.[] | { Node, NodeMeta, ServiceMeta }'
```
```json
[
  {
    "ID": "b27a1a90-dff4-4ff8-9fe8-cc3b573a85b7",
    "Node": "node-01.eu-dc1.metrics.prod",
    "Datacenter": "eu-dc1",
    "NodeMeta": { "env": "metrics", "stage": "prod" },
    "ServiceID": "wireguard",
    "ServiceName": "wireguard",
    "ServiceAddress": "10.10.0.17",
    "ServicePort": 51820
  },
  {
    "ID": "03deab88-ddd4-46ca-a38a-e75a4635c3a3",
    "Node": "node-02.eu-dc1.metrics.prod",
    "Datacenter": "eu-dc1",
    "NodeMeta": { "env": "metrics", "stage": "prod" },
    "ServiceName": "wireguard",
    "ServiceAddress": "10.10.0.18",
    "ServicePort": 51820
  },
]
```
The Catalog also includes information about data centers(`/v1/catalog/datacenters`).

# Task

The fleets require a firewall which allows different fleets access to different ports on the hosts:

* `5141` - [Logstash](https://www.elastic.co/logstash/) `rsyslog` port on `logs.*`, required access from __ALL__ hosts.
* `9100` - [Node exporter](https://github.com/prometheus/node_exporter) on __ALL__ hosts, required access by `metrics.*`.
* `9104` - [MySQL exporter](https://github.com/prometheus/mysqld_exporter) on `app.*` hosts, required access by `metrics.*`.
* `3306` - [MySQL](https://www.mysql.com/) database on `app.*`, requires access by `backups.*`.

Design and implement an automated way of updating firewall rules based on Consul catalog data. Note that `*` is a wildcard, not a regex.

You are free to use any firewall implementation(ex.: `iptables`,`nftables`,`firewalld`), tool to interact with the firewall, and scripting or programming language you are familiar with. The goal is to asses your problem solving, not knowledge of a specific technology. It is recommended to submit the task result as a Git repository. The resulting script would be run periodically on each host to keep the firewall rules up-to-date.

Example Consul catalog data is available [here](https://gist.github.com/jakubgs/dbf1df154f2d94541dc01baf1116d69f).

A partial solution is fine too, as long as you document what you think is missing or needs improvement.
