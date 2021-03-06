#!/usr/bin/python3.4
from datetime import datetime
from datetime import timedelta

# Argparse

import argparse
import sys
import dca_cfg
config = dca_cfg.cfg()

from elasticsearch import Elasticsearch
# from elasticsearch_xpack import XPackClient
es = Elasticsearch(hosts=config.eshosts, http_auth=(config.username, config.password))
# XPackClient.infect_client(es) # necessary if using any xpack functions

def getargs():
    parser = argparse.ArgumentParser()
    mini_parser = argparse.ArgumentParser(add_help=False)
    mini_parser.add_argument('--mini', '-m', action='store_true')
    subparsers = parser.add_subparsers()

    tenant_parser = subparsers.add_parser('tenant')
    tenant_parser.set_defaults(action='tenant')
    tenant_subparsers = tenant_parser.add_subparsers()
    add_tenant_parser = tenant_subparsers.add_parser('add', parents=[mini_parser])
    add_tenant_parser.set_defaults(subaction='add')
    add_tenant_parser.add_argument('--tenant', required=True)
    add_tenant_parser.add_argument('--credit', type=float, default=0.0)
    disable_tenant_parser = tenant_subparsers.add_parser('disable', parents=[mini_parser])
    disable_tenant_parser.set_defaults(subaction='disable')
    disable_tenant_parser.add_argument('--tenant', required=True)
    disable_tenant_parser.add_argument('-y', action='store_true')
    modify_tenant_parser = tenant_subparsers.add_parser('modify', parents=[mini_parser])
    modify_tenant_parser.set_defaults(subaction='modify')
    modify_tenant_parser.add_argument('--tenant', required=True)
    modify_tenant_parser.add_argument('--credit', type=float, required=True)
    payment_tenant_parser = tenant_subparsers.add_parser('payment', parents=[mini_parser])
    payment_tenant_parser.set_defaults(subaction='payment')
    payment_tenant_parser.add_argument('--tenant', required=True)
    payment_tenant_parser.add_argument('--payment', type=float, required=True)

    project_parser = subparsers.add_parser('project')
    project_parser.set_defaults(action='project')
    project_subparsers = project_parser.add_subparsers()
    add_project_parser = project_subparsers.add_parser('add', parents=[mini_parser])
    add_project_parser.set_defaults(subaction='add')
    add_project_parser.add_argument('--tenant', required=True)
    add_project_parser.add_argument('--project', required=True)
    add_project_parser.add_argument('--balance', type=float, default=0.0)
    add_project_parser.add_argument('--credit', type=float, default=0.0)
    disable_project_parser = project_subparsers.add_parser('disable', parents=[mini_parser])
    disable_project_parser.set_defaults(subaction='disable')
    disable_project_parser.add_argument('--project', required=True)
    disable_project_parser.add_argument('-y', action='store_true')
    movebudget_project_parser = project_subparsers.add_parser('movebudget', parents=[mini_parser])
    movebudget_project_parser.set_defaults(subaction='movebudget')
    movebudget_project_parser.add_argument('--from', dest='_from', required=True) # from is a keyword
    movebudget_project_parser.add_argument('--to', required=True)
    movebudget_project_parser.add_argument('--balance', type=float, default=0.0)
    movebudget_project_parser.add_argument('--credit', type=float, default=0.0)
    movebudget_project_parser.add_argument('--type', required=True, choices=['p2p', 't2p', 'p2t'])

    user_parser = subparsers.add_parser('user', parents=[mini_parser])
    user_parser.set_defaults(action='user')
    user_subparsers = user_parser.add_subparsers()
    add_user_parser = user_subparsers.add_parser('add', parents=[mini_parser])
    add_user_parser.set_defaults(subaction='add')
    add_user_parser.add_argument('--project', required=True)
    add_user_parser.add_argument('--user', required=True)
    delete_user_parser = user_subparsers.add_parser('delete', parents=[mini_parser])
    delete_user_parser.set_defaults(subaction='delete')
    delete_user_parser.add_argument('--project', required=True)
    delete_user_parser.add_argument('--user', required=True)

    list_parser = subparsers.add_parser('list', parents=[mini_parser])
    list_parser.set_defaults(action='list')
    list_parser.add_argument('--tenant')
    list_parser.add_argument('--project')
    list_parser.add_argument('--user')

    rate_parser = subparsers.add_parser('rate')
    rate_parser.set_defaults(action='rate')
    rate_subparsers = rate_parser.add_subparsers()
    set_rate_parser = rate_subparsers.add_parser('set', parents=[mini_parser])
    set_rate_parser.set_defaults(subaction='set')
    set_rate_parser.add_argument('--rate', type=float, required=True)
    get_rate_parser = rate_subparsers.add_parser('get', parents=[mini_parser])
    get_rate_parser.set_defaults(subaction='get')

    transaction_parser = subparsers.add_parser('transaction')
    transaction_parser.set_defaults(action='transaction')
    transaction_subparsers = transaction_parser.add_subparsers()
    reservebudget_transaction_parser = transaction_subparsers.add_parser('reservebudget', parents=[mini_parser])
    reservebudget_transaction_parser.set_defaults(subaction='reservebudget')
    reservebudget_transaction_parser.add_argument('--project', required=True)
    reservebudget_transaction_parser.add_argument('--estimate', type=int, required=True)
    charge_transaction_parser = transaction_subparsers.add_parser('charge', parents=[mini_parser])
    charge_transaction_parser.set_defaults(subaction='charge')
    charge_transaction_parser.add_argument('--project', required=True)
    charge_transaction_parser.add_argument('--user', required=True)
    charge_transaction_parser.add_argument('--estimate', type=int, required=True)
    charge_transaction_parser.add_argument('--jobtime', type=int, required=True)
    charge_transaction_parser.add_argument('--start', required=True)
   
    bill_parser = subparsers.add_parser('bill')
    bill_parser.set_defaults(action='bill')
    bill_subparsers = bill_parser.add_subparsers()
    generate_bill_parser = bill_subparsers.add_parser('generate', parents=[mini_parser])
    generate_bill_parser.set_defaults(subaction='generate')
    generate_bill_parser.add_argument('--project', required=True)
    generate_bill_parser.add_argument('--time_period', required=True)

    # if run with no arguments, simply print the help message
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()
    
# Helpers

# # pretty print json
# def pretty(jjson):
#     import json
#     print(json.dumps(jjson, sort_keys=False, indent=4, separators=(',', ': ')))

# alternatively,
def pretty(jjson):
    from pprint import pprint
    pprint(jjson)

# case insensitive comparison, result is the expected result (similar to (str1 == str2) == result)
def cic(str1, str2, result=True):
    # strings are equal XOR negate - returns True only when booleans are T/F or F/T
    return (str1.lower() == str2.lower()) ^ (not result)

# case insensitive in (ex. 'user' in users)
# works for both lists and dicts
def cii(string, array, result=True):
    if isinstance(array, list):
        return (string.lower() in [elem.lower() for elem in array]) ^ (not result)
    return (string.lower() in {k.lower():v for k,v in array.items()}) ^ (not result)

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

def ismoney(val):
    if not (isint(val) or isfloat(val)):
        return False
    return float(val) >= 0

def ispercent(val):
    if not (isint(val) or isfloat(val)):
        return False
    val = float(val)
    return val >= 0 and val <= 100

# not to be confused with isdate, istime checks an integer difference in time measured in seconds
def istime(val):
    if not isint(val):
        return False
    return int(val) >= 0

datefmt = '%Y-%m-%d %H:%M:%S' # used to insert/retrieve dates from elasticsearch; same format used for both
def isdate(date, datefmt=datefmt): # works with dates, non-negative integers (epoch time), strings using datefmt
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
def todate(date, datefmt=datefmt): # converts strings, dates, non-negative integers into a date object
    if isinstance(date, datetime):
        return date
    if isint(date):
        return datetime.fromtimestamp(int(date))
    return datetime.strptime(date, datefmt)

def tostrdate(date, datefmt=datefmt): # converts a date to a string (defaults to elasticsearch date format)
    return date.strftime(datefmt)

def confirmation(): # used when disabling tenant/project, double checks that the user wants to do something
    print('Are you sure? (y/n) ', end='')
    if cic(input(), 'y', False):
        return status_msg(False, 'failed to disable: no confirmation')
    return 0

now = lambda: datetime.now().replace(microsecond=0) # returns current time
rnd = lambda n: round(n, 2) # short hand for rounding to 2 decimals
money_fmt = lambda n: '{0:.2f}'.format(n)

# Query functions

def num_hits(result): # returns number of results from a count/search query
    if 'count' in result:
        return result['count']
    return result['hits']['total']

def get_data(result, field=''): # returns the data from a get/search query
    if 'found' in result: # result is from es.get
        return result['_source'][field] if field else result['_source']
    data = [] # result is from es.search
    for hit in result['hits']['hits']:
        data.append(hit['_source'][field] if field else hit['_source'])
    return data

def multiquery(matches, ranges): # creates a query that satisfies all equivalences/ranges provided as args
    num_matches, num_ranges = len(matches), len(ranges)
    if num_matches + num_ranges == 0:
        return ''
    if num_matches == 1 and num_ranges == 0:
        return '"query": {"match": {' + matches[0] + '}}'
    if num_ranges == 1 and num_matches == 0:
        return '"query": {"range": {' + ranges[0] + '}}'
    # whenever there are at least two queries that need to be satisfied
    queries = ['{"match": {' + match + '}}' for match in matches]
    queries.extend(['{"range": {' + rang + '}}' for rang in ranges]) # range is a keyword, rang is used instead
    return '"query": {"bool": {"must": ' + str(queries).replace("'", '') + '}}'

# from a field/value dictionary (provided in the form of two lists) create a parameters dictionary suitable for ES
def generate_params(fields, values):
    params = ''
    for i in range(len(fields)):
        if i != 0:
            params += ', '
        field, value = fields[i], values[i]
        params += '"' + field + '": '
        if isinstance(value, list):
            params += str(value).replace("'", '"')
        elif isint(value) or isfloat(value):
            params += str(value)
        else:
            params += '"' + value + '"'
    return params

# Query functions

query_size = 500000
def es_query(func, index, body=None, id=None, size=None): # all ES function calls go through this function
    if id == None:
        if size == None:
            return func(index=index, doc_type=index, body=('{' + body + '}'))
        else:
            return func(index=index, doc_type=index, body=('{' + body + '}'), size=size)
    if body == None:
        return func(index=index, doc_type=index, id=id)
    if size == None:
        return func(index=index, doc_type=index, id=id, body=('{' + body + '}'))
    return func(index=index, doc_type=index, id=id, body=('{' + body + '}'), size=size)

def es_index(index, body, id=None): # adding a document
    return es_query(es.index, index, body, id)

def es_count(index, matches=[], ranges=[]): # counting num results
    return es_query(es.count, index, multiquery(matches, ranges))

def es_get(index, id): # getting a known document
    return es_query(es.get, index, id=id)

def es_search(index, matches=[], ranges=[]): # searching for results, obtaining all that satisfy query
    return es_query(es.search, index, multiquery(matches, ranges), size=query_size)

def es_delete(index, matches=[], ranges=[]): # delete documents satisfying query
    return es_query(es.delete_by_query, index, multiquery(matches, ranges), size=query_size)

def es_update(index, id, script='', fields=[], values=[]): # update known document
    params = generate_params(fields, values)
    return es_query(es.update, index, '"script": {"inline": "' + script + '"' + (', "params": {' + params
            + '}' if fields else '') + '}', id=id)

# update all documents that satisfy a query
# script should already contain data about which values should be changed to what params
def es_update_by_query(index, matches=[], ranges=[], script='', fields=[], values=[]):
    params = generate_params(fields, values)
    body = multiquery(matches, ranges)
    return es_query(es.update_by_query, index, (body + ', ' if body else '') + '"script": {"inline": "'
            + script + '"' + (', "params": {' + params + '}' if fields else '') + '}', size=query_size)

def es_log(category, action, details): # log details of actions
    return es_query(es.index, 'log', '"category": "' + category + '", "action": "' + action + '", "details": "'
            + details + '", "date": "' + tostrdate(now()) + '"')

# List of errors

def invalid_project(args):
    res = es_search('project', ['"project": "' + args.project + '"'])
    if num_hits(res) == 0:
        return status_msg(False, 'project does not exist')
    project_data = get_data(res)[0]
    if project_data['d']:
        return status_msg(False, 'project is disabled')
    return project_data

def invalid_credit(args):
    # checks if credit is an invalid value
    if not ismoney(args.credit):
        return status_msg(False, 'invalid credit amount')
    return 0

def invalid_budget(args):
    # checks if bal/cred is an invalid value
    if not ismoney(args.balance) or not ismoney(args.credit):
        return status_msg(False, 'invalid budget')
    return 0

def insufficient_bal_credit(proj, args, tenant_data, projects_data):
    total_bal, total_credit = args.balance, args.credit
    for project in projects_data:
        if cic(project['project'], proj, False):
            pass
        total_bal += project['balance']
        total_credit += project['credit']
    if total_bal > tenant_data['balance']:
        return status_msg(False, 'insufficient balance in tenant')
    if total_credit > tenant_data['credit']:
        return status_msg(False, 'insufficient credit in tenant')
    return 0

# called at the end of an API call's life - should terminate the program and either spit out an error or result
# an argumentless function call indicates no error
mini = False
def status_msg(success=True, error='no error', status={}):
    status['status'] = 'success' if success else 'failed'
    status['error'] = error
    print(status) if mini else pretty(status) # pretty print vs mini (normal) print
    return int(not success) # True returns 0, False returns 1

# API Functions

def lst(args):
    tenants = get_data(es_search('tenant', ['"d": false']
            + (['"name": "' + args.tenant + '"'] if args.tenant else [])
            + (['"projects": "' + args.project + '"'] if args.project else [])))
    if len(tenants) == 0:
        if args.tenant:
            res = es_search('tenant', ['"name": "' + args.tenant + '"'])
            if num_hits(res) == 0:
                return status_msg(False, 'tenant not found')
            if get_data(res, 'd')[0]:
                return status_msg(False, 'tenant is disabled')
        if args.project:
            project_data = invalid_project(args)
            if project_data == 1:
                return 1
            # if tenant has been specified but is not the tenant of this project
            if args.tenant and cic(project_data['tenant'], args.tenant, False):
                return status_msg(False, 'tenant does not have this project')

    if args.project: # if project has been specified
        tenant = tenants[0] # there can only be one tenant
        project_data = get_data(es_get('project', args.project))
        if project_data['d']:
            return status_msg(False, 'project is disabled')
        del tenant['d']
        del project_data['d']
        # if user has been specified and is not in the user list
        if args.user:
            if cii(args.user, project_data['users'], False):
                return status_msg(False, 'project does not have this user')
            project_data['users'] = [args.user]
        tenant['projects'] = [project_data]
        # tenant is put into an array with a single element for consistency
        return status_msg(status={'list': [tenant]})

    found_user = False
    for tenant in tenants: # project cannot have been specified at this point
        del tenant['d']
        projects = get_data(es_search('project', ['"tenant": "' + tenant['name'] + '"', '"d": false']
                + (['"users": "' + args.user + '"'] if args.user else [])))
        if args.user and len(projects) != 0:
            found_user = True
        for project in projects:
            del project['d']
        tenant['projects'] = projects
    if args.user and not found_user:
        return status_msg(False, 'no such user found' + (' for specified tenant' if args.tenant else ''))
    return status_msg(status={'list': tenants})

def add_tenant(args):
    res = es_search('tenant', ['"name": "' + args.tenant + '"'])
    if num_hits(res) > 0:
        if get_data(res, 'd')[0]: # if the existing tenant is disabled
            return status_msg(False, 'existing disabled tenant')
        return status_msg(False, 'tenant already exists') 
    if not (len(args.tenant) <= 32 and args.tenant.isalnum()):
        return status_msg(False, 'invalid tenant name')
    if invalid_credit(args):
        return 1
    es_index('tenant', '"name": "' + args.tenant + '", "balance": 0.0, "credit": ' + str(args.credit)
            + ', "projects": [], "d": false', args.tenant)
    es_log(args.action, args.subaction, 'name: ' + args.tenant + ', credit: ' + str(args.credit))
    return status_msg()

def disable_tenant(args):
    if not args.y:
        if confirmation():
            return 1

    res = es_search('tenant', ['"name": "' + args.tenant + '"'])
    if num_hits(res) == 0:
        return status_msg(False, 'tenant does not exist')
    tenant_data = get_data(res)[0]
    if tenant_data['d']:
        return status_msg(False, 'tenant is already disabled')

    for project in tenant_data['projects']:
        if get_data(es_get('project', project), 'requested') != 0:
            return status_msg(False, 'tenant has a project with pending transactions')
        es_update('project', project, 'ctx._source.d = true')
    es_update('tenant', args.tenant, 'ctx._source.d = true')
    es_log(args.action, args.subaction, 'name: ' + args.tenant)
    return status_msg()

def modify_tenant(args):
    res = es_search('tenant', ['"name": "' + args.tenant + '"'])
    if num_hits(res) == 0:
        return status_msg(False, 'tenant does not exist')
    if get_data(res, 'd')[0]:
        return status_msg(False, 'tenant is disabled')
    if invalid_credit(args):
        return 1
    projects_data = get_data(es_search('project', ['"tenant": "' + args.tenant + '"']))
    total_credit = sum([project['credit'] for project in projects_data])
    if total_credit > args.credit:
        return status_msg(False, 'too much credit allocated to projects to reduce tenant credit')

    es_update('tenant', args.tenant, 'ctx._source.credit=' + str(args.credit))
    es_log(args.action, args.subaction, 'name: ' + args.tenant + ', credit: ' + str(args.credit))
    return status_msg()

def payment_tenant(args):
    res = es_search('tenant', ['"name": "' + args.tenant + '"'])
    if num_hits(res) == 0:
        return status_msg(False, 'tenant does not exist')
    if get_data(res, 'd')[0]:
        return status_msg(False, 'tenant is disabled')
    if not ismoney(args.payment):
        return status_msg(False, 'invalid payment')

    es_update('tenant', args.tenant, 'ctx._source.balance+=' + str(args.payment))
    es_index('payment', '"tenant": "' + args.tenant + '", "date": "' + tostrdate(now()) + '", "payment": '
            + str(args.payment))
    es_log(args.action, args.subaction, 'name: ' + args.tenant + ', payment: ' + str(args.payment))
    return status_msg()

def add_project(args):
    res = es_search('tenant', ['"name": "' + args.tenant + '"'])
    if num_hits(res) == 0:
        return status_msg(False, 'tenant does not exist')
    tenant_data = get_data(res)[0]
    if tenant_data['d']:
        return status_msg(False, 'tenant is disabled')
    res = es_search('project', ['"project": "' + args.project + '"'])
    if num_hits(res) > 0:
        if get_data(res, 'd')[0]:
            return status_msg(False, 'existing disabled project')
        return status_msg(False, 'project already exists')
    if not (len(args.project) <= 32 and args.project.isalnum()):
        return status_msg(False, 'invalid project name')
    if invalid_budget(args):
        return 1

    projects_data = get_data(es_search('project', ['"tenant": "' + args.tenant + '"']))
    if insufficient_bal_credit(args.project, args, tenant_data, projects_data):
        return 1

    rate = get_data(es_get('rate', 'rate'), 'rate')       # hardcoded way of getting the rate
    es_update('tenant', args.tenant, 'ctx._source.projects.add(params.project)', ['project'],
            [args.project])
    es_index('project', '"tenant": "' + args.tenant + '", "project": "' + args.project + '", ' + '"balance": '
            + str(args.balance) + ', "credit": ' + str(args.credit) + ', ' + '"requested": 0.0, "rate": '
            + str(rate) + ', "users": [], "d": false', args.project)
    es_log(args.action, args.subaction, 'project: ' + args.project + ', tenant: ' + args.tenant + ', balance: '
            + str(args.balance) + ', credit: ' + str(args.credit))
    return status_msg()

def disable_project(args):
    if not args.y:
        if confirmation():
            return 1
    
    res = es_search('project', ['"project": "' + args.project + '"'])
    if num_hits(res) == 0:
        return status_msg(False, 'project does not exist')
    data = get_data(res)[0]
    if data['d']:
        return status_msg(False, 'project is already disabled')
    if data['requested'] != 0:
        return status_msg(False, 'project cannot be disabled: pending transaction')

    es_update('project', args.project, 'ctx._source.d = true')
    es_log(args.action, args.subaction, 'project: ' + args.project)
    return status_msg()

def movebudget_project(args):
    # check if either 'from' or 'to' argument does not exist/is disabled
    types = args.type.split('2')
    if types[0] == 'p':
        res = es_search('project', ['"project": "' + args._from + '"'])
        if num_hits(res) == 0:
            return status_msg(False, 'from-project does not exist')
        from_data = get_data(res)[0]
        if from_data['d']:
            return status_msg(False, 'from-project is disabled')
    else:
        res = es_search('tenant', ['"name": "' + args._from + '"'])
        if num_hits(res) == 0:
            return status_msg(False, 'tenant does not exist')
        from_data = get_data(res)[0]
        if from_data['d']:
            return status_msg(False, 'tenant is disabled')

    if types[1] == 'p':
        res = es_search('project', ['"project": "' + args.to + '"'])
        if num_hits(res) == 0:
            return status_msg(False, 'to-project does not exist')
        to_data = get_data(res)[0]
        if to_data['d']:
            return status_msg(False, 'to-project is disabled')
    else:
        res = es_search('tenant', ['"name": "' + args.to + '"'])
        if num_hits(res) == 0:
            return status_msg(False, 'tenant does not exist')
        to_data = get_data(res)[0]
        if to_data['d']:
            return status_msg(False, 'tenant is disabled')
    
    # ensure ownership (p belongs to t, both p are under same t)
    if types[0] == 'p' and types[1] == 'p':
        if cic(from_data['tenant'], to_data['tenant'], False):
            return status_msg(False, 'projects do not belong to the same tenant')
    elif types[0] == 'p' and cic(from_data['tenant'], args.to, False) \
        or types[1] == 'p' and cic(args._from, to_data['tenant'], False):
        return status_msg(False, 'project does not belong to tenant')

    # if from tenant, check that this tenant has enough bal/cred
    if types[0] == 't':
        projects_data = get_data(es_search('project', ['"tenant": "' + args._from + '"']))
        # safe to assume money is moving to a project (since it's from a tenant)
        if insufficient_bal_credit(args.to, args, from_data, projects_data):
            return 1
    else: # if from project, check the same, update the project bal
        if from_data['balance'] < args.balance:
            return status_msg(False, 'insufficient balance')
        if from_data['credit'] < args.credit:
            return status_msg(False, 'insufficient credit')
        es_update('project', args._from, 'ctx._source.balance -= params.balance; '
                + 'ctx._source.credit -= params.credit', ['balance', 'credit'], [args.balance, args.credit])

    # if no errors, update only if to-project (tenant does not need to be updated)
    if types[1] == 'p':
        es_update('project', args.to, 'ctx._source.balance += params.balance; ctx._source.credit += params.credit',
                ['balance', 'credit'], [args.balance, args.credit])

    es_log(args.action, args.subaction, 'from: ' + args._from + ', to: ' + args.to + ', balance: '
            + str(args.balance) + ', credit: ' + str(args.credit) + ', type: ' + args.type)
    return status_msg()

def add_user(args):
    project_data = invalid_project(args)
    if project_data == 1:
        return 1
    if cii(args.user, project_data['users']):
        return status_msg(False, 'project already has this user')
    if not (len(args.user) <= 32 and args.user.isalnum()):
        return status_msg(False, 'invalid user name')
    
    es_update('project', args.project, 'ctx._source.users.add(params.user)', ['user'], [args.user])
    es_log(args.action, args.subaction, 'project: ' + args.project + ', user: ' + args.user)
    return status_msg()

def delete_user(args):
    project_data = invalid_project(args)
    if project_data == 1:
        return 1
    if cii(args.user, project_data['users'], False):
        return status_msg(False, 'project does not have this user')

    es_update('project', args.project, 'ctx._source.users.remove(ctx._source.users.indexOf(params.user))',
            ['user'], [args.user])
    es_log(args.action, args.subaction, 'project: ' + args.project + ', user: ' + args.user)
    return status_msg()

def set_rate(args):
    if not ismoney(args.rate):
        return status_msg(False, 'invalid rate')
    es_update('rate', 'rate', 'ctx._source.rate=' + str(args.rate))
    es_update_by_query('project', [], [], 'ctx._source.rate=' + str(args.rate))
    es_log(args.action, args.subaction, 'rate: ' + str(args.rate))
    return status_msg()

def get_rate(args):
    rate = get_data(es_get('rate', 'rate'), 'rate')
    return status_msg(status={'rate': rate})

def reservebudget_transaction(args):
    # validate arguments, calculate and update amount requested to the project
    project_data = invalid_project(args)
    if project_data == 1:
        return 1
    if not istime(args.estimate):
        return status_msg(False, 'invalid estimate')
    cost = project_data['rate'] * args.estimate / 3600 # rate is in hrs, estimate in seconds
    if project_data['balance'] + project_data['credit'] - project_data['requested'] < cost:
        return status_msg(False, 'insufficient project budget')

    es_update('project', args.project, 'ctx._source.requested+=params.requested', ['requested'], [cost])
    return status_msg()

def charge_transaction(args):
    # validate arguments, calculate project's new bal/cred, calculate tenant's new bal/cred, index transaction
    project_data = invalid_project(args)
    if project_data == 1:
        return 1
    if not istime(args.estimate):
        return status_msg(False, 'invalid estimate')
    if not istime(args.jobtime):
        return status_msg(False, 'invalid jobtime')
    if not isdate(args.start):
        return status_msg(False, 'invalid start time')
    if cii(args.user, project_data['users'], False): # if user is not found in user list
        return status_msg(False, 'project does not contain this user')
    
    cost = project_data['rate'] * args.jobtime / 3600
    requested = project_data['rate'] * args.estimate / 3600
    if cost <= project_data['balance']:
        new_bal, new_credit = project_data['balance'] - cost, project_data['credit']
    elif cost <= project_data['balance'] + project_data['credit']:
        new_bal, new_credit = 0.0, project_data['credit'] - (cost - project_data['balance'])
    else:
        new_bal, new_credit = project_data['balance'] - (cost - project_data['credit']), 0.0

    es_update('project', args.project,
            'ctx._source.requested -= params.requested; ctx._source.balance = params.new_bal;'
            + 'ctx._source.credit = params.new_credit', ['requested', 'new_bal', 'new_credit'],
            [requested, new_bal, new_credit])
    es_update('tenant', project_data['tenant'],
            'if (params.cost <= ctx._source.balance) {'
            + 'ctx._source.balance -= params.cost;'
            + '} else if (params.cost <= ctx._source.balance + ctx._source.credit) {'
            + 'ctx._source.credit -= params.cost - ctx._source.balance;'
            + 'ctx._source.balance = 0;'
            + '} else {'
            + 'ctx._source.balance -= params.cost - ctx._source.credit;'
            + 'ctx._source.credit = 0;'
            + '}', ['cost'], [cost])
    es_index('transaction', '"project": "' + args.project + '", "user": "' + args.user + '", "start": "'
            + tostrdate(todate(args.start)) + '", "end": "'
            + tostrdate(todate(args.start) + timedelta(seconds=args.jobtime)) + '", "runtime": '
            + str(args.jobtime) + ', "cost": ' + str(cost))
    return status_msg()

def generate_bill(args):
    # ensure validity of arguments
    res = es_search('project', ['"project": "' + args.project + '"'])
    if num_hits(res) == 0:
        return status_msg(False, 'project does not exist')

    bill_datefmt = '%Y-%m-%d'
    curtime, dates = now(), args.time_period.split(',')
    if len(dates) == 2:
        if not isdate(dates[0], bill_datefmt) or not isdate(dates[1], bill_datefmt):
            return status_msg(False, 'invalid date format')
        start, end = todate(dates[0], bill_datefmt), todate(dates[1], bill_datefmt)
    elif args.time_period == 'last_day':
        start, end = curtime-timedelta(days=1), curtime
    elif args.time_period == 'last_week':
        start, end = curtime-timedelta(days=7), curtime
    elif args.time_period == 'last_month':
        start, end = curtime-timedelta(days=30), curtime
    else:
        return status_msg(False, 'invalid date')
    
    # obtain data from documents
    project_data = get_data(res)[0]
    tenant_data = get_data(es_get('tenant', project_data['tenant']))
    transaction_data = get_data(es_search('transaction', ['"project": "' + args.project + '"'],
            ['"end": {"gte": "' + tostrdate(start) + '"}']))
    payment_data = get_data(es_search('payment', ['"tenant": "' + project_data['tenant'] + '"'],
            ['"date": {"gte": "' + tostrdate(start) + '"}']))
    
    # sum of transactions/payments within the date range specified
    range_transactions, range_transaction_total, range_payment_total = [], 0.0, 0.0
    # sum of transactions/payments after the date range specified (but before today)
    post_transaction_total, post_payment_total = 0.0, 0.0
    for transaction in transaction_data:
        date = todate(transaction['end'])
        if date > end:
            post_transaction_total += transaction['cost']
        else:
            range_transactions.append(transaction)
            range_transaction_total += transaction['cost']
    for payment in payment_data:
        date = todate(payment['date'])
        if date > end:
            post_payment_total += payment['payment']
        else:
            range_payment_total += payment['payment']

    # calculate bbalance/ebalance
    ending_bal = tenant_data['balance'] - post_payment_total + post_transaction_total
    starting_bal = ending_bal - range_payment_total + range_transaction_total

    # calculate user hour usage
    for transaction in range_transactions:
        transaction['end'] = tostrdate(todate(transaction['end']), bill_datefmt)
    dates = set([x['end'] for x in transaction_data])
    bill = [{'date': date, 'activity': []} for date in dates]
    total_cost, total_hours = 0.0, 0.0

    # each transaction is inserted into the bill
    for transaction in range_transactions:
        runtime = transaction['runtime'] / 3600 # runtime in hours
        total_hours += runtime
        total_cost += transaction['cost']
        
        # find the entry in the bill whose date corresponds with the transaction's
        for b in bill:
            if b['date'] == transaction['end']:
                # find the specified user in the bill entry - if not found, create the user
                found = False
                for u in b['activity']:
                    if u['user'] == transaction['user']:
                        found = True
                        u['hours'] += runtime
                        break
                if not found:
                    b['activity'].append({'user': transaction['user'],
                            'hours': runtime})
                break

    # rounding values
    for b in bill:
        for u in b['activity']:
            u['hours'] = rnd(u['hours'])
    
    # aggregate data
    bill = {'tenant': project_data['tenant'], 'project': args.project,
            'from': tostrdate(start, bill_datefmt), 'to': tostrdate(end, bill_datefmt), 'bill': bill,
            'total_hours': rnd(total_hours), 'total_cost': money_fmt(rnd(total_cost)),
            'bbalance': money_fmt(rnd(starting_bal)), 'payments': money_fmt(rnd(range_payment_total)),
            'ebalance': money_fmt(rnd(ending_bal))}

    return status_msg(status={'bill': bill})


# Main

def main():
    args = getargs()
    global mini
    mini = args.mini
    
    if args.action == 'list': # no subaction
        lst(args)
    
    elif args.action == 'tenant':
        if args.subaction == 'add':
            add_tenant(args)
        elif args.subaction == 'disable':
            disable_tenant(args)    
        elif args.subaction == 'modify':
            modify_tenant(args)
        elif args.subaction == 'payment':
            payment_tenant(args)
    
    elif args.action == 'project':
        if args.subaction == 'add':
            add_project(args)
        elif args.subaction == 'disable':
            disable_project(args)
        elif args.subaction == 'movebudget': 
            movebudget_project(args)
    
    elif args.action == 'user':
        if args.subaction == 'add':
            add_user(args)
        elif args.subaction == 'delete':
            delete_user(args)    
    
    elif args.action == 'rate':
        if args.subaction == 'set':
            set_rate(args)        
        elif args.subaction == 'get':
            get_rate(args)
    
    elif args.action == 'transaction':
        if args.subaction == 'reservebudget':
            reservebudget_transaction(args)
        elif args.subaction == 'charge':
            charge_transaction(args)
    
    elif args.action == 'bill':
        if args.subaction == 'generate':
            generate_bill(args)

if __name__ == '__main__':
    main()
