import sys
import re
import json

def parse_charmap(css_file):
    with open(css_file, 'r', encoding='utf-8') as inf:
        css_content = inf.read()

    charmap = {}

    pattern = re.compile(r'\.icofont-([\w\-]+?):before\n{\s*content:\s*"\\(\w+?)";')
    for match in pattern.finditer(css_content):
        grps = match.groups()
        charmap[grps[0]] = grps[1]

    return charmap


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.stderr.writelines(["incorrect number of arguments"])
        sys.exit(1)

    charmap = parse_charmap(sys.argv[1])

    with open(sys.argv[2], 'w', encoding='utf-8') as outf:
        json.dump(charmap, outf, indent=2)
