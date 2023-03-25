import json
import uos as os

class Configurator:
    def __init__(self, fname):
        self._fname = fname
        self.config = self._load()

    def get_config_str(self):
        cnf = ""
        for i in self.config:
            cnf += "{}:{},".format(i, self.config[i])
        return cnf[:-1]

    def update(self, cfgs):
        if isinstance(cfgs, str):
            try:
                c = cfgs.split(",")
                for cnf in c:
                    kv = cnf.split(':')
                    self.config.update({kv[0]: kv[1]})
            except:
                print("Error: Invalid configuration string.")
        elif isinstance(cfgs, dict):
            self.config = cfgs
        else:
            print("Error: Invalid input for updating configuration.")
        self._save()

    def _load(self):
        if self._fname in os.listdir():
            with open(self._fname, 'r') as infile:
                try:
                    return json.loads(infile.read())
                except ValueError:
                    print("Error: Configuration file contains invalid JSON.")
                    return dict()
        else:
            with open(self._fname, 'w') as infile:
                return dict()

    def _save(self):
        with open(self._fname, 'w') as outfile:
            outfile.write(json.dumps(self.config))