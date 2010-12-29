import urllib2, re

PAGES = """
http://www.lyricsforall.com/awards/rs/
http://www.lyricsforall.com/awards/rs/2
http://www.lyricsforall.com/awards/rs/3
http://www.lyricsforall.com/awards/rs/4
http://www.lyricsforall.com/awards/rs/5"""

all_songs = []

pages = PAGES.split()

song_info_re = r'<TD align="left" class="small" bgcolor="#DEE3E9">\s*<a class="small" href="(.*?)">(.*?)</a></TD>'

song_lyric_re = r'<p><font class="small">((.|\s)*?)<table>'

def crawl_pages():
    for page in pages:
        content = "".join(urllib2.urlopen(page).readlines())
        song_list = re.findall(song_info_re, content)
        all_songs.extend(zip(song_list[::2], song_list[1::2]))

def fetch_lyrics(url):
    content = urllib2.urlopen(url).readlines()
    content_str = "".join(content)
    
    lyrics = re.findall(song_lyric_re, content_str)
    lyrics = [l[0] for l in lyrics]
    lyrics = "".join(lyrics)

    lyrics = re.sub(r"(<br>|<BR>)", "\n", lyrics)
    lyrics = re.sub(r"<.*?>", " ", lyrics)

    return lyrics


def crawl_all_lyrics():
    f = open("save.txt", 'w')
    for count, song in enumerate(all_songs):
        url = song[0][0]
        name = song[0][1]
        artist = song[1][1]

        f.write("\n%s -- %s\n%s\n%s\n%s\n" %(name, artist,
                                         "*"*40, fetch_lyrics(url), "*"*40))
        f.flush()
        print "%s) %s -- %s" %(count+1, name, artist)

    f.close()
    
    

# crawl_pages()

# crawl_all_lyrics()
