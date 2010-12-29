import sys, re

if len(sys.argv) < 2:
    print "Usage - %s filename" %sys.argv[0]

f = open(sys.argv[1])

freq = {}
for line in f:
    line = re.sub(r'[,!;?\'" ()-=/]+', " ", line.lower())
    words = line.strip().split()
    
    for key in words:
        if key in freq:
            freq[key] += 1
        else:
            freq[key] = 1

words = [(freq[word], word) for word in freq]
print words[:10]

hi_freq = sorted(words, reverse=True)

colors = ["red", "blue", "green", "yellow", "white", "black", "purple", "pink", "orange", "brown", "violet", "indigo"]

for freq, word in hi_freq:
    if [word for color in colors if word.startswith(color)]:
        print "%10s  %4s" %(word, freq)


