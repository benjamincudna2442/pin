from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)

def fetch_pinterest_data(pin_url):
    base_site = "https://www.savepin.app/"
    endpoint = "download.php"
    full_url = urllib.parse.urljoin(base_site, endpoint)
    params = {
        "url": pin_url,
        "lang": "en",
        "type": "redirect"
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(full_url, params=params, headers=headers)
    if response.status_code != 200:
        return None
    return response.text

def find_720p_option(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Pinterest Media"

    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 3:
            quality = cols[0].text.strip()
            href = cols[2].find("a")["href"]
            if "720p" in quality:
                full_url = urllib.parse.urljoin(base_url, href)
                return title, full_url

    return title, None

@app.route('/dl', methods=['GET'])
def download_720p():
    pin_url = request.args.get('url')
    if not pin_url:
        return jsonify({"error": "Missing 'url' query parameter"}), 400

    html = fetch_pinterest_data(pin_url)
    if not html:
        return jsonify({"error": "Failed to fetch data from Pinterest"}), 500

    title, dl_url = find_720p_option(html, "https://www.savepin.app/")
    if not dl_url:
        return jsonify({"error": "720p quality not available for this media"}), 404

    return jsonify({
        "dl_url": dl_url,
        "title": title,
        "developer": "@ISmartDevs"
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)