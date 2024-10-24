import socket
class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://",1)
        assert self.scheme == 'http'
        if '/' not in url:
            url = url + '/'
        self.host, url= url.split('/', 1)
        self.path = '/' + url
        
    
        