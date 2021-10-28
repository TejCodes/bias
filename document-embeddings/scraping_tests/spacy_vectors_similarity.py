'''
Requirements:
python -m spacy download en_core_web_md

Similarity is determined by comparing word vectors or “word embeddings”, 
multi-dimensional meaning representations of a word.

spaCy is able to compare two objects, and make a prediction of how similar they are. 
'''

import spacy
nlp = spacy.load("en_core_web_md")


def test_1(text):
    tokens = nlp(text)
    print("Test_1 with {}".format(text))
    print("Token Text, Token Has_Vector, Token Vector_Norm, Token Is_OOV")
    for token in tokens:
        print(token.text, token.has_vector, token.vector_norm, token.is_oov)


def test_2(text):
    tokens = nlp(text)
    print("Test_2 with {}".format(text))
    print("Token 1 Text, Token 2 Text, Token1-Token2 Similarity")
    for token1 in tokens:
        for token2 in tokens:
            print(token1.text, token2.text, token1.similarity(token2))

if __name__ == '__main__':
   test_1("dog cat banana afskfsd")
   test_2("dog cat banana")
