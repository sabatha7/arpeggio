

class StorageAPI:
    def __init__(self, json):
        self.json = json

    def load_json(self, path_to_file, json_map = {}):

        try:
            json_map = self.json.load(open(path_to_file, 'rt'))
        except IOError:
            logger.error("cannot load json required")
        return json_map

    def save_json(self, python_map, fn):

        j = self.json.dumps(python_map)
        with open(fn, 'w') as f:
            f.write(j)
            f.close()
