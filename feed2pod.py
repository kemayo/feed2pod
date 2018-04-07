#!/usr/bin/env python

import argparse
import feedparser
from bs4 import BeautifulSoup
import xml.etree.ElementTree as etree


def file_from_entry(entry):
    """Extract the best audio file we can from an `entry`

    'Best' means, in order:
    1. <enclosure> with a `type` that references audio
    2. <enclosure> with a file that looks audio-y
    3. <content>: an <audio> tag's <source> which is audio/mpeg
    4. <content>: an <audio> tag's <source> of any type
    5. <content>: an <audio> tag's `src`
    """
    if entry.enclosures:
        # We sooooo cannot trust anything here.
        for enclosure in entry.enclosures:
            if 'audio/' in enclosure['type']:
                return enclosure['href'], enclosure['type'], enclosure['length']
            if enclosure['href'].endswith('.ogg') or enclosure['href'].endswith('.mp3'):
                return enclosure['href'], None, enclosure['length']
    # That's the easy stuff done with... now the bits we're really scraping for:
    for content in entry.content:
        if content['type'] == 'text/html':
            soup = BeautifulSoup(content['value'], "html.parser")
            audio = soup.find('audio')
            if audio:
                # prioritize mp3, for support
                source = audio.find('source', type='audio/mpeg')
                if source:
                    return source['src'], source['type'], None
                source = audio.find('source')
                if source:
                    return source['src'], source['type'], None
                if 'src' in audio:
                    return audio['src'], None, None

    return None, None, None


def feed2pod(url):
    feed = feedparser.parse(url)

    # We're going RSS2 here
    rss = etree.Element('rss', version="2.0")
    channel = etree.SubElement(rss, 'channel')
    etree.SubElement(channel, 'title').text = feed.feed.title
    etree.SubElement(channel, 'link').text = feed.feed.link
    etree.SubElement(channel, 'description').text = feed.feed.description
    if 'published' in feed.feed:
        etree.SubElement(channel, 'pubDate').text = feed.feed.published
    if 'author' in feed.feed and '@' in feed.feed.author:
        # Only use the author if it might be RSS-valid, i.e. an email address
        etree.SubElement(channel, 'author').text = feed.feed.published
    if 'generator' in feed.feed:
        etree.SubElement(channel, 'generator').text = 'feed2pod (from: {})'.format(feed.feed.generator)
    else:
        etree.SubElement(channel, 'generator').text = 'feed2pod'
    if 'image' in feed.feed:
        image = etree.SubElement(channel, 'image')
        etree.SubElement(image, 'href').text = feed.feed.image.link
        etree.SubElement(image, 'title').text = feed.feed.image.title or feed.feed.title
        etree.SubElement(image, 'link').text = feed.feed.image.link or feed.feed.link
        if 'width' in feed.feed.image:
            etree.SubElement(image, 'width').text = str(feed.feed.image.width)
        if 'height' in feed.feed.image:
            etree.SubElement(image, 'height').text = str(feed.feed.image.height)

    # TODO: there's a bunch of podcast-y attributes, mostly `itunes:` stuff,
    # which we should translate in if possible, or override somehow if they're
    # absent. If nothing else, an image override might be useful, since iTunes
    # has specific requirements for a HUGE image, which a non-podcast feed is
    # unlikely to have.
    # https://resourcecenter.odee.osu.edu/digital-media-production/how-write-podcast-rss-xml

    for entry in feed.entries:
        file, ftype, flength = file_from_entry(entry)
        if file:
            if not ftype:
                if file.endswith('.mp3'):
                    ftype = 'audio/mpeg'
                elif file.endswith('.ogg'):
                    ftype = 'audio/ogg'
            item = etree.SubElement(channel, 'item')
            etree.SubElement(item, 'title').text = entry.title
            if 'id' in entry:
                # Note to self: isPermalink mostly means "is the GUID also a link"
                if entry.id == entry.link:
                    etree.SubElement(item, 'guid', isPermalink='true').text = entry.id
                else:
                    etree.SubElement(item, 'guid', isPermalink='false').text = entry.id
            if 'author' in entry and '@' in entry.author:
                etree.SubElement(item, 'author').text = entry.author
            if 'link' in entry:
                etree.SubElement(item, 'link').text = entry.link
            if 'published' in entry:
                etree.SubElement(item, 'pubDate').text = entry.published
            if entry.content:
                etree.SubElement(item, 'description').text = entry.content[0].value
            elif 'summary' in entry:
                etree.SubElement(item, 'description').text = entry.summary
            # TODO: length; we should see if a HEAD can at least fill it in
            etree.SubElement(item, 'enclosure', url=file, type=ftype, length=flength or "0")

    # TODO: should we support paging / history? it'd need more arguments
    # passed in, or some sort of persistent entry-storage by feed URL.
    # Arguably the client's job. Adding it gets closer to this turning into a
    # podcast client backend server.

    # persuading etree to do this? weirdly complicated
    return '<?xml version="1.0" encoding="UTF-8"?>' + etree.tostring(rss, encoding='unicode')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help="url of a feed")
    parser.add_argument('--filename', default=False, help="output filename")
    args = parser.parse_args()

    rss = feed2pod(args.url)
    if args.filename:
        with open(args.filename, 'wb') as f:
            f.write(rss)
    else:
        print(rss)
