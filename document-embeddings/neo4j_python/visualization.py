import networkx as nx
import json
import os
import matplotlib.pyplot as plt

def walk(node):
    for key, item in node.items():
        for i in item:
            if i!= "type" and i!="title" and i!="similarity":
                G.add_edge(key,node[key][i])


if __name__ == "__main__":
    my_path = os.path.dirname(__file__)
    with open(os.path.join(my_path, 'Selected_documents.json')) as f:
        js = json.load(f)
    G=nx.Graph()
    for key in js.keys():
        G.add_edge('ROOT',key, color='r',weight=2)
    walk(js)
    color_map = []
    node_size = []
    for node in G:
        if node == "ROOT": 
             color_map.append('red')
             node_size.append(100)
        elif node in js.keys():
             if js[node]['type'] == "paper":
                 #papers are blue
                 color_map.append('blue')
                 node_size.append(js[node]['similarity']*10000)
             else:
                 #projects are in orange
                 color_map.append('orange')
                 node_size.append(js[node]['similarity']*10000)
        elif node != 'similarity':
            #people are green
            color_map.append('green')      
            node_size.append(100)
   
    plt.figure(figsize=(20,10))
    #comment this line if you want to have the name of the nodes
    nx.draw(G,with_labels=True, node_color=color_map, node_size= node_size)
    #comment this line if you do not want to have the name of the nodes 
    #nx.draw(G,with_labels=False, node_color=color_map)
    plt.savefig("NetworkSelectDocuments.png")
    
