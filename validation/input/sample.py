import yaml

data = {
    'x': 123,
    'y': 123
}

with open('output.yml', 'wt') as fh:
    yaml.safe_dump(data, fh)

