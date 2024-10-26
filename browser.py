import socket
import ssl      
import gzip
import re
class URL:
    redirect = 0
    def __init__(self, url):
        self.view_source = False
        if url.startswith('view-source:'):
            self.view_source = True
            url = url.removeprefix('view-source:')
        self.scheme, url = re.split(':/*',url, maxsplit=1)
        assert self.scheme in ['http', 'https','file','data']
        if self.scheme == 'http':
            self.port = 80
        elif self.scheme == 'https':
            self.port = 443
        elif self.scheme in ['data','file'] and not url.startswith('/'):
            url = '/' + url 
        if '/' not in url:
            url = url + '/'
        self.host, url= re.split('/',url, 1)
        if ':' in self.host:
            self.host, port = self.host.split(':', 1)
            self.port =int(port)
        self.path = '/' + url
        
    def request(self):
        if self.scheme == 'file':
            path = self.path.strip('/')
            self.type = path.rsplit('.', 1)
            with open(path,'r') as response:
                content = response.read()
                return content
        elif self.scheme == 'data': 
            content = self.path.strip('/')
            self.type, content = content.split(',', 1)
            return content
        else:    
            s = socket.socket(
                family = socket.AF_INET, 
                type = socket.SOCK_STREAM,
                proto = socket.IPPROTO_TCP,
            )
            
            if self.scheme == 'https':
                ctx = ssl.create_default_context()
                s =ctx.wrap_socket(s, server_hostname=self.host)
            s.connect((self.host, self.port))
            request = 'GET {} HTTP/1.0\r\n'.format(self.path)
            request += 'Host: {}\r\n'.format(self.host)
            # request += 'Connection: close\r\n'
            request += 'User-Agent: test\r\n'
            request += 'Accept-Encoding: gzip\r\n'
            request += '\r\n'
            s.send(request.encode('utf8'))
            response = s.makefile('r', encoding='utf8', newline='\r\n')
            statusline = response.readline()
            version, status, explanation = statusline.split(' ', 2)
            if 300 <= int(status) < 400:
                if self.__class__.redirect > 3:
                    return 'too many redirects'
                self.__class__.redirect += 1
                url = response_headers['location']
                if url.startswith('/'):
                    return self.request()
                else:
                    self.__init__(url)
                    return self.request()
            response_headers = {}
            while True:
                line = response.readline()
                if line == '\r\n': break 
                header, value = line.split(':', 1)
                response_headers[header.casefold()] = value.strip()
            if response_headers.get('transfer-encoding','') == 'chunked':
                while True:
                    size = response.readline()
                    if int(size) == 0:
                        break
                    content += response.readline(int(size))
                return content
            if response_headers.get('content-encoding','') == 'gzip':
                response = s.makefile('rb', newline='\r\n')
                content = gzip.decompress(response.read())
                return content
            size = response_headers['content-length']
            content = response.read(int(size))
            __class__.socket = s
            return content
    
    
def lex(body):
    in_tag = False
    content = ''
    for c in body:
        if c == '<':
            in_tag = True
        elif c == '>':
            in_tag = False
        elif not in_tag:
            content += c
        content = content.replace('&gt;','>').replace('&lt;','<')
    return content

def layout(text):
    HSTEP, VSTEP = 13,18
    cursor_x, cursor_y = HSTEP, VSTEP
    display_list = []
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list

              
import tkinter
WIDTH, HEIGHT = 800, 600

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()
        self.scroll = 0
        
    def draw(self):
        for x, y, c in self.display_list:
            self.canvas.create_text(x, y - self.scroll, text=c)
        
    def load(self, url):
        body = url.request()
        text = ''
        if url.view_source:
            text = body
        else:
            text = lex(body)
        self.display_list = layout(text)
        self.draw()
        

if __name__ == '__main__':
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
    
