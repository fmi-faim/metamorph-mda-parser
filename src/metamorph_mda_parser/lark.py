from lark import Lark, Transformer


class NDInfoTransformer(Transformer):
    def __init__(self):
        self.wave_names = []
        self.wave_do_z = []
        self.stage_positions = []

    def start(self, items):
        result = dict(i for i in items if i is not None)
        result["WaveNames"] = self.wave_names
        result["WaveDoZ"] = self.wave_do_z
        result["StagePositions"] = self.stage_positions
        return result

    def line(self, key_value):
        key, value = key_value
        if key.startswith("WaveName"):
            self.wave_names.append(value)
            return None  # We handle WaveName entries separately
        if key.startswith("Stage"):
            self.stage_positions.append(value)
            return None  # We handle Stage entries separately
        if key.startswith("WaveDoZ"):
            self.wave_do_z.append(value)
            return None  # We handle WaveDoZ entries separately
        return (key, value)

    def boolean_value(self, b):
        return b[0].value == "TRUE"


def parse(content):
    parser = Lark.open("nd_grammar.lark", rel_to=__file__, parser="lalr", transformer=NDInfoTransformer())
    return parser.parse(content)
