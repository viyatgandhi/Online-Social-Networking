"""
collect.py
"""
from TwitterAPI import TwitterAPI
import configparser
import pickle
import time
import datetime
import sys

def get_twitter(config):
    twitter = TwitterAPI(
                   config.get('twitter', 'consumer_key'),
                   config.get('twitter', 'consumer_secret'),
                   config.get('twitter', 'access_token'),
                   config.get('twitter', 'access_token_secret'))
    return twitter

def get_tweets(twitter,no_tweets,search_keyword):
    tweets = []
    users = []
    idx=0;
    print("total number tweets to fetch are: %d" % no_tweets)
    print("keyword to search in tweets: %s" % search_keyword)

    while  len(tweets) < no_tweets:
        until=(datetime.datetime.now()-datetime.timedelta(days=idx)).strftime('%Y-%m-%d')
        #print("until for fetching set to: %s and loop count is %d" % (until,idx+1))
        for res in robust_request(twitter, 'search/tweets', {'q': search_keyword, 'count': 100 , 'lang': 'en','until':until}):
            #if res['user']['screen_name'] not in users and res['retweet_count']==0:
            #if res['retweet_count']==0:
            if res['user']['screen_name'] not in users:
                users.append(res['user']['screen_name'])
                tweets.append(res)
                if len(tweets) % 50 == 0:
                    print('%d tweets fetched' % len(tweets))
                    #print('sleeping for 10 second before next request')
                    outputfile = open('newmytweets.pkl', 'wb')
                    pickle.dump(tweets, outputfile)
                    outputfile.close()
        idx +=1
        if idx >= 8:
            print("max limit reached for fetching tweets")
            print("tweets collected are %s , rest of the program will run on this tweets data" % len(tweets))
            print("if require more tweets please run program again for keyword which is more common")
            break

    print('fetched %d tweets from unique users' % len(tweets))
    print ("tweets saved to pickle file newmytweets.pkl")
    return tweets

def get_friends(tweets,twitter,limit_users,internalData):
    print ("limiting user info as lookup for /friends/ids will take long time to fetch data for all user")
    print ("user limit to fetch is: %d , you can change the limit in twitter.cfg for paramter clusterUserLimit" % limit_users)
    if internalData == "False":
        print("Total tweets with unique users are: %d" % len(tweets))
        snlist = list(set(d['user']['screen_name'] for d in tweets[:limit_users]))
        users = [{'screen_name':s} for s in snlist]
        print("Starting to get following(friends ids) according to user limit set in twitter.cfg :"+str(len(snlist)))
        userFidsDict = {}
        #print(snlist)
        #print(users)
        for user in users:
            friendids = robust_request(twitter, 'friends/ids', {'screen_name':user['screen_name'], 'count': 5000})
            fids = friendids.json()
            sfids = sorted(fids['ids'])
            userFidsDict[user['screen_name']] = sfids
            if len(userFidsDict) % 5 == 0:
                print('%d friends ids fetched' % len(userFidsDict))
            outputfile = open('newmyusers.pkl', 'wb')
            pickle.dump(userFidsDict, outputfile)
            outputfile.close()

        print ("followers ids saved to pickle file newmyusers.pkl")

def search_tweet_time_required(twitter):
    rate_limit = twitter.request('application/rate_limit_status')
    tlist = [r for r in rate_limit]
    return str(datetime.datetime.fromtimestamp(tlist[0]['resources']['search']['/search/tweets']['reset']) - datetime.datetime.now()).split(':')

def friends_ids_time_required(twitter):
    rate_limit = twitter.request('application/rate_limit_status')
    tlist = [r for r in rate_limit]
    return str(datetime.datetime.fromtimestamp(tlist[0]['resources']['friends']['/friends/ids']['reset']) - datetime.datetime.now()).split(':')

def robust_request(twitter, resource, params, max_tries=50):
    for i in range(max_tries):
        request = twitter.request(resource, params)
        if request.status_code == 200:
            return request
        else:
            print('Got error %s \nneed to sleep for some time.' % request.text)
            sys.stderr.flush()
            if resource == "search/tweets":
                remaining_time = search_tweet_time_required(twitter)
                print ('We need to wait for %s Hours %s minutes and %s seconds before your next search/tweets API request' % (remaining_time[0], remaining_time[1], remaining_time[2]))
                print ('sleeping...')
                time.sleep(1 + (65 * int(remaining_time[1])))
            elif resource == "friends/ids":
                remaining_time = friends_ids_time_required(twitter)
                print ('We need to wait for %s Hours %s minutes and %s seconds before your next friends/ids API request' % (remaining_time[0], remaining_time[1], remaining_time[2]))
                print ('sleeping...')
                print ('You can exit at any time to continue to run program on retrieved data...')
                time.sleep(1 + (65 * int(remaining_time[1])))

def main():
    config =  configparser.ConfigParser()
    config.read('twitter.cfg')
    internalData = str(config.get('twitter', 'useDataFile'))

    if internalData == "True":
        print("No need to collect data as useDataFile is set to true in twitter.cfg")
        print("we will use already generated data files - collect.py - mytweets.pkl and myusers.pkl")
        print("if you still want to run collect.py please set useDataFile to true in twitter.cfg")
        print("keyword data in tweets: cubs")

        filename = 'data/mydownloadeddata/mytweets.pkl'

        readtweets = open(filename, 'rb')
        tweets = pickle.load(readtweets)
        readtweets.close()

        outputfile = open('datacollect.pkl', 'wb')
        pickle.dump(tweets, outputfile)
        outputfile.close()

    elif internalData == "False":
        print("collecting new data as useDataFile is set to false")
        twitter = get_twitter(config)
        no_tweets =  int(config.get('twitter', 'numberOfTweets'))
        search_keyword = str(config.get('twitter', 'keywordForTweets'))
        tweets = get_tweets (twitter,no_tweets,search_keyword)
        outputfile = open('datacollect.pkl', 'wb')
        pickle.dump(tweets, outputfile)
        outputfile.close()
        limit_users =  int(config.get('twitter', 'clusterUserLimit'))
        get_friends(tweets,twitter,limit_users,internalData)


if __name__ == '__main__':
    main()
