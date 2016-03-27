import codecs
import re
import unicodedata
import sys


year = re.compile('[0-9]{4}')
alias = re.compile(r'_\(.*?\)')
alldigitalphabet = re.compile(r'^[0-9a-zA-Z]+$')
controll_chars = [chr(i) for i in range(0, 32)]

def isValid(word):
    """wordが登録対象の単語のときTrueを返す"""
    # 1文字の単語は登録しない
    if len(word) == 1:
        return False
    # 年(西暦)は登録しない
    if re.search(year, word):
        return False
    # コジコジ_(小惑星)のように別名は登録しない wikipedia
    if alias.search(word) != None:
        return False
    # 英数字だけの単語は登録しない
    if alldigitalphabet.search(word) != None:
        return False
    # 仮名2文字の単語は登録しない
    if len(word) == 2 and unicodedata.name(word[0])[0:8] == "HIRAGANA" and unicodedata.name(word[1])[0:8] == "HIRAGANA":
        return False
    # 制御文字が含まれる場合登録しない hatena
    for ng_ch in controll_chars:
        if ng_ch in word:
            return False
    # 仮名、漢字、数字、英字以外の文字を含む単語は登録しない
    for c in word:
        if not (unicodedata.name(c)[0:8] == "HIRAGANA" or
                unicodedata.name(c)[0:8] == "KATAKANA" or
                unicodedata.name(c)[0:3] == "CJK" or
                unicodedata.name(c)[0:5] == "DIGIT" or
                unicodedata.name(c)[0:5] == "LATIN"):
            return False
    return True

if __name__ == "__main__":
    argvs = sys.argv
    argc = len(argvs)
    if (argc != 4):
        print('Usage: # python %s Keyword_Type Input_FileName Output_FileName' % argvs[0])
        quit()

    keyword_type = argvs[1]
    if (keyword_type not in ['hatena', 'wikipedia', 'pntable']):
        print('Keyword_Type is hatena or wikipedia or pntable')
        quit()

    fin_name = argvs[2]
    fout_name = argvs[3]

    in_char = 'utf-8' if keyword_type == 'pntable' else 'utf-8'
    with open(fout_name, mode='w', encoding='utf-8') as fout:
        with open(fin_name, mode='r', encoding=in_char) as fin:
            for line in fin:
                # Wikipedia見出し語を整形
                if keyword_type == 'wikipedia':
                    word = line.rstrip()
                # Hatena
                elif keyword_type == 'hatena':
                    word = line[:-1].split('\t')[1]
                # PNtable
                elif keyword_type == 'pntable':
                    word = line.split(':')[0]

                word = unicodedata.normalize('NFKC', word)
                word = word.lower()

                if keyword_type in ['hatena', 'wikipedia']:
                    if isValid(word):
                        cost = int(max(-36000, -400 * len(word)**1.5))
                        fout.write("%s,-1,-1,%d,名詞,一般,*,*,*,*,*,*,*,%s\n"
                                   % (word, cost, keyword_type))
