from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import urllib.parse

app = Flask(__name__)

@app.route('/')
def status():
    # Serve status.html from templates folder
    try:
        return render_template('status.html')
    except Exception as e:
        return jsonify({"status": "error", "message": "Status page not found. Please create status.html."}), 404

@app.route('/dl', methods=['GET'])
def download_pinterest_media():
    # Get Pinterest URL from query parameter
    pinterest_url = request.args.get('url', '').strip()
    
    if not pinterest_url:
        return jsonify({
            "status": "error",
            "input_url": pinterest_url,
            "message": "No URL provided",
            "api_dev": "@ISmartCoder",
            "updates_channel": "t.me/TheSmartDev"
        }), 400
    
    # API endpoint and parameters for savepin.app
    base_url = "https://www.savepin.app/download.php"
    params = {
        "url": pinterest_url,
        "lang": "en",
        "type": "redirect"
    }
    
    # Headers to mimic browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.savepin.app/"
    }
    
    try:
        # Send GET request to savepin.app
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Save full HTML response for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"pinterest_response_{timestamp}.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        # Parse HTML response with BeautifulSoup
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
                            # Decode URL to make it clean
                            media_url = urllib.parse.unquote(media_url)
                            download_links.append({
                                "quality": quality,
                                "url": media_url,
                                "type": f"{'image/jpeg' if format_type == 'jpg' else 'video/mp4'}"
                            })
        
        # Construct JSON response
        result = {
            "status": "success",
            "input_url": pinterest_url,
            "title": title,
            "media": download_links,
            "api_dev": "@ISmartCoder",
            "updates_channel": "t.me/TheSmartDev",
            "debug_file": debug_file
        }
        
        if not download_links:
            result["status"] = "error"
            result["message"] = "No media found for the provided URL"
            result["html_snippet"] = response.text[:500]
        
        return jsonify(result), 200
        
    except requests.exceptions.RequestException as e:
        # Handle errors
        error_response = {
            "status": "error",
            "input_url": pinterest_url,
            "message": f"Failed to fetch media: {str(e)}",
            "api_dev": "@ISmartCoder",
            "updates_channel": "t.me/TheSmartDev"
        }
        return jsonify(error_response), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
