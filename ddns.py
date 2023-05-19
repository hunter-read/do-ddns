#!/usr/bin/python3
import json
import logging
import os
import requests
import schedule
import time

logger = logging.getLogger("ddns")
hdlr = logging.StreamHandler()
hdlr.setFormatter(
    logging.Formatter("%(levelname)s:%(asctime)s: %(message)s", "%Y-%m-%d %H:%M:%S")
)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)


def get_ip(server: str) -> str:
    if server is None:
        return None
    try:
        response: requests.Response = requests.get(server, timeout=30)
        if response.status_code == 200:
            return response.text.strip()
    except requests.exceptions.RequestException:
        pass
    logger.error("Unable to get IP from server: %s", server)
    return None


def get_ipv4() -> str:
    return get_ip(os.environ.get("IPV4_SERVER", "https://ipv4.icanhazip.com"))


def get_ipv6() -> str:
    return get_ip(os.environ.get("IPV6_SERVER", None))


def get_subdomain_data(domain: str, subdomains: list, headers: dict) -> dict:
    result: dict = {}
    for subdomain in subdomains:
        response: requests.Response = requests.get(
            f"https://api.digitalocean.com/v2/domains/{domain}/records?name={subdomain}",
            headers=headers,
        )
        if response.status_code == 200:
            json_data: dict = response.json().get("domain_records")
            a_record: str = None
            aaaa_record: str = None
            for record in json_data:
                if record.get("type") == "A":
                    a_record = record
                elif record.get("type") == "AAAA":
                    aaaa_record = record
            result[subdomain] = (a_record, aaaa_record)
        else:
            result[subdomain] = None
    return result


def update_record(
    domain: str, subdomain: str, old: dict, new: str, type: str, headers: dict
) -> bool:
    if new is None:
        return False

    data: dict = {
        "name": subdomain.removesuffix(f".{domain}"),
        "data": new,
        "type": type,
        "ttl": os.environ.get("TTL", 3600),
    }
    if old is None:
        #  Create the record
        response: requests.Response = requests.post(
            f"https://api.digitalocean.com/v2/domains/{domain}/records",
            data=json.dumps(data),
            headers=headers,
        )
        if response.status_code == 201:
            logger.info("Successfully created %s: %s to %s", type, subdomain, new)
            return True
        else:
            logger.error("Unable to create %s: %s to %s - %s", type, subdomain, new)

    elif old.get("data") != new:
        # Update the record
        response: requests.Response = requests.patch(
            f'https://api.digitalocean.com/v2/domains/{domain}/records/{old.get("id")}',
            data=json.dumps(data),
            headers=headers,
        )
        if response.status_code == 200:
            logger.info("Successfully updated %s: %s to %s", type, subdomain, new)
            return True
        else:
            logger.error("Unable to update %s: %s to %s", type, subdomain, new)
    return False


def update_records() -> None:
    ipv4: str = get_ipv4()
    ipv6: str = get_ipv6()
    if not (ipv4 or ipv6):
        logger.error("Unable to get IP from any server")
        return

    api_key: str = os.environ.get("API_KEY")
    if not api_key:
        logger.critical("API_KEY environment variable not set")
        return
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    domains: list = json.loads(os.environ.get("DOMAINS"))
    updated = False
    
    for domain_json in domains:
        domain: str = domain_json.get("domain")
        subdomains: list = domain_json.get("subdomains")
        current_dns: dict = get_subdomain_data(domain, subdomains, headers)
        for subdomain in subdomains:
            if current_dns.get(subdomain) is None:
                logger.info("Subdomain %s not found in current DNS data", subdomain)
                continue
            old_ipv4, old_ipv6 = current_dns.get(subdomain)
            updated |= update_record(domain, subdomain, old_ipv4, ipv4, "A", headers)
            updated |= update_record(domain, subdomain, old_ipv6, ipv6, "AAAA", headers)
    if not updated:
        logger.info("No records were updated")

if __name__ == "__main__":
    logger.info("Starting ddns")
    update_records()
    frequency: int = int(os.environ.get("FREQUENCY", 3600))
    schedule.every(frequency).seconds.do(update_records)

    while frequency > 0:
        schedule.run_pending()
        time.sleep(frequency)
