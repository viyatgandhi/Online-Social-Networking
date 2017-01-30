"""
classify.py
"""

import re
import pickle
import configparser
from collections import Counter, defaultdict
from itertools import chain, combinations
import glob
import numpy as np
import os
from scipy.sparse import csr_matrix
from sklearn.cross_validation import KFold
from sklearn.linear_model import LogisticRegression

def get_unique_tweets(filename):
    print("getting unique tweets from pickle file")
    readtweets = open(filename, 'rb')
    tweets = pickle.load(readtweets)
    readtweets.close()
    utlist = set()
    for t in tweets:
        utlist.add(t['text'].encode('utf8').decode('unicode_escape').encode('ascii','ignore').decode("utf-8"))
    print("found %d unique tweets from file" % len(utlist))

    return list(utlist)

def get_afinn_sentiment(affin_filename):
    print("forming pos and neg word list from affin sentiment file")
    pos = []
    neg = []
    with open(affin_filename) as f:
        for line in f:
            tl = re.split(r'\t+', line.rstrip('\t'))
            if int(tl[1]) > 0:
                pos.append(tl[0].encode('ascii','ignore').decode("utf-8"))
            elif int(tl[1]) < 0:
                neg.append(tl[0].encode('ascii','ignore').decode("utf-8"))

    return pos,neg

def dsum(*dicts):
    ret = defaultdict(int)
    for d in dicts:
        for k, v in d.items():
            ret[k] += v
    return dict(ret)

def read_data(path):
    fnames = sorted([f for f in glob.glob(os.path.join(path, 'pos', '*.txt'))])
    data = [(1, open(f).readlines()[0]) for f in sorted(fnames[:1000])]
    fnames = sorted([f for f in glob.glob(os.path.join(path, 'neg', '*.txt'))])
    data += [(0, open(f).readlines()[0]) for f in sorted(fnames[:1000])]
    data = sorted(data, key=lambda x: x[1])
    return np.array([d[1] for d in data]), np.array([d[0] for d in data])

def tokenize(doc):
    tnp = []
    for x in doc.lower().split():
        tnp.append(re.sub('^\W+', '',re.sub('\W+$', '',x)))
    #return tnp
    return np.array(tnp)

def token_features(tokens, feats,pos,neg):
    feats.update(dsum(dict(Counter(Counter(["token=" + s for s in tokens]))),feats))

def token_pair_features(tokens,feats,pos,neg):
    k=3
    for i in range(len(tokens)-k+1):
        for e in list(combinations(list(tokens[i:k+i]), 2)):
            feats['token_pair='+e[0]+'__'+e[1]] += 1

def lexicon_features(tokens,feats,pos_words,neg_words):
    feats.update(dsum(dict(Counter({'pos_words': len([x for x in list(s.lower() for s in tokens) if x in pos_words]) , 'neg_words' : len([x for x in list(s.lower() for s in tokens) if x in neg_words]) })),feats))

def featurize(tokens,feature_fns,pos,neg):
    feats = defaultdict(lambda : 0)
    for fn in feature_fns:
        fn(tokens,feats,pos,neg)
    return sorted(list(feats.items()), key=lambda x: (x[0]))

def vectorize(tokens_list,pos,neg,vocab=None):
    feature_fns = [token_pair_features,lexicon_features]
    #feature_fns = [token_pair_features,lexicon_features,token_features]
    min_freq = 2

    vf = []
    vocabSec = {}

    for t in tokens_list:
        vf.append(list(featurize(t,feature_fns,pos,neg)))

    if vocab is None:
        vocabSec = {i:x for x,i in enumerate(sorted(list([k for k,v in dict(Counter(list([e[0] for e in list(chain(*vf)) if e[1]>0]))).items() if v >=min_freq])))}
    else:
        vocabSec = vocab

    column=[]
    data=[]
    rows=[]

    row=0
    for f in vf:
        for e in f:
            if e[0] in vocabSec:
                rows.append(row)
                column.append(vocabSec[e[0]])
                data.append(e[1])
        row+=1

    data=np.array(data,dtype='int64')
    rows=np.array(rows,dtype='int64')
    column=np.array(column,dtype='int64')
    X=csr_matrix((data, (rows,column)), shape=(len(tokens_list), len(vocabSec)))

    #print (X.toarray())
    #print (sorted(vocabSec.items(), key=lambda x: x[1]))

    # for x in vocabSec:
    #     x1 = re.sub('token=', '', x)
    #     line = re.sub('token_pair=', '', x1)
    #     print(line.encode('ascii','ignore').decode("utf-8"))

    return X,vocabSec

def fit_train_classifier(docs, labels,pos,neg):
    tokens_list = [ tokenize(d) for d in docs ]
    X,vocab = vectorize(tokens_list,pos,neg)
    model = LogisticRegression()
    model.fit(X,labels)

    return model,vocab

def parse_test_data(tweets,vocab,pos,neg):
    tokenslist = [ tokenize(d) for d in tweets ]
    X_test,vocb=vectorize(tokenslist,pos,neg,vocab)
    return X_test

def print_classification(tweets,X_test,clf):
    predicted = clf.predict(X_test)
    saveclassifydata = {}
    print("Number of pos and neg tweets: "+str(Counter(predicted)))
    for idx,t in  enumerate(tweets[:10]):
        label = ''
        if predicted[idx] == 1:
            label = "Positive"
            saveclassifydata['positivetweet'] = t
        elif predicted[idx] == 0:
            label = "Negative"
            saveclassifydata['negativetweet']  = t
        print("Classified as : %s Tweet Text: %s " % (label,t))

    saveclassifydata['pos'] = dict(Counter(predicted))[1]
    saveclassifydata['neg'] = dict(Counter(predicted))[0]

    outputfile = open('dataclassify.pkl', 'wb')
    pickle.dump(saveclassifydata, outputfile)
    outputfile.close()


def main():
    config =  configparser.ConfigParser()
    config.read('twitter.cfg')
    internalData =  str(config.get('twitter', 'useDataFile'))
    affin_filename = 'data/affin/AFINN-111.txt'
    filename = ''
    if internalData == "True":
        print("As internalData is set to True we will use tweets in file mytweets.pkl")
        filename = 'data/mydownloadeddata/mytweets.pkl'
    elif internalData == "False":
        print("As internalData is set to False we will use new tweets file newmytweets.pkl")
        filename = 'newmytweets.pkl'
    tweets = get_unique_tweets(filename)
    pos,neg = get_afinn_sentiment(affin_filename)
    print("Total pos words are %d" % int(len(pos)))
    print("Total neg words are %d" % int(len(neg)))
    print("Reading and fitting train data")
    docs, labels = read_data(os.path.join('data', 'train'))
    clf, vocab = fit_train_classifier(docs,labels,pos,neg)
    print ("Length of vocab is %d" % int(len(vocab)))
    X_test = parse_test_data(tweets,vocab,pos,neg)
    print_classification(tweets,X_test,clf)

if __name__ == '__main__':
    main()
