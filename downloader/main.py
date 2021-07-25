import subprocess
import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urljoin, quote
from feedgen.feed import FeedGenerator

EXTERNAL_URL_TO_FILES = os.environ['EXTERNAL_URL_TO_FILES']
DATA_PATH = '/data'


def get_playlist(playlist_url):
    res = subprocess.run(f'youtube-dl "{playlist_url}" --flat-playlist -J', shell=True, check=True, capture_output=True)
    playlist_info = json.loads(res.stdout.decode())
    return playlist_info

def get_media_files(files_path):
    files = [f for f in os.listdir(files_path) if not f.endswith('.rss') and not f.endswith('.txt')]
    files_with_ts = [(name, os.path.getmtime(os.path.join(files_path, name))) for name in files]
    files_with_ts_sorted = sorted(files_with_ts, key=lambda x: x[1], reverse=True)
    files_sorted = [x[0] for x in files_with_ts_sorted]
    return files_sorted


def download(playlist_url, files_path, episodes_limit=1):
    print('downloading...')
    if not os.path.exists(files_path):
        os.mkdir(files_path)
    res = subprocess.run(f'youtube-dl "{playlist_url}" --playlist-items 1 -f bestaudio -o "{files_path}/%(title)s.%(ext)s"', shell=True, check=True, capture_output=True, timeout=180)
    print('downloaded, cleaning...')
    files = get_media_files(files_path=files_path)
    passed = 0
    deleted = 0
    for name in files:
        if name.endswith('.part'):
            os.remove(os.path.join(files_path, name))
            continue
        if name.endswith('.rss') or name.endswith('.txt'):
            continue
        passed += 1
        if episodes_limit and passed > episodes_limit:
            os.remove(os.path.join(files_path, name))
            deleted += 1
    print(f'removed {deleted}')


def get_last_title(playlist):
    return playlist.get('entries', [''])[0].get('title')


def get_downloaded_title(last_title_filename) -> str:
    if not os.path.exists(last_title_filename):
        return ''
    with open(last_title_filename, 'rt') as f:
        return f.read()


def set_downloaded_title(last_title_filename, title):
    with open(last_title_filename, 'wt') as f:
        return f.write(title)


def generate_rss(podcast_title, podcast_description, podcast_url, files_path, rss_filename, rss_name):
    print('generating rss...')
    files = get_media_files(files_path=files_path)

    fg = FeedGenerator()
    fg.title(podcast_title)
    fg.description(podcast_description)
    fg.link(href=podcast_url, rel='alternate')
    fg.load_extension('podcast')

    for file in files:
        name, ext = file.rsplit('.', 1)
        url = urljoin(urljoin(EXTERNAL_URL_TO_FILES, quote(rss_name)) + '/', quote(file))
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
    for i in range(1, 11):
        playlist_url = os.environ.get(f'PLAYLIST_URL_{i}')
        if not playlist_url:
            continue
        podcast_url = os.environ.get(f'PODCAST_URL_{i}', playlist_url)
        rss_name = os.environ[f'RSS_NAME_{i}']
        podcast_title = os.environ[f'PODCAST_TITLE_{i}']
        podcast_description = os.environ.get(f'PODCAST_DESCRIPTION_{i}', podcast_title)
        episodes_limit = int(os.environ.get(f'EPISODES_LIMIT_{i}', os.environ.get('EPISODES_LIMIT')))
        files_path = os.path.join(DATA_PATH, rss_name)
        last_title_filename = os.path.join(DATA_PATH, f'{rss_name}_last.txt')
        rss_filename = os.path.join(DATA_PATH, rss_name + '.rss')

        print(f'processing {rss_name}...')

        playlist = get_playlist(playlist_url)
        current_last_title = get_last_title(playlist)
        last_downloaded_title = get_downloaded_title(last_title_filename)

        if current_last_title and current_last_title != last_downloaded_title:
            print(f'new founded: {current_last_title}')
            download(playlist_url, files_path, episodes_limit)
            set_downloaded_title(last_title_filename, current_last_title)
            generate_rss(
                podcast_title=podcast_title, 
                podcast_description=podcast_description, 
                podcast_url=podcast_url, 
                files_path=files_path, 
                rss_filename=rss_filename,
                rss_name=rss_name,
            )
    print('===== end =====')

if __name__ == '__main__':
    main()
