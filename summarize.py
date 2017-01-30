"""
sumarize.py
"""

import pickle

file= open("datacollect.pkl", "rb")
tweets=pickle.load(file)
file.close()

file= open("datacluster.pkl", "rb")
components=pickle.load(file)
file.close()

file= open("dataclassify.pkl", "rb")
classify=pickle.load(file)
file.close()

text_file = open("summary.txt", "w")
text_file.write("Number of users collected: %s "%(len(tweets)))
text_file.write("\nNumber of messages collected: %s "%(len(tweets)))
text_file.write("\nNumber of communities discovered: %s"%(len(components['communities'])))
text_file.write("\nAverage number of users per community: %s "%(components['size']))
text_file.write("\nNumber of instances per class found: positive tweets: %d negative tweets:%d"%(classify['pos'],classify['neg']))
text_file.write("\nOne example from each class:\npositive tweet: %s \nnegative tweet: %s"%(classify['positivetweet'],classify['negativetweet']))
text_file.close()
