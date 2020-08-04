# Qualys Scripts

## Help
```bash
$ python qualys_query.py 
usage: qualys_query.py [-h] [-t] [-u USERNAME] [-p] [-url URL] [-a ACTION]
                       [-d DATE]
                       {cagent,asset} ...

Qualys Query Tool

positional arguments:
  {cagent,asset}        Qualys modules
    cagent              Cloud Agent
    asset               Asset Management

optional arguments:
  -h, --help            show this help message and exit

Configuration:
  -t, --test_authentication
                        Test authentication buy get a count of all hosts
  -u USERNAME, --username USERNAME
                        Username for Qualys
  -p, --password        Test authentication buy get a count of all hosts
  -url URL, --url URL   Qualys API server domain

Commands:
  -a ACTION, --action ACTION
                        Action to perform on results Supported actions:
                        query,scan,remove,uninstall,deactivate

Filters:
  -d DATE, --date DATE  Set the date you want to start checking back from.
                        Format: 2018-08-25T00:00:01
                        Example: -d 2019-03-20T00:00:01


```

```bash
$ python qualys_query.py -h
usage: qualys_query.py [-h] [-t] [-u USERNAME] [-p] [-url URL] [-m MODULE]
                       [-c CALL] [-f [FILTERS [FILTERS ...]]]

Qualys Query Tool

optional arguments:
  -h, --help            show this help message and exit
  -m MODULE, --module MODULE
                        Supply the Qualys module you want to query
  -c CALL, --call CALL  Make API call and execute action
  -f [FILTERS [FILTERS ...]], --filters [FILTERS [FILTERS ...]]
                        Pass all filter arguments in using the format

Configuration:
  -t, --test_authentication
                        Test authentication buy get a count of all hosts
  -u USERNAME, --username USERNAME
                        Username for Qualys
  -p, --password        Test authentication buy get a count of all hosts
  -url URL, --url URL   Qualys API server domain


```

```bash
$ python qualys_query.py asset
usage: qualys_query.py asset [-h] [-tc] [-tl]

optional arguments:
  -h, --help       show this help message and exit
  -tc, --tagcount  Get tag count.
  -tl, --taglist   Get list of tags.

```

## Example Queries

* Querying assets
```bash
# Get total count of tags
$ python qualys_query.py asset -tc
Count is: 160

# Get tag list
$ python qualys_query.py asset -tl
Finished processing all pages
Creating Report...
Total tags: 160
Filename will be: tags_2019-04-01.csv
```

## Supported fitlers
```bash
tags.name, ec2.instanceState, action
```

* Querying agents
```bash
# Find all agents that have checked in before 2019-03-20 and with the "Cloud Agent" Tag
python qualys_query.py -a query -d 2019-03-20T00:00:01 cagent -al "Cloud Agent"
```

```bash
# Deactivate VM module for agents that have checked in before 2019-03-20 and with the "Cloud Agent" Tag
python qualys_query.py -a deactivate -d 2019-03-20T00:00:01 cagent -al "Cloud Agent"
```

# TODO
## Add following run to cron
* Count All agents using csp tags that last checkin was a day or more ago
```bash
python qualys_query.py -m ca -c count -f tags.name=csp_cspdev_jumpbox,csp_cspdev_bastion,csp_cspdev_kops,csp_staging_bastion,csp_staging_jumpbox,csp_staging_kops,csp_dev_bastion,csp_dev_jumpbox,csp_dev_kops updated="-2019-04-15T00:00:01"
```
* Deactivate VM module for each tag with active agents
```bash
python qualys_query.py -m ca -c deactivate -f tags.name=csp_cspdev_jumpbox,csp_cspdev_bastion,csp_cspdev_kops,csp_staging_bastion,csp_staging_jumpbox,csp_staging_kops,csp_dev_bastion,csp_dev_jumpbox,csp_dev_kops updated="-2019-04-15T00:00:01"
```
* Activate VM module for each tag with active agents
```bash
python qualys_query.py -m ca -c activate -f tags.name=csp_cspdev_jumpbox,csp_cspdev_bastion,csp_cspdev_kops,csp_staging_bastion,csp_staging_jumpbox,csp_staging_kops,csp_dev_bastion,csp_dev_jumpbox,csp_dev_kops updated="-2019-04-15T00:00:01"
```

* Search for all active agents
```bash
python qualys_query.py -m ca -c search -f tags.name=csp_cspdev_jumpbox,csp_cspdev_bastion,csp_cspdev_kops,csp_staging_bastion,csp_staging_jumpbox,csp_staging_kops,csp_dev_bastion,csp_dev_jumpbox,csp_dev_kops

```

## Search in Qualys
Locate all active agents that have checkedin in the last day 
```bash
(tags.name:csp_staging_bastion or tags.name:csp_staging_kops or tags.name:csp_dev_kops) and activatedForModules:"VM"
```


```bash
python qualys_query.py -d 2019-03-20T00:00:01 cagent -al csp_cspdev_jumpbox csp_cspdev_bastion csp_cspdev_kops csp_staging_bastion csp_staging_jumpbox csp_staging_kops csp_dev_bastion csp_dev_jumpbox csp_dev_kops
python qualys_query.py -m ca -c count -f updated="+2019-04-15T00:00:01"
python qualys_query.py -m ca -c count -f tags.name=csp_cspdev_jumpbox,csp_cspdev_bastion,csp_cspdev_kops,csp_staging_bastion,csp_staging_jumpbox,csp_staging_kops,csp_dev_bastion,csp_dev_jumpbox,csp_dev_kops updated="+2019-04-15T00:00:01"
# Deactivate
python qualys_query.py -m ca -c deactivate -f tags.name=csp_cspdev_jumpbox,csp_cspdev_bastion,csp_cspdev_kops,csp_staging_bastion,csp_staging_jumpbox,csp_staging_kops,csp_dev_bastion,csp_dev_jumpbox,csp_dev_kops updated="-2019-04-15T00:00:01"


```

## References
* https://www.qualys.com/docs/qualys-api-vmpc-user-guide.pdf
* https://www.qualys.com/docs/qualys-ca-api-user-guide.pdf
* https://www.qualys.com/docs/qualys-api-quick-reference.pdf
* https://www.qualys.com/docs/qualys-asset-management-tagging-api-user-guide.pdf
* https://community.qualys.com/community/developer
* https://github.com/Qualys/community
* https://community.qualys.com/thread/19443-api-purge-hosts-not-scanned-within-xx-days
* https://github.com/paragbaxi/qualysapi
* https://github.atl.pdrop.net/rsubramanian/scan-and-parse
* https://jira.atl.pdrop.net/browse/SEC-133