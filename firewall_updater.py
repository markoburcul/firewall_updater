import subprocess
import requests
import socket
import logging

# Configure logging

CONSUL_URL = "http://localhost:8500/"

def retrieve_filtered_nodes_data(catalog_filter=""):
    logging.info("Retrieving filtered nodes data from Consul")
    params = {} if catalog_filter == "" else {"filter": catalog_filter}
    try:
        response = requests.get(f"{CONSUL_URL}v1/catalog/service/wireguard", params=params)
        # Raise exception for bad status code
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error("Error retrieving filtered nodes data from Consul: %s", e)
        return None

def configure_iptables(ip_rules):
    logging.info("Configuring iptables")
    chain_name = "consul"

    try:
        # Flush the existing rules in the chain
        subprocess.run(["nft", "flush", "chain", "inet", "filter", chain_name], check=True)
    except subprocess.CalledProcessError as e:
        logging.error("Error flushing chain: %s", e)
        return

    # Iterate through the ip_rules dictionary and add rules
    for port, ips in ip_rules.items():
        for ip in ips:
            try:
                logging.info("Adding rule for IP %s and port %d", ip, port)
                subprocess.run(["nft", "add", "rule", "inet", "filter", chain_name, "ip", "saddr", ip, "tcp", "dport", str(port), "meta", "mark", "set", "0x1", "accept"], check=True)
                subprocess.run(["nft", "add", "rule", "inet", "filter", chain_name, "ip", "saddr", ip, "udp", "dport", str(port), "meta", "mark", "set", "0x1", "accept"], check=True)
            except subprocess.CalledProcessError as e:
                logging.error("Error adding rule: %s", e)
                return

def fetch_host_config():
    logging.info("Retrieving host config from Consul...")
    try:
        response = requests.get(f"{CONSUL_URL}v1/agent/self")
        # Raise exception for bad status code
        response.raise_for_status()
        host_config = response.json()["Config"]
        return host_config
    except requests.RequestException as e:
        logging.error("Error retrieving host config from Consul: %s", e)
        return None

def main():
    # Configure decent logging output
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Script execution started.")
    
    # Rules contain pairs port=[ip addresses]
    ip_rules = {}
    
    # Fetch host config through Consul
    host_config = fetch_host_config()
    if host_config is None:
        logging.error("Failed to retrieve host config from Consul. Gracefully shutting down.")
        exit()
    
    host_id = host_config["NodeID"]

    # Retrieve data for the host
    host_data = retrieve_filtered_nodes_data(f"ID=={host_id}")
    
    # Retrieve data for all nodes except host
    other_nodes_data = retrieve_filtered_nodes_data(f"ID!={host_id}")

    # Extract metrics nodes ips since we need to give them access to port 9100
    metrics_nodes_ips = [ x["ServiceAddress"] for x in other_nodes_data if x["NodeMeta"]["env"] == "metrics"]
    ip_rules[9100] = metrics_nodes_ips
    
    # Open port 5141 on 'logs' nodes for all other nodes
    if host_data["NodeMeta"]["env"] == "logs":
        all_nodes_ips = [ x["ServiceAddress"] for x in other_nodes_data ]
        ip_rules[5141] = all_nodes_ips
    
    # Open port 9104 on 'app' nodes for 'metrics' nodes
    # Open port 3306 on 'app' nodes for 'backups' nodes
    elif host_data["NodeMeta"]["env"] == "app":
        backups_nodes_ips = [ x["ServiceAddress"] for x in other_nodes_data if x["NodeMeta"]["env"] == "backups"]
        ip_rules[9104] = metrics_nodes_ips
        ip_rules[3306] = backups_nodes_ips

    # Apply firewall rules
    configure_iptables(ip_rules)

if __name__ == "__main__":
    main()
