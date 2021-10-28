import json
import os

from gensim.models.doc2vec import Doc2Vec

from doc2vec_prep import stem_text

if __name__ == "__main__":
    my_path = os.path.dirname(__file__)
    with open(os.path.join(my_path, 'UoE_staff.json')) as f:
        people = json.load(f)
    model = Doc2Vec.load(os.path.join(my_path, 'doc2vec_v2.model'), mmap='r')

    test_doc = ''' 
DARE will deliver a new working environment for the teams of professionals wrestling with the challenge of extreme data, computing and complexity. It will present methods, in abstract terms, so that domain experts can understand, change and use them effectively. It will provide a set of tools that visualise the runs of these methods in summary form still without distracting technical detail. Those tools will allow drill down for diagnostics and validation, and help with the organisation of campaigns involving multiple runs and immense amount of data. This holistic abstract presentation together with automation that eliminates chores will push back the complexity barrier, accelerate innovation and improve the productivity of our hard-pressed expert teams. The data-scale barrier will be pushed by a combination of optimised mappings and automation. To achieve this, we depend on learning the critical parameters in the cost functions dynamically, taking into account data movement, storage costs, limits and other resource costs in formulae weighted by community choices and priorities. The computational scale barrier will be pushed by a similar strategy. However, the methods we enable often have a mixture of computationally challenging parts and data challenging parts, best allocated to different platforms. In today’s R&D the practitioners have to organise this and the inherent data movement themselves. DARE’s optimised mappings will automatically partition parts of the work to different platforms and organise the coupled use of those platforms including any necessary data movements and adaptations. Most professional R&D requires sustained use of such methods. Sustaining their meaning across platforms means that working practices do not need to change and that the original investment in learning and in method development is retained. DARE will work with two research infrastructures: EPOS (European Plate Observing System) and IS-ENES (Infrastructure for the European Network of Earth System Modelling), engaging in the co-design and production use of extreme methods that address these challenges. With our partners, we will show:Accelerated innovation in the face of all three extremes. Significantly increased productivity for expert teams and a wide range of users. Substantial advances in the science and applications achievable in campaigns.'''

    vector = model.infer_vector(stem_text(test_doc))
    simdocs = model.docvecs.most_similar(positive=[vector])
    
    for simdoc in simdocs:
        person_id = simdoc[0]
        similarity = simdoc[1]
        print(people[person_id]['name'])
        
