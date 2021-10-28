import operator
import json
import os

#algorithm that returns the recommended people based on the number of papers/projects and similarities values.


if __name__ == "__main__":
    my_path = os.path.dirname(__file__)
    with open(os.path.join(my_path, 'Selected_documents.json')) as f:
        js = json.load(f)
    authors={}
    for document in js.keys():
        similarity = js[document]["similarity"]
        for elem in js[document]:
            if elem!="title" and elem!="similarity" and elem!="type":
                 author_name=js[document][elem]
                 if author_name not in authors:
                     authors[author_name]= []
                 authors[author_name].append(similarity)


    x_authors_a={}
    for author in authors:
        sim_a=0
        for sim in authors[author]:
            sim_a+=sim
        x_authors_a[author]=sim_a

    total_sim=0
    for author in x_authors_a:
        total_sim+=x_authors_a[author]
 
    x_authors_b={}
    for author in x_authors_a:
        x_authors_b[author]=x_authors_a[author]/total_sim

    x_authors_sorted = sorted(x_authors_b.items(), key=operator.itemgetter(1), reverse=True)
    print(x_authors_sorted)
