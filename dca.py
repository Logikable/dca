#!/usr/bin/python3.4
from elasticsearch import Elasticsearch
es = Elasticsearch()

from datetime import datetime

# Argparse

import argparse
import sys

def getargs():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()


    tenant_parser = subparsers.add_parser('tenant')
    tenant_subparsers = tenant_parser.add_subparsers()

    add_tenant_parser = tenant_subparsers.add_parser('add')
    add_tenant_parser.add_argument('--tenant', required=True)
    add_tenant_parser.add_argument('--rate', default='default')
    add_tenant_parser.add_argument('--credit', type=float, default=0)

    delete_tenant_parser = tenant_subparsers.add_parser('delete')
    delete_tenant_parser.add_argument('--tenant', required=True)

    modify_tenant_parser = tenant_subparsers.add_parser('modify')
    modify_tenant_parser.add_argument('--tenant', required=True)
    modify_tenant_parser.add_argument('--rate')
    modify_tenant_parser.add_argument('--credit', type=float)

    payment_tenant_parser = tenant_subparsers.add_parser('payment')
    payment_tenant_parser.add_argument('--tenant', required=True)
    payment_tenant_parser.add_argument('--payment', type=float, required=True)
    payment_tenant_parser.add_argument('--expiry', default='never')

    list_tenant_parser = tenant_subparsers.add_parser('list')
    list_tenant_parser.add_argument('--tenant')


    project_parser = subparsers.add_parser('project')
    project_subparsers = project_parser.add_subparsers()

    add_project_parser = project_subparsers.add_parser('add')
    add_project_parser.add_argument('--tenant', required=True)
    add_project_parser.add_argument('--project', required=True)
    add_project_parser.add_argument('--budget_percent', type=float, required=True)

    delete_project_parser = project_subparsers.add_parser('delete')
    delete_project_parser.add_argument('--tenant')
    delete_project_parser.add_argument('--project', required=True)

    modify_project_parser = project_subparsers.add_parser('modify')
    modify_project_parser.add_argument('--tenant')
    modify_project_parser.add_argument('--project', required=True)
    modify_project_parser.add_argument('--budget_percent', type=float, required=True)

    list_project_parser = project_subparsers.add_parser('list')
    list_project_parser.add_argument('--tenant')
    list_project_parser.add_argument('--project')


    user_parser = subparsers.add_parser('user')
    user_subparsers = user_parser.add_subparsers()

    add_user_parser = user_subparsers.add_parser('add')
    add_user_parser.add_argument('--tenant', required=True)
    add_user_parser.add_argument('--project', required=True)
    add_user_parser.add_argument('--user', required=True)

    delete_user_parser = user_subparsers.add_parser('delete')
    delete_user_parser.add_argument('--tenant', required=True)
    delete_user_parser.add_argument('--project', required=True)
    delete_user_parser.add_argument('--user', required=True)


    rate_parser = subparsers.add_parser('rate')
    rate_subparsers = rate_parser.add_subparsers()

    add_rate_parser = rate_subparsers.add_parser('add')
    add_rate_parser.add_argument('--rate', required=True)
    add_rate_parser.add_argument('--default', action='store_true')
    add_rate_parser.add_argument('--rates', default='all', required=True)

    delete_rate_parser = rate_subparsers.add_parser('delete')
    delete_rate_parser.add_argument('--rate', required=True)

    list_rate_parser = rate_subparsers.add_parser('list')
    list_rate_parser.add_argument('--rate')


    transaction_parser = subparsers.add_parser('transaction')
    transaction_subparsers = transaction_parser.add_subparsers()

    reservebudget_transaction_parser = transaction_subparsers.add_parser('reservebudget')
    reservebudget_transaction_parser.add_argument('--project', required=True)
    reservebudget_transaction_parser.add_argument('--user', required=True)
    reservebudget_transaction_parser.add_argument('--jobtime', required=True)
    reservebudget_transaction_parser.add_argument('--mem', required=True)

    charge_transaction_parser = transaction_subparsers.add_parser('charge')
    charge_transaction_parser.add_argument('--project', required=True)
    charge_transaction_parser.add_argument('--user', required=True)
    charge_transaction_parser.add_argument('--jobtime', required=True)
    charge_transaction_parser.add_argument('--mem', required=True)


    bill_parser = subparsers.add_parser('bill')
    bill_subparsers = bill_parser.add_subparsers()

    generate_bill_parser = bill_subparsers.add_parser('generate')
    generate_bill_parser.add_argument('--project', required=True)
    generate_bill_parser.add_argument('--time_period', required=True)

    showreserve_bill_parser = bill_subparsers.add_parser('showreserve')
    showreserve_bill_parser.add_argument('--project')	

    # if run with no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    return args
    
# Helpers

# Pretty print json
def pretty(jjson):
    import json
    print(json.dumps(jjson, sort_keys=False, indent=4, separators=(',', ': ')))

def isint(s):
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False

def isfloat(s):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False

datefmt = '%Y-%m-%d %H:%M:%S'
datenever = datetime(3333, 1, 1)
def isdate(date):
    if isinstance(date, datetime):
        return True
    if isint(date):
        return int(date) >= 0
    try:
        datetime.strptime(date, datefmt)
        return True
    except ValueError:
        return False

# please check that date is a date before using this function
# returns in datefmt
def todate(date):
    if isinstance(date, datetime):
        return date
    if date == "never":
        return datenever
    if isint(date):
        return datetime.fromtimestamp(int(date))
    return datetime.strptime(date, datefmt)

def tostrdate(date):
    return date.strftime(datefmt)

def now():
    return datetime.now().replace(microsecond=0)

def ismoney(val):
    if not (isint(val) or isfloat(val)):
        return False
    return val >= 0

def ispercent(val):
    if not (isint(val) or isfloat(val)):
        return False
    return val >= 0 and val <= 100

# Query functions

def num_hits(result):
    if 'count' in result:
        return result['count']
    return result['hits']['total']

def get_data(result, field=''):
    if field: # if field contains something
        return get_data(result)[field]
    return result['hits']['hits'][0]['_source']

def es_query(func, doc_type, body):
    print(body)
    return func(index="dca", doc_type=doc_type, body=body)

def es_index(doc_type, body):
    return es_query(es.index, doc_type, '{' + body + '}')

def es_count(doc_type, body):
    return es_query(es.count, doc_type, '{"query": {"match": {' + body + '}}}')

def es_search(doc_type, body):
    return es_query(es.search, doc_type, '{"query": {"match": {' + body + '}}}')

def es_delete(doc_type, body):
    return es_query(es.delete_by_query, doc_type, '{"query": {"match": {' + body + '}}}')

# script should already contain data about which values should be changed to what params
# fields (& values) is either a list or an individual value
# values whose fields are lists should themselves be lists (e.g. users: ['u3'] instead of just 'u3')
def es_update(doc_type, body, script, fields, values):
    params = ''
    if not isinstance(fields, (list, tuple)):
        fields, values = [fields], [values]
    for i in range(len(fields)):
        if i != 0:
            params += ', '
        field, value = fields[i], values[i]
        params += '"' + field + '": '
        if isinstance(value, (list, tuple)):
            result = es_search(doc_type, body)
            data = get_data(result, field)
            data.extend(value)
            params += str(data).replace("'", '"')
        elif isint(value) or isfloat(value):
            params += '' + str(value) + ''
        else:
            params += '"' + value + '"'
    return es_query(es.update_by_query, doc_type, '{"query": {"match": {' + body + '}}, "script": {"inline": "'
            + script + '", "params": {' + params + '}}}')

# List of errors

def invalid_tenant_name(args):
    # checks if new tenant name is valid
    if not (len(args.tenant) <= 32 and args.tenant.isalnum()):
        return status_msg(False, 'invalid tenant name')
    return 0

def invalid_project_name(args):
    # checks if new project name is valid
    if not (len(args.project) <= 32 and args.tenant.isalnum()):
        return status_msg(False, 'invalid project name')
    return 0

def existing_tenant(args):
    # checks if tenant exists already
    existing_tenants = es_count('tenant', '"name": "' + args.tenant + '"')
    if num_hits(existing_tenants) != 0:
        return status_msg(False, 'tenant already exists')   
    return 0

def invalid_tenant(args):
    # checks if tenant doesn't exist
    existing_tenants = es_count('tenant', '"name": "' + args.tenant + '"')
    if num_hits(existing_tenants) == 0:
        return status_msg(False, 'tenant not found')
    return 0

def invalid_credit(args):
    # checks if credit is an invalid value
    if not ismoney(args.credit):
        return status_msg(False, 'invalid credit amount')
    return 0

def invalid_payment(args):
    # checks if payment is an invalid value
    if not ismoney(args.payment):
        return status_msg(False, 'invalid payment')
    return 0

def invalid_date(date):
    # checks if date is valid
    if date == 'never':
        return 0
    if not isdate(date):
        return status_msg(False, 'invalid date')
    return 0

def invalid_expiry(args):
    # checks if date if before today
    if args.expiry == 'never':
        return 0
    date = todate(args.expiry)
    if date <= now():
        return status_msg(False, 'expiry cannot be before today')
    return 0

def invalid_percent(args):
    if not ispercent(args.budget_percent):
        return status_msg(False, 'invalid percentage')
    percent = float(args.budget_percent)
    if percent == 0:
        return status_msg(False, 'percent cannot be 0')
    percent_used = get_data(es_search('tenant', '"name": "' + args.tenant + '"'), 'percent_used')
    if percent + percent_used > 100:
        return status_msg(False, 'invalid percentage: total above 100')
    return 0

def invalid_rate(args):
    # checks if default rate exists
    if args.rate.lower() == "default":
        default_rate = es_count('rate', '"default": true')
        if num_hits(default_rate) == 0:
            return status_msg(False, 'default rate not found')
    # checks if specified rate exists
    else:
        existing_rates = es_count('rate', '"name": "' + args.rate + '"')
        if num_hits(existing_rates) == 0:
            return status_msg(False, 'rate not found')
    return 0

# an argumentless function call indicates no error
def status_msg(success=True, error='no error'):
    print('{"status": ' + ('success' if success else 'failed') + ', "error": "' + error + '"}')
    return int(not success) # True returns 0, False returns 1

# Main

def main():
    args = getargs()
    
    # it is guaranteed that there are at least two arguments by here
    action, subaction = sys.argv[1], sys.argv[2]   # sys.argv[0] is this file's name

    if action == 'tenant':
        if subaction == 'add':
            if invalid_tenant_name(args) or existing_tenant(args) or invalid_credit(args) or invalid_rate(args):
                return 1
            es_index('tenant', '"name": "' + args.tenant + '", "rate_name": "' + args.rate + '", "credit": "'
                    + str(args.credit) + '", "balance": 0, "percent_used": 0, "expiry": "' + tostrdate(datenever)
                    + '", "projects": [], "payments": []')
            return status_msg()

        elif subaction == 'delete':
            if invalid_tenant(args):
                return 1
            es_delete('tenant', '"name": "' + args.tenant + '"')
            es_delete('project', '"tenant": "' + args.tenant + '"')
            es_delete('user', '"tenant": "' + args.tenant + '"')
            es_delete('payment', '"tenant": "' + args.tenant + '"')
            return status_msg()

        elif subaction == 'modify':
            if invalid_tenant(args):
                return 1
            credit, rate = args.credit, args.rate # None acts as a false value
            # if a credit or rate has been specified, then check for errors
            if (credit and invalid_credit(args)) or (rate and invalid_rate(args)):
                return 1
            if credit or rate:
                params, values = [], []
                if credit:
                    params.append('credit')
                    values.append(args.credit)
                if rate:
                    params.append('rate_name')
                    values.append(args.rate)
                es_update('tenant', '"name": "' + args.tenant + '"',
                        ('ctx._source.credit=params.credit' if credit else '') + (';' if credit and rate else '')
                        + ('ctx._source.rate_name=params.rate_name' if rate else ''), params, values)
            return status_msg()

        elif subaction == 'payment':
            if invalid_tenant(args) or invalid_payment(args) or invalid_date(args.expiry) or invalid_expiry(args):
                return 1
            date, curtime = todate(args.expiry), str(now())
            es_update('tenant', '"name": "' + args.tenant + '"', 'ctx._source.balance+=params.payment;'
                    + 'ctx._source.expiry=params.expiry;ctx._source.payments=params.payments',
                    ['payment', 'expiry', 'payments'], [str(args.payment), tostrdate(date), [curtime]])
            es_index('payment', '"tenant": "' + args.tenant + '", "date": "' + curtime + '", "payment": "'
                    + str(args.payment) + '"')
            return status_msg()

    elif action == 'project':
        if subaction == 'add':
            if invalid_tenant(args) or invalid_project_name(args) or invalid_percent(args):
                return 1
            es_update('tenant', '{"name": "' + args.tenant + '"}', '"ctx._source.percent_used+='
                    + str(args.budget_percent) + '"' + 'ctx._source.projects+={}')
            return status_msg()

        elif subaction == 'delete':
            return status_msg()
        
        elif subaction == 'modify':
            return status_msg()

if __name__ == '__main__':
    main()
