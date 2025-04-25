from ConfigLoader import ConfigLoader

class DeBug:
    def __init__(self):
        loader = ConfigLoader()
        self.is_debug = loader.get("is_debug", False)

    def print(self, message):
        if self.is_debug:
            print(f"[DEBUG] {message}")
