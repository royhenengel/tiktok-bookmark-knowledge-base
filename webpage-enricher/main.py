"""
Webpage Enricher Cloud Function

Fetches webpages and extracts enriched metadata for the Bookmark Knowledge Base.

Responsibilities (per ARCHITECTURE.md):
- Fetch webpage content
- Extract metadata (title, author, publish date)
- Calculate reading time
- Detect content type
- Generate AI summary and analysis
- Extract price if product page
- Extract code snippets if dev resource

Does NOT:
- Write to Notion/Raindrop (n8n's job)
- Handle retries (n8n's job)
- Make routing decisions (n8n's job)
"""

import functions_framework
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import json
import os
import google.generativeai as genai
from datetime import datetime

# Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# URL patterns for type detection
VIDEO_PATTERNS = ['youtube.com', 'youtu.be', 'vimeo.com', 'tiktok.com', 'twitch.tv']
SOCIAL_PATTERNS = ['twitter.com', 'x.com', 'instagram.com', 'linkedin.com/posts', 'facebook.com', 'threads.net']
CODE_PATTERNS = ['github.com', 'gitlab.com', 'stackoverflow.com', 'codepen.io', 'jsfiddle.net', 'replit.com']
PRODUCT_PATTERNS = ['amazon.', 'ebay.', 'etsy.com', 'shopify.', 'aliexpress.', 'walmart.com', 'target.com']
PODCAST_PATTERNS = ['spotify.com/episode', 'podcasts.apple.com', 'overcast.fm', 'pocketcasts.com']


def detect_content_type(url: str, soup: BeautifulSoup) -> str:
    """Detect the type of content based on URL and page content."""
    domain = urlparse(url).netloc.lower()

    # Check URL patterns first
    for pattern in VIDEO_PATTERNS:
        if pattern in domain:
            return 'video'

    for pattern in PODCAST_PATTERNS:
        if pattern in url.lower():
            return 'podcast'

    for pattern in SOCIAL_PATTERNS:
        if pattern in domain:
            return 'social'

    for pattern in CODE_PATTERNS:
        if pattern in domain:
            return 'code'

    for pattern in PRODUCT_PATTERNS:
        if pattern in domain:
            return 'product'

    # Check page content for product indicators
    if soup:
        # Look for price indicators
        price_patterns = soup.find_all(attrs={'class': re.compile(r'price|cost|amount', re.I)})
        add_to_cart = soup.find_all(text=re.compile(r'add to cart|buy now|purchase', re.I))
        if price_patterns or add_to_cart:
            return 'product'

        # Look for code blocks
        code_blocks = soup.find_all(['pre', 'code'])
        if len(code_blocks) > 3:
            return 'code'

    return 'article'


def extract_metadata(url: str, soup: BeautifulSoup) -> dict:
    """Extract metadata from the webpage."""
    metadata = {
        'title': None,
        'author': None,
        'published_date': None,
        'main_image': None,
        'description': None,
    }

    if not soup:
        return metadata

    # Title - try multiple sources
    og_title = soup.find('meta', property='og:title')
    twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
    title_tag = soup.find('title')
    h1_tag = soup.find('h1')

    metadata['title'] = (
        og_title.get('content') if og_title else
        twitter_title.get('content') if twitter_title else
        title_tag.get_text(strip=True) if title_tag else
        h1_tag.get_text(strip=True) if h1_tag else
        None
    )

    # Author
    author_meta = soup.find('meta', attrs={'name': 'author'})
    author_prop = soup.find('meta', property='article:author')
    author_rel = soup.find('a', rel='author')
    author_class = soup.find(attrs={'class': re.compile(r'author|byline', re.I)})

    metadata['author'] = (
        author_meta.get('content') if author_meta else
        author_prop.get('content') if author_prop else
        author_rel.get_text(strip=True) if author_rel else
        author_class.get_text(strip=True) if author_class else
        None
    )

    # Clean up author if found
    if metadata['author']:
        metadata['author'] = re.sub(r'^by\s+', '', metadata['author'], flags=re.I).strip()

    # Published date
    date_meta = soup.find('meta', property='article:published_time')
    date_time = soup.find('time', attrs={'datetime': True})

    date_str = (
        date_meta.get('content') if date_meta else
        date_time.get('datetime') if date_time else
        None
    )

    if date_str:
        try:
            # Parse ISO format
            metadata['published_date'] = date_str[:10]  # Just YYYY-MM-DD
        except:
            pass

    # Main image
    og_image = soup.find('meta', property='og:image')
    twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})

    metadata['main_image'] = (
        og_image.get('content') if og_image else
        twitter_image.get('content') if twitter_image else
        None
    )

    # Description
    og_desc = soup.find('meta', property='og:description')
    meta_desc = soup.find('meta', attrs={'name': 'description'})

    metadata['description'] = (
        og_desc.get('content') if og_desc else
        meta_desc.get('content') if meta_desc else
        None
    )

    return metadata


def extract_main_content(soup: BeautifulSoup) -> str:
    """Extract the main text content from the page."""
    if not soup:
        return ""

    # Remove script, style, nav, footer, header elements
    for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
        element.decompose()

    # Try to find main content area
    main_content = (
        soup.find('article') or
        soup.find('main') or
        soup.find(attrs={'class': re.compile(r'content|post|article|entry', re.I)}) or
        soup.find('body')
    )

    if main_content:
        text = main_content.get_text(separator=' ', strip=True)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text[:15000]  # Limit to ~15k chars for AI processing

    return ""


def calculate_reading_time(text: str) -> int:
    """Calculate estimated reading time in minutes."""
    if not text:
        return 0

    # Average reading speed: 200-250 words per minute
    word_count = len(text.split())
    reading_time = max(1, round(word_count / 225))
    return reading_time


def extract_price(soup: BeautifulSoup) -> dict:
    """Extract price information from product pages."""
    result = {'price': None, 'currency': None}

    if not soup:
        return result

    # Common price patterns
    price_selectors = [
        {'class': re.compile(r'price', re.I)},
        {'itemprop': 'price'},
        {'data-price': True},
    ]

    for selector in price_selectors:
        element = soup.find(attrs=selector)
        if element:
            text = element.get_text(strip=True)
            # Extract price with regex
            match = re.search(r'[\$\£\€]?\s*(\d+(?:[.,]\d{2})?)', text)
            if match:
                price_str = match.group(1).replace(',', '.')
                try:
                    result['price'] = float(price_str)
                except:
                    pass

                # Detect currency
                if '$' in text:
                    result['currency'] = 'USD'
                elif '£' in text:
                    result['currency'] = 'GBP'
                elif '€' in text:
                    result['currency'] = 'EUR'

                break

    return result


def extract_code_snippets(soup: BeautifulSoup) -> list:
    """Extract code snippets from the page."""
    snippets = []

    if not soup:
        return snippets

    # Find code blocks
    code_blocks = soup.find_all(['pre', 'code'])

    for block in code_blocks:
        code = block.get_text(strip=True)
        if len(code) > 20 and len(code) < 5000:  # Reasonable code block size
            # Detect language from class
            classes = block.get('class', [])
            language = None
            for cls in classes:
                if 'language-' in cls:
                    language = cls.replace('language-', '')
                    break

            snippets.append({
                'code': code[:2000],  # Limit size
                'language': language
            })

    return snippets[:5]  # Max 5 snippets


def generate_ai_analysis(url: str, title: str, content: str, content_type: str) -> dict:
    """Generate AI-cleaned title, summary and analysis using Gemini."""
    result = {
        'title': title,  # Fallback to original
        'summary': None,
        'analysis': None,
        'error': None
    }

    if not GEMINI_API_KEY:
        result['error'] = 'GEMINI_API_KEY not configured'
        return result

    if not content or len(content) < 100:
        result['error'] = 'Insufficient content for analysis'
        return result

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')

        prompt = f"""Analyze this webpage and provide:

1. **Title**: Clean up the raw title. Keep it as close to the original as possible but:
   - Remove site names, separators like " | " or " - Site Name" at the end
   - Keep it under 100 characters
   - Make it descriptive and recognizable
   - If the title includes a long description after ":" or "-", keep only the main title part

2. **Summary**: A 2-3 sentence summary of what this page is about.

3. **Analysis**: Why might someone save this bookmark? What are the key takeaways or value? Who would find this useful?

URL: {url}
Raw Title: {title}
Content Type: {content_type}

Page Content:
{content[:10000]}

Respond in this exact JSON format:
{{
  "title": "Cleaned title here (max 100 chars)",
  "summary": "2-3 sentence summary here",
  "analysis": "Why this is useful, key takeaways, target audience"
}}
"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            parsed = json.loads(json_match.group())
            result['title'] = parsed.get('title') or title
            result['summary'] = parsed.get('summary')
            result['analysis'] = parsed.get('analysis')
        else:
            # Fallback: use whole response as analysis
            result['analysis'] = response_text

    except Exception as e:
        result['error'] = str(e)

    return result


def fetch_webpage(url: str) -> tuple:
    """Fetch webpage content. Returns (html, error)."""
    try:
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()

        return response.text, None

    except requests.exceptions.Timeout:
        return None, 'Request timed out'
    except requests.exceptions.HTTPError as e:
        return None, f'HTTP error: {e.response.status_code}'
    except requests.exceptions.RequestException as e:
        return None, f'Request failed: {str(e)}'


@functions_framework.http
def enrich_webpage(request):
    """
    Main Cloud Function entry point.

    Expected JSON input:
    {
        "url": "https://example.com/article",
        "options": {
            "skip_ai": false,
            "extract_code": true
        }
    }
    """
    # Handle CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        request_json = request.get_json(silent=True)

        if not request_json or 'url' not in request_json:
            return (json.dumps({
                'error': 'Missing required field: url'
            }), 400, headers)

        url = request_json['url']
        options = request_json.get('options', {})
        skip_ai = options.get('skip_ai', False)
        extract_code = options.get('extract_code', True)

        # Extract domain
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')

        # Fetch the webpage
        html, fetch_error = fetch_webpage(url)

        if fetch_error:
            return (json.dumps({
                'url': url,
                'domain': domain,
                'error': {
                    'stage': 'fetch',
                    'message': fetch_error,
                    'recoverable': True
                }
            }), 200, headers)  # Return 200 with error in body per ARCHITECTURE.md

        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Detect content type
        content_type = detect_content_type(url, soup)

        # Extract metadata
        metadata = extract_metadata(url, soup)

        # Extract main content
        main_content = extract_main_content(soup)

        # Calculate reading time
        reading_time = calculate_reading_time(main_content) if content_type == 'article' else None

        # Extract price if product
        price_info = extract_price(soup) if content_type == 'product' else {'price': None, 'currency': None}

        # Extract code snippets if code resource
        code_snippets = extract_code_snippets(soup) if (content_type == 'code' and extract_code) else []

        # Generate AI analysis (includes cleaned title)
        ai_result = {'title': metadata['title'], 'summary': None, 'analysis': None, 'error': None}
        if not skip_ai:
            ai_result = generate_ai_analysis(url, metadata['title'], main_content, content_type)

        # Build response - use AI-cleaned title
        response = {
            'url': url,
            'domain': domain,
            'type': content_type,
            'title': ai_result.get('title') or metadata['title'],
            'author': metadata['author'],
            'published_date': metadata['published_date'],
            'main_image': metadata['main_image'],
            'description': metadata['description'],
            'reading_time': reading_time,
            'price': price_info['price'],
            'currency': price_info['currency'],
            'code_snippets': code_snippets,
            'ai_summary': ai_result['summary'],
            'ai_analysis': ai_result['analysis'],
            'processed_at': datetime.utcnow().isoformat() + 'Z',
        }

        # Include errors if any (partial success per ARCHITECTURE.md)
        if ai_result.get('error'):
            response['error'] = {
                'stage': 'ai_analysis',
                'message': ai_result['error'],
                'recoverable': True
            }

        return (json.dumps(response), 200, headers)

    except Exception as e:
        return (json.dumps({
            'error': {
                'stage': 'processing',
                'message': str(e),
                'recoverable': False
            }
        }), 500, headers)
