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
from models import Page, AuditDetail, Project
from models.audit_detail import AuditDetail
from uuid import uuid4
import random
from sqlalchemy.orm import Session

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
            "metadata": self._calculate_metadata_score(data),
            "content": self._calculate_content_score(data),
            "technical": self._calculate_technical_score(data),
            "links": self._calculate_links_score(data),
            "media": self._calculate_media_score(data),
            "international": self._calculate_international_score(data)
        }
        
        weights = {
            "metadata": 25,
            "content": 25,
            "technical": 20,
            "links": 15,
            "media": 10,
            "international": 5
        }
        
        total_score = 0
        for category, weight in weights.items():
            category_data = scorecard[category]
            category_score = sum(subcategory["score"] for subcategory in category_data.values())
            max_possible = sum(subcategory["max_score"] for subcategory in category_data.values())
            
            if max_possible > 0:
                category_percentage = (category_score / max_possible) * 100
                weighted_contribution = (category_percentage * weight) / 100
                total_score += weighted_contribution
        
        scorecard["total_score"] = max(0, min(100, round(total_score)))
        return scorecard

    def _calculate_metadata_score(self, data):
        scores = {
            "title": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "meta_description": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "other_meta_tags": {"score": 0, "max_score": 100, "details": {"recommendations": []}}
        }
        
        if data.get("title"):
            title_length = data["title_length"]
            if 30 <= title_length <= 60:
                scores["title"]["score"] = 100
                scores["title"]["details"]["status"] = "excellent"
            elif 20 <= title_length <= 70:
                scores["title"]["score"] = 80
                scores["title"]["details"]["status"] = "good"
            elif title_length > 0:
                scores["title"]["score"] = 60
                scores["title"]["details"]["status"] = "needs improvement"
                if title_length > 70:
                    scores["title"]["details"]["recommendations"].append("Title is too long - consider shortening to under 60 characters")
                elif title_length < 30:
                    scores["title"]["details"]["recommendations"].append("Title is too short - consider expanding to 30-60 characters")
        else:
            scores["title"]["details"]["recommendations"].append("Missing page title - add a descriptive title tag")
        
        if data.get("meta_description"):
            desc_length = data["meta_description_length"]
            if 120 <= desc_length <= 160:
                scores["meta_description"]["score"] = 100
                scores["meta_description"]["details"]["status"] = "excellent"
            elif 100 <= desc_length <= 180:
                scores["meta_description"]["score"] = 80
                scores["meta_description"]["details"]["status"] = "good"
            elif desc_length > 0:
                scores["meta_description"]["score"] = 60
                scores["meta_description"]["details"]["status"] = "needs improvement"
                if desc_length > 180:
                    scores["meta_description"]["details"]["recommendations"].append("Meta description is too long - keep it under 160 characters")
                elif desc_length < 120:
                    scores["meta_description"]["details"]["recommendations"].append("Meta description is too short - expand to 120-160 characters")
        else:
            scores["meta_description"]["details"]["recommendations"].append("Missing meta description - add a compelling description")
        
        meta_score = 0
        if data.get("meta_viewport"):
            meta_score += 25
        else:
            scores["other_meta_tags"]["details"]["recommendations"].append("Add viewport meta tag for mobile optimization")
            
        if data.get("meta_charset"):
            meta_score += 15
        else:
            scores["other_meta_tags"]["details"]["recommendations"].append("Add charset meta tag for proper encoding")
            
        if data.get("meta_og_tags"):
            meta_score += 30
        else:
            scores["other_meta_tags"]["details"]["recommendations"].append("Add Open Graph tags for better social media sharing")
            
        if data.get("meta_twitter_tags"):
            meta_score += 20
        else:
            scores["other_meta_tags"]["details"]["recommendations"].append("Add Twitter Card tags for enhanced Twitter sharing")
            
        if data.get("meta_robots"):
            meta_score += 10
        else:
            scores["other_meta_tags"]["details"]["recommendations"].append("Consider adding robots meta tag for crawling directives")
            
        scores["other_meta_tags"]["score"] = meta_score
        
        return scores

    def _calculate_content_score(self, data):
        scores = {
            "headings": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "content_quality": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "keyword_optimization": {"score": 0, "max_score": 100, "details": {"recommendations": []}}
        }
        
        h1_count = data.get("headings_count", {}).get("h1", 0)
        h2_count = data.get("headings_count", {}).get("h2", 0)
        h3_count = data.get("headings_count", {}).get("h3", 0)
        
        if h1_count == 1:
            scores["headings"]["score"] += 50
        elif h1_count == 0:
            scores["headings"]["details"]["recommendations"].append("Add exactly one H1 tag as the main page heading")
        elif h1_count > 1:
            scores["headings"]["details"]["recommendations"].append("Use only one H1 tag per page - convert others to H2 or H3")
            scores["headings"]["score"] += 30
        
        if h2_count >= 2:
            scores["headings"]["score"] += 30
        elif h2_count == 1:
            scores["headings"]["score"] += 20
        else:
            scores["headings"]["details"]["recommendations"].append("Add H2 tags to structure your content better")
        
        if h3_count > 0:
            scores["headings"]["score"] += 20
        else:
            scores["headings"]["details"]["recommendations"].append("Consider using H3 tags for detailed content structure")
        
        word_count = data.get("word_count", 0)
        if word_count >= 300:
            scores["content_quality"]["score"] = min(100, 60 + (word_count - 300) / 20)
        elif word_count >= 150:
            scores["content_quality"]["score"] = 40
            scores["content_quality"]["details"]["recommendations"].append("Increase content length to at least 300 words for better SEO")
        else:
            scores["content_quality"]["score"] = 20
            scores["content_quality"]["details"]["recommendations"].append("Content is too short - aim for at least 300 words of quality content")
        
        text_html_ratio = data.get("text_html_ratio", 0)
        if text_html_ratio < 10:
            scores["content_quality"]["details"]["recommendations"].append("Low text-to-HTML ratio - reduce unnecessary markup")
        
        keyword_density = data.get("keywords_density", {})
        if keyword_density:
            top_densities = [info["density"] for info in keyword_density.values()][:5]
            avg_density = sum(top_densities) / len(top_densities) if top_densities else 0
            
            if 1.0 <= avg_density <= 3.0:
                scores["keyword_optimization"]["score"] = 100
            elif 0.5 <= avg_density < 1.0 or 3.0 < avg_density <= 5.0:
                scores["keyword_optimization"]["score"] = 70
            elif avg_density > 5.0:
                scores["keyword_optimization"]["score"] = 40
                scores["keyword_optimization"]["details"]["recommendations"].append("Keyword density is too high - reduce repetitive keywords")
            else:
                scores["keyword_optimization"]["score"] = 50
                scores["keyword_optimization"]["details"]["recommendations"].append("Improve keyword usage for better topical relevance")
        else:
            scores["keyword_optimization"]["score"] = 30
            scores["keyword_optimization"]["details"]["recommendations"].append("No clear keyword focus detected - optimize content for target keywords")
        
        return scores

    def _calculate_technical_score(self, data):
        scores = {
            "structured_data": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "mobile_friendly": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "page_speed_indicators": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "security": {"score": 0, "max_score": 100, "details": {"recommendations": []}}
        }
        
        if data.get("has_structured_data"):
            sd_count = data.get("structured_data_count", 0)
            if sd_count >= 2:
                scores["structured_data"]["score"] = 100
            else:
                scores["structured_data"]["score"] = 70
        else:
            scores["structured_data"]["score"] = 20
            scores["structured_data"]["details"]["recommendations"].append("Add structured data markup to help search engines understand your content")
        
        mobile_score = 0
        if data.get("has_viewport_meta"):
            mobile_score += 60
        else:
            scores["mobile_friendly"]["details"]["recommendations"].append("Add responsive viewport meta tag")
        
        if data.get("has_mobile_friendly_design"):
            mobile_score += 40
        else:
            scores["mobile_friendly"]["details"]["recommendations"].append("Implement responsive design with CSS media queries")
        
        scores["mobile_friendly"]["score"] = mobile_score
        
        page_size_kb = data.get("page_size_bytes", 0) / 1024
        speed_score = 100
        
        if page_size_kb > 3000:
            speed_score = 40
            scores["page_speed_indicators"]["details"]["recommendations"].append("Page size is very large - optimize images and remove unused code")
        elif page_size_kb > 1500:
            speed_score = 60
            scores["page_speed_indicators"]["details"]["recommendations"].append("Page size is large - consider optimizing resources")
        elif page_size_kb > 500:
            speed_score = 80
        
        script_count = data.get("script_sources_count", 0)
        if script_count > 10:
            speed_score -= 15
            scores["page_speed_indicators"]["details"]["recommendations"].append("Too many external scripts - consolidate or remove unused scripts")
        
        css_count = data.get("style_links_count", 0)
        if css_count > 5:
            speed_score -= 10
            scores["page_speed_indicators"]["details"]["recommendations"].append("Multiple CSS files detected - consider combining stylesheets")
        
        scores["page_speed_indicators"]["score"] = max(0, speed_score)
        
        if data.get("has_https"):
            scores["security"]["score"] = 100
        else:
            scores["security"]["score"] = 0
            scores["security"]["details"]["recommendations"].append("Implement HTTPS for secure data transmission")
        
        return scores

    def _calculate_links_score(self, data):
        scores = {
            "internal_links": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "external_links": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "canonical": {"score": 0, "max_score": 100, "details": {"recommendations": []}}
        }
        
        internal_count = data.get("internal_links_count", 0)
        if internal_count >= 5:
            scores["internal_links"]["score"] = min(100, 60 + internal_count * 4)
        elif internal_count >= 2:
            scores["internal_links"]["score"] = 50
        elif internal_count >= 1:
            scores["internal_links"]["score"] = 30
        else:
            scores["internal_links"]["details"]["recommendations"].append("Add internal links to improve site navigation and SEO")
        
        internal_with_text_pct = data.get("internal_links_with_text_percentage", 0)
        if internal_with_text_pct < 80 and internal_count > 0:
            scores["internal_links"]["details"]["recommendations"].append("Ensure all internal links have descriptive anchor text")
        
        external_count = data.get("external_links_count", 0)
        if 1 <= external_count <= 10:
            scores["external_links"]["score"] = 100
        elif 11 <= external_count <= 20:
            scores["external_links"]["score"] = 80
        elif external_count > 20:
            scores["external_links"]["score"] = 60
            scores["external_links"]["details"]["recommendations"].append("Too many external links - consider reducing or adding nofollow attributes")
        else:
            scores["external_links"]["score"] = 70
            scores["external_links"]["details"]["recommendations"].append("Consider adding relevant external links to authoritative sources")
        
        if data.get("canonical_url"):
            if data.get("canonical_matches_url"):
                scores["canonical"]["score"] = 100
            else:
                scores["canonical"]["score"] = 80
                scores["canonical"]["details"]["recommendations"].append("Canonical URL doesn't match current page URL - verify if intentional")
        else:
            scores["canonical"]["score"] = 60
            scores["canonical"]["details"]["recommendations"].append("Add canonical URL to prevent duplicate content issues")
        
        return scores

    def _calculate_media_score(self, data):
        scores = {
            "images": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "videos_and_audio": {"score": 0, "max_score": 100, "details": {"recommendations": []}}
        }
        
        total_images = data.get("total_images", 0)
        if total_images > 0:
            alt_percentage = data.get("images_with_alt_percentage", 0)
            if alt_percentage >= 90:
                scores["images"]["score"] = 100
            elif alt_percentage >= 70:
                scores["images"]["score"] = 80
            elif alt_percentage >= 50:
                scores["images"]["score"] = 60
            else:
                scores["images"]["score"] = 40
            
            if alt_percentage < 90:
                scores["images"]["details"]["recommendations"].append(f"Add alt text to {data.get('images_without_alt', 0)} images for better accessibility")
        else:
            scores["images"]["score"] = 100
            scores["images"]["details"]["recommendations"].append("Consider adding relevant images to enhance content")
        
        videos_count = data.get("videos_count", 0)
        audios_count = data.get("audios_count", 0)
        
        if videos_count > 0 or audios_count > 0:
            scores["videos_and_audio"]["score"] = 90
        else:
            scores["videos_and_audio"]["score"] = 85
        
        return scores

    def _calculate_international_score(self, data):
        scores = {
            "language": {"score": 0, "max_score": 100, "details": {"recommendations": []}},
            "hreflang": {"score": 0, "max_score": 100, "details": {"recommendations": []}}
        }
        
        if data.get("has_language"):
            scores["language"]["score"] = 100
        else:
            scores["language"]["score"] = 70
            scores["language"]["details"]["recommendations"].append("Add lang attribute to HTML tag to specify page language")
        
        if data.get("has_hreflang"):
            scores["hreflang"]["score"] = 100
        else:
            scores["hreflang"]["score"] = 85
        
        return scores

    def _get_schema_type(self, structured_data):
        if isinstance(structured_data, dict):
            return structured_data.get("@type", "Unknown")
        return "Unknown"

    def get_internal_links(self, html, page_url):
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        internal_links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            if not href or href.startswith('#'):
                continue
            full_url = urljoin(page_url, href)
            if self.is_valid_internal_url(full_url) and full_url not in self.visited_urls:
                internal_links.append(full_url)
        return internal_links

    def audit_page(self, url):
        if url in self.visited_urls or self.pages_audited >= self.max_pages:
            return None
        
        self.visited_urls.add(url)
        print(f"Auditing: {url}")
        
        html = self.fetch_html(url)
        if not html:
            return None
        
        seo_data = self.extract_seo_data(html, url)
        if not seo_data:
            return None
        
        scorecard = self.calculate_scorecard(seo_data)
        seo_data["scorecard"] = scorecard
        
        self.pages_audited += 1
        self.all_results[url] = seo_data
        
        if self.depth > 0 and self.pages_audited < self.max_pages:
            internal_links = self.get_internal_links(html, url)
            for link in internal_links[:min(5, self.max_pages - self.pages_audited)]:
                time.sleep(random.uniform(0.5, 1.5))
                self.audit_page(link)
        
        return seo_data

    def run_audit(self):
        start_time = time.time()
        print(f"Starting SEO audit for: {self.base_url}")
        
        main_result = self.audit_page(self.base_url)
        
        end_time = time.time()
        audit_duration = round(end_time - start_time, 2)
        
        summary = {
            "audit_id": str(uuid4()),
            "base_url": self.base_url,
            "total_pages_audited": self.pages_audited,
            "audit_duration_seconds": audit_duration,
            "timestamp": datetime.now().isoformat(),
            "pages": self.all_results
        }
        
        if main_result:
            summary["overall_score"] = main_result["scorecard"]["total_score"]
            summary["main_page_data"] = main_result
        
        return summary

    def save_to_database(self, audit_summary, session: Session, project_id: str):
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project with ID {project_id} does not exist.")

            audit_run_id = audit_summary.get("audit_id")
            all_pages_data = audit_summary.get("pages", {})

            for page_url, page_data in all_pages_data.items():
                # Step 2: Create or update Page instance
                page = session.query(Page).filter(
                    Page.project_id == project.id,
                    Page.url == page_url
                ).first()

                if not page:
                    page = Page(project_id=project.id)

                # Update basic page details
                page.url = page_url
                page.title = page_data.get("title")
                page.meta_description = page_data.get("meta_description")
                page.content_hash = page_data.get("content_hash")
                page.page_size_bytes = page_data.get("page_size_bytes")
                page.last_audited = datetime.utcnow()

                # Update scores
                scorecard = page_data.get("scorecard", {})
                page.seo_score = scorecard.get("total_score")
                page.audit_score = scorecard.get("total_score")

                # --- Copy everything else as-is ---
                page.word_count = page_data.get("word_count")
                page.text_html_ratio = page_data.get("text_html_ratio")
                page.paragraphs_count = page_data.get("paragraphs_count")
                page.paragraphs_data = page_data.get("paragraphs")

                page.title_length = page_data.get("title_length")
                page.meta_description_length = page_data.get("meta_description_length")
                page.meta_robots = page_data.get("meta_robots")
                page.meta_keywords = page_data.get("meta_keywords")
                page.meta_viewport = page_data.get("meta_viewport")
                page.meta_charset = page_data.get("meta_charset")
                page.canonical_url = page_data.get("canonical_url")
                page.canonical_matches_url = page_data.get("canonical_matches_url")
                page.language = page_data.get("language")
                page.has_language = page_data.get("has_language", False)

                page.meta_og_tags = page_data.get("meta_og_tags")
                page.meta_twitter_tags = page_data.get("meta_twitter_tags")

                page.has_https = page_data.get("has_https", False)
                page.has_viewport_meta = page_data.get("has_viewport_meta", False)
                page.has_mobile_friendly_design = page_data.get("has_mobile_friendly_design", False)
                page.has_favicon = page_data.get("has_favicon", False)
                page.favicon_url = page_data.get("favicon")
                page.has_doctype = page_data.get("has_doctype", False)

                page.has_structured_data = page_data.get("has_structured_data", False)
                page.structured_data_count = page_data.get("structured_data_count", 0)
                page.structured_data_types = page_data.get("structured_data_types")
                page.structured_data = page_data.get("structured_data")

                headings_count = page_data.get("headings_count", {})
                page.headings_data = page_data.get("headings")
                page.h1_count = headings_count.get("h1", 0)
                page.h2_count = headings_count.get("h2", 0)
                page.h3_count = headings_count.get("h3", 0)
                page.h4_count = headings_count.get("h4", 0)
                page.h5_count = headings_count.get("h5", 0)
                page.h6_count = headings_count.get("h6", 0)

                page.total_links = page_data.get("total_links", 0)
                page.internal_links_count = page_data.get("internal_links_count", 0)
                page.external_links_count = page_data.get("external_links_count", 0)
                page.internal_links_with_text = page_data.get("internal_links_with_text", 0)
                page.external_links_with_text = page_data.get("external_links_with_text", 0)
                page.internal_links_with_text_percentage = page_data.get("internal_links_with_text_percentage", 0)
                page.external_links_with_nofollow = page_data.get("external_links_with_nofollow", 0)
                page.external_links_with_nofollow_percentage = page_data.get("external_links_with_nofollow_percentage", 0)
                page.internal_links_data = page_data.get("internal_links")
                page.external_links_data = page_data.get("external_links")

                page.total_images = page_data.get("total_images", 0)
                page.images_with_alt = page_data.get("images_with_alt", 0)
                page.images_without_alt = page_data.get("images_without_alt", 0)
                page.images_with_alt_percentage = page_data.get("images_with_alt_percentage", 0)
                page.images_data = page_data.get("images")

                page.videos_count = page_data.get("videos_count", 0)
                page.audios_count = page_data.get("audios_count", 0)
                page.videos_data = page_data.get("videos")
                page.audios_data = page_data.get("audios")

                page.strong_tags_count = page_data.get("strong_tags_count", 0)
                page.em_tags_count = page_data.get("em_tags_count", 0)
                page.b_tags_count = page_data.get("b_tags_count", 0)
                page.i_tags_count = page_data.get("i_tags_count", 0)
                page.strong_tags_data = page_data.get("strong_tags")
                page.em_tags_data = page_data.get("em_tags")
                page.b_tags_data = page_data.get("b_tags")
                page.i_tags_data = page_data.get("i_tags")

                page.keywords_density = page_data.get("keywords_density")

                page.script_sources_count = page_data.get("script_sources_count", 0)
                page.style_links_count = page_data.get("style_links_count", 0)
                page.inline_styles = page_data.get("inline_styles", 0)
                page.inline_scripts = page_data.get("inline_scripts", 0)
                page.script_sources = page_data.get("script_sources")
                page.style_links = page_data.get("style_links")

                page.resource_hints = page_data.get("resource_hints")

                page.has_hreflang = page_data.get("has_hreflang", False)
                page.hreflang_tags = page_data.get("hreflang_tags")

                if not page.id:
                    session.add(page)
                session.flush()

                # Step 3: Remove existing audit details for this page to avoid duplicates
                session.query(AuditDetail).filter(AuditDetail.page_id == page.id).delete()

                # Step 4: Save audit details
                self._save_audit_details(session, page.id, audit_run_id, page_data, scorecard)

                # Step 5: Update issue/opportunity counts
                issues_count = session.query(AuditDetail).filter(
                    AuditDetail.page_id == page.id,
                    AuditDetail.status.in_(['fail', 'warning', 'needs_improvement'])
                ).count()

                opportunities_count = session.query(AuditDetail).filter(
                    AuditDetail.page_id == page.id,
                    AuditDetail.recommendations.isnot(None)
                ).count()

                page.issues_count = issues_count
                page.opportunities_count = opportunities_count

            # Step 6: Commit once after all pages are saved
            session.commit()
            print(f"Successfully saved audit data for {len(all_pages_data)} pages.")
            return True

        except Exception as e:
            session.rollback()
            print(f"Database save error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _save_audit_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict, scorecard: dict):
        """Save comprehensive audit details to database"""
        
        # 1. Save scorecard details
        categories = ["metadata", "content", "technical", "links", "media", "international"]
        for category in categories:
            category_data = scorecard.get(category, {})
            for subcategory, details in category_data.items():
                if isinstance(details, dict) and "score" in details:
                    detail = AuditDetail(
                        page_id=page_id,
                        audit_run_id=audit_run_id,
                        category=category,
                        subcategory=subcategory,
                        metric_name=f"{category}_{subcategory}_score",
                        metric_value=float(details.get("score", 0)),
                        score=float(details.get("score", 0)),
                        max_score=float(details.get("max_score", 100)),
                        status=details.get("details", {}).get("status", "info"),
                        recommendations=details.get("details", {}).get("recommendations", []),
                        details=details.get("details", {}),
                        message=f"{subcategory.replace('_', ' ').title()} analysis completed"
                    )
                    session.add(detail)

        # 2. Save detailed content analysis
        self._save_content_analysis_details(session, page_id, audit_run_id, page_data)
        
        # 3. Save technical analysis details
        self._save_technical_analysis_details(session, page_id, audit_run_id, page_data)
        
        # 4. Save links analysis details
        self._save_links_analysis_details(session, page_id, audit_run_id, page_data)
        
        # 5. Save media analysis details
        self._save_media_analysis_details(session, page_id, audit_run_id, page_data)
        
        # 6. Save metadata analysis details
        self._save_metadata_analysis_details(session, page_id, audit_run_id, page_data)

    def _save_content_analysis_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict):
        """Save content-related audit details"""
        
        # Word count analysis
        word_count = page_data.get("word_count", 0)
        status = "excellent" if word_count >= 300 else "needs_improvement" if word_count < 150 else "good"
        recommendations = []
        if word_count < 300:
            recommendations.append(f"Increase content length. Current: {word_count} words, recommended: 300+ words")
        
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="content",
            subcategory="word_count",
            metric_name="content_word_count",
            metric_value=float(word_count),
            status=status,
            recommendations=recommendations,
            message=f"Page contains {word_count} words"
        ))
        
        # Text to HTML ratio
        text_html_ratio = page_data.get("text_html_ratio", 0)
        status = "good" if text_html_ratio >= 15 else "warning" if text_html_ratio >= 10 else "needs_improvement"
        recommendations = []
        if text_html_ratio < 15:
            recommendations.append(f"Improve text-to-HTML ratio. Current: {text_html_ratio}%, recommended: 15%+")
        
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="content",
            subcategory="text_html_ratio",
            metric_name="text_html_ratio",
            metric_value=text_html_ratio,
            status=status,
            recommendations=recommendations,
            message=f"Text-to-HTML ratio is {text_html_ratio}%"
        ))
        
        # Keyword density analysis
        keywords_density = page_data.get("keywords_density", {})
        if keywords_density:
            top_keywords = list(keywords_density.items())[:5]
            session.add(AuditDetail(
                page_id=page_id,
                audit_run_id=audit_run_id,
                category="content",
                subcategory="keyword_analysis",
                metric_name="keyword_density",
                json_value=keywords_density,
                status="info",
                message=f"Top keywords identified: {', '.join([kw for kw, _ in top_keywords])}"
            ))

    def _save_technical_analysis_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict):
        """Save technical SEO audit details"""
        
        # HTTPS check
        has_https = page_data.get("has_https", False)
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="technical",
            subcategory="security",
            metric_name="https_enabled",
            boolean_value=has_https,
            status="pass" if has_https else "fail",
            severity="critical" if not has_https else None,
            recommendations=[] if has_https else ["Implement HTTPS for secure data transmission"],
            message="HTTPS is enabled" if has_https else "HTTPS is not enabled"
        ))
        
        # Mobile friendliness
        has_mobile_friendly = page_data.get("has_mobile_friendly_design", False)
        has_viewport = page_data.get("has_viewport_meta", False)
        recommendations = []
        if not has_viewport:
            recommendations.append("Add responsive viewport meta tag")
        if not has_mobile_friendly:
            recommendations.append("Implement responsive design with CSS media queries")
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="technical",
            subcategory="mobile_optimization",
            metric_name="mobile_friendly",
            boolean_value=has_mobile_friendly and has_viewport,
            status="pass" if (has_mobile_friendly and has_viewport) else "warning",
            recommendations=recommendations,
            message="Mobile optimization is configured" if (has_mobile_friendly and has_viewport) else "Mobile optimization needs improvement"
        ))
        
        # Page size analysis
        page_size_bytes = page_data.get("page_size_bytes", 0)
        page_size_kb = page_size_bytes / 1024 if page_size_bytes else 0
        status = "excellent" if page_size_kb < 500 else "good" if page_size_kb < 1500 else "warning" if page_size_kb < 3000 else "needs_improvement"
        recommendations = []
        if page_size_kb > 1500:
            recommendations.append(f"Page size is large ({page_size_kb:.1f}KB). Consider optimizing images and removing unused code")
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="technical",
            subcategory="performance",
            metric_name="page_size",
            metric_value=page_size_kb,
            status=status,
            recommendations=recommendations,
            message=f"Page size is {page_size_kb:.1f}KB"
        ))

    def _save_links_analysis_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict):
        """Save links analysis audit details"""
        
        # Internal links analysis
        internal_count = page_data.get("internal_links_count", 0)
        internal_with_text_pct = page_data.get("internal_links_with_text_percentage", 0)
        
        recommendations = []
        if internal_count < 2:
            recommendations.append("Add more internal links to improve site navigation and SEO")
        if internal_with_text_pct < 80:
            recommendations.append("Ensure all internal links have descriptive anchor text")
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="links",
            subcategory="internal_links",
            metric_name="internal_links_count",
            metric_value=float(internal_count),
            status="excellent" if internal_count >= 5 else "good" if internal_count >= 2 else "needs_improvement",
            recommendations=recommendations,
            json_value=page_data.get("internal_links"),
            message=f"Found {internal_count} internal links"
        ))
        
        # External links analysis
        external_count = page_data.get("external_links_count", 0)
        external_nofollow_pct = page_data.get("external_links_with_nofollow_percentage", 0)
        
        recommendations = []
        if external_count > 20:
            recommendations.append("Too many external links - consider reducing or adding nofollow attributes")
        elif external_count == 0:
            recommendations.append("Consider adding relevant external links to authoritative sources")
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="links",
            subcategory="external_links",
            metric_name="external_links_count",
            metric_value=float(external_count),
            status="excellent" if 1 <= external_count <= 10 else "good" if external_count <= 20 else "warning",
            recommendations=recommendations,
            json_value=page_data.get("external_links"),
            message=f"Found {external_count} external links"
        ))

    def _save_media_analysis_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict):
        """Save media analysis audit details"""
        
        # Images analysis
        total_images = page_data.get("total_images", 0)
        images_with_alt = page_data.get("images_with_alt", 0)
        images_without_alt = page_data.get("images_without_alt", 0)
        alt_percentage = page_data.get("images_with_alt_percentage", 0)
        
        recommendations = []
        if images_without_alt > 0:
            recommendations.append(f"Add alt text to {images_without_alt} images for better accessibility")
        if total_images == 0:
            recommendations.append("Consider adding relevant images to enhance content")
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="media",
            subcategory="images",
            metric_name="images_alt_text",
            metric_value=alt_percentage,
            status="excellent" if alt_percentage >= 90 else "good" if alt_percentage >= 70 else "needs_improvement",
            recommendations=recommendations,
            json_value=page_data.get("images"),
            message=f"Found {total_images} images, {images_with_alt} with alt text ({alt_percentage:.1f}%)"
        ))

    def _save_metadata_analysis_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict):
        """Save metadata analysis audit details"""
        
        # Title analysis
        title = page_data.get("title")
        title_length = page_data.get("title_length", 0)
        recommendations = []
        
        if not title:
            status = "fail"
            recommendations.append("Missing page title - add a descriptive title tag")
        elif title_length > 70:
            status = "warning"
            recommendations.append("Title is too long - consider shortening to under 60 characters")
        elif title_length < 30:
            status = "warning"
            recommendations.append("Title is too short - consider expanding to 30-60 characters")
        else:
            status = "pass"
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="metadata",
            subcategory="title",
            metric_name="title_optimization",
            metric_value=float(title_length),
            status=status,
            severity="high" if not title else "medium" if status == "warning" else None,
            recommendations=recommendations,
            text_value=title,
            message=f"Title length: {title_length} characters" if title else "Missing title tag"
        ))
        
        # Meta description analysis
        meta_description = page_data.get("meta_description")
        meta_desc_length = page_data.get("meta_description_length", 0)
        recommendations = []
        
        if not meta_description:
            status = "fail"
            recommendations.append("Missing meta description - add a compelling 150-160 character description")
        elif meta_desc_length > 170:
            status = "warning"
            recommendations.append("Meta description is too long - consider shortening to under 160 characters")
        elif meta_desc_length < 120:
            status = "warning"
            recommendations.append("Meta description is too short - consider expanding to 120-160 characters")
        else:
            status = "pass"
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="metadata",
            subcategory="meta_description",
            metric_name="meta_description_optimization",
            metric_value=float(meta_desc_length),
            status=status,
            severity="high" if not meta_description else "medium" if status == "warning" else None,
            recommendations=recommendations,
            text_value=meta_description,
            message=f"Meta description length: {meta_desc_length} characters" if meta_description else "Missing meta description"
        ))
        
        # Canonical URL analysis
        canonical_url = page_data.get("canonical_url")
        canonical_matches = page_data.get("canonical_matches_url", False)
        recommendations = []
        
        if not canonical_url:
            status = "warning"
            recommendations.append("Consider adding canonical URL to prevent duplicate content issues")
        elif not canonical_matches:
            status = "warning"
            recommendations.append("Canonical URL doesn't match current page URL - verify this is intentional")
        else:
            status = "pass"
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="metadata",
            subcategory="canonical",
            metric_name="canonical_url_setup",
            boolean_value=bool(canonical_url),
            status=status,
            recommendations=recommendations,
            text_value=canonical_url,
            message="Canonical URL is properly configured" if canonical_url and canonical_matches else "Canonical URL needs attention"
        ))
        
        # Open Graph tags analysis
        og_tags = page_data.get("meta_og_tags", {})
        og_count = len(og_tags) if og_tags else 0
        recommendations = []
        
        required_og_tags = ['og:title', 'og:description', 'og:type', 'og:url']
        missing_og_tags = [tag for tag in required_og_tags if tag not in og_tags]
        
        if missing_og_tags:
            status = "needs_improvement"
            recommendations.append(f"Add missing Open Graph tags: {', '.join(missing_og_tags)}")
        elif og_count >= 4:
            status = "excellent"
        else:
            status = "good"
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="metadata",
            subcategory="open_graph",
            metric_name="og_tags_completeness",
            metric_value=float(og_count),
            status=status,
            recommendations=recommendations,
            json_value=og_tags,
            message=f"Found {og_count} Open Graph tags"
        ))
        
        # Twitter Card tags analysis
        twitter_tags = page_data.get("meta_twitter_tags", {})
        twitter_count = len(twitter_tags) if twitter_tags else 0
        recommendations = []
        
        if twitter_count == 0:
            status = "needs_improvement"
            recommendations.append("Add Twitter Card meta tags for better social media sharing")
        elif twitter_count >= 3:
            status = "excellent"
        else:
            status = "good"
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="metadata",
            subcategory="twitter_cards",
            metric_name="twitter_tags_completeness",
            metric_value=float(twitter_count),
            status=status,
            recommendations=recommendations,
            json_value=twitter_tags,
            message=f"Found {twitter_count} Twitter Card tags"
        ))
        
        # Language and internationalization
        language = page_data.get("language")
        has_language = page_data.get("has_language", False)
        has_hreflang = page_data.get("has_hreflang", False)
        hreflang_tags = page_data.get("hreflang_tags", [])
        
        recommendations = []
        if not has_language:
            recommendations.append("Add language declaration to HTML tag (e.g., <html lang='en'>)")
        if not has_hreflang and len(hreflang_tags) == 0:
            recommendations.append("Consider adding hreflang tags if content is available in multiple languages")
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="international",
            subcategory="language_setup",
            metric_name="language_configuration",
            boolean_value=has_language,
            status="pass" if has_language else "warning",
            recommendations=recommendations,
            text_value=language,
            json_value=hreflang_tags,
            message=f"Language set to '{language}'" if language else "Language not specified"
        ))

    def _save_headings_analysis_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict):
        """Save headings structure analysis details"""
        
        headings_count = page_data.get("headings_count", {})
        headings_data = page_data.get("headings", [])
        
        h1_count = headings_count.get("h1", 0)
        h2_count = headings_count.get("h2", 0)
        total_headings = sum(headings_count.values())
        
        recommendations = []
        severity = None
        
        # H1 analysis
        if h1_count == 0:
            status = "fail"
            severity = "high"
            recommendations.append("Missing H1 tag - add a single, descriptive H1 heading")
        elif h1_count > 1:
            status = "warning"
            severity = "medium"
            recommendations.append(f"Multiple H1 tags found ({h1_count}) - use only one H1 per page")
        else:
            status = "pass"
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="content",
            subcategory="headings_h1",
            metric_name="h1_optimization",
            metric_value=float(h1_count),
            status=status,
            severity=severity,
            recommendations=recommendations,
            json_value=headings_data,
            message=f"Found {h1_count} H1 tag(s)"
        ))
        
        # Overall heading structure
        if total_headings < 2:
            status = "needs_improvement"
            recommendations = ["Add more headings (H2, H3) to improve content structure and readability"]
        elif h2_count == 0 and total_headings > 1:
            status = "warning"
            recommendations = ["Consider using H2 tags to better organize content sections"]
        else:
            status = "good"
            recommendations = []
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="content",
            subcategory="headings_structure",
            metric_name="headings_hierarchy",
            metric_value=float(total_headings),
            status=status,
            recommendations=recommendations,
            json_value=headings_count,
            message=f"Total headings: {total_headings} (H1:{h1_count}, H2:{h2_count})"
        ))

    def _save_structured_data_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict):
        """Save structured data analysis details"""
        
        has_structured_data = page_data.get("has_structured_data", False)
        structured_data_count = page_data.get("structured_data_count", 0)
        structured_data_types = page_data.get("structured_data_types", [])
        structured_data = page_data.get("structured_data", [])
        
        recommendations = []
        
        if not has_structured_data:
            status = "needs_improvement"
            recommendations.append("Add structured data (JSON-LD, microdata, or RDFa) to help search engines understand your content")
        elif structured_data_count >= 3:
            status = "excellent"
        elif structured_data_count >= 1:
            status = "good"
        else:
            status = "needs_improvement"
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="technical",
            subcategory="structured_data",
            metric_name="structured_data_implementation",
            metric_value=float(structured_data_count),
            boolean_value=has_structured_data,
            status=status,
            recommendations=recommendations,
            json_value={
                "types": structured_data_types,
                "data": structured_data
            },
            message=f"Found {structured_data_count} structured data items" if has_structured_data else "No structured data found"
        ))

    def _save_performance_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict):
        """Save performance-related analysis details"""
        
        # Script and style resources
        script_count = page_data.get("script_sources_count", 0)
        style_count = page_data.get("style_links_count", 0)
        inline_scripts = page_data.get("inline_scripts", 0)
        inline_styles = page_data.get("inline_styles", 0)
        
        recommendations = []
        
        if script_count > 10:
            recommendations.append(f"High number of script files ({script_count}) - consider combining or using a bundler")
        if style_count > 5:
            recommendations.append(f"High number of CSS files ({style_count}) - consider combining stylesheets")
        if inline_scripts > 5:
            recommendations.append("Consider moving inline scripts to external files for better caching")
        if inline_styles > 10:
            recommendations.append("Consider moving inline styles to external CSS files")
            
        total_resources = script_count + style_count
        status = "excellent" if total_resources <= 5 else "good" if total_resources <= 10 else "warning"
        
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="technical",
            subcategory="resources",
            metric_name="resource_optimization",
            metric_value=float(total_resources),
            status=status,
            recommendations=recommendations,
            json_value={
                "scripts": script_count,
                "styles": style_count,
                "inline_scripts": inline_scripts,
                "inline_styles": inline_styles,
                "script_sources": page_data.get("script_sources", []),
                "style_links": page_data.get("style_links", [])
            },
            message=f"Found {script_count} scripts and {style_count} stylesheets"
        ))
        
        # Resource hints
        resource_hints = page_data.get("resource_hints", [])
        hint_count = len(resource_hints) if resource_hints else 0
        
        recommendations = []
        if hint_count == 0:
            recommendations.append("Consider adding resource hints (preload, prefetch, dns-prefetch) to improve loading performance")
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="technical",
            subcategory="resource_hints",
            metric_name="resource_hints_usage",
            metric_value=float(hint_count),
            status="good" if hint_count > 0 else "info",
            recommendations=recommendations,
            json_value=resource_hints,
            message=f"Found {hint_count} resource hints" if hint_count > 0 else "No resource hints found"
        ))

    def _save_content_enhancement_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict):
        """Save content enhancement tags analysis details"""
        
        # Text formatting tags analysis
        strong_count = page_data.get("strong_tags_count", 0)
        em_count = page_data.get("em_tags_count", 0)
        b_count = page_data.get("b_tags_count", 0)
        i_count = page_data.get("i_tags_count", 0)
        
        recommendations = []
        
        # Check for semantic vs presentational tags
        if b_count > strong_count:
            recommendations.append("Use <strong> instead of <b> for better semantic meaning")
        if i_count > em_count:
            recommendations.append("Use <em> instead of <i> for better semantic meaning")
            
        total_emphasis = strong_count + em_count + b_count + i_count
        word_count = page_data.get("word_count", 1)
        emphasis_ratio = (total_emphasis / word_count) * 100 if word_count > 0 else 0
        
        if emphasis_ratio > 5:
            recommendations.append("High emphasis tag usage - ensure they're used meaningfully")
        elif emphasis_ratio < 0.5 and word_count > 200:
            recommendations.append("Consider adding emphasis tags to highlight important content")
            
        status = "good" if 0.5 <= emphasis_ratio <= 3 else "info"
        
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="content",
            subcategory="text_formatting",
            metric_name="emphasis_tags_usage",
            metric_value=emphasis_ratio,
            status=status,
            recommendations=recommendations,
            json_value={
                "strong_tags": strong_count,
                "em_tags": em_count,
                "b_tags": b_count,
                "i_tags": i_count,
                "strong_data": page_data.get("strong_tags", []),
                "em_data": page_data.get("em_tags", []),
                "b_data": page_data.get("b_tags", []),
                "i_data": page_data.get("i_tags", [])
            },
            message=f"Text formatting: {strong_count} <strong>, {em_count} <em>, {b_count} <b>, {i_count} <i>"
        ))

    def _save_accessibility_details(self, session: Session, page_id: str, audit_run_id: str, page_data: dict):
        """Save accessibility-related analysis details"""
        
        # Overall accessibility score based on multiple factors
        accessibility_factors = []
        score = 0
        max_score = 0
        recommendations = []
        
        # Images with alt text
        total_images = page_data.get("total_images", 0)
        images_with_alt = page_data.get("images_with_alt", 0)
        if total_images > 0:
            alt_score = (images_with_alt / total_images) * 25
            accessibility_factors.append(f"Images with alt text: {images_with_alt}/{total_images}")
            score += alt_score
            max_score += 25
            if images_with_alt < total_images:
                recommendations.append(f"Add alt text to {total_images - images_with_alt} images")
        
        # Language declaration
        has_language = page_data.get("has_language", False)
        if has_language:
            score += 15
            accessibility_factors.append("Language declared")
        else:
            recommendations.append("Add language declaration to HTML tag")
        max_score += 15
        
        # Heading structure (H1 presence)
        h1_count = page_data.get("headings_count", {}).get("h1", 0)
        if h1_count == 1:
            score += 10
            accessibility_factors.append("Proper H1 structure")
        elif h1_count == 0:
            recommendations.append("Add H1 heading for better structure")
        else:
            recommendations.append("Use only one H1 heading per page")
        max_score += 10
        
        # Meta description for screen readers
        meta_description = page_data.get("meta_description")
        if meta_description:
            score += 10
            accessibility_factors.append("Meta description present")
        else:
            recommendations.append("Add meta description for better accessibility")
        max_score += 10
        
        final_score = (score / max_score * 100) if max_score > 0 else 0
        status = "excellent" if final_score >= 80 else "good" if final_score >= 60 else "needs_improvement"
        
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="technical",
            subcategory="accessibility",
            metric_name="accessibility_score",
            metric_value=final_score,
            status=status,
            recommendations=recommendations,
            json_value={
                "factors": accessibility_factors,
                "score_breakdown": {
                    "images_alt": alt_score if total_images > 0 else 0,
                    "language": 15 if has_language else 0,
                    "headings": 10 if h1_count == 1 else 0,
                    "meta_description": 10 if meta_description else 0
                }
            },
            message=f"Accessibility score: {final_score:.1f}% ({', '.join(accessibility_factors)})"
        ))

    def _save_comprehensive_summary(self, session: Session, page_id: str, audit_run_id: str, page_data: dict, scorecard: dict):
        """Save comprehensive audit summary"""
        
        # Calculate overall health score
        total_score = scorecard.get("total_score", 0)
        max_possible = scorecard.get("max_score", 100)
        
        # Count critical issues
        critical_issues = []
        warnings = []
        recommendations = []
        
        # Check for critical SEO issues
        if not page_data.get("title"):
            critical_issues.append("Missing page title")
        if not page_data.get("meta_description"):
            critical_issues.append("Missing meta description")
        if not page_data.get("has_https"):
            critical_issues.append("Not using HTTPS")
        if page_data.get("headings_count", {}).get("h1", 0) != 1:
            critical_issues.append("Improper H1 structure")
            
        # Check for warnings
        if page_data.get("word_count", 0) < 300:
            warnings.append("Low word count")
        if page_data.get("total_images", 0) > 0 and page_data.get("images_with_alt_percentage", 0) < 80:
            warnings.append("Images missing alt text")
        if page_data.get("external_links_count", 0) > 20:
            warnings.append("Too many external links")
            
        # General recommendations
        if not page_data.get("has_structured_data"):
            recommendations.append("Add structured data markup")
        if not page_data.get("meta_og_tags"):
            recommendations.append("Add Open Graph tags")
        if page_data.get("script_sources_count", 0) > 10:
            recommendations.append("Optimize resource loading")
            
        # Determine overall status
        if len(critical_issues) > 3:
            overall_status = "critical"
        elif len(critical_issues) > 0:
            overall_status = "needs_improvement"
        elif len(warnings) > 2:
            overall_status = "warning"
        elif total_score >= 80:
            overall_status = "excellent"
        else:
            overall_status = "good"
            
        session.add(AuditDetail(
            page_id=page_id,
            audit_run_id=audit_run_id,
            category="summary",
            subcategory="overall_health",
            metric_name="page_health_score",
            metric_value=total_score,
            status=overall_status,
            severity="high" if overall_status == "critical" else "medium" if overall_status == "needs_improvement" else None,
            recommendations=critical_issues + warnings + recommendations,
            json_value={
                "critical_issues": critical_issues,
                "warnings": warnings,
                "recommendations": recommendations,
                "score_breakdown": scorecard,
                "metrics_summary": {
                    "word_count": page_data.get("word_count", 0),
                    "total_images": page_data.get("total_images", 0),
                    "total_links": page_data.get("total_links", 0),
                    "page_size_kb": round(page_data.get("page_size_bytes", 0) / 1024, 1),
                    "headings_total": sum(page_data.get("headings_count", {}).values()),
                    "structured_data_count": page_data.get("structured_data_count", 0)
                }
            },
            message=f"Overall health: {total_score:.1f}% - {len(critical_issues)} critical issues, {len(warnings)} warnings"
        ))


def auditSite(url, depth, max_pages, session, project_id):
    url = url
    depth = depth
    max_pages = max_pages
    
    auditor = SEOAudit(url, depth=depth, max_pages=max_pages)
    results = auditor.run_audit()
    
    print(f"\nAudit Complete!")
    print(f"Overall Score: {results.get('overall_score', 0)}/100")
    print(f"Pages Audited: {results['total_pages_audited']}")
    print(f"Duration: {results['audit_duration_seconds']} seconds")
    
    with open(f"seo_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    auditor.save_to_database(audit_summary=results, session=session, project_id=project_id)