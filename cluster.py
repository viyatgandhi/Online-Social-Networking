"""
cluster.py
"""
from itertools import combinations
import matplotlib.pyplot as plt
import configparser
import pickle
import time
import datetime
import sys
import os
import networkx as nx
import itertools
from itertools import islice
from collections import Counter

def get_friends(limit_users,internalData):
    filename = ''
    if internalData == "False":
        print("as internalData is set to false we will read from new users file: newmyusers.pkl")
        filename = 'newmyusers.pkl'
    elif internalData == "True":
        print("as internalData is set to true we will read from my users file: myusers.pkl from data/mydownloadeddata")
        filename = "data/mydownloadeddata/myusers.pkl"

    readusers = open(filename, 'rb')
    userFidsDict = pickle.load(readusers)
    readusers.close()

    if len(userFidsDict) < limit_users:
        limit_users = len(userFidsDict)

    n_items = list(islice(userFidsDict.items(),limit_users))
    userFidsDict = dict(n_items)
    return userFidsDict

def jaccard_similarity(x,y):
    if len(x)>0 and len(y)>0:
	       return len(set.intersection(*[set(x), set(y)]))/len(set.union(*[set(x), set(y)]))
    else:
        return 0

def create_graph(users):

    graph = nx.Graph()
    userlist = list(users.keys())
    for u in userlist:
        graph.add_node(u)

    for u in combinations(userlist,2):
        fid1 = [users[u[0]]]
        fid2 = [users[u[1]]]
        ew = jaccard_similarity(fid1[0],fid2[0])
        if ew > 0.009 :
            graph.add_edge(u[0],u[1],weight=ew)

    remove = [node for node,degree in graph.degree().items() if degree <= 1]
    graph.remove_nodes_from(remove)
    print("Removed %d nodes from graph as they had less than 1 degree to reduce clutter in graph" % int(len(remove)))
    print("Also edge weight threshold is set to 0.009 to reduce clutter in graph")

    return graph

def find_best_edge(graph):
    centrality = nx.edge_betweenness_centrality(graph, weight='weight')
    return max(centrality, key=centrality.get)

def get_communities(G,no_communities):
    print("Total communities to identify are: %d" % no_communities )
    print("Graph has %d nodes and %d edges" % (int(G.number_of_nodes()),int(G.number_of_edges())))
    components = [c for c in nx.connected_component_subgraphs(G)]
    count = 0
    while len(components) < no_communities:
        edge_to_remove = find_best_edge(G)
        #print('removing ' + str(edge_to_remove))
        G.remove_edge(*edge_to_remove)
        components = [c for c in nx.connected_component_subgraphs(G)]
        count +=1

    result = [c.nodes() for c in components]
    #print('components=' + str(result))
    print("Total edges removed by girvan_newman algo from graph are: "+str(count))
    return result

def main():
    config =  configparser.ConfigParser()
    config.read('twitter.cfg')
    no_communities = int(config.get('twitter', 'communities'))
    limit_users =  int(config.get('twitter', 'clusterUserLimit'))
    internalData =  str(config.get('twitter', 'useDataFile'))
    userinfo = get_friends(limit_users,internalData)
    graph = create_graph(userinfo)
    result = get_communities(graph,no_communities)
    saveclusterdata = {}
    #print('resulting communities are :' + str(result))
    total_users = graph.number_of_nodes()
    communities_list_count = dict(Counter([len(l) for l in result]))
    #print("Count of communities by users is: "+ str(communities_list_count))
    size = str(total_users*(sum((d[0]*d[1])/total_users for d in communities_list_count.items())/no_communities))
    print('Average number of users per community :'+ size )
    saveclusterdata['communities']  = result
    saveclusterdata['size']  = size
    outputfile = open('datacluster.pkl', 'wb')
    pickle.dump(saveclusterdata, outputfile)
    outputfile.close()

if __name__ == '__main__':
    main()
