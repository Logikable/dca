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

