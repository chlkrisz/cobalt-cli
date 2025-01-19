#!/usr/bin/env python3

"""
Cobalt.tools CLI wrapper
Made by liba

https://github.com/chlkrisz/cobalt-cli
"""

import argparse
import requests
import sys
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description='Cobalt.tools CLI wrapper')
    parser.add_argument('url', type=str, help='URL of video to download')
    parser.add_argument('--instance', type=str, help='Cobalt.tools instance to use')
    parser.add_argument('--output', type=str, help='Output file name')
    parser.add_argument("--video-quality", type=str, help="Video quality to download", 
                        choices=["144", "240", "360", "480", "720", "1080", "max"], 
                        default="720")
    parser.add_argument("--audio-format", type=str, help="Audio format", 
                        choices=["best", "mp3", "ogg", "wav", "opus"], default="best")
    parser.add_argument("--download-mode", type=str, help="Download mode", 
                        choices=["auto", "audio", "mute"], default="auto")
    parser.add_argument("--always-proxy", action='store_true', 
                        help="Tunnels all downloads through the processing server, even when not necessary.", 
                        default=True)
    parser.add_argument("--twitter-gif", action='store_true', 
                        help="Download Twitter videos as GIFs", 
                        default=True)
    parser.add_argument("--file-name-style", type=str, help="File name style", 
                        choices=["classic", "pretty", "basic", "nerdy"], 
                        default="pretty")

    args = parser.parse_args()

    if args.instance:
        instance = args.instance
        try:
            with open('cobalt.ini', 'w') as f:
                f.write(f'instance={instance}')
        except FileNotFoundError:
            print('Failed to save instance to cobalt.ini')
    else:
        try:
            with open('cobalt.ini', 'r') as f:
                instance = f.readline().split('=')[1].strip()
        except FileNotFoundError:
            print('No instance specified and no cobalt.ini found in current directory.')
            print('To set a default instance, use the --instance argument.')
            sys.exit(1)

    if not instance.startswith('https://') and not instance.startswith('http://'):
        instance = 'http://' + instance

    url = args.url
    output_file = args.output

    data = {
        "url": url,
        "videoQuality": args.video_quality,
        "audioFormat": args.audio_format,
        "downloadMode": args.download_mode,
        "alwaysProxy": args.always_proxy,
        "twitterGif": args.twitter_gif,
        "filenameStyle": args.file_name_style
    }

    print(f"Contacting Cobalt.tools instance at {instance}...")
    try:
        response = requests.post(
            instance,
            json=data,
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to {instance}. Error: {e}")
        sys.exit(1)

    if response.status_code != 200:
        print(f"Failed to fetch video: Status code {response.status_code}")
        print(response.text)
        sys.exit(1)

    try:
        json_data = response.json()
        download_url = json_data['url']
        filename_suggested = json_data['filename']
    except (ValueError, KeyError) as e:
        print("Failed to parse response JSON or missing fields.")
        print(f"Error: {e}")
        sys.exit(1)

    if not output_file:
        output_file = filename_suggested
    
    print("Starting download...")
    try:
        download_resp = requests.get(download_url, stream=True, timeout=30)
        if download_resp.status_code != 200:
            print(f"Failed to download file from {download_url}.")
            print(f"Status code: {download_resp.status_code}")
            sys.exit(1)

        total_size_in_bytes = int(download_resp.headers.get('content-length', 0))
        block_size = 1024
        
        with open(output_file, 'wb') as f, tqdm(
            total=total_size_in_bytes, 
            unit='iB', 
            unit_scale=True, 
            desc="Downloading", 
            ncols=80
        ) as bar:
            for chunk in download_resp.iter_content(chunk_size=block_size):
                f.write(chunk)
                bar.update(len(chunk))

        print(f"\nDownload completed: {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
