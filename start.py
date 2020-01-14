#!/usr/bin/env python
# -*- coding: latin-1 -*-

import base64
import frontmatter
import hashlib
import os
import re
import sys
import time
import wget
from io import BytesIO
from papirus import PapirusComposite
from urllib2 import urlopen

DIR = os.path.dirname(os.path.realpath(__file__))
FONTPATH = "%s/fonts/RobotoMono-Medium.ttf" % DIR
REMOTE_VIDEO_LOCATION = "https://s3.amazonaws.com/sfpc.io/video"

# Check EPD_SIZE is defined
EPD_SIZE = 0.0
if os.path.exists('/etc/default/epd-fuse'):
    exec(open('/etc/default/epd-fuse').read())
if EPD_SIZE == 0.0:
    print("Please select your screen size by running 'papirus-config'.")
    sys.exit()

# Running as root only needed for older Raspbians without /dev/gpiomem
if not (os.path.exists('/dev/gpiomem') and os.access('/dev/gpiomem', os.R_OK | os.W_OK)):
    user = os.getuid()
    if user != 0:
        print("Please run script as root")
        sys.exit()


def load_playlist():
    with open('%s/playlist' % DIR) as f:
        playlist = [load_project(slug) for slug in filter(lambda slug: len(slug) > 0 and slug[0] != '#', [
            item.strip() for item in f.read().splitlines()])]
    # Remove None values (e.g. if video file is missing)
    return [project for project in playlist if project]


def load_project(slug):
    markdown_path = "%s/media/%s.md" % (DIR, slug)
    video_path = "%s/media/%s.mp4" % (DIR, slug)

    markdown_exists = os.path.exists(markdown_path)
    video_exists = os.path.exists(video_path)

    if not video_exists:
        video_url = "%s/%s.mp4" % (REMOTE_VIDEO_LOCATION, slug)
        print "Downloading %s ..." % video_url
        wget.download(video_url, video_path)

    if not markdown_exists or not video_exists:
        return None

    project = frontmatter.load(markdown_path)
    project['slug'] = slug
    project['markdown_path'] = markdown_path
    project['video_path'] = video_path
    project['has_audio_track'] = has_audio_track(project)
    if (project["instagram"] and len(project['instagram']) > 0):
        project["social"] = "Instagram\n@%s" % project["instagram"]
    elif (project["twitter"] and len(project['twitter']) > 0):
        project["social"] = "Twitter\n@%s" % project["twitter"]
    elif (project["github"] and len(project['github']) > 0):
        project["social"] = "GitHub\n%s" % project["github"]
    else:
        project["social"] = ""

    load_base64_qr_code_image(project)

    return project


def load_base64_qr_code_image(project):
    slug = project['slug']
    url = project['website']
    # generate a hash of the URL to ensure we generate a new QR code if the url changes
    urlhash = hashlib.sha1(url).hexdigest()[0:7]
    # try to load cached slug first
    filename = '%s/media/%s-%s.qrcode.txt' % (DIR, slug, urlhash)

    if (not os.path.exists(filename)):
        base64Img = url_to_qrcode_base64(url)
        file = open(filename, 'w')
        file.write(base64Img)

    f = open(filename, 'r')
    contents = f.read()
    return contents


def debug_project(project):
    print project['slug']
    print project['title']
    print project['artist']
    print project['year']
    print project['social']
    print project['video_path']
    print "audio" if project['has_audio_track'] else "no audio"
    print "---"
    time.sleep(3)


def update_wall_text(project):
    base64Img = load_base64_qr_code_image(project)
    # create image from base64 string
    imgPaPiRus = BytesIO(base64.b64decode(base64Img))
    textNImg = PapirusComposite(False)

    artist_title_year_audio = "%s\n\n%s\n%s\n%s" % (
        project['artist'], project['title'], project['year'], "" if project["has_audio_track"] else " (no audio)")

    textNImg.AddText(artist_title_year_audio, 10, 10,
                     16, Id="ArtistTitleYearAudio", fontPath=FONTPATH)

    if project['social'] and len(project['social']) > 0:
        textNImg.AddText(project['social'], 10, 140,
                         14, Id="Social", fontPath=FONTPATH)

    textNImg.AddImg(imgPaPiRus, 200, 110, (60, 60))
    textNImg.WriteAll()


def has_audio_track(project):
    cmd = 'ffprobe -loglevel error -show_entries stream=codec_type -of default=nw=1 %s' % project['video_path']
    output = os.popen(cmd).read()
    audio_found = re.search("codec_type=audio", output, re.MULTILINE)
    return True if audio_found else False


def play_video(project):
    os.system(
        '/usr/bin/omxplayer --aspect-mode letterbox --threshold 5 --no-osd %s > %s/log.txt 2>&1' % (project['video_path'], DIR))


def url_to_qrcode_base64(url):
    qrurl = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=%s" % url
    response = urlopen(qrurl)
    data = response.read()
    return data.encode("base64")


def main():
    print("Starting SFPC media wall...")

    playlist = load_playlist()

    while True:
        # clear console
        os.system('clear')

        for project in playlist:
            # debug_project(project)
            update_wall_text(project)
            play_video(project)
        # This line allows the playlist to be updated while the script is running
        playlist = load_playlist()


if __name__ == '__main__':
    main()
