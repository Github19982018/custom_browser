class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://")