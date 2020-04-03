import subprocess
import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urljoin, quote
from feedgen.feed import FeedGenerator


playlist_url = os.environ['PLAYLIST_URL']
rss_name = os.environ['RSS_FILENAME']
external_url_to_files = os.environ['EXTERNAL_URL_TO_FILES']
podcast_title = os.environ['PODCAST_TITLE']
podcast_description = os.environ['PODCAST_DESCRIPTION']
podcast_url = os.environ['PODCAST_URL']
episodes_limit = int(os.environ['EPISODES_LIMIT'])

data_path = '/data'
files_path = os.path.join(data_path, 'files')
last_title_filename = os.path.join(data_path, 'last.txt')
rss_filename = os.path.join(files_path, rss_name)


def get_playlist():
    res = subprocess.run(f'youtube-dl "{playlist_url}" --flat-playlist -J', shell=True, check=True, capture_output=True)
    playlist_info = json.loads(res.stdout.decode())
    return playlist_info

def get_media_files():
    files = [f for f in os.listdir(files_path) if f != rss_name]
    files_with_ts = [(name, os.path.getmtime(os.path.join(files_path, name))) for name in files]
    files_with_ts_sorted = sorted(files_with_ts, key=lambda x: x[1], reverse=True)
    files_sorted = [x[0] for x in files_with_ts_sorted]
    return files_sorted


def download():
    print('downloading...')
    res = subprocess.run(f'youtube-dl "{playlist_url}" --playlist-items 1 -f bestaudio -o "/data/files/%(title)s.%(ext)s"', shell=True, check=True, capture_output=True)
    print('downloaded, cleaning...')
    files = get_media_files()
    passed = 0
    deleted = 0
    for name in files:
        if name.endswith('.part'):
            os.remove(os.path.join(files_path, name))
            continue
        passed += 1
        if episodes_limit and passed > episodes_limit:
            os.remove(os.path.join(files_path, name))
            deleted += 1
    print(f'removed {deleted}')


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
    files = get_media_files()

    fg = FeedGenerator()
    fg.title(podcast_title)
    fg.description(podcast_description)
    fg.link(href=podcast_url, rel='alternate')
    fg.load_extension('podcast')

    for file in files:
        name, ext = file.rsplit('.', 1)
        url = urljoin(external_url_to_files, quote(file))
        mod_time_unix = os.path.getmtime(os.path.join(files_path, file))
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

if __name__ == '__main__':
    main()
