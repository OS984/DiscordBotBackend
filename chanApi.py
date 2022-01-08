# A python module for 4channel navigation
import requests
import re
import html
import time

class Board:
    
    def __init__(self, b_n):
        self.board = b_n
        self.catalog = self.genJson()
        self.threads = self.genThreads()
        
    def genJson(self):
        url = "https://a.4cdn.org/" + self.board + '/catalog.json'
        querystring = {"lang":"en"}
        headers = {}
        response = requests.request("GET", url, headers=headers, params=querystring)
        json_response = response.json()
        return json_response

    def genThreads(self):
        gotthreads = []
        for entry in self.catalog:
            for thread in entry['threads']:
                gotthreads.append(Thread(thread, self.board))
        return gotthreads
    
    def getThreads(self):
        return self.threads
    
    def getCatalog(self):
        return self.catalog

class Thread:
    
    def __init__(self, topview, board):
        self.board = board
        self.topview = topview
        self.no = self.topview['no']
        self.json_repr = self.makeJson()
        self.posts = self.genPosts()
        self.name = self.topview['semantic_url']
    def makeJson(self):
        try:
            url = "https://a.4cdn.org/" + self.board + '/thread/'+str(self.no)+'.json'
        except:
            #API is probably annoyed for requesting too fast
            time.sleep(1)
            url = "https://a.4cdn.org/" + self.board + '/thread/'+str(self.no)+'.json'
        querystring = {"lang":"en"}
        headers = {}
        response = requests.request("GET", url, headers=headers, params=querystring)
        json_response = response.json()
        return json_response
    
    def genPosts(self):
        posts = []
        for post in self.json_repr['posts']:
            _post = Post(post)
            posts.append(_post)
        return posts

    def getPosts(self):
        return self.posts
    
    def getNum(self):
        return self.no
    
    def getBoard(self):
        return self.board
    
    def getName(self):
        return self.name
    
class Post:
    
    def __init__(self, json):
        self.json = json
        # Do a little trick to figure out if post has media
        try:
            self.tim = self.json['tim']
            self.media_link = 'https://i.4cdn.org/'+str(self.tim)+self.json['ext']
            self.media = True
        except:
            self.media = False
            self.media_link = ''
        #Represent self.no as a string for ease of reply comparison.
        self.no = str(self.json['no'])
        try:
            self.content = self.json['com']
        except:
            self.content = ''
        self.nice_content = html.unescape(self.remove_html_tags())
        
    def remove_html_tags(self):
        """Remove html tags from a string"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', self.content)
    
    def getNum(self):
        return self.no
    
    def numReplTo(self):
        replyForm = re.compile('>>?[0-9]+')
        return len(re.findall(replyForm, self.nice_content))
    
    def replyNums(self):
        replyForm = re.compile('>>?[0-9]+')
        return re.findall(replyForm, self.nice_content)
    
    def getContent(self):
        return self.nice_content
    
    def getStrippedContent(self):
        try:
            to_remove = self.replyNums()[0]
            return self.nice_content.replace(to_remove, '')
        except:
            # Handles the case of the OP post.
            return self.nice_content
        
    def hasMedia(self):
        return self.media
