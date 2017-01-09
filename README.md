# Usage:
Install Python 3 (any version above is fine), ElasticSearch 5, and Elasticsearch-py (using pip). Java 1.7 and ES5 are presumably already installed and functional.

Run dca_setup first to construct the indexing structure. This will also set the rate in which tenants are charged (defaults to $3000/hr). dca is then ready to be used.

# Commands:
- dca tenant add --tenant=<name> [--credit=<amount>]
- dca tenant disable --tenant=<name> [-y]
- dca tenant modify --tenant=<name> --credit=<amount>
- dca tenant payment --tenant=<name> --payment=<amount>

- dca project add --project=<name> --tenant=<name> [--balance=<amount>] [--credit=<amount>]
- dca project disable --project=<name> [-y]
- dca project movebudget --from=<name> --to=<name> [--balance=<amount>] [--credit=<amount>] --type=p2p|t2p|p2t

- dca user add --project=<name> --user=<name>
- dca user delete --project=<name> --user=<name>

- dca list [--tenant=<name>] [--project=<name>] [--user=<name>]

- dca rate set --rate=<rate>
- dca rate get

- dca transaction reservebudget --project=<name> --estimate=<time>
- dca transaction charge --project=<name> --user=<name> --estimate=<time> --jobtime=<time> --start=<time>

- dca bill generate --project=<name> --time_period=last_day|last_week|last_month|<date>,<date>
