"""
The purpose of this file is to accept sparql queries run them against the online datasets and return a resultset.
The dependancies are SPARQLWrapper and JSON classes. Which in turn are dependent on rdflib for python.
"""

from SPARQLWrapper import SPARQLWrapper, JSON
endpoint = SPARQLWrapper("http://dbpedia.org/sparql")#"http://14.139.155.23:8890/sparql")#"http://dbpedia.org/sparql")
#endpoint.addNamedGraph("http://localLOD.org")
query1="""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dbp: <http://dbpedia.org/property/>

       """



query2="""  
SELECT DISTINCT ?s WHERE{

?s rdfs:label ?l. ?l bif:contains "'%(name)s'". FILTER regex(?l,"%(name)s" ,"i") . FILTER (langMatches(lang(?l), "en")) . FILTER regex(?s,"^http://dbpedia.org/resource/.*","i") . FILTER regex(?s,"^http://dbpedia.org/resource/(?!Category).*","i")
}

"""


query3="""  
select distinct ?z where{
<%(resource)s> <%(prop)s> ?z
}

"""





def findAnnotation(name):
    query=query1+query2%{'name':name}
    return runSparql2(query,{'s':'value'})


def findDate(resource, prop):
    query=query1+query3%{'resource':resource, 'prop': prop}
    result = runSparql2(query,{'z':'value'})
    if len(result) == 0:
        resource = findPageRedirects(resource)[0]['z']['value']
        return findDate(resource, prop)
    else:
        return result


def findPageRedirects(resource):
    query=query1+query3%{'resource':resource, 'prop': 'http://dbpedia.org/ontology/wikiPageRedirects'}
    return runSparql2(query,{'z':'value'})


def runSparql2(queryAppend,dictionary):
    queryAppend=query1+queryAppend #Add the select statements and etc. from the calling program
    endpoint.setQuery(queryAppend)
    endpoint.setReturnFormat(JSON)
    flag=True
    while flag:
        try:
            results=endpoint.query().convert()
        except:
            continue
        flag=False
    return results["results"]["bindings"]



if __name__=='__main__':
    rlist=Trial() 
    print len(rlist)
    for r in rlist:
        print r
