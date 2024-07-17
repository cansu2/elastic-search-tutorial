import re
from flask import Flask, render_template, request
from search import Search

app = Flask(__name__)
es = Search()


@app.get('/')
def index():
    return render_template('index.html')


# @app.post('/')
# def handle_search():
#     query = request.form.get('query', '')
#     results = es.search(
#         query={
#             'match': {
#                 'name': {
#                     'query': query
#                 }
#             }
#         }
#     )
#     # render template because there is no search implementation yet
#     # return render_template(
#     #     'index.html', query=query, results=[], from_=0, total=0)

#     return render_template('index.html', resilts=results['hits']['hits'], 
#                         query=query, from_=0,
#                         total=results['hits']['total']['value'])


# adding multi_match and pagination
# @app.post('/')
# def handle_search():
#     query = request.form.get('query', '')
#     # from_ and size are added for pagination
#     from_ = request.form.get('from_', type=int, default=0)
#     results = es.search(
#         query={
#             'multi_match': {
#                 'query': query,
#                 'fields': ['name', 'summary', 'content'],
#             }
#         }, size=5, from_=from_
#     )
#     return render_template('index.html', results=results['hits']['hits'],
#                            query=query, from_=from_,
#                            total=results['hits']['total']['value'])


# adding filtered search

# @app.post('/')
# def handle_search():
#     query = request.form.get('query', '')
#     filters, parsed_query = extract_filters(query)
#     from_ = request.form.get('from_', type=int, default=0)

#     results = es.search(
#         query={
#             'bool': {
#                 'must': {
#                     'multi_match': {
#                         'query': parsed_query,
#                         'fields': ['name', 'summary', 'content'],
#                     }
#                 },
#                 **filters
#             }
#         },
#         size=5,
#         from_=from_
#     )
#     return render_template('index.html', results=results['hits']['hits'],
#                            query=query, from_=from_,
#                            total=results['hits']['total']['value'])


# multi_match is replaces with multi_all prevent the case is search text is empty 
# @app.post('/')
# def handle_search():
#     query = request.form.get('query', '')
#     filters, parsed_query = extract_filters(query)
#     from_ = request.form.get('from_', type=int, default=0)

#     if parsed_query:
#         search_query = {
#             'must': {
#                 'multi_match': {
#                     'query': parsed_query,
#                     'fields': ['name', 'summary', 'content'],
#                 }
#             }
#         }
#     else:
#         search_query = {
#             'must': {
#                 'match_all': {}
#             }
#         }

#     results = es.search(
#         query={
#             'bool': {
#                 **search_query,
#                 **filters
#             }
#         },
#         size=5,
#         from_=from_
#     )
#     return render_template('index.html', results=results['hits']['hits'],
#                            query=query, from_=from_,
#                            total=results['hits']['total']['value'])

# Adding faceted search -> aggregations
# @app.post('/')
# def handle_search():
#     query = request.form.get('query', '')
#     filters, parsed_query = extract_filters(query)
#     from_ = request.form.get('from_', type=int, default=0)

#     if parsed_query:
#         search_query = {
#             'must': {
#                 'multi_match': {
#                     'query': parsed_query,
#                     'fields': ['name', 'summary', 'content'],
#                 }
#             }
#         }
#     else:
#         search_query = {
#             'must': {
#                 'match_all': {}
#             }
#         }

#     results = es.search(
#         query={
#             'bool': {
#                 **search_query,
#                 **filters
#             }
#         },
#         aggs={
#             'category-agg': {
#                 'terms': {
#                     'field': 'category.keyword',
#                 }
#             },
#             'year-agg': {
#                 'date_histogram': {
#                     'field': 'updated_at',
#                     'calendar_interval': 'year',
#                     'format': 'yyyy',
#                 },
#             },
#         },
#         size=5,
#         from_=from_
#     )
#     aggs = {
#         'Category': {
#             bucket['key']: bucket['doc_count']
#             for bucket in results['aggregations']['category-agg']['buckets']
#         },
#         'Year': {
#             bucket['key_as_string']: bucket['doc_count']
#             for bucket in results['aggregations']['year-agg']['buckets']
#             if bucket['doc_count'] > 0
#         },
#     }
#     return render_template('index.html', results=results['hits']['hits'],
#                            query=query, from_=from_,
#                            total=results['hits']['total']['value'], aggs=aggs)

@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    filters, parsed_query = extract_filters(query)
    from_ = request.form.get('from_', type=int, default=0)

    results = es.search(
        knn={
            'field': 'embedding',
            'query_vector': es.get_embedding(parsed_query),
            'k': 10,
            'num_candidates': 50,
            **filters,
        },
        aggs={
            'category-agg': {
                'terms': {
                    'field': 'category.keyword',
                }
            },
            'year-agg': {
                'date_histogram': {
                    'field': 'updated_at',
                    'calendar_interval': 'year',
                    'format': 'yyyy',
                },
            },
        },
        size=5,
        from_=from_
    )
    aggs = {
        'Category': {
            bucket['key']: bucket['doc_count']
            for bucket in results['aggregations']['category-agg']['buckets']
        },
        'Year': {
            bucket['key_as_string']: bucket['doc_count']
            for bucket in results['aggregations']['year-agg']['buckets']
            if bucket['doc_count'] > 0
        },
    }
    return render_template('index.html', results=results['hits']['hits'],
                           query=query, from_=from_,
                           total=results['hits']['total']['value'], aggs=aggs)




@app.get('/document/<id>')
def get_document(id):
    document = es.retrieve_document(id)
    title = document['_source']['name']
    paragraphs = document['_source']['content'].split('\n')
    return render_template('document.html', title=title, paragraphs=paragraphs)

@app.cli.command()
def reindex():
    """Regenerate the Elasticsearch index."""
    response = es.reindex()
    print(f'Index with {len(response["items"])} documents created '
          f'in {response["took"]} milliseconds.')

# adding filter use case: category of the source
# def extract_filters(query):
#     filters = []

#     filter_regex = r'category:([^\s]+)\s*'
#     m = re.search(filter_regex, query)
#     if m:
#         filters.append({
#             'term': {
#                 'category.keyword': {
#                     'value': m.group(1)
#                 }
#             }
#         })
#         query = re.sub(filter_regex, '', query).strip()

#     return {'filter': filters}, query

# adding range filters, use case: year
def extract_filters(query):
    filters = []

    filter_regex = r'category:([^\s]+)\s*'
    m = re.search(filter_regex, query)
    if m:
        filters.append({
            'term': {
                'category.keyword': {
                    'value': m.group(1)
                }
            },
        })
        query = re.sub(filter_regex, '', query).strip()

    filter_regex = r'year:([^\s]+)\s*'
    m = re.search(filter_regex, query)
    if m:
        filters.append({
            'range': {
                'updated_at': {
                    # gte is lower bound and lte is upper bound parameters
                    'gte': f'{m.group(1)}||/y',
                    'lte': f'{m.group(1)}||/y',
                }
            },
        })
        query = re.sub(filter_regex, '', query).strip()

    return {'filter': filters}, query
