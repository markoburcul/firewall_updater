# Firewall Updater

The purpose of this script is to retrieve data from a Consul instance running on the local machine regarding nodes from other fleets, create a set of firewall rules, and apply them.

For details on how the rules are created for each fleet, please refer to the `infra_task.md` document.

## Installation

To install the firewall updater, execute the installation script as the root user using the following command:
```bash
sudo install.sh
```

The script will be installed in the `/opt/scripts/` directory and will run every hour by default. You can adjust the frequency in the installation script if waiting one hour between firewall updates is too long.

Logs of the script can be found in the `/var/log/firewall_updater.log` file.

## Firewall explanation
For firewall rule management, this solution utilizes nftables. It is assumed that nftables is installed on the host where the firewall is to be updated and that no rules are set up initially. The firewall consists of two chains with different priorities, both hooked on the input hook. One chain is dynamically updated based on Consul data, while the other remains static and is populated with common security rules, including:

- allow communication between processes on the same machine
- accept incoming ICMP (ping)
- accept SSH
- accept connections on Consul ports(8300, 8301, 8302, 8600) from the VPN network
- reject everything else

Additionally, there is an accept rule that accepts all connections marked with a mask. This mask is added to processed packets in the first "dynamic" chain, and if they satisfy certain rules, they are automatically accepted when they arrive at the second chain.
