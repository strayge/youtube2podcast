import subprocess
import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urljoin, quote
from feedgen.feed import FeedGenerator


playlist_url = 'https://www.youtube.com/playlist?list=PLRd7kI_0sLY533RmBkeMcLT7UYf28lCoe'
last_title_filename = '/data/last.txt'
rss_filename = '/data/dtkd.rss'
external_files_url = 'https://strayge.com/dtkd/files/'


def get_playlist():
    res = subprocess.run(f'youtube-dl "{playlist_url}" --flat-playlist -J', shell=True, check=True, capture_output=True)
    playlist_info = json.loads(res.stdout.decode())
    return playlist_info


def download():
    print('downloading...')
    res = subprocess.run(f'youtube-dl "{playlist_url}" --playlist-items 1 -f bestaudio -o "/data/files/%(title)s.%(ext)s"', shell=True, check=True, capture_output=True)
    print('downloaded')


def get_last_title(playlist):
    return playlist.get('entries', [''])[0].get('title')


def get_downloaded_title() -> str:
    if not os.path.exists(last_title_filename):
        return ''
    with open(last_title_filename, 'rt') as f:
        return f.read()


def set_downloaded_title(title):
    with open(last_title_filename, 'wt') as f:
        return f.write(title)


def generate_rss():
    print('generating rss...')
    files = os.listdir('/data/files')
    files = [f for f in files if not f.endswith('.part')]

    fg = FeedGenerator()
    fg.title('ДТКД')
    fg.description('ДТКД')
    fg.link(href=playlist_url, rel='alternate')
    fg.load_extension('podcast')
    fg.podcast.itunes_category('Technology', 'Podcasting')

    for file in files:
        name, ext = file.rsplit('.', 1)
        url = urljoin(external_files_url, quote(file))
        mod_time_unix = os.path.getmtime(os.path.join('/data/files/', file))
        mod_time = datetime.fromtimestamp(mod_time_unix).replace(tzinfo=timezone.utc)
        entry_id = str(uuid.uuid5(uuid.NAMESPACE_URL, name))
        fe = fg.add_entry()
        fe.id(entry_id)
        fe.published(mod_time)
        fe.title(name)
        fe.description(name)
        fe.enclosure(url, 0, 'audio/mpeg')
    fg.rss_file(rss_filename, pretty=True)
    print('generated')


def main():
    print('===== start =====')
    
    playlist = get_playlist()
    current_last_title = get_last_title(playlist)
    last_downloaded_title = get_downloaded_title()
    if current_last_title and current_last_title != last_downloaded_title:
        print(f'new founded: {current_last_title}')
        download()
        set_downloaded_title(current_last_title)
        generate_rss()
    
    print('===== end =====')
    
    #from time import sleep
    #while 1:
    #    sleep(1)

if __name__ == '__main__':
    main()
