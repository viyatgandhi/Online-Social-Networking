# Online-Social-Networking
* Use of scikit-learn, networkx, scipy, numpy and nltk to perform real time analysis of data.

* Initially tweets are collected from twitter api using a keyword configured in file.
Use of jaccard similarity and girvan_newman algo is used for finding communities.
Tweets are classified into two classes Positive and Negative sentiment using a text classifier.
Please refer to description.txt for more information.
execute in below order:
* python collect.py
* python cluster.py
* python classify.py
* python summarize.py
