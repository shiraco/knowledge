from tweepy import OAuthHandler, API, Cursor
import sys

from settings import consumer_key, consumer_secret, access_token, access_token_secret


class TweetCollector():

    ITEM_BATCH_SIZE = 200
    MAX_ITEM_LIMIT = 4000

    def __init__(self):
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = API(auth)

    def user_timeline(self, twitter_id):
        statuses = Cursor(self.api.user_timeline, id=twitter_id, count=self.ITEM_BATCH_SIZE).items(self.MAX_ITEM_LIMIT)
        statuses = [tweet for tweet in statuses]
        return Statuses(statuses)

    def favorites(self, twitter_id):
        statuses = Cursor(self.api.favorites, id=twitter_id, count=self.ITEM_BATCH_SIZE).items(self.MAX_ITEM_LIMIT)
        statuses = [tweet for tweet in statuses]
        return Statuses(statuses)


class Statuses():

    OUT_DIR = 'data/out/'

    def __init__(self, statuses):
        self.statuses = statuses

    def to_csv(self, file):
        import pandas as pd

        tweets = [{'tweet_id': obj.id,
                   'timestamp': obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                   'text': obj.text,
                   'retweeted_status_id': obj.retweeted_status.id if hasattr(obj, 'retweeted_status') else None}
                  for obj in self.statuses]

        tweets = pd.DataFrame(tweets, columns=['tweet_id', 'timestamp', 'text', 'retweeted_status_id'])
        tweets = tweets.sort('timestamp', ascending=False)
        tweets = tweets.drop_duplicates(subset=['tweet_id'])
        tweets.to_csv(self.OUT_DIR + file)


if __name__ == '__main__':

    argvs = sys.argv
    argc = len(argvs)
    if len(argvs) != 2:
        print('Usage: # python %s TWITTER_ACCOUNT_NAME' % argvs[0])
        quit()

    # twitter screen name
    target_screen_name = argvs[1]

    tc = TweetCollector()

    tc.user_timeline(target_screen_name).to_csv('tweets_' + target_screen_name + '_user_timeline.csv')
    tc.favorites(target_screen_name).to_csv('tweets_' + target_screen_name + '_favorites.csv')
