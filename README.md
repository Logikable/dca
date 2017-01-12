# Introduction

dca is an accounting RESTful API that keeps track of job processing hours used by users and charges the respective tenant using Elasticsearch, a NoSQL document-based database. It is meant to be used in conjunction with a backend transactions system and optionally a web-based interface for viewing transactions and bills. dca can be interacted with through commands and outputs a json string containing the results.
   
Its data follows the hierarchy of having individual tenants that oversee a number of projects, each of which has a list of users that work on said project. Each tenant has their own budget which can then be distributed amongst their projects to be used by the users. dca has the ability to track the usage of budget on a per-user basis, and create a bill for the administrator that overviews how much each user spent each day. On top of having a basic budget system, dca also has a credit system that allows an administrator to dispense credit to tenants who may have underused their budget one month and require more the next. dca is quite flexible and is simple to set up.

## Setup

To use dca, Elasticsearch 5 (and consequently Java 1.7.0+) should have already been installed and properly configured. From here, Python 3+, Elasticsearch-py, and Elasticsearch XPack of the same version as ES should also be installed. Assuming an internet connection is available, the associated commands are:
```
yum install python-pip
pip install elasticsearch==5
%ESHOME%/bin/elasticsearch-plugin install x-pack –batch
```
Replace `%ESHOME%` with the installation path of elasticsearch. By default, the path is `/usr/share/elasticsearch`.

The default password of the ES superuser (name: elastic) is changeme. To change this password, run the command

```
curl -XPUT -u elastic 'localhost:9200/_xpack/security/user/elastic/_password' -d '{
  "password" : "newpassword"
}'
```

Next, create a directory and download the dca files from https://github.com/Logikable/dca. From this directory, run `./dca_setup` in order to configure dca. Most likely, when the setup process is first run, you will be prompted to create the directory `~/.dca`. After creating the directory, run the setup file once more. This time, a config file will be created and you will be prompted to fill out the relevant information. The location of the config file is `~/.dca/config`. As of now, the necessary information are a set of ES credentials (username and password) and a comma-separated list of ES hosts. By default, it is recommended to use the ES superuser.

Once this information has been entered into the config file, **`./dca_setup` should be run one last time** to create the necessary ES indices and mappings. It should not be run again unless the entire dca ES database is meant to be reset.

dca is now properly set up!

## Commands:
```
dca tenant add --tenant=<name> [--credit=<amount>]
dca tenant disable --tenant=<name> [-y]
dca tenant modify --tenant=<name> --credit=<amount>
dca tenant payment --tenant=<name> --payment=<amount>

dca project add --project=<name> --tenant=<name> [--balance=<amount>] [--credit=<amount>]
dca project disable --project=<name> [-y]
dca project movebudget --from=<name> --to=<name> [--balance=<amount>] [--credit=<amount>] --type=p2p|t2p|p2t

dca user add --project=<name> --user=<name>
dca user delete --project=<name> --user=<name>

dca list [--tenant=<name>] [--project=<name>] [--user=<name>]

dca rate set --rate=<rate>
dca rate get

dca transaction reservebudget --project=<name> --estimate=<time>
dca transaction charge --project=<name> --user=<name> --estimate=<time> --jobtime=<time> --start=<time>

dca bill generate --project=<name> --time_period=last_day|last_week|last_month|<date>,<date>
```
