from json import loads, dumps


class Configurator:
    def __init__(self, fname):
        self._fname = fname
        self.config = self._load()

    def get_config_str(self):
        cnf = ""
        for i in self.config:
            cnf += i + ":"
            cnf += str(self.config[i]) + ","
        return cnf[:-1]

    def update(self, cfgs):
        if isinstance(cfgs, str):
            try:
                c = cfgs.split(",")
                for cnf in c:
                    kv = cnf.split(':')
                    self.config.update({kv[0]: int(kv[1])})
            except:
                pass
        elif isinstance(cfgs, dict):
            self.config.update(cfgs)
        self._save()

    def _load(self):
        with open(self._fname, 'r') as infile:
            return loads(infile.read())

    def _save(self):
        with open(self._fname, 'w') as outfile:
            outfile.write(dumps(self.config))

