import codecs
import re
import unicodedata
import sys



if __name__ == "__main__":
    argvs = sys.argv
    argc = len(argvs)
    if (argc != 3):
        print('Usage: # python %s Input_FileName Output_FileName' % argvs[0])
        quit()

    fin_name = argvs[1]
    fout_name = argvs[2]

    fin = codecs.open(fin_name, "r", "sjis")
    fout = codecs.open(fout_name, "w", "utf-8")

    for line in fin:
        line = line.rstrip().split(':')

        word = line[0]

        # ja
        # score = line[3]
        # en
        score = line[2]

        word = unicodedata.normalize('NFKC', word)
        word = word.lower()

        fout.write("%s,%s\n" % (word, score))

    fin.close()
    fout.close()
