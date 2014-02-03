# import modules for argument parsing
import getopt, sys
# import feedparser for parsing rss feeds
import feedparser
# import urllib for downloading files
import urllib.request
import urllib.parse
import urllib.error

# import modules for threading and file I/O
import os
import threading

# import modules for logging and json manipulation
import json
import logging

logging.basicConfig(filename='downloader.log',filemode='a', format='%(levelname)s : %(asctime)s : %(message)s',level=logging.DEBUG)
#logging.info('Logging started')


# print sample usage of this srcipt

def usage():
    logging.info('Wrongly typed command')
    print("-----------------------------------------------------------------------")
    print("Wrongly typed command. Sample usage is given below")
    print("python ",sys.argv[0],"--feed=<feedurl> --output=<output file location>")
    print("-----------------------------------------------------------------------")




# return dictionary {feed:'',output:''} commands from commandline

def get_commands(args):
    commands = {'feed':'', 'output':''}
    try:
        optlist, args = getopt.getopt(args,'',['feed=','output='])
        for k, v in optlist:
            if k=='--feed':
                commands['feed'] = v
            elif k=='--output':
                commands['output'] = v
    except getopt.GetoptError:
        usage()
        #sys.exit(2)
    return commands


	
# Item Downloader thread for downloading single item

class ItemDownLoader(threading.Thread):
   
    #initialize with title, lock object, semaphore that restricts max number of parallel threads, output file handle, input response stream, 
    #start and end bytes to download, list that keeps fully downloaded item's id, file handle to store downloadedList 
    def __init__(self,itemTitle,lock,semaphore,guid,outFile,response,startBytes,endBytes,downloadedList,downloadedListFile):
        threading.Thread.__init__(self)
        self.semaphore = semaphore
        self.itemTitle = itemTitle
        self.lock = lock		
        self.guid = guid
        self.outFile = outFile
        self.response = response
        self.startBytes = startBytes
        self.endBytes = endBytes
        self.downloadedList = downloadedList
        self.downloadedListFile = downloadedListFile

    def run(self):
        print("\nItem Downloader for {0} started\n".format(self.itemTitle))
        try:
            with self.outFile:
                while self.startBytes < self.endBytes:
                    data = self.response.read(1024)
                    self.outFile.write(data)
                    self.startBytes = self.outFile.tell()
                    percent = int((self.startBytes/self.endBytes)*100.0)
                    #lock sys.stdout
                    #self.lock.acquire()					
                    #sys.stdout.write('\r                                                       ')
                    #sys.stdout.write('\r{0}% complete of {1}'.format(percent,self.itemTitle))
                    #sys.stdout.flush()
                    #unlock sys.stdout
                    #self.lock.release()
                    #logging.info('Downloaded '+ str(downloadedSize) + ' bytes')
             
                self.lock.acquire()
                print('\ndone!!!\nDownload complete of{0}\n'.format(self.itemTitle))
                logging.info('Download complete of '+self.itemTitle)
                self.downloadedList.append(self.guid)
                with open(self.downloadedListFile,"w") as f:
                    f.write(json.dumps(self.downloadedList))
                self.lock.release()
            
        except Exception as e:
            logging.exception(e)
            print(e)
        finally:
            self.semaphore.release()		
        print("\nItem Downloader for {0} completed\n".format(self.itemTitle))

# Downloader class handles all operations regrding downloading files from rss feed

class Downloader(object):
    
    def __init__(self,feedUrl,outLocation):
        print("Initializing downloader ...")
        self.feedUrl = feedUrl
        self.outLocation = outLocation
        self.downloadedListFile = 'dlist.json'
        self.MAX_THREAD = 3
        self.semaphore = threading.BoundedSemaphore(value=self.MAX_THREAD)
        self.downloadedList = []
        
        with open(self.downloadedListFile,"a+") as f:
            f.seek(0,0)
            data = f.read()
            try:
                self.downloadedList = json.loads(str(data))
            except:
                #print("json error")
                self.downloadedList = []
        print("Initialization complete!!!")	

    def download(self):
        try:
            print("Parsing rss feed ...")
            logging.info('Parsing rss feed from '+str(self.feedUrl))
            rssfeed = feedparser.parse(self.feedUrl)
            logging.info('Parsed rss feed from '+str(self.feedUrl))
            print("This feed has ",len(rssfeed.entries)," download sources")
            lock = threading.Lock()
            
            for item in rssfeed.entries:
                
                print("Downloading ",item.title)
                logging.info('Downloading from '+ str(item.link))
                if item.guid in self.downloadedList:
                    print(item.title,' already downloaded')
                    logging.info(str(item.title) + 'already downloaded')
                    continue

                fileName = item.link.split('/')[-1]
                fileName = self.outLocation + '/' +fileName
                downloadedSize = 0
                if os.path.exists(fileName):
                    downloadedSize = float(os.path.getsize(fileName))
                request = urllib.request.Request(item.link,headers={ 'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)', 'Range' : 'bytes=0-'})
                response = urllib.request.urlopen(request)

                supportsPartialDownload = response.status == 206
                logging.info('Does server has partial download support '+ str(supportsPartialDownload))
                totalSize = float(response.info()['Content-Length'].strip())
                logging.info('Content size is '+ str(totalSize))
                try:
                    userAgent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)';
                    rangeHeader = 'bytes=' + str(int(downloadedSize)) + '-'
                    headers = { 'User-Agent' : userAgent, 'Range' : rangeHeader}
                    request = urllib.request.Request(item.link,headers=headers)
                    response = urllib.request.urlopen(request)

                    outFile = None
                    try:
                        
                        if downloadedSize < totalSize:
                            #check if server supports HTTP partial download
                            if supportsPartialDownload:
                                outFile = open(fileName, 'ab')
                            else:
                                outFile = open(fileName, 'wb')
                                downloadedSize = 0

                        else:
                            print("File already exists at ",fileName)
                            logging.info('File already exists at '+fileName)
                        if outFile!=None:
                            self.semaphore.acquire()
                            p = ItemDownLoader(item.title,lock,self.semaphore,item.guid,outFile,response,downloadedSize,totalSize,self.downloadedList,self.downloadedListFile)
                            p.start()
                            #p.join()		
                            
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                except Exception as e:
                    logging.exception(e)
                    print(e)
        except Exception as e:
            logging.exception(e)
            print("Could not parse from ",self.feedUrl)
            print(e)




def main():
   commands = get_commands(sys.argv[1:])
   aDownloader = Downloader(commands['feed'],commands['output'])
   aDownloader.download()
   
if __name__ == '__main__':
    main()
