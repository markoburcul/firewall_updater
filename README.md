# Firewall updater
The aim of this script is to fetch data from Consul instance running on local machine about other nodes from other fleets,
create a set of firewall rules and apply them.

The explanation how the rules are created for the fleet can be seen in the `infra_task.md` document.

## Install
To install the firewall updater it is necessary to run install script it as `root` user.
`sudo install.sh`

The script will be installed in the `/opt/scripts/` folder and it will be run every hour. The frequency can be adjusted in the install script if one hour is too long interval to wait for the firewall update.

Logs of the script can be found in the `/var/log/firewall_updater.log` file.

## Firewall explanation
For the firewall rule management, the solution is using `nftables`. The assumption is that they are installed on the host where we want to update firewall and that there are no rules set up front.
The firewall itself is composed out of two chains with different priority that are hooked on the input hook. The reasoning behind this is that one chain will be dynamically updated as we read Consul data and the other one won't change and thus it will be populated with common security rules such as:
- allow communication between processes on the same machine
- accept incoming ICMP (ping)
- accept SSH
- accept connections on Consul ports(8300, 8301, 8302, 8600) from the VPN network
- reject everything else
Additionally to this there is an accept rule that accepts all connections marked with a mask. This mask is actually added to the processed packets in the first 'dynamic' chain ,if they satisfy some of the rules in it, so when it arrives to the second chain it gets automatically accepted.
