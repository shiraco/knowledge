import os
import sys
import re
import unicodedata

import MeCab
import pandas as pd
from gensim import corpora, models
from gensim.utils import any2unicode
import requests
import json


class Cleanser():

    @staticmethod
    def cleanse_input(string):
        # Convert a string (bytestring in encoding or unicode), to unicode.
        cleansed = any2unicode(string)

        # remove URL
        cleansed = re.sub(r'(?:^|[\s　]*)((?:https?|ftp)://[\w/:%#\$&\?\(\)~\.=\+\-]+)', '，', cleansed)

        # remove tag
        cleansed = re.sub(r'<(\".*?\"|\'.*?\'|[^\'\"])*?>', ' ', cleansed)

        cleansed = re.sub('[\.:/]', ' ', cleansed)

        # unicode正規化（半角カナ→全角カナなど）
        # https://gist.github.com/ikegami-yukino/8186853
        cleansed = unicodedata.normalize('NFKC', cleansed)

        # 英字小文字変換
        cleansed = cleansed.lower()

        # 連続スペース圧縮
        cleansed = re.sub(r' +', ' ', cleansed)

        # 連続カンマ圧縮
        cleansed = re.sub(r',+', '，', cleansed)

        return cleansed

    @staticmethod
    def cleanse_output(string):

        # Convert a string (bytestring in encoding or unicode), to unicode.
        cleansed = any2unicode(string)

        cleansed = re.sub(r'[，  ]+', ' ', cleansed)

        return cleansed


class CompoundWords(MeCab.Tagger, Cleanser):

    def __init__(self, args='-Ochasen -u data/dic/original.dic'):

        MeCab.Tagger.__init__(self, args)
        self.all_digit_alphabet = re.compile(r'^[0-9a-zA-Z_\-@#]+$')
        self.tag_df = pd.read_csv('data/table/pn_score_all.csv', header=None, names=['word', 'score'])
        self.tag_list = self.tag_df['word'].tolist()
        self.tag_score_dict = self.tag_df.set_index('word').to_dict()['score']

    def wakatis(self, sentences):

        result = []
        for sentence in sentences:
            # 空要素の除去
            if isinstance(sentence, list):
                while sentence.count('') > 0:
                    sentence.remove('')
            if self.all_digit_alphabet.search(sentence) is not None:
                result.append(sentence)
            elif sentence != '':
                result.append(self.wakati(sentence))

        return ' '.join(result)

    def wakati(self, sentence):

        p = self.parseToNode(self.cleanse_input(sentence))
        out = []
        while p is not None:
            feature = tuple(p.feature.rsplit(','))
            pos = feature[0]

            if pos in ['名詞', '動詞', '形容詞', '副詞']:
                out.append(p.surface)

            p = p.next

        return self.cleanse_output(' '.join(out))

    @staticmethod
    def pre_filter(text):

        # TODO URL は除外するようにする

        # 特定のパターンの前後にスペースを入れる
        text = re.sub(r'([^a-zA-Z0-9_@]@[a-zA-Z0-9_]+)', r' \1 ', text)
        text = re.sub(r'#', r' ', text)
        text = text.strip()

        # unicode正規化（半角カナ→全角カナなど）
        # https://gist.github.com/ikegami-yukino/8186853
        text = unicodedata.normalize('NFKC', text)

        # 英字小文字変換
        text = text.lower()

        return text

    @staticmethod
    def concatenate(text_list):
        """
        text_list を連結したtext を戻す
        """
        result_text = ' '.join(text_list)
        return result_text


class Tweets():

    def __init__(self):
        self.cw = CompoundWords()
        self.dictionary = None

    def wakati(self, tweet_series, name='wakati_tweet'):

        result_series = tweet_series
        result_series = result_series.map(lambda x: self.cw.pre_filter(x))
        result_series = result_series.str.split(r'\s+|"|\'|、|。|\?|!|\[|\]|\(|\)|\\|「|」')
        result_series = result_series.map(lambda x: self.cw.wakatis(x))
        result_series.name = name

        return result_series

    def create_dictionary(self, token_list):

        self.dictionary = corpora.Dictionary(token_list)

        return self.dictionary

    @staticmethod
    def tokenize(tweet_series, name='tweets_words'):

        result_series = tweet_series
        result_series = result_series.str.strip().str.split(r'\s+')
        # result_series.map(lambda x: x.remove(''))
        result_series.name = name

        return result_series

    @staticmethod
    def bow(tweet_list):

        result_list = tweet_list
        result_list = [sorted(tweet_info, key=lambda x: (-x[1], x[0])) for tweet_info in result_list]

        return result_list

    @staticmethod
    def tfidf(tweet_list, lower_limit=0.1):

        result_list = tweet_list
        result_list = [sorted(tweet_info, key=lambda x: (-x[1], x[0])) for tweet_info in result_list]

        # filter
        tweets_tfidf_top100w = []
        for tweet_info in result_list:
            tweets_tfidf_top100w.append([w for w in tweet_info if w[1] > lower_limit])
        result_list = tweets_tfidf_top100w

        return result_list

    @staticmethod
    def lsi(tweet_list):

        result_list = tweet_list
        result_list = [sorted(tweet_info, key=lambda x: (-x[1], x[0])) for tweet_info in result_list]

        return result_list

    @staticmethod
    def lda(tweet_list):

        result_list = tweet_list
        result_list = [sorted(tweet_info, key=lambda x: (-x[1], x[0])) for tweet_info in result_list]

        return result_list

    def disp_series(self, tweet_list, name, dictionaried=True, rounded=False):

        result_list = tweet_list
        if dictionaried:
            if rounded:
                result_list = [[(self.dictionary[w[0]], '%.3f' % round(w[1], 3)) for w in tweet_info] for tweet_info in result_list]
            else:
                result_list = [[(self.dictionary[w[0]], w[1]) for w in tweet_info] for tweet_info in result_list]
                if rounded:
                    result_list = [[(w[0], '%.3f' % round(w[1], 3)) for w in tweet_info] for tweet_info in result_list]
                else:
                    result_list = [[(w[0], w[1]) for w in tweet_info] for tweet_info in result_list]
        else:
            pass

        result_series = pd.Series(result_list, name=name)

        return result_series

    @staticmethod
    def extract_named_entity(sentence):
        url = 'https://labs.goo.ne.jp/api/entity'

        payload = {'app_id': os.environ.get('GOO_APP_ID'), 'sentence': sentence}
        headers = {'Accept': 'application/json', 'content-type': 'application/json'}

        r = requests.post(url, data=json.dumps(payload), headers=headers)

        return r.json()['ne_list']





if __name__ == '__main__':

    argvs = sys.argv
    argc = len(argvs)
    if len(argvs) != 2:
        print('Usage: # python %s TWITTER_ACCOUNT_NAME' % argvs[0])
        quit()

    # twitter screen name
    target_screen_name = argvs[1]

    IN_DIR = 'data/in/'
    OUT_DIR = 'data/out/' + target_screen_name + '/'
    TWEETS_COLUMN_NAME = 'text'

    # READ Tweets
    tweets_df = pd.read_csv(IN_DIR + 'tweets_' + target_screen_name + '.csv')

    # Sampling for development
    tweets_df = tweets_df[0:5000]

    tweets = Tweets()

    # 前処理＆わかち書き
    tweets_wakati_series = tweets.wakati(tweets_df[TWEETS_COLUMN_NAME].copy(), 'wakati_tweet')

    # トークン化
    tweets_words_series = tweets.tokenize(tweets_wakati_series.copy(), 'tweets_words')

    # 辞書を作成
    all_tokens = tweets_words_series.copy().tolist()
    dictionary = tweets.create_dictionary(all_tokens)
    dictionary.save_as_text(OUT_DIR + 'tweets_text.dict')

    # Bag-of-Words(=corpus)化
    corpus = [dictionary.doc2bow(tweet) for tweet in all_tokens]
    tweets_bow = corpus.copy()
    tweets_bow = tweets.bow(tweets_bow)
    tweets_bow_series = tweets.disp_series(tweets_bow, name='bow_score', dictionaried=True, rounded=False)
    tweets_bow_series.to_csv(OUT_DIR + 'tweets_bow.txt', index=False)

    sum_tweets_bow = []
    [sum_tweets_bow.extend(tweets_bow_list) for tweets_bow_list in tweets_bow_series]
    sum_tweets_bow = sorted(sum_tweets_bow, key=lambda x: (-int(x[1])))
    with open(OUT_DIR + 'sum_bow_score_' + target_screen_name + '.csv', 'w') as f:
        [f.write('%s,%s\n' % (w[0], w[1])) for w in sum_tweets_bow]

    # NamedEntity
    tweets_wakati_series = tweets.wakati(tweets_df[TWEETS_COLUMN_NAME].copy(), 'wakati_tweet')


    # TF-IDF
    tfidf_model = models.TfidfModel(corpus)
    tweets_tfidf = tfidf_model[tweets_bow]
    tweets_tfidf = tweets.tfidf(tweets_tfidf)
    tweets_tfidf_series = tweets.disp_series(tweets_tfidf, name='tfidf_score', dictionaried=True, rounded=True)
    tweets_tfidf_series.to_csv(OUT_DIR + 'tweets_tfidf.txt', index=False)

    sum_tweets_tfidf = []
    [sum_tweets_tfidf.extend(tweets_tfidf_list) for tweets_tfidf_list in tweets_tfidf_series]
    sum_tweets_tfidf = sorted(sum_tweets_tfidf, key=lambda x: (-float(x[1])))
    sum_tweets_tfidf = [tweets_tfidf for tweets_tfidf in sum_tweets_tfidf if tweets_tfidf[0] != '']
    with open(OUT_DIR + 'sum_tfidf_score_' + target_screen_name + '.csv', 'w') as f:
        [f.write('%s,%s\n' % (w[0], w[1])) for w in sum_tweets_tfidf]

    # LSI
    lsi = models.LsiModel(tweets_tfidf, id2word=dictionary, num_topics=10)
    tweets_lsi = lsi[tweets_tfidf]
    tweets_lsi = tweets.tfidf(tweets_lsi)
    tweets_lsi_series = tweets.disp_series(tweets_lsi, name='lsi_score', dictionaried=False, rounded=True)

    lsi_topics = lsi.print_topics(10)
    with open(OUT_DIR + 'lsi_model_' + target_screen_name + '.txt', 'w') as f:
        [f.write('%s\n' % topic) for topic in lsi_topics]

    # LDA
    lda = models.LdaModel(tweets_tfidf, id2word=dictionary, num_topics=10)
    tweets_lda = lda[tweets_tfidf]
    tweets_lda = tweets.lda(tweets_lda)
    tweets_lda_series = tweets.disp_series(tweets_lda, name='lda_score', dictionaried=False, rounded=True)

    lda_topics = lda.print_topics(10)
    with open(OUT_DIR + 'lda_model_' + target_screen_name + '.txt', 'w') as f:
        [f.write('%s\n' % topic) for topic in lda_topics]

    sum_tweets_lsi = []
    [sum_tweets_lsi.extend(tweets_lsi_list) for tweets_lsi_list in tweets_lsi_series]
    sum_tweets_lsi = sorted(sum_tweets_lsi, key=lambda x: (-float(x[1])))
    with open(OUT_DIR + 'sum_lsi_score_' + target_screen_name + '.csv', 'w') as f:
        [f.write('%s,%s\n' % (w[0], w[1])) for w in sum_tweets_lsi]

    sum_tweets_lda = []
    [sum_tweets_lda.extend(tweets_lda_list) for tweets_lda_list in tweets_lda_series]
    sum_tweets_lda = sorted(sum_tweets_lda, key=lambda x: (-float(x[1])))
    with open(OUT_DIR + 'sum_lda_score_' + target_screen_name + '.csv', 'w') as f:
        [f.write('%s,%s\n' % (w[0], w[1])) for w in sum_tweets_lda]

    # summary
    sum_tweets_words = []
    [sum_tweets_words.extend(tweets_words_list) for tweets_words_list in tweets_words_series]
    sum_row = pd.Series(['summary', sum_tweets_words, sum_tweets_bow, sum_tweets_tfidf],
                        index=['tweet_id', 'tweets_words', 'bow_score', 'tfidf_score'], name='sum')

    # MERGE DataFrame
    tweets_df = pd.concat([tweets_df['tweet_id'],
                           tweets_df['timestamp'],
                           tweets_df[TWEETS_COLUMN_NAME],
                           tweets_wakati_series,
                           tweets_words_series,
                           tweets_bow_series,
                           tweets_tfidf_series,
                           tweets_lsi_series,
                           tweets_lda_series,
                           tweets_ne_series,
                           ],
                          axis=1)

    # tweets_df = tweets_df.append(sum_row, ignore_index=True)

    # WRITE csv file
    tweets_df.to_csv(OUT_DIR + 'tweets_wakati_' + target_screen_name + '.csv')

    # for Excel
    tweets_df = pd.read_csv(OUT_DIR + 'tweets_wakati_' + target_screen_name + '.csv')
    tweets_df['tweets_words'] = [re.sub(r',\s', ',\r', score) for score in tweets_df['tweets_words']]
    tweets_df['bow_score'] = [re.sub(r'\),\s', '),\r', score) for score in tweets_df['bow_score']]
    tweets_df['tfidf_score'] = [re.sub(r'\),\s', '),\r', score) for score in tweets_df['tfidf_score']]
    tweets_df['lsi_score'] = [re.sub(r'\),\s', '),\r', score) for score in tweets_df['lsi_score']]
    tweets_df['lda_score'] = [re.sub(r'\),\s', '),\r', score) for score in tweets_df['lda_score']]
    tweets_df.to_csv(OUT_DIR + 'tweets_wakati_view_' + target_screen_name + '.csv')
    os.system('nkf -s --overwrite %s' % OUT_DIR + 'tweets_wakati_view_' + target_screen_name + '.csv')
