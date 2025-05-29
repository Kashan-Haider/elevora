import requests
from bs4 import BeautifulSoup

def get_backlinks_from_openlinkprofiler(domain):
    url = f"https://www.openlinkprofiler.org/r/{domain}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    links = []
    rows = soup.select("table#linklist tbody tr")

    for row in rows:
        try:
            source = row.select_one("td:nth-child(2) a")['href']
            anchor = row.select_one("td:nth-child(3)").get_text(strip=True)
            date = row.select_one("td:nth-child(5)").get_text(strip=True)
            links.append({
                "source_url": source,
                "anchor_text": anchor,
                "link_date": date
            })
        except:
            continue

    return links

# Example usage
backlinks = get_backlinks_from_openlinkprofiler("ali.com")
for link in backlinks[:5]:
    print(link)
