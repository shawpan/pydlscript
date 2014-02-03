pydlscript
==========

Two python scripts to download files from rss feeds (parallel + non-parallel)


Usage Example
=============

```
python downloader.py --feed=https://dl.dropboxusercontent.com/u/6160850/downloads.rss --output=c:/
```

multi threaded version:
change the MAX_THREAD value in ItemDownloader class for desired number of parallel downloads, default is 3
```
python downloader2.py --feed=https://dl.dropboxusercontent.com/u/6160850/downloads.rss --output=c:/
```
