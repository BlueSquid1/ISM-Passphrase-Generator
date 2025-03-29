output = []
with open('words-orig.txt') as f:
    for line in f:
        line = line.strip()
        if line.startswith('#'):
            continue
        if len(line) < 4: # only want words with 4 or more characters
            continue
        
        if line[0].isupper():
            continue
        output.append(line)

with open('words.txt', 'w') as f:
    for line in output:
        f.write(line + '\n')