"""Check public citation links without treating reachability as fact verification."""

import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlsplit

import requests

from guide_experience import OUT, documents, load_page


def check(url):
    row = {'source_url':url,'status':'unavailable','http_status':'','final_url':'','detail':'','last_checked':datetime.now(timezone.utc).isoformat()}
    try:
        response = requests.get(url,timeout=18,stream=True)
        row.update(http_status=response.status_code,final_url=response.url,status='available' if response.status_code==200 else 'blocked' if response.status_code in {401,403,429} else 'unavailable')
        if 'abuse-detection-apology' in response.url:
            row['status']='blocked'
        response.close()
        row['detail'] = 'Link reachability check only; not a new regulatory fact review.'
    except requests.RequestException as error:
        row['detail'] = type(error).__name__
    return row


def main():
    urls = set()
    for path in documents():
        for anchor in load_page(path).select('main li a[href^="https://"], main li a[href^="http://"]'):
            url=anchor['href']
            parsed=urlsplit(url)
            if parsed.hostname and parsed.hostname!='flashcargoglobal.com' and not parsed.username:
                urls.add(url)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(check,sorted(urls)))
    OUT.mkdir(parents=True,exist_ok=True)
    for filename,selected in [('source-link-checks.csv',rows),('source-link-errors.csv',[row for row in rows if row['status']!='available'])]:
        with (OUT/filename).open('w',encoding='utf-8-sig',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(selected)
    print({'links':len(rows),'available':sum(row['status']=='available' for row in rows),'blocked_or_unavailable':sum(row['status']!='available' for row in rows)})


if __name__=='__main__':
    main()
