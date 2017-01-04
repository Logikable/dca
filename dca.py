#!/usr/bin/python3.4
from elasticsearch import Elasticsearch
es = Elasticsearch()

from datetime import datetime
from datetime import timedelta

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
    add_tenant_parser.add_argument('--credit', type=float, default=0)

    delete_tenant_parser = tenant_subparsers.add_parser('delete')
    delete_tenant_parser.add_argument('--tenant', required=True)

    modify_tenant_parser = tenant_subparsers.add_parser('modify')
    modify_tenant_parser.add_argument('--tenant', required=True)
    modify_tenant_parser.add_argument('--credit', type=float, required=True)

    payment_tenant_parser = tenant_subparsers.add_parser('payment')
    payment_tenant_parser.add_argument('--tenant', required=True)
    payment_tenant_parser.add_argument('--payment', type=float, required=True)


    project_parser = subparsers.add_parser('project')
    project_subparsers = project_parser.add_subparsers()

    add_project_parser = project_subparsers.add_parser('add')
    add_project_parser.add_argument('--tenant', required=True)
    add_project_parser.add_argument('--project', required=True)
    add_project_parser.add_argument('--budget', type=float, required=True)

    delete_project_parser = project_subparsers.add_parser('delete')
    delete_project_parser.add_argument('--project', required=True)

    modify_project_parser = project_subparsers.add_parser('modify')
    modify_project_parser.add_argument('--project', required=True)
    modify_project_parser.add_argument('--budget', type=float, required=True)


    user_parser = subparsers.add_parser('user')
    user_subparsers = user_parser.add_subparsers()

    add_user_parser = user_subparsers.add_parser('add')
    add_user_parser.add_argument('--project', required=True)
    add_user_parser.add_argument('--user', required=True)

    delete_user_parser = user_subparsers.add_parser('delete')
    delete_user_parser.add_argument('--project', required=True)
    delete_user_parser.add_argument('--user', required=True)


    list_parser = subparsers.add_parser('list')
    list_parser.add_argument('--tenant')
    list_parser.add_argument('--project')
    list_parser.add_argument('--user')


    rate_parser = subparsers.add_parser('rate')
    rate_subparsers = rate_parser.add_subparsers()

    set_rate_parser = rate_subparsers.add_parser('set')
    set_rate_parser.add_argument('--rate', type=float, required=True)

    get_rate_parser = rate_subparsers.add_parser('get')


    transaction_parser = subparsers.add_parser('transaction')
    transaction_subparsers = transaction_parser.add_subparsers()

    reservebudget_transaction_parser = transaction_subparsers.add_parser('reservebudget')
    reservebudget_transaction_parser.add_argument('--project', required=True)
    reservebudget_transaction_parser.add_argument('--estimate', type=int, required=True)

    charge_transaction_parser = transaction_subparsers.add_parser('charge')
    charge_transaction_parser.add_argument('--project', required=True)
    charge_transaction_parser.add_argument('--user', required=True)
    charge_transaction_parser.add_argument('--estimate', type=int, required=True)
    charge_transaction_parser.add_argument('--jobtime', type=int, required=True)
    charge_transaction_parser.add_argument('--start', required=True)
   

    bill_parser = subparsers.add_parser('bill')
    bill_subparsers = bill_parser.add_subparsers()

    generate_bill_parser = bill_subparsers.add_parser('generate')
    generate_bill_parser.add_argument('--project', required=True)
    generate_bill_parser.add_argument('--time_period', required=True)

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

# case insensitive comparison
def cic(str1, str2, negate=False):
    # strings are equal XOR negate - returns True only when booleans are T/F or F/T
    return (str1.lower() == str2.lower()) ^ negate

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

def istime(val):
    if not isint(val):
        return False
    return int(val) >= 0

datefmt = '%Y-%m-%d %H:%M:%S'
datenever = datetime(3333, 1, 1)
def isdate(date, datefmt=datefmt):
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
def todate(date, datefmt=datefmt):
    if isinstance(date, datetime):
        return date
    if cic(date, "never"):
        return datenever
    if isint(date):
        return datetime.fromtimestamp(int(date))
    return datetime.strptime(date, datefmt)

def tostrdate(date, datefmt=datefmt):
    return date.strftime(datefmt)

def now():
    return datetime.now().replace(microsecond=0)

# Query functions

def num_hits(result):
    if 'count' in result:
        return result['count']
    return result['hits']['total']

def get_data(result, field=''):
    data = []
    for hit in result['hits']['hits']:
        data.append(hit['_source'][field] if field else hit['_source'])
    return data

def es_query(func, doc_type, body):
    return func(index="dca", doc_type=doc_type, body=body)

def es_index(doc_type, body):
    return es_query(es.index, doc_type, '{' + body + '}')

def es_count(doc_type, body):
    return es_query(es.count, doc_type, '{"query": {"match": {' + body + '}}}')

# flexible mode allows for non-match queries
def es_search(doc_type, body, flexible=False):
    # checks if body contains nothing
    if not body:
        return es_query(es.search, doc_type, '')
    if flexible:
        return es_query(es.search, doc_type, '{"query": {"bool": {' + body + '}}}')
    return es_query(es.search, doc_type, '{"query": {"match": {' + body + '}}}')

def es_delete(doc_type, body):
    return es_query(es.delete_by_query, doc_type, '{"query": {"match": {' + body + '}}}')

# script should already contain data about which values should be changed to what params
def es_update(doc_type, body, script, fields=[], values=[]):
    params = ''
    if not isinstance(fields, (list, tuple)):
        fields, values = [fields], [values]
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
    return es_query(es.update_by_query, doc_type, '{' + ('"query": {"match": {' + body + '}}, ' if body else '')
            + '"script": {"inline": "' + script + '"' + (', "params": {' + params + '}' if fields else '') + '}}')

# List of errors

def invalid_tenant(args):
    # checks if tenant doesn't exist
    if num_hits(es_count('tenant', '"name": "' + args.tenant + '"')) == 0:
        return status_msg(False, 'tenant not found')
    return 0

def invalid_project(args):
    # checks if project doesn't exist
    if num_hits(es_count('project', '"project": "' + args.project + '"')) == 0:
        return status_msg(False, 'project not found')
    return 0

def invalid_credit(args):
    # checks if credit is an invalid value
    if not ismoney(args.credit):
        return status_msg(False, 'invalid credit amount')
    return 0

def invalid_budget(args):
    # checks if budget is an invalid value
    if not ismoney(args.budget) or args.budget <= 0:
        return status_msg(False, 'invalid budget')
    return 0

# an argumentless function call indicates no error
def status_msg(success=True, error='no error', status={}):
    status['status'] = 'success' if success else 'failed'
    status['error'] = error
    print(status)
    return int(not success) # True returns 0, False returns 1

# Main

def main():
    args = getargs()
    
    # it is guaranteed that there is at least 1 argument
    action = sys.argv[1]   # sys.argv[0] is this file's name

    if action == 'list': # no subaction
        tenants = get_data(es_search('tenant', (('"name": "' + args.tenant + '"') if args.tenant else '')
                + (', ' if args.tenant and args.project else '')
                + (('"projects": "' + args.project + '"') if args.project else '')))
        if len(tenants) == 0:
            if args.tenant and invalid_tenant(args):
                return 1
            if args.project:
                res = es_search('project', '"project": "' + args.project + '"')
                if num_hits(res) == 0:
                    return status_msg(False, 'project does not exist')
                # if tenant has been specified but is not the tenant of this project
                if args.tenant and cic(get_data(res)[0], args.tenant, True):
                    return status_msg(False, 'tenant does not have this project')

        if args.project: # if project has been specified
            tenant = tenants[0] # there can only be one tenant
            project_data = get_data(es_search('project', '"project": "' + args.project + '"'))[0]
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
            projects = get_data(es_search('project', '"tenant": "' + tenant['name'] + '"'))
            if args.user: # if user has been specified
                # if the user belongs to a project, keep it in the list
                new_projects = []
                for project in projects:
                    if cii(args.user, project['users']):
                        new_projects.append(project)
                        found_user = True
            tenant['projects'] = projects
        if args.user and not found_user:
            return status_msg(False, 'no such user found' + (' for specified tenant' if args.tenant else ''))
        return status_msg(status={'list': tenants})

    else:
        subaction = sys.argv[2]

    if action == 'tenant':
        if subaction == 'add': # 1 count tenant, 1 index tenant
            if num_hits(es_count('tenant', '"name": "' + args.tenant + '"')) > 0:
                return status_msg(False, 'tenant already exists')
            if not (len(args.tenant) <= 32 and args.tenant.isalnum()):
                return status_msg(False, 'invalid tenant name')
            if invalid_credit(args):
                return 1
            es_index('tenant', '"name": "' + args.tenant + '", "balance": 0.0, "credit": ' + str(args.credit)
                    + ', "total_allocated": 0.0, "projects": []')
            return status_msg()

        elif subaction == 'delete': # 1 count tenant, 1 delete tenant
            if invalid_tenant(args):
                return 1
            es_delete('tenant', '"name": "' + args.tenant + '"')
            return status_msg()

        elif subaction == 'modify': # 1 search tenant, 1 update tenant
            res = es_search('tenant', '"name": "' + args.tenant + '"')
            if num_hits(res) == 0:
                return status_msg(False, 'tenant does not exist')
            if invalid_credit(args):
                return 1

            es_update('tenant', '"name": "' + args.tenant + '"', 'ctx._source.credit=' + str(args.credit))
            return status_msg()

        elif subaction == 'payment': # 1 search tenant, 1 update tenant, 1 index payment
            res = es_search('tenant', '"name": "' + args.tenant + '"')
            if num_hits(res) == 0:
                return status_msg(False, 'tenant does not exist')
            if not ismoney(args.payment):
                return status_msg(False, 'invalid payment')

            es_update('tenant', '"name": "' + args.tenant + '"', 'ctx._source.balance+=' + str(args.payment))
            es_index('payment', '"tenant": "' + args.tenant + '", "date": "' + tostrdate(now())
                    + '", "payment": ' + str(args.payment))
            return status_msg()

    elif action == 'project':
        if subaction == 'add': # 1 search tenant, 1 count project, 1 search rate, 1 update tenant, 1 index project
            res = es_search('tenant', '"name": "' + args.tenant + '"')
            if num_hits(res) == 0:
                return status_msg(False, 'tenant does not exist')
            if num_hits(es_count('project', '"project": "' + args.project + '"')) > 0:
                return status_msg(False, 'project already exists')
            if not (len(args.project) <= 32 and args.project.isalnum()):
                return status_msg(False, 'invalid project name')
            if invalid_budget(args):
                return 1

            data = get_data(res)[0]
            bal = data['balance'] + data['credit']
            if bal < data['total_allocated'] + args.budget:
                return status_msg(False, 'insufficient budget: overallocation by '
                        + str(data['total_allocated'] + args.budget - bal))

            project_bal = data['balance']/bal * args.budget
            project_credit = data['credit']/bal * args.budget
            rate = get_data(es_search('rate', ''), 'rate')[0]       # hardcoded way of getting the rate

            es_update('tenant', '"name": "' + args.tenant + '"', 'ctx._source.projects.add(params.project);'
                    + 'ctx._source.total_allocated += params.alloc', ['project', 'alloc'],
                    [args.project, args.budget])
            es_index('project', '"tenant": "' + args.tenant + '", "project": "' + args.project + '", '
                    + '"budget": ' + str(project_bal + project_credit) + ', "balance": '
                    + str(project_bal) + ', "credit": ' + str(project_credit) + ', '
                    + '"requested": 0.0, "rate": ' + str(rate) + ', "users": []')
            return status_msg()

        elif subaction == 'delete': # 1 search project, 1 delete project, 1 update tenant
            res = es_search('project', '"project": "' + args.project + '"')
            if num_hits(res) == 0:
                return status_msg(False, 'project does not exist')
            data = get_data(res)[0]
            if data['requested'] != 0:
                return status_msg(False, 'failed to delete project: pending transaction')

            es_delete('project', '"project": "' + args.project + '"')
            es_update('tenant', '"name": "' + data['tenant'] + '"', 'ctx._source.total_allocated -= '
                    + str(data['budget']))
            return status_msg()

        elif subaction == 'modify': # 1 search project, 1 search tenant, 1 update project, 1 update tenant
            res = es_search('project', '"project": "' + args.project + '"')
            if num_hits(res) == 0:
                return status_msg(False, 'project does not exist')
            if invalid_budget(args):
                return 1
            
            project_data = get_data(res)[0]
            tenant_data = get_data(es_search('tenant', '"name": "' + project_data['tenant'] + '"'))[0] 

            bal = tenant_data['balance'] + tenant_data['credit']
            new_alloc = tenant_data['total_allocated'] + args.budget - project_data['budget']
            if bal < new_alloc:
                return status_msg(False, 'insufficient budget: overallocation by ' + str(new_alloc - bal))

            project_bal = tenant_data['balance']/bal * args.budget
            project_credit = tenant_data['credit']/bal * args.budget
            es_update('project', '"project": "' + args.project + '"',
                    'ctx._source.balance = params.bal; ctx._source.credit = params.credit; '
                    + 'ctx._source.budget = params.budget',
                    ['bal', 'credit', 'budget'], [project_bal, project_credit, args.budget])
            es_update('tenant', '"name": "' + project_data['tenant'] + '"', 'ctx._source.total_allocated='
                    + str(new_alloc))
            return status_msg()

    elif action == 'user':
        if subaction == 'add': # 1 count project, 1 update project
            if invalid_project(args):
                return 1
            if not (len(args.user) <= 32 and args.user.isalnum()):
                return status_msg(False, 'invalid user name')

            es_update('project', '"project": "' + args.project + '"', 'ctx._source.users.add(params.user)',
                    ['user'], [args.user])
            return status_msg()

        elif subaction == 'delete': #1 count project, 1 update project
            if invalid_project(args):
                return 1

            es_update('project', '"project": "' + args.project + '"',
                    'ctx._source.users.remove(ctx._source.users.indexOf(params.user))', ['user'], [args.user])
            return status_msg()
    
    elif action == 'rate':
        if subaction == 'set': # 1 update rate, 1 update project
            if not ismoney(args.rate):
                return status_msg(False, 'invalid rate')
            es_update('rate', '', 'ctx._source.rate=' + str(args.rate))
            es_update('project', '', 'ctx._source.rate=' + str(args.rate))
            return status_msg()
        
        elif subaction == 'get': # 1 search rate
            rate = get_data(es_search('rate', ''), 'rate')[0]
            return status_msg(status={'rate': rate})

    elif action == 'transaction':
        if subaction == 'reservebudget': # 1 search project, 1 update project
            res = es_search('project', '"project": "' + args.project + '"')
            if num_hits(res) == 0:
                return status_msg(False, 'project does not exist')
            if not istime(args.estimate):
                return status_msg(False, 'invalid estimate')
            data = get_data(res)[0]
            cost = data['rate'] * args.estimate / 3600 # rate is in hrs, estimate in seconds
            if data['balance'] + data['credit'] - data['requested'] < cost:
                return status_msg(False, 'insufficient project budget')

            es_update('project', '"project": "' + args.project + '"', 'ctx._source.requested+=params.requested',
                    ['requested'], [cost])
            return status_msg()
        
        elif subaction == 'charge': # 1 search project, 1 search tenant, 1 update project, 1 update tenant,
                                    # 1 index transaction
            res = es_search('project', '"project": "' + args.project + '"')
            if num_hits(res) == 0:
                return status_msg(False, 'project does not exist')
            if not istime(args.estimate):
                return status_msg(False, 'invalid estimate')
            if not istime(args.jobtime):
                return status_msg(False, 'invalid jobtime')
            if not isdate(args.start):
                return status_msg(False, 'invalid start time') 
            project_data = get_data(res)[0]
            if cii(args.user, project_data['users'], False): # if user is not found in user list
                return status_msg(False, 'project does not contain this user')
            
            cost = project_data['rate'] * args.jobtime / 3600
            requested = project_data['rate'] * args.estimate / 3600
            if cost <= project_data['balance']:
                new_bal, new_credit = project_data['balance'] - cost, project_data['credit']
            elif cost <= project_data['balance'] + project_data['credit']:
                new_bal, new_credit = 0, project_data['credit'] - (cost - project_data['balance'])
            else:
                new_bal, new_credit = project_data['balance'] - (cost - project_data['credit']), 0

            es_update('project', '"project": "' + args.project + '"', 'ctx._source.requested -= params.requested;'
                    + 'ctx._source.balance = params.new_bal; ctx._source.credit = params.new_credit',
                    ['requested', 'new_bal', 'new_credit'], [requested, new_bal, new_credit])

            tenant_data = get_data(es_search('tenant', '"name": "' + project_data['tenant'] + '"'))[0]
            if cost <= tenant_data['balance']:
                new_bal, new_credit = tenant_data['balance'] - cost, tenant_data['credit']
            elif cost <= tenant_data['balance'] + tenant_data['credit']:
                new_bal, new_credit = 0, tenant_data['credit'] - (cost - tenant_data['balance'])
            else:
                new_bal, new_credit = tenant_data['balance'] - (cost - tenant_data['credit'])

            es_update('tenant', '"name": "' + project_data['tenant'] + '"', 'ctx._source.balance = params.new_bal;'
                    + 'ctx._source.credit = params.new_credit', ['new_bal', 'new_credit'], [new_bal, new_credit])

            es_index('transaction', '"project": "' + args.project + '", "user": "' + args.user + '", "start": "'
                    + tostrdate(todate(args.start)) + '", "end": "'
                    + tostrdate(todate(args.start) + timedelta(seconds=args.jobtime)) + '", "runtime": '
                    + str(args.jobtime) + ', "cost": ' + str(cost) + ', "tenant_balance": ' + str(new_bal))
            return status_msg()

    elif action == 'bill':
        if subaction == 'generate':
            res = es_search('project', '"project": "' + args.project + '"')
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

            project_data = get_data(res)[0]
            tenant_data = get_data(es_search('tenant', '"name": "' + project_data['tenant'] + '"'))[0]
            transaction_data = get_data(es_search('transaction', '"must": [{"match": {"project": "' + args.project
                    + '"}}, {"range": {"end": {"gte": "' + tostrdate(start) + '", "lte": "' + tostrdate(end)
                    + '"}}}]', True))

            starting_bal = min(transaction_data, key=lambda x: x['end'])['tenant_balance']
            ending_bal = max(transaction_data, key=lambda x: x['end'])['tenant_balance']

            for transaction in transaction_data:
                transaction['end'] = tostrdate(todate(transaction['end']).replace(hour=0, minute=0, second=0),
                        bill_datefmt)
            dates = set([x['end'] for x in transaction_data])
            bill = [{'date': date, 'activity': []} for date in dates]
            total_cost, total_hours = 0, 0

            for transaction in transaction_data:
                runtime = transaction['runtime'] / 3600 # runtime in hours
                total_hours += runtime
                total_cost += transaction['cost']
                
                for b in bill:
                    if b['date'] == transaction['end']:
                        found = False 
                        for u in b['activity']:
                            if u['user'] == transaction['user']:
                                found = True
                                u['hours'] += runtime
                                break
                        if not found:
                            b['activity'].append({'user': transaction['user'],
                                    'hours': transaction['runtime' / 3600]})
                        break
 
            payment_data = get_data(es_search('payment', '"must": [{"match": {"tenant": "' + project_data['tenant'] 
                    + '"}}, {"range": {"date": {"gte": "' + tostrdate(start) + '", "lte": "' + tostrdate(end)
                    + '"}}}]', True))
            total_payment = sum([payment['payment'] for payment in payment_data])

            bill = {'tenant': project_data['tenant'], 'project': args.project,
                    'from': tostrdate(start, bill_datefmt), 'to': tostrdate(end, bill_datefmt), 'bill': bill,
                    'total_hours': total_hours, 'total_cost': total_cost, 'bbalance': starting_bal,
                    'payments': total_payment, 'ebalance': ending_bal}

            return status_msg(status={'bill': bill})

if __name__ == '__main__':
    main()
