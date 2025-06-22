from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import urllib.parse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

# Configure session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

@app.route('/')
def status():
    try:
        return render_template('status.html')
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Status page not found. Please create status.html.",
            "api_dev": "@ISmartCoder",
            "updates_channel": "t.me/TheSmartDev"
        }), 404

@app.route('/dl', methods=['GET'])
def download_pinterest_media():
    pinterest_url = request.args.get('url', '').strip()
    
    if not pinterest_url:
        return jsonify({
            "status": "error",
            "input_url": pinterest_url,
            "message": "No URL provided",
            "api_dev": "@ISmartCoder",
            "updates_channel": "t.me/TheSmartDev"
        }), 400
    
    base_url = "https://www.savepin.app/download.php"
    params = {
        "url": pinterest_url,
        "lang": "en",
        "type": "redirect"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.savepin.app/"
    }
    
    try:
        response = session.get(base_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Check if response is JSON or HTML
        content_type = response.headers.get('content-type', '').lower()
        if 'application/json' in content_type:
            return jsonify({
                "status": "error",
                "input_url": pinterest_url,
                "message": "Unexpected JSON response from savepin.app",
                "api_dev": "@ISmartCoder",
                "updates_channel": "t.me/TheSmartDev"
            }), 500
        
        # Parse HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Unknown"
        
        # Extract download links from table
        download_links = []
        table = soup.find('table', {'border': '1'})
        if table:
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 3:
                    quality = cells[0].text.strip()
                    format_type = cells[1].text.strip().lower()
                    link_tag = cells[2].find('a', {'class': 'button is-success is-small'})
                    if link_tag and 'href' in link_tag.attrs:
                        href = link_tag['href']
                        if href.startswith('force-save.php?url='):
                            media_url = href.replace('force-save.php?url=', '')
                            media_url = urllib.parse.unquote(media_url)
                            download_links.append({
                                "quality": quality,
                                "url": media_url,
                                "type": f"{'image/jpeg' if format_type == 'jpg' else 'video/mp4'}"
                            })
        
        result = {
            "status": "success",
            "input_url": pinterest_url,
            "title": title,
            "media": download_links,
            "api_dev": "@ISmartCoder",
            "updates_channel": "t.me/TheSmartDev"
        }
        
        if not download_links:
            result["status"] = "error"
            result["message"] = "No media found for the provided URL"
            result["html_snippet"] = response.text[:500]
        
        return jsonify(result), 200
        
    except requests.exceptions.RequestException as e:
        error_response = {
            "status": "error",
            "input_url": pinterest_url,
            "message": f"Failed to fetch media: {str(e)}",
            "api_dev": "@ISmartCoder",
            "updates_channel": "t.me/TheSmartDev"
        }
        if isinstance(e, requests.exceptions.HTTPError) and e.response:
            error_response["html_snippet"] = e.response.text[:500]
        return jsonify(error_response), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
