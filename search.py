import json
from pprint import pprint
import os
import time

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()


class Search:
    def __init__(self):
        self.es = Elasticsearch('http://localhost:9200/')
        # self.es = Elasticsearch(cloud_id=os.environ['ELASTIC_CLOUD_ID'],
        #                         api_key=os.environ['ELASTIC_API_KEY'])
        client_info = self.es.info()
        print('Connected to Elasticsearch!')
        pprint(client_info.body)
    

    def create_index(self):
        # deletes the index first, ignore unavailable option prevents if the index is not found
        self.es.indices.delete(index="my_documents", ignore_unavailable=True)
        self.es.indices.create(index="my_documents")


    def insert_document(self, document):
        # this method accepts the ES client and a document from the caller, and inserts the doc into the my_documents index
        return self.es.index(index='my_documents', body=document)    


    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({'index': {'_index': 'my_documents'}})
            operations.append(document)
        return self.es.bulk(operations=operations)


    def reindex(self):
        self.create_index()
        with open('data.json', 'rt') as f:
            documents = json.loads(f.read())
        return self.insert_documents(documents)


    def search(self, **query_args):
        return self.es.search(index='my_documents', **query_args)
    
    
    def retrieve_document(self, id):
        return self.es.get(index='my_documents', id=id)
    
