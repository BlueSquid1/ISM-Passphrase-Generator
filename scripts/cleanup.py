output = []
with open('../server/data/en_US.dic') as f:
    for line in f:
        line = line.strip()
        line = ''.join(line.split('/')[:-1])
        if line.startswith('#'):
            continue
        if len(line) < 2:
            continue

        if len(line) > 8: # long words are hard to remember
            continue
        
        if line[0].isupper(): # places and names is not always common knowledge
            continue
        output.append(line)

with open('../server/data/words.txt', 'w') as f:
    for line in output:
        f.write(line + '\n')