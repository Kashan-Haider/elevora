import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import re
import concurrent.futures
import time
from collections import Counter
import hashlib
from datetime import datetime
from models.page import Page
from models.audit_detail import AuditDetail
from uuid import uuid4

class SEOAudit:
    def __init__(self, url, user_agent=None, depth=0, max_pages=1):
        self.base_url = url
        self.domain = urlparse(url).netloc
        self.scheme = urlparse(url).scheme
        self.depth = depth
        self.max_pages = max_pages
        self.pages_audited = 0
        self.visited_urls = set()
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; SEOAuditBot/1.0; +https://example.com/bot)"
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.all_results = {}

    def fetch_html(self, url, retry=2):
        attempt = 0
        while attempt <= retry:
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                return response.text
            except requests.RequestException:
                attempt += 1
                if attempt > retry:
                    return None
                time.sleep(1)

    def is_valid_internal_url(self, url):
        if not url or not url.startswith(('http://', 'https://')):
            return False
        parsed_url = urlparse(url)
        return parsed_url.netloc == self.domain

    def extract_seo_data(self, html, page_url):
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        data = {
            "page_url": page_url,
            "content_hash": hashlib.md5(html.encode()).hexdigest(),
            "page_size_bytes": len(html),
        }
        
        data["title"] = soup.title.string.strip() if soup.title else None
        data["title_length"] = len(data["title"]) if data["title"] else 0
        
        meta_description = soup.find("meta", attrs={"name": "description"})
        data["meta_description"] = meta_description.get("content", "").strip() if meta_description else None
        data["meta_description_length"] = len(data["meta_description"]) if data["meta_description"] else 0
        
        data["meta_robots"] = soup.find("meta", attrs={"name": "robots"}).get("content", "").strip() if soup.find("meta", attrs={"name": "robots"}) else None
        data["meta_keywords"] = soup.find("meta", attrs={"name": "keywords"}).get("content", "").strip() if soup.find("meta", attrs={"name": "keywords"}) else None
        data["meta_viewport"] = soup.find("meta", attrs={"name": "viewport"}).get("content", "").strip() if soup.find("meta", attrs={"name": "viewport"}) else None
        data["meta_charset"] = soup.find("meta", attrs={"charset": True}).get("charset", "").strip() if soup.find("meta", attrs={"charset": True}) else None
        data["meta_og_tags"] = self._extract_og_tags(soup)
        data["meta_twitter_tags"] = self._extract_twitter_tags(soup)

        canonical = soup.find("link", rel="canonical")
        data["canonical_url"] = canonical["href"].strip() if canonical and canonical.has_attr("href") else None
        data["canonical_matches_url"] = (data["canonical_url"] == page_url) if data["canonical_url"] else False

        headings = {}
        for i in range(1, 7):
            tag = f"h{i}"
            headings[tag] = [{"text": h.get_text(strip=True), "length": len(h.get_text(strip=True))} for h in soup.find_all(tag)]
        data["headings"] = headings
        data["headings_count"] = {f"h{i}": len(headings[f"h{i}"]) for i in range(1, 7)}
        
        data["paragraphs"] = [p.get_text(strip=True) for p in soup.find_all("p")]
        data["paragraphs_count"] = len(data["paragraphs"])
        data["word_count"] = self._calculate_word_count(soup)
        data["text_html_ratio"] = self._calculate_text_html_ratio(soup, html)
        data["keywords_density"] = self._extract_keyword_density(soup)

        data["strong_tags"] = [s.get_text(strip=True) for s in soup.find_all("strong")]
        data["strong_tags_count"] = len(data["strong_tags"])
        data["em_tags"] = [e.get_text(strip=True) for e in soup.find_all("em")]
        data["em_tags_count"] = len(data["em_tags"])
        data["b_tags"] = [b.get_text(strip=True) for b in soup.find_all("b")]
        data["b_tags_count"] = len(data["b_tags"])
        data["i_tags"] = [i.get_text(strip=True) for i in soup.find_all("i")]
        data["i_tags_count"] = len(data["i_tags"])

        images = []
        for img in soup.find_all("img"):
            image_data = {
                "src": urljoin(page_url, img.get("src")) if img.get("src") else None,
                "alt": img.get("alt", "").strip(),
                "alt_length": len(img.get("alt", "").strip()) if img.get("alt") else 0,
                "title": img.get("title", "").strip(),
                "width": img.get("width"),
                "height": img.get("height"),
                "lazy_loaded": img.has_attr("loading") and img["loading"] == "lazy"
            }
            images.append(image_data)
        data["images"] = images
        data["images_with_alt"] = sum(1 for img in images if img["alt"])
        data["images_without_alt"] = sum(1 for img in images if not img["alt"] and img["src"])
        data["total_images"] = len(images)
        data["images_with_alt_percentage"] = round((data["images_with_alt"] / data["total_images"]) * 100, 2) if data["total_images"] > 0 else 0
        
        internal_links = []
        external_links = []
        
        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            if not href or href.startswith('#'):
                continue
                
            full_url = urljoin(page_url, href)
            parsed_url = urlparse(full_url)
            
            link_data = {
                "href": full_url,
                "text": a.get_text(strip=True),
                "text_length": len(a.get_text(strip=True)),
                "title": a.get("title", "").strip(),
                "nofollow": "nofollow" in a.get("rel", ""),
                "has_text": bool(a.get_text(strip=True)),
            }
            
            if parsed_url.netloc == self.domain:
                internal_links.append(link_data)
            else:
                external_links.append(link_data)
                
        data["internal_links"] = internal_links
        data["external_links"] = external_links
        data["total_links"] = len(internal_links) + len(external_links)
        data["internal_links_count"] = len(internal_links)
        data["external_links_count"] = len(external_links)
        data["internal_links_with_text"] = sum(1 for link in internal_links if link["has_text"])
        data["external_links_with_text"] = sum(1 for link in external_links if link["has_text"])
        data["internal_links_with_text_percentage"] = round((data["internal_links_with_text"] / data["internal_links_count"]) * 100, 2) if data["internal_links_count"] > 0 else 0
        data["external_links_with_nofollow"] = sum(1 for link in external_links if link["nofollow"])
        data["external_links_with_nofollow_percentage"] = round((data["external_links_with_nofollow"] / data["external_links_count"]) * 100, 2) if data["external_links_count"] > 0 else 0

        structured_data = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if script.string:
                    json_content = json.loads(script.string)
                    structured_data.append(json_content)
            except:
                continue
        data["structured_data"] = structured_data
        data["has_structured_data"] = len(structured_data) > 0
        data["structured_data_count"] = len(structured_data)
        data["structured_data_types"] = [self._get_schema_type(sd) for sd in structured_data]

        data["videos"] = [{"src": urljoin(page_url, video.get("src"))} for video in soup.find_all("video") if video.get("src")]
        data["videos_count"] = len(data["videos"])
        data["audios"] = [{"src": urljoin(page_url, audio.get("src"))} for audio in soup.find_all("audio") if audio.get("src")]
        data["audios_count"] = len(data["audios"])

        data["script_sources"] = [urljoin(page_url, script.get("src")) for script in soup.find_all("script") if script.get("src")]
        data["script_sources_count"] = len(data["script_sources"])
        data["style_links"] = [urljoin(page_url, link.get("href")) for link in soup.find_all("link", rel="stylesheet") if link.get("href")]
        data["style_links_count"] = len(data["style_links"])
        data["inline_styles"] = len(soup.find_all("style"))
        data["inline_scripts"] = sum(1 for s in soup.find_all("script") if not s.get("src") and s.string)

        favicon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        data["favicon"] = urljoin(page_url, favicon["href"]) if favicon and favicon.has_attr("href") else None
        data["has_favicon"] = bool(data["favicon"])

        html_tag = soup.find("html")
        data["language"] = html_tag.get("lang", "").strip() if html_tag and html_tag.has_attr("lang") else None
        data["has_language"] = bool(data["language"])

        data["has_viewport_meta"] = bool(data["meta_viewport"])
        data["has_mobile_friendly_design"] = self._check_mobile_friendly(soup)

        data["resource_hints"] = self._extract_resource_hints(soup, page_url)
        data["has_https"] = page_url.startswith("https://")
        data["hreflang_tags"] = self._extract_hreflang_tags(soup)
        data["has_hreflang"] = len(data["hreflang_tags"]) > 0
        data["has_doctype"] = bool(soup.find("doctype") or soup.find("!DOCTYPE"))
        
        return data

    def _extract_og_tags(self, soup):
        og_tags = {}
        for tag in soup.find_all("meta", property=re.compile(r"^og:")):
            name = tag.get("property", "").strip()
            content = tag.get("content", "").strip()
            if name and content:
                og_tags[name] = content
        return og_tags

    def _extract_twitter_tags(self, soup):
        twitter_tags = {}
        for tag in soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")}):
            name = tag.get("name", "").strip()
            content = tag.get("content", "").strip()
            if name and content:
                twitter_tags[name] = content
        return twitter_tags

    def _calculate_word_count(self, soup):
        text = soup.body.get_text(" ", strip=True) if soup.body else ""
        for script in soup.find_all(["script", "style"]):
            script.extract()
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        return len(cleaned_text.split())

    def _calculate_text_html_ratio(self, soup, html):
        for script in soup.find_all(["script", "style"]):
            script.extract()
        text = soup.get_text(" ", strip=True)
        if not html:
            return 0
        text_length = len(text)
        html_length = len(html)
        return round((text_length / html_length) * 100, 2) if html_length > 0 else 0

    def _extract_keyword_density(self, soup):
        for script in soup.find_all(["script", "style"]):
            script.extract()
        text = soup.get_text(" ", strip=True)
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                     'have', 'has', 'had', 'be', 'been', 'being', 'to', 'of', 'for', 
                     'with', 'by', 'on', 'at', 'in', 'this', 'that', 'these', 'those'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        word_count = Counter(filtered_words)
        total_words = len(filtered_words)
        densities = {}
        if total_words > 0:
            for word, count in word_count.most_common(20):
                densities[word] = {
                    "count": count,
                    "density": round((count / total_words) * 100, 2)
                }
        return densities
    
    def _check_mobile_friendly(self, soup):
        viewport = soup.find("meta", attrs={"name": "viewport"})
        has_viewport = viewport and "width=device-width" in viewport.get("content", "")
        style_tags = soup.find_all("style")
        has_media_queries = any("@media" in style.string for style in style_tags if style.string)
        return has_viewport or has_media_queries

    def _extract_resource_hints(self, soup, base_url):
        hints = {
            "preload": [],
            "prefetch": [],
            "preconnect": [],
            "dns-prefetch": []
        }
        for link in soup.find_all("link", rel=True):
            rel = link.get("rel", [""])[0] if isinstance(link.get("rel"), list) else link.get("rel", "")
            if rel in hints and link.get("href"):
                hints[rel].append(urljoin(base_url, link.get("href")))
        return hints
        
    def _extract_hreflang_tags(self, soup):
        hreflang_tags = []
        for link in soup.find_all("link", rel="alternate", hreflang=True):
            if link.get("href"):
                hreflang_tags.append({
                    "hreflang": link.get("hreflang"),
                    "href": link.get("href")
                })
        return hreflang_tags

    def calculate_scorecard(self, data):
        if not data:
            return {"total_score": 0, "categories": {}}
            
        scorecard = {
            "metadata": {
                "title": {"score": 0, "max_score": 10, "details": {}},
                "meta_description": {"score": 0, "max_score": 10, "details": {}},
                "other_meta_tags": {"score": 0, "max_score": 10, "details": {}}
            },
            "content": {
                "headings": {"score": 0, "max_score": 15, "details": {}},
                "content_quality": {"score": 0, "max_score": 15, "details": {}},
                "keyword_optimization": {"score": 0, "max_score": 10, "details": {}}
            },
            "media": {
                "images": {"score": 0, "max_score": 10, "details": {}},
                "videos_and_audio": {"score": 0, "max_score": 5, "details": {}}
            },
            "technical": {
                "structured_data": {"score": 0, "max_score": 10, "details": {}},
                "mobile_friendly": {"score": 0, "max_score": 10, "details": {}},
                "page_speed_indicators": {"score": 0, "max_score": 10, "details": {}},
                "security": {"score": 0, "max_score": 5, "details": {}}
            },
            "links": {
                "internal_links": {"score": 0, "max_score": 10, "details": {}},
                "external_links": {"score": 0, "max_score": 5, "details": {}},
                "canonical": {"score": 0, "max_score": 5, "details": {}}
            },
            "international": {
                "language": {"score": 0, "max_score": 5, "details": {}},
                "hreflang": {"score": 0, "max_score": 5, "details": {}}
            }
        }
        
        title_score = scorecard["metadata"]["title"]
        if data.get("title"):
            title_length = data.get("title_length", 0)
            if 30 <= title_length <= 60:
                title_score["score"] = 10
                title_score["details"]["status"] = "optimal"
            elif 20 <= title_length < 30 or 60 < title_length <= 70:
                title_score["score"] = 7
                title_score["details"]["status"] = "acceptable"
            else:
                title_score["score"] = 4
                title_score["details"]["status"] = "needs improvement"
        else:
            title_score["details"]["status"] = "missing"
        title_score["details"]["length"] = data.get("title_length", 0)
        title_score["details"]["recommendations"] = []
        if not data.get("title"):
            title_score["details"]["recommendations"].append("Add a title tag")
        elif data.get("title_length", 0) < 30:
            title_score["details"]["recommendations"].append("Title is too short, aim for 30-60 characters")
        elif data.get("title_length", 0) > 60:
            title_score["details"]["recommendations"].append("Title may be truncated in search results, consider shortening")
            
        meta_desc_score = scorecard["metadata"]["meta_description"]
        if data.get("meta_description"):
            desc_length = data.get("meta_description_length", 0)
            if 120 <= desc_length <= 160:
                meta_desc_score["score"] = 10
                meta_desc_score["details"]["status"] = "optimal"
            elif 80 <= desc_length < 120 or 160 < desc_length <= 200:
                meta_desc_score["score"] = 7
                meta_desc_score["details"]["status"] = "acceptable"
            else:
                meta_desc_score["score"] = 4
                meta_desc_score["details"]["status"] = "needs improvement"
        else:
            meta_desc_score["details"]["status"] = "missing"
        meta_desc_score["details"]["length"] = data.get("meta_description_length", 0)
        meta_desc_score["details"]["recommendations"] = []
        if not data.get("meta_description"):
            meta_desc_score["details"]["recommendations"].append("Add a meta description")
        elif data.get("meta_description_length", 0) < 120:
            meta_desc_score["details"]["recommendations"].append("Meta description is too short, aim for 120-160 characters")
        elif data.get("meta_description_length", 0) > 160:
            meta_desc_score["details"]["recommendations"].append("Meta description may be truncated in search results")
            
        other_meta_score = scorecard["metadata"]["other_meta_tags"]
        other_meta_score["score"] = 0
        if data.get("meta_robots"): other_meta_score["score"] += 2
        if data.get("meta_viewport"): other_meta_score["score"] += 3
        if data.get("meta_charset"): other_meta_score["score"] += 1
        if data.get("meta_og_tags") and len(data.get("meta_og_tags", {})) >= 3: other_meta_score["score"] += 2
        if data.get("meta_twitter_tags") and len(data.get("meta_twitter_tags", {})) >= 2: other_meta_score["score"] += 2
        other_meta_score["details"]["present_tags"] = []
        other_meta_score["details"]["missing_tags"] = []
        other_meta_score["details"]["recommendations"] = []
        if data.get("meta_robots"):
            other_meta_score["details"]["present_tags"].append("robots")
        else:
            other_meta_score["details"]["missing_tags"].append("robots")
            other_meta_score["details"]["recommendations"].append("Add a meta robots tag")
        if data.get("meta_viewport"):
            other_meta_score["details"]["present_tags"].append("viewport")
        else:
            other_meta_score["details"]["missing_tags"].append("viewport")
            other_meta_score["details"]["recommendations"].append("Add a viewport meta tag for mobile optimization")
        if not data.get("meta_og_tags"):
            other_meta_score["details"]["missing_tags"].append("Open Graph tags")
            other_meta_score["details"]["recommendations"].append("Add Open Graph meta tags for better social sharing")
        
        headings_score = scorecard["content"]["headings"]
        headings_score["details"]["counts"] = {}
        for tag, headings in data.get("headings", {}).items():
            headings_score["details"]["counts"][tag] = len(headings)
        has_h1 = headings_score["details"]["counts"].get("h1", 0) > 0
        has_single_h1 = headings_score["details"]["counts"].get("h1", 0) == 1
        has_h2 = headings_score["details"]["counts"].get("h2", 0) > 0
        has_structure = all(headings_score["details"]["counts"].get(f"h{i}", 0) >= 
                           headings_score["details"]["counts"].get(f"h{i+1}", 0) 
                           for i in range(1, 5))
        headings_score["details"]["recommendations"] = []
        if has_single_h1 and has_h2 and has_structure:
            headings_score["score"] = 15
            headings_score["details"]["status"] = "optimal"
        elif has_h1 and has_h2:
            headings_score["score"] = 10
            headings_score["details"]["status"] = "good"
            if not has_single_h1:
                headings_score["details"]["recommendations"].append("Use exactly one H1 tag per page")
            if not has_structure:
                headings_score["details"]["recommendations"].append("Improve heading hierarchy structure")
        elif has_h1 or has_h2:
            headings_score["score"] = 5
            headings_score["details"]["status"] = "needs improvement"
            if not has_h1:
                headings_score["details"]["recommendations"].append("Add an H1 tag that includes your primary keyword")
            if not has_h2:
                headings_score["details"]["recommendations"].append("Add H2 tags to structure your content")
        else:
            headings_score["score"] = 0
            headings_score["details"]["status"] = "poor"
            headings_score["details"]["recommendations"].append("Add proper heading structure with H1 and H2 tags")
            
        content_score = scorecard["content"]["content_quality"]
        word_count = data.get("word_count", 0)
        text_html_ratio = data.get("text_html_ratio", 0)
        content_score["details"] = {
            "word_count": word_count,
            "text_html_ratio": text_html_ratio,
            "recommendations": []
        }
        if word_count >= 800:
            content_score["score"] += 8
        elif word_count >= 500:
            content_score["score"] += 5
        elif word_count >= 300:
            content_score["score"] += 3
        else:
            content_score["details"]["recommendations"].append("Add more content, aim for at least 500 words")
        if text_html_ratio >= 25:
            content_score["score"] += 7
        elif text_html_ratio >= 15:
            content_score["score"] += 4
        else:
            content_score["score"] += 2
            content_score["details"]["recommendations"].append("Improve text to HTML ratio, aim for at least 15%")
        content_score["score"] = min(content_score["score"], 15)
        
        keyword_score = scorecard["content"]["keyword_optimization"]
        keyword_densities = data.get("keywords_density", {})
        top_keywords = []
        if keyword_densities:
            top_keywords = sorted(keyword_densities.items(), key=lambda x: x[1]["density"], reverse=True)[:5]
        keyword_score["details"] = {
            "top_keywords": [{k: v} for k, v in top_keywords],
            "recommendations": []
        }
        if top_keywords:
            title_keywords = [kw for kw, _ in top_keywords if data.get("title") and kw.lower() in data.get("title", "").lower()]
            h1_keywords = []
            for h1 in data.get("headings", {}).get("h1", []):
                h1_text = h1.get("text", "").lower()
                h1_keywords.extend([kw for kw, _ in top_keywords if kw.lower() in h1_text])
            optimal_density = any(1.5 <= info["density"] <= 2.5 for _, info in top_keywords[:3])
            if title_keywords and h1_keywords and optimal_density:
                keyword_score["score"] = 10
            elif title_keywords or h1_keywords:
                keyword_score["score"] = 6
                if not title_keywords:
                    keyword_score["details"]["recommendations"].append("Include main keywords in the page title")
                if not h1_keywords:
                    keyword_score["details"]["recommendations"].append("Include main keywords in the H1 heading")
                if not optimal_density:
                    keyword_score["details"]["recommendations"].append("Aim for keyword density between 1.5-2.5% for primary keywords")
            else:
                keyword_score["score"] = 3
                keyword_score["details"]["recommendations"].append("Improve keyword usage in title, headings, and content")
        else:
            keyword_score["details"]["recommendations"].append("Add more focused content around target keywords")
            
        images_score = scorecard["media"]["images"]
        images_count = data.get("total_images", 0)
        images_with_alt = data.get("images_with_alt", 0)
        images_score["details"] = {
            "total_images": images_count,
            "images_with_alt": images_with_alt,
            "images_without_alt": data.get("images_without_alt", 0),
            "alt_percentage": round((images_with_alt / images_count) * 100, 1) if images_count > 0 else 0,
            "recommendations": []
        }
        if images_count > 0:
            if images_with_alt == images_count:
                images_score["score"] = 10
            elif images_with_alt / images_count >= 0.8:
                images_score["score"] = 8
                images_score["details"]["recommendations"].append("Add alt text to all remaining images")
            elif images_with_alt / images_count >= 0.5:
                images_score["score"] = 5
                images_score["details"]["recommendations"].append("Add descriptive alt text to more images")
            else:
                images_score["score"] = 3
                images_score["details"]["recommendations"].append("Add alt text to images for accessibility and SEO")
        else:
            images_score["score"] = 5
            images_score["details"]["recommendations"].append("Consider adding relevant images with alt text")
            
        media_score = scorecard["media"]["videos_and_audio"]
        has_video = bool(data.get("videos"))
        has_audio = bool(data.get("audios"))
        media_score["details"] = {
            "videos_count": len(data.get("videos", [])),
            "audios_count": len(data.get("audios", [])),
            "recommendations": []
        }
        if has_video or has_audio:
            media_score["score"] = 5
        else:
            media_score["score"] = 0
            media_score["details"]["recommendations"].append("Consider adding multimedia content for engagement")
            
        sd_score = scorecard["technical"]["structured_data"]
        has_structured_data = data.get("has_structured_data", False)
        structured_data_count = len(data.get("structured_data", []))
        sd_score["details"] = {
            "present": has_structured_data,
            "count": structured_data_count,
            "types": [self._get_schema_type(sd) for sd in data.get("structured_data", [])],
            "recommendations": []
        }
        if has_structured_data:
            sd_score["score"] = 10 if structured_data_count >= 2 else 7
        else:
            sd_score["score"] = 0
            sd_score["details"]["recommendations"].append("Add structured data like Schema.org markup")
            
        mobile_score = scorecard["technical"]["mobile_friendly"]
        mobile_score["details"] = {
            "has_viewport_meta": data.get("has_viewport_meta", False),
            "has_mobile_friendly_design": data.get("has_mobile_friendly_design", False),
            "recommendations": []
        }
        if data.get("has_viewport_meta") and data.get("has_mobile_friendly_design"):
            mobile_score["score"] = 10
        elif data.get("has_viewport_meta"):
            mobile_score["score"] = 7
            mobile_score["details"]["recommendations"].append("Ensure design is fully responsive")
        else:
            mobile_score["score"] = 0
            mobile_score["details"]["recommendations"].append("Add viewport meta tag and ensure mobile-friendly design")
            
        speed_score = scorecard["technical"]["page_speed_indicators"]
        resource_hints = data.get("resource_hints", {})
        has_preload = bool(resource_hints.get("preload"))
        has_prefetch = bool(resource_hints.get("prefetch"))
        has_preconnect = bool(resource_hints.get("preconnect"))
        has_dns_prefetch = bool(resource_hints.get("dns-prefetch"))
        speed_score["details"] = {
            "resource_hints_used": [k for k, v in resource_hints.items() if v],
            "resource_hints_missing": [k for k, v in resource_hints.items() if not v],
            "js_resources": len(data.get("script_sources", [])),
            "css_resources": len(data.get("style_links", [])),
            "inline_styles": data.get("inline_styles", 0),
            "inline_scripts": data.get("inline_scripts", 0),
            "page_size_kb": round(data.get("page_size_bytes", 0) / 1024, 2),
            "recommendations": []
        }
        resource_hint_score = 0
        if has_preload: resource_hint_score += 2
        if has_prefetch: resource_hint_score += 2
        if has_preconnect or has_dns_prefetch: resource_hint_score += 2
        page_size_kb = data.get("page_size_bytes", 0) / 1024
        size_score = 5 if page_size_kb < 100 else (3 if page_size_kb < 200 else 1)
        speed_score["score"] = min(resource_hint_score + size_score, 10)
        if not has_preload and not has_prefetch:
            speed_score["details"]["recommendations"].append("Use preload/prefetch resource hints for critical resources")
        if not has_preconnect and not has_dns_prefetch:
            speed_score["details"]["recommendations"].append("Use preconnect/dns-prefetch for external domains")
        if page_size_kb >= 200:
            speed_score["details"]["recommendations"].append("Reduce page size to improve load speed")

        security_score = scorecard["technical"]["security"]
        security_score["details"] = {
            "has_https": data.get("has_https", False),
            "has_content_security_policy": "Content-Security-Policy" in data.get("headers", {}),
            "recommendations": []
        }
        if data.get("has_https"):
            security_score["score"] = 5
        else:
            security_score["score"] = 0
            security_score["details"]["recommendations"].append("Switch to HTTPS for secure connections")

        internal_links_score = scorecard["links"]["internal_links"]
        internal_links = data.get("internal_links", [])
        internal_links_count = len(internal_links)
        internal_links_with_text = sum(1 for link in internal_links if link.get("has_text"))
        internal_links_score["details"] = {
            "count": internal_links_count,
            "with_descriptive_text": internal_links_with_text,
            "recommendations": []
        }
        if internal_links_count >= 3:
            if internal_links_with_text == internal_links_count:
                internal_links_score["score"] = 10
            elif internal_links_with_text / internal_links_count >= 0.8:
                internal_links_score["score"] = 8
                internal_links_score["details"]["recommendations"].append("Add descriptive text to all internal links")
            else:
                internal_links_score["score"] = 5
                internal_links_score["details"]["recommendations"].append("Add descriptive anchor text to internal links")
        else:
            internal_links_score["score"] = 3
            internal_links_score["details"]["recommendations"].append("Add more internal links to improve site structure")

        external_links_score = scorecard["links"]["external_links"]
        external_links = data.get("external_links", [])
        external_links_count = len(external_links)
        external_links_with_nofollow = sum(1 for link in external_links if link.get("nofollow"))
        external_links_score["details"] = {
            "count": external_links_count,
            "with_nofollow": external_links_with_nofollow,
            "recommendations": []
        }
        if external_links_count > 0:
            if external_links_count <= 100:
                external_links_score["score"] = 5
            else:
                external_links_score["score"] = 3
                external_links_score["details"]["recommendations"].append("Too many external links may dilute page authority")
        else:
            external_links_score["score"] = 2
            external_links_score["details"]["recommendations"].append("Consider adding a few high-quality external links")

        canonical_score = scorecard["links"]["canonical"]
        has_canonical = bool(data.get("canonical_url"))
        canonical_matches = data.get("canonical_matches_url", False)
        canonical_score["details"] = {
            "has_canonical": has_canonical,
            "canonical_matches_url": canonical_matches,
            "canonical_url": data.get("canonical_url"),
            "recommendations": []
        }
        if has_canonical:
            if canonical_matches:
                canonical_score["score"] = 5
            else:
                canonical_score["score"] = 3
                canonical_score["details"]["recommendations"].append("Canonical URL does not match page URL")
        else:
            canonical_score["score"] = 0
            canonical_score["details"]["recommendations"].append("Add canonical tag to prevent duplicate content issues")

        language_score = scorecard["international"]["language"]
        has_language = bool(data.get("language"))
        language_score["details"] = {
            "has_language_attribute": has_language,
            "language": data.get("language"),
            "recommendations": []
        }
        if has_language:
            language_score["score"] = 5
        else:
            language_score["score"] = 0
            language_score["details"]["recommendations"].append("Add lang attribute to html tag")

        hreflang_score = scorecard["international"]["hreflang"]
        has_hreflang = bool(data.get("hreflang_tags"))
        hreflang_score["details"] = {
            "has_hreflang": has_hreflang,
            "hreflang_count": len(data.get("hreflang_tags", [])),
            "recommendations": []
        }
        if has_hreflang:
            hreflang_score["score"] = 5
        else:
            hreflang_score["score"] = 0
            hreflang_score["details"]["recommendations"].append("Add hreflang tags if targeting multiple languages/regions")

        total_max_score = sum(category["max_score"] for section in scorecard.values() for category in section.values())
        total_score = sum(category["score"] for section in scorecard.values() for category in section.values())
        scorecard["total_score"] = round((total_score / total_max_score) * 100) if total_max_score > 0 else 0
        
        return scorecard

    def _get_schema_type(self, schema_data):
        if isinstance(schema_data, dict):
            return schema_data.get("@type", "Unknown")
        return "Unknown"

    def extract_links(self, html, base_url):
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            if not href or href.startswith('#'):
                continue
            full_url = urljoin(base_url, href)
            if self.is_valid_internal_url(full_url):
                links.append(full_url)
        return links

    def crawl_page(self, url, current_depth=0):
        self.pages_audited += 1
        if url in self.visited_urls or self.pages_audited > self.max_pages:
            return

        self.visited_urls.add(url)
        html = self.fetch_html(url)
        if not html:
            return

        data = self.extract_seo_data(html, url)
        scorecard = self.calculate_scorecard(data)
        self.all_results[url] = {
            "data": data,
            "scorecard": scorecard
        }
        
        if current_depth < self.depth:
            links = self.extract_links(html, url)
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(self.crawl_page, link, current_depth + 1)
                    for link in links if link not in self.visited_urls
                ]
                concurrent.futures.wait(futures)

    def generate_summary(self):
        summary = {
            "audit_info": {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "base_url": self.base_url,
                "pages_audited": len(self.all_results),
                "max_depth": self.depth
            },
            "overall_score": {
                "score": 0,
                "max_score": 100
            },
            "category_scores": {},
            "top_issues": [],
            "pages": {}
        }
        
        if not self.all_results:
            return summary
            
        total_score = 0
        category_counter = {}
        all_recommendations = []
        
        for url, result in self.all_results.items():
            page_scorecard = result.get("scorecard", {})
            page_score = page_scorecard.get("total_score", 0)
            summary["pages"][url] = {
                "score": page_score,
                "title": result.get("data", {}).get("title", "Unknown Page")
            }
            total_score += page_score
            
            for section_name, section in page_scorecard.items():
                if section_name == "total_score":
                    continue
                    
                for category_name, category in section.items():
                    key = f"{section_name}.{category_name}"
                    if key not in category_counter:
                        category_counter[key] = {
                            "total_score": 0,
                            "count": 0,
                            "max_score": category.get("max_score", 0),
                            "section": section_name,
                            "category": category_name
                        }
                    
                    category_counter[key]["total_score"] += category.get("score", 0)
                    category_counter[key]["count"] += 1
                    
                    recommendations = category.get("details", {}).get("recommendations", [])
                    if recommendations:
                        all_recommendations.extend([(r, key, category.get("score", 0), category.get("max_score", 0)) for r in recommendations])
        
        num_pages = len(self.all_results) or 1
        summary["overall_score"]["score"] = round(total_score / num_pages)
        
        for key, data in category_counter.items():
            if data["count"] > 0:
                avg_score = data["total_score"] / data["count"]
                percentage = round((avg_score / data["max_score"]) * 100) if data["max_score"] > 0 else 0
                
                if data["section"] not in summary["category_scores"]:
                    summary["category_scores"][data["section"]] = {}
                    
                summary["category_scores"][data["section"]][data["category"]] = {
                    "score": percentage,
                    "avg_points": round(avg_score, 1),
                    "max_points": data["max_score"]
                }
        
        recommendation_counter = {}
        for rec, key, score, max_score in all_recommendations:
            if rec not in recommendation_counter:
                recommendation_counter[rec] = {
                    "count": 0,
                    "category": key,
                    "importance": (max_score - score) / max_score if max_score > 0 else 0
                }
            recommendation_counter[rec]["count"] += 1
        
        sorted_recommendations = sorted(
            [(rec, data) for rec, data in recommendation_counter.items()],
            key=lambda x: (x[1]["importance"], x[1]["count"]),
            reverse=True
        )
        
        summary["top_issues"] = [
            {
                "issue": rec,
                "count": data["count"],
                "category": data["category"],
                "importance": round(data["importance"] * 10)
            }
            for rec, data in sorted_recommendations[:10]
        ]
        
        return summary

    def run(self):
        self.crawl_page(self.base_url)
        return {
            "summary": self.generate_summary(),
            "detailed_results": self.all_results
        }


def save_audit_details(session, audit_id, data, scorecard):
    """
    Save detailed audit metrics for visualization purposes
    """
    detail_records = []
    
    # Metadata metrics
    if data.get("title"):
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="metadata",
            subcategory="title",
            metric_name="title_length",
            metric_value=data.get("title_length", 0),
            text_value=data.get("title")
        ))
        
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="metadata",
            subcategory="title",
            metric_name="score",
            metric_value=scorecard["metadata"]["title"]["score"]
        ))
        
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="metadata",
            subcategory="title",
            metric_name="status",
            text_value=scorecard["metadata"]["title"]["details"].get("status")
        ))
    
    if data.get("meta_description"):
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="metadata",
            subcategory="meta_description",
            metric_name="meta_description_length",
            metric_value=data.get("meta_description_length", 0),
            text_value=data.get("meta_description")
        ))
        
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="metadata",
            subcategory="meta_description",
            metric_name="score",
            metric_value=scorecard["metadata"]["meta_description"]["score"]
        ))
        
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="metadata",
            subcategory="meta_description",
            metric_name="status",
            text_value=scorecard["metadata"]["meta_description"]["details"].get("status")
        ))
    
    # Other meta tags
    meta_tags = ["meta_robots", "meta_viewport", "meta_charset", "meta_keywords"]
    for tag in meta_tags:
        if data.get(tag):
            detail_records.append(AuditDetail(
                audit_id=audit_id,
                category="metadata",
                subcategory="other_meta_tags",
                metric_name=tag,
                text_value=data.get(tag),
                boolean_value=True
            ))
    
    if data.get("meta_og_tags"):
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="metadata",
            subcategory="other_meta_tags",
            metric_name="og_tags_count",
            metric_value=len(data.get("meta_og_tags", {})),
            json_value=data.get("meta_og_tags")
        ))
    
    if data.get("meta_twitter_tags"):
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="metadata",
            subcategory="other_meta_tags",
            metric_name="twitter_tags_count",
            metric_value=len(data.get("meta_twitter_tags", {})),
            json_value=data.get("meta_twitter_tags")
        ))
    
    # Content metrics
    # Headings
    for heading_type, count in data.get("headings_count", {}).items():
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="content",
            subcategory="headings",
            metric_name=f"{heading_type}_count",
            metric_value=count
        ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="content",
        subcategory="headings",
        metric_name="score",
        metric_value=scorecard["content"]["headings"]["score"]
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="content",
        subcategory="headings",
        metric_name="status",
        text_value=scorecard["content"]["headings"]["details"].get("status")
    ))
    
    # Content quality
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="content",
        subcategory="content_quality",
        metric_name="word_count",
        metric_value=data.get("word_count", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="content",
        subcategory="content_quality",
        metric_name="text_html_ratio",
        metric_value=data.get("text_html_ratio", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="content",
        subcategory="content_quality",
        metric_name="paragraphs_count",
        metric_value=data.get("paragraphs_count", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="content",
        subcategory="content_quality",
        metric_name="score",
        metric_value=scorecard["content"]["content_quality"]["score"]
    ))
    
    # Keyword optimization
    if data.get("keywords_density"):
        top_keywords = sorted(data["keywords_density"].items(), key=lambda x: x[1]["density"], reverse=True)[:10]
        for i, (keyword, info) in enumerate(top_keywords):
            detail_records.append(AuditDetail(
                audit_id=audit_id,
                category="content",
                subcategory="keyword_optimization",
                metric_name=f"keyword_{i+1}",
                text_value=keyword,
                metric_value=info["density"],
                json_value={"count": info["count"], "density": info["density"]}
            ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="content",
        subcategory="keyword_optimization",
        metric_name="score",
        metric_value=scorecard["content"]["keyword_optimization"]["score"]
    ))
    
    # Media metrics
    # Images
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="media",
        subcategory="images",
        metric_name="total_images",
        metric_value=data.get("total_images", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="media",
        subcategory="images",
        metric_name="images_with_alt",
        metric_value=data.get("images_with_alt", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="media",
        subcategory="images",
        metric_name="images_without_alt",
        metric_value=data.get("images_without_alt", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="media",
        subcategory="images",
        metric_name="images_with_alt_percentage",
        metric_value=data.get("images_with_alt_percentage", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="media",
        subcategory="images",
        metric_name="score",
        metric_value=scorecard["media"]["images"]["score"]
    ))
    
    # Videos and audio
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="media",
        subcategory="videos_and_audio",
        metric_name="videos_count",
        metric_value=data.get("videos_count", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="media",
        subcategory="videos_and_audio",
        metric_name="audios_count",
        metric_value=data.get("audios_count", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="media",
        subcategory="videos_and_audio",
        metric_name="score",
        metric_value=scorecard["media"]["videos_and_audio"]["score"]
    ))
    
    # Technical metrics
    # Structured data
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="structured_data",
        metric_name="has_structured_data",
        boolean_value=data.get("has_structured_data", False)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="structured_data",
        metric_name="structured_data_count",
        metric_value=data.get("structured_data_count", 0)
    ))
    
    if data.get("structured_data_types"):
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="technical",
            subcategory="structured_data",
            metric_name="structured_data_types",
            json_value=data.get("structured_data_types")
        ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="structured_data",
        metric_name="score",
        metric_value=scorecard["technical"]["structured_data"]["score"]
    ))
    
    # Mobile friendly
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="mobile_friendly",
        metric_name="has_viewport_meta",
        boolean_value=data.get("has_viewport_meta", False)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="mobile_friendly",
        metric_name="has_mobile_friendly_design",
        boolean_value=data.get("has_mobile_friendly_design", False)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="mobile_friendly",
        metric_name="score",
        metric_value=scorecard["technical"]["mobile_friendly"]["score"]
    ))
    
    # Page speed indicators
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="page_speed_indicators",
        metric_name="page_size_kb",
        metric_value=data.get("page_size_bytes", 0) / 1024
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="page_speed_indicators",
        metric_name="js_resources_count",
        metric_value=data.get("script_sources_count", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="page_speed_indicators",
        metric_name="css_resources_count",
        metric_value=data.get("style_links_count", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="page_speed_indicators",
        metric_name="inline_styles",
        metric_value=data.get("inline_styles", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="page_speed_indicators",
        metric_name="inline_scripts",
        metric_value=data.get("inline_scripts", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="page_speed_indicators",
        metric_name="score",
        metric_value=scorecard["technical"]["page_speed_indicators"]["score"]
    ))
    
    # Resource hints
    for hint_type, urls in data.get("resource_hints", {}).items():
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="technical",
            subcategory="page_speed_indicators",
            metric_name=f"has_{hint_type}",
            boolean_value=bool(urls)
        ))
    
    # Security
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="security",
        metric_name="has_https",
        boolean_value=data.get("has_https", False)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="technical",
        subcategory="security",
        metric_name="score",
        metric_value=scorecard["technical"]["security"]["score"]
    ))
    
    # Links metrics
    # Internal links
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="internal_links",
        metric_name="internal_links_count",
        metric_value=data.get("internal_links_count", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="internal_links",
        metric_name="internal_links_with_text",
        metric_value=data.get("internal_links_with_text", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="internal_links",
        metric_name="internal_links_with_text_percentage",
        metric_value=data.get("internal_links_with_text_percentage", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="internal_links",
        metric_name="score",
        metric_value=scorecard["links"]["internal_links"]["score"]
    ))
    
    # External links
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="external_links",
        metric_name="external_links_count",
        metric_value=data.get("external_links_count", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="external_links",
        metric_name="external_links_with_text",
        metric_value=data.get("external_links_with_text", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="external_links",
        metric_name="external_links_with_nofollow",
        metric_value=data.get("external_links_with_nofollow", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="external_links",
        metric_name="external_links_with_nofollow_percentage",
        metric_value=data.get("external_links_with_nofollow_percentage", 0)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="external_links",
        metric_name="score",
        metric_value=scorecard["links"]["external_links"]["score"]
    ))
    
    # Canonical
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="canonical",
        metric_name="has_canonical",
        boolean_value=bool(data.get("canonical_url"))
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="canonical",
        metric_name="canonical_matches_url",
        boolean_value=data.get("canonical_matches_url", False)
    ))
    
    if data.get("canonical_url"):
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="links",
            subcategory="canonical",
            metric_name="canonical_url",
            text_value=data.get("canonical_url")
        ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="links",
        subcategory="canonical",
        metric_name="score",
        metric_value=scorecard["links"]["canonical"]["score"]
    ))
    
    # International metrics
    # Language
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="international",
        subcategory="language",
        metric_name="has_language",
        boolean_value=data.get("has_language", False)
    ))
    
    if data.get("language"):
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="international",
            subcategory="language",
            metric_name="language",
            text_value=data.get("language")
        ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="international",
        subcategory="language",
        metric_name="score",
        metric_value=scorecard["international"]["language"]["score"]
    ))
    
    # Hreflang
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="international",
        subcategory="hreflang",
        metric_name="has_hreflang",
        boolean_value=data.get("has_hreflang", False)
    ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="international",
        subcategory="hreflang",
        metric_name="hreflang_count",
        metric_value=len(data.get("hreflang_tags", []))
    ))
    
    if data.get("hreflang_tags"):
        detail_records.append(AuditDetail(
            audit_id=audit_id,
            category="international",
            subcategory="hreflang",
            metric_name="hreflang_tags",
            json_value=data.get("hreflang_tags")
        ))
    
    detail_records.append(AuditDetail(
        audit_id=audit_id,
        category="international",
        subcategory="hreflang",
        metric_name="score",
        metric_value=scorecard["international"]["hreflang"]["score"]
    ))
    
    # Add all detail records to the database
    for record in detail_records:
        session.add(record)
    
    session.commit()


def auditSite(session, project_id:str, url, depth=1, max_pages=1):
    audit = SEOAudit(url, depth=depth, max_pages=max_pages)
    audit_result = audit.run()
    db = session
    audit_time = datetime.utcnow()

    try:
        print("Auditing site....")
        for url, payload in audit_result["detailed_results"].items():
            page_title = payload["data"].get("title")
            page_score = payload["scorecard"].get("total_score")

            # 1. Upsert Page
            page = db.query(Page).filter_by(url=url, project_id=project_id).first()
            if not page:
                page = Page(
                    id=str(uuid4()),
                    url=url,
                    title=page_title,
                    project_id=project_id,
                    last_audited=audit_time
                )
                db.add(page)
                db.commit()
                db.refresh(page)
            else:
                page.title = page_title
                page.last_audited = audit_time
                db.commit()

            # 2. Create Audit entry
            audit = Audit(
                id=str(uuid4()),
                page_id=page.id,
                audit_type="full",
                score=page_score,
                issues=payload["scorecard"],
                recommendations=audit_result["summary"]["top_issues"],
                created_at=audit_time
            )
            db.add(audit)
            db.commit()
            db.refresh(audit)
            
            # 3. Save detailed metrics for visualization
            save_audit_details(db, audit.id, payload["data"], payload["scorecard"])

        db.commit()
        
        import urllib.parse

        def extract_domain(url: str) -> str | None:
            try:
                if not urllib.parse.urlparse(url).scheme:
                    url = "http://" + url # Prepend a default scheme

                parsed_url = urllib.parse.urlparse(url)
                return parsed_url.hostname
            except Exception as e:
                # Catch any potential errors during parsing
                print(f"Error parsing URL '{url}': {e}")
                return None

        
        name = extract_domain(url)
        with open(f'./{name}.json', 'w') as f:
            json.dump(audit_result, f)
    
        print(json.dumps(audit_result, indent=2))

    finally:
        db.close()
        
    return audit_result