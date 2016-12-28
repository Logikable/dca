from elasticsearch import Elasticsearch
es = Elasticsearch()

def pretty(jjson):
    import json
    print(json.dumps(jjson, sort_keys=False, indent=4, separators=(',', ': ')))

def es_query(func, doc_type, body):
    index = (func == es.index)
    if index:
        new_body = '{"query": {"term": '
    new_body = new_body + body
    if index:
        new_body = new_body + '}}'
    print(body)
    return func(index="dca", doc_type=doc_type, body=new_body)

def clr():
    es.indices.delete("dca")

def setup():
    import dca_setup
