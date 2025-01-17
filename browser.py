import socket
import ssl      
import gzip
import re
class URL:
    redirect = 0
    socket = {}
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
            if self.host in self.__class__.socket:
                s = self.__class__.socket[self.host]
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
            __class__.socket[self.host] = s 
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
    font = tkinter.font.Font()
    cursor_x, cursor_y = HSTEP, VSTEP
    display_list = []
    for word in text.split():
        w = font.measure(word)
        if cursor_x + w >= WIDTH - HSTEP:
            cursor_y += font.metrics("linespace") * 1.25
            cursor_x = HSTEP
        display_list.append((cursor_x, cursor_y, word))
        cursor_x += w + font.measure(" ")
    return display_list

              
import tkinter
import tkinter.font

HSTEP, VSTEP = 13,18
WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 100

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack(expand=True,fill='both')
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.scrollmouse)
        self.window.bind("<Configure>",self.resize)
        
       
    def scrollmouse(self, e):
        if e.delta < 0:
            if self.scroll > len(self.display_list):
                return
            self.scroll += SCROLL_STEP
        else:
            if self.scroll == 0:
                return
            self.scroll -= SCROLL_STEP
        self.draw()
        
    def scrolldown(self, e):
        if self.scroll > len(self.display_list):
            return
        self.scroll += SCROLL_STEP
        self.draw()
        
    def scrollup(self, e):
        if self.scroll == 0:
            return
        self.scroll -= SCROLL_STEP
        self.draw()
        
    def resize(self, e):
        global HEIGHT, WIDTH
        HEIGHT = e.height
        WIDTH = e.width
        self.display_list = layout(self.text)
        self.draw()
        
    def draw(self):
        self.canvas.delete('all')
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)
        
    def load(self, url):
        body = url.request()
        self.text = ''
        if url.view_source:
            self.text = body
        else:
            self.text = lex(body)
        self.display_list = layout(self.text)
        self.draw()
        

if __name__ == '__main__':
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
    
