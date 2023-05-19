# DO-DDNS

_DO-DDNS_ is a dynamic DNS helper for Digital Ocean users to utilize their DO account as a Dynamic DNS resolver.

## Installation
Can be run bare metal or in docker. Docker is preferred, and will automatically run

### Docker
1. Build the docker container with `docker build . -t ddns`
2. If ipv6 is needed, enable ipv6 by following the IPv6 instructions below.  
3. Update the .env.sample file with api_key and other configuration options.  
4. Start the container `docker run --name ddns --rm --env-file=.env -d --restart=always ddns`

Alternatively use the docker image:  
`docker run --name ddns --rm --env-file=.env -d --restart=always hunterreadca/do-ddns`

### Bare Metal

1. Copy the ddns.py file to /usr/local/bin and make it executable.  
`chmod +x ddns.py` 
2. Run `pip3 install -r requirements.txt` to install all requirements.
3. Set the env variables with a script. (See below)
4. Setup a crontab. To run the app every 6 hours with cron add the following line to your crontab. Make sure you set the correct paths.    
`0 */6 * * *  /path/to/setenv && /usr/bin/python3 /path/to/ddns.py`


## Customization and Configuration
### Environment variables
| ENV Variable | Default | Description |
| --- | --- | --- |
| API_KEY | | **Required** Api Key to update DNS records |
| DOMAINS | | **Required** JSON String of domains and subdomains. See below. |
| IPV4_SERVER | https://ipv4.icanhazip.com | Override the IP server lookup to use for ipv4 |
| IPV6_SERVER | None | Override the IP server lookup to use for ipv6 |
| FREQUENCY | 3600 | Frequency to run ddns update in seconds. Set to **zeroe** if the interval will be managed by cron. |
| TTL | 3600 | Record TTL |

### Domain config
Json String:
```
DOMAINS=[
    {
        "domain": "domain1.tld", 
        "subdomains": [
            "sub1.domain1.tld",
            "sub2.domain1.tld"
        ]
    },
    {
        "domain": "domain2.tld",
        ...
    }
]
```
See .env.sample for an example

### IPv6 Support in Docker
Before you proceed, you will need a very recent docker installation, version 20.10.2 or later, recently merged with this pull-request. Otherwise, manually set-up SNAT using ip6tables, or try the other 2 approaches.

To enable ip6tables handling, the experimental flag must be enabled. Put the following in /etc/docker/daemon.json or adjust to fit:

```
{
	"ipv6": true,
	"fixed-cidr-v6": "fd00:ffff::/80",
	"ip6tables": true,
	"experimental": true
}
```
Then, restart the docker daemon:

`sudo service docker restart.`

### Set Env Variables on Bare Metal
1. Create a file `setenv`
2. In the file export each env variable.
```
export API_KEY=<your_api_key>
export DOMAINS=<your_domains>
```