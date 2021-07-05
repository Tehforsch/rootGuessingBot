class Log:
    def __init__(self):
        self.content = ""

    def write(self, text, newline=True):
        self.content = self.content + text + ("\n" if newline else "")

    def dump(self):
        buf = self.content
        self.content = ""
        return buf
