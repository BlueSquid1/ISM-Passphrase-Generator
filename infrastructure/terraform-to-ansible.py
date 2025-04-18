import argparse
import json

parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='What the program does',
                    epilog='Text at the bottom of help')

parser.add_argument('-i', '--input', type=str, help='node details as json')
parser.add_argument('-o', '--output', type=str, help='output file name')

args = parser.parse_args()
nodeJson = args.input
output = args.output

nodes = json.loads(nodeJson)

with open(output, 'w') as f:
    for node in nodes:
        name = node['name']
        ip = node['ip_address']
        f.write(f"[{name}]\n")
        f.write(f"{ip}\n")
