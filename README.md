# Distributed Computing Accounting (dca)

This README has been revised after dca was rewritten for Java and MySQL.

## Introduction

dca is an accounting service that allows distributed computing systems to keep track of job processing hours used by users and charges the respective tenant. Originally written in Python and using Elasticsearch as a database system, it has been rewritten in Java using a MySQL database to increase performance and security. It is meant to be used in conjunction with a backend transactions system and optionally a web-based interface for viewing transactions and bills. dca is a CLI and outputs as a RESTful API.

Unlike traditional payment services like Venmo, and similar to most distributed computing systems, dca uses a tenant-project-user hierarchy. Tenants make payments, create projects and assign users to each project, and tenants are billed for the computing time their users use. dca has the ability to track the usage of budget on a per-user basis, and create a bill for the administrator that overviews how much each user spent each day. On top of having a basic budget system, dca also has a credit system that allows an administrator to dispense credit to tenants who may have underused their budget one month and require more the next. dca also has a permissions system 

It is important to identify what dca is not. dca does not actually bill any financial accounts. dca is not a persistent background service, it is more like an interface between the user and a database.

## Setup

To use dca, Java 1.8.0 and MySQL-server need to be installed.

__On Windows__, the links are:
```
JRE 1.8.0: http://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html
MySQL: https://www.mysql.com/downloads/
```
Once both are installed, setup and launch the MySQL server.

__On CentOS 7__, the associated commands to download Java/MySQL and to run the server are:
```
sudo yum install java-1.8.0 mysql-server
service mysqld start
```

Verify that the MySQL server has been properly set up by running `mysql -u root -p` and logging in with a blank password.

If it claims that the password is incorrect or that it needs to be changed, this is because MySQL generates a random password upon installation that needs to be changed. On CentOS, open up `/var/log/mysqld.log` in your text editor and search for `temporary password`. Use that to log in again.

Try to create the `dca` database by running `CREATE DATABASE dca;`. If it tells you that your password needs to be changed, execute either `ALTER USER 'root'@'localhost' IDENTIFIED BY 'password';` or `SET PASSWORD FOR 'root'@'localhost' = PASSWORD('password');` to change your password. One of these statements should successfully change your password to `password`. Once completed, execute the database creation statement once more: `CREATE DATABASE dca;`.

Now that MySQL has been setup, it is time to set up dca. This process is relatively simple: in the folder that you have downloaded dca, run `./dca setup`. This must be run as root.

Congratulations! dca is now properly configured.

### Wiping MySQL

In the event of a corrupted database or the need for a reset, it is simple to wipe dca's data. Simply run `./dca wipe` and `./dca setup` to start again with a fresh database.

## Commands

All of the supported commands are listed below:

Setup/breakdown of dca's MySQL database:
```
dca setup
dca wipe
```
Role addition or deletion:
```
dca role add admin -u|--user=<name>
dca role delete admin -u|--user=<name>
dca role add tenantadmin -u|--user=<name>
dca role delete tenantadmin -u|--user=<name>
```
Tenant related commands – adding, disabling, adding credit, adding balance:
```
dca tenant add -t|--tenant=<name> [-c|--credit=<amount>]
dca tenant disable -t|--tenant=<name> [-y]
dca tenant modify -t|--tenant=<name> -c|--credit=<amount>
dca tenant payment -t|--tenant=<name> -p|--payment=<amount>
```
Project related commands – adding, disabling, and moving budget around between projects and the tenant:
```
dca project add -p|--project=<name> -t|--tenant=<name> [-b|--balance=<amount>] [-c|--credit=<amount>]
dca project disable -p|--project=<name> [-y]
dca project movebudget --from=<name> --to=<name> [-b|--balance=<amount>] [-c|--credit=<amount>] --type=p2p|t2p|p2t
```
User related commands – adding and deleting users:
```
dca user add -p|--project=<name> -u|--user=<name>
dca user delete -p|--project=<name> -u|--user=<name>
```
Listing information about a specified tenant, project, user, or any combination of the three: 
```
dca list [-t|--tenant=<name>] [-p|--project=<name>] [-u|--user=<name>]
```
Rate related commands – setting and getting the rate:
```
dca rate set -r|--rate=<rate>
dca rate get
```
Transaction related commands – reserving part of a project’s budget and charging the project:
```
dca transaction reservebudget -p|--project=<name> -e|--estimate=<time>
dca transaction charge -p|--project=<name> -e|--estimate=<time> -j|--jobtime=<time> -s|--start=<time>
```
Generating a bill:
```
dca bill generate -p|--project=<name> --time_period=last_day|last_week|last_month|<date>,<date>
```

There are restrictions and guidelines to what the argument values can be. All restrictions are listed below.

* By default, all of the outputs will be pretty printed (human readable format). In order to receive a mini output (flat, no indentation), use the optional argument `-m` or `--mini`. 
* Tenant, project, and usernames must be alphanumeric and less than (or exactly) 32 characters in length. Project names must be unique.
* Deleting tenants and projects does not actually delete them. It merely disables them (which requires a confirmation). This is so that bills can still be generated 
* Balance, credit, and payments amounts must be a non-negative numeric value.
* The type argument under project movebudget determines whether the from and to destinations are projects (p) or tenants (t).
* The `rate` is measured in dollars per hour.
* Transaction `estimate` and `jobtime` are measured in seconds, and must be an integer value.
* The start time must be in the format YYYY-MM-DD HH:mm:ss, or a Unix epoch value.
* `time_period` (if a default one is not chosen) must be two dates in the format YYYY-MM-DD.

### Permissions

There are 4 levels of permissions built into dca. Each user can have any combination of them (with the exception of root).

* Root: They are capable of executing any command. Only the root user may have this permission. 
* Admin: They are capable of running any command excluding those that manage the admin role or the MySQL database. The admin permission may be given using the command `dca role add admin -u|--user=<name>`.
* Tenantadmin: Tenantadmins may run any `project`, `user`, `list`, and `bill` command. The tenantadmin permission may be given using the command `dca role add tenantadmin -u|--user=<name>`. 
* User: Users are tied to projects, and can only execute `transaction` commands. They can be added to a project using the command `dca user add -p|--project=<name> -u|--user=<name>`.

## Database Schema

Below you can find the dca database schema that is generated after dca is set up.
```
tenant
- name VARCHAR(32)
- balance FLOAT
- credit FLOAT
- projects VARCHAR(4096)
- d BOOLEAN

project
- tenant VARCHAR(32)
- project VARCHAR(32)
- balance FLOAT
- credit FLOAT
- requested FLOAT
- rate FLOAT
- users VARCHAR(4096)
- d BOOLEAN

transaction
- project VARCHAR(32)
- user VARCHAR(32)
- start DATETIME
- end DATETIME
- runtime INT
- cost FLOAT

payment
- tenant VARCHAR(32)
- date DATETIME
- payment FLOAT

rate
- rate FLOAT

log
- category VARCHAR(32)
- action VARCHAR(32)
- details VARCHAR(4096)
- date DATETIME

role
- name VARCHAR(32)
- tenantadmin boolean
- admin boolean
```

## Future Plans

As is the case with a lot of software, dca has room for improvement. We hope to see a more flexible rate system that can accommodate CPU cores used, memory allocated, and other metrics in order to accurately charge tenants for their users' usage.
