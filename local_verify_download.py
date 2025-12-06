import requests
import time
import json
import sys

BASE_URL = 'https://hqmx.net/api/downloader'
ALBUM_URL = 'https://www.instagram.com/p/DRr5qxrE-23/?utm_source=ig_web_copy_link&igsh=MzRlODBiNWFlZA=='

def test():
    print(f'1. Analyzing URL: {ALBUM_URL}')
    try:
        resp = requests.post(f'{BASE_URL}/analyze', json={'url': ALBUM_URL})
        if resp.status_code != 200:
            print(f'Analysis failed: {resp.text}')
            return
    except Exception as e:
        print(f'Analysis request error: {e}')
        return
    
    data = resp.json()
    entries = data.get('entries', [])
    print(f'Analysis successful. Found {len(entries)} entries.')
    
    target_entry = None
    if len(entries) < 2:
        print('Not enough entries to test specific item download. Trying first item instead.')
        if entries:
            target_entry = entries[0]
    else:
        # Pick the second item (Index 1)
        target_entry = entries[1]

    if not target_entry:
        print("No entries found to download.")
        return

    print(f"2. Downloading entry: {target_entry.get('url')[:50]}...")
    
    payload = {
        'url': target_entry.get('url'),
        'mediaType': target_entry.get('media_type', 'image'),
        'formatType': 'jpg' if target_entry.get('media_type') == 'image' else 'mp4',
        'quality': 'best',
        'skip_album_check': True,
        'extracted_url': target_entry.get('url')
    }
    
    print(f'Payload: {json.dumps(payload, indent=2)}')
    
    try:
        resp = requests.post(f'{BASE_URL}/download', json=payload)
        if resp.status_code != 200:
            print(f'Download request failed: {resp.text}')
            return
    except Exception as e:
        print(f'Download request error: {e}')
        return

    task_id = resp.json().get('task_id')
    print(f'Task ID: {task_id}')
    
    print('3. Waiting for completion (Max 300s)...')
    start_time = time.time()
    while True:
        try:
            status_resp = requests.get(f'{BASE_URL}/check-status/{task_id}')
            status = status_resp.json()
            print(f"Status: {status.get('status')} - {status.get('percentage')}% - {status.get('message')}")
            
            if status.get('status') == 'complete':
                print('Download Complete!')
                break
            if status.get('status') == 'error':
                print(f"Download Failed: {status.get('message')}")
                break
        except Exception as e:
            print(f'Status check error: {e}')
            
        if time.time() - start_time > 300:
            print('Timeout reached.')
            break
        
        time.sleep(5)

if __name__ == '__main__':
    test()
