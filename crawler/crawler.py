import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import sys
import re
import time
import jdatetime


if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

class NewsCrawler:
    def __init__(self, base_url="https://www.asriran.com"):
        self.base_url = base_url
        self.news_list = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def persian_to_english_numbers(self, text):
        if not text:
            return text
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        translation_table = str.maketrans(persian_digits, english_digits)
        return text.translate(translation_table)
        
    def persian_to_gregorian(self, persian_date):
        try:
            
            persian_date = self.persian_to_english_numbers(persian_date)
            
            
            parts = persian_date.split('/')
            if len(parts) != 3:
                return None
            
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            
            
            j_date = jdatetime.date(year, month, day)
            g_date = j_date.togregorian()
            
            return f"{g_date.year}/{g_date.month:02d}/{g_date.day:02d}"
        except Exception as e:
            print(f"[ERROR] خطا در تبدیل تاریخ {persian_date}: {e}")
            return None
    
    def parse_date_and_time_from_text(self, text):
        if not text:
            return None, None
            
        
        text = self.persian_to_english_numbers(text)
        
        date_str = None
        time_str = None
        
        
        pattern_dash = r'(\d{1,2}:\d{1,2})\s*[-–]\s*(\d{1,2})[-–](\d{1,2})[-–](\d{4})'
        match = re.search(pattern_dash, text)
        if match:
            time_str = match.group(1)
            day = match.group(2)
            month = match.group(3)
            year = match.group(4)
            
            if 1300 <= int(year) <= 1500:
                date_str = f"{year}/{month.zfill(2)}/{day.zfill(2)}"
        
        
        if not date_str:
            pattern_with_time = r'(\d{4}/\d{1,2}/\d{1,2})\s+(\d{1,2}:\d{1,2})'
            match = re.search(pattern_with_time, text)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)
        
        
        if not date_str:
            pattern = r'(\d{4}/\d{1,2}/\d{1,2})'
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
        
        
        if not date_str:
            pattern_dash_only = r'(\d{1,2})[-–](\d{1,2})[-–](\d{4})'
            match = re.search(pattern_dash_only, text)
            if match:
                day = match.group(1)
                month = match.group(2)
                year = match.group(3)
                if 1300 <= int(year) <= 1500:
                    date_str = f"{year}/{month.zfill(2)}/{day.zfill(2)}"
        
        if date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                year = int(parts[0])
                if 1300 <= year <= 1500:
                    
                    gregorian_date = self.persian_to_gregorian(date_str)
                    return gregorian_date, time_str
                else:
                    return date_str, time_str
        
        return None, None
    
    def parse_date_from_text(self, text):
        date, _ = self.parse_date_and_time_from_text(text)
        return date
    
    def get_news_from_advanced_search(self, from_date_shamsi, to_date_shamsi, page=1):
        try:
            
            url = f"{self.base_url}/fa/archive"
            params = {
                'service_id': -1,
                'sec_id': -1,
                'cat_id': -1,
                'rpp': 50,
                'from_date': from_date_shamsi,
                'to_date': to_date_shamsi,
                'p': page
            }
            
            print(f"[INFO] صفحه {page}: {url}?service_id=-1&sec_id=-1&cat_id=-1&rpp=50&from_date={from_date_shamsi}&to_date={to_date_shamsi}&p={page}")
            
            response = self.session.get(url, params=params, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"[ERROR] خطا: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            
            main_content = None
            
            
            possible_selectors = [
                'div.archive-content',
                'div.content',
                'div.main-content',
                'div.archive',
                'main',
                'section.archive',
                'div[class*="archive"]',
                'div[class*="content"]'
            ]
            
            for selector in possible_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            
            if not main_content:
                main_content = soup.find('body')
                if main_content:
                    
                    for unwanted in main_content.find_all(['aside', 'nav', 'header', 'footer']):
                        unwanted.decompose()
                    
                    for sidebar in main_content.find_all('div', class_=lambda x: x and ('sidebar' in str(x).lower() or 'side' in str(x).lower())):
                        sidebar.decompose()
            
            if not main_content:
                print(f"[WARNING] بخش اصلی آرشیو پیدا نشد!")
                return []
            
            
            main_links = []
            
            
            lists = main_content.find_all(['ul', 'ol'])
            for list_elem in lists:
                
                parent_classes = ' '.join([str(c) for c in (list_elem.get('class', []) or [])])
                if 'sidebar' not in parent_classes.lower() and 'side' not in parent_classes.lower():
                    links = list_elem.find_all('a', href=lambda h: h and '/fa/news/' in h)
                    main_links.extend(links)
            
            
            headings = main_content.find_all(['h2', 'h3'])
            for heading in headings:
                
                parent = heading.find_parent(['aside', 'nav', 'div'])
                if parent:
                    parent_classes = ' '.join([str(c) for c in (parent.get('class', []) or [])])
                    if 'sidebar' in parent_classes.lower() or 'side' in parent_classes.lower():
                        continue
                
                link = heading.find('a', href=lambda h: h and '/fa/news/' in h)
                if link:
                    main_links.append(link)
            
            
            articles = main_content.find_all('article')
            for article in articles:
                links = article.find_all('a', href=lambda h: h and '/fa/news/' in h)
                main_links.extend(links)
            
            
            if len(main_links) < 10:
                news_divs = main_content.find_all('div', class_=lambda x: x and ('news' in str(x).lower() or 'item' in str(x).lower()))
                for div in news_divs:
                    link = div.find('a', href=lambda h: h and '/fa/news/' in h)
                    if link:
                        main_links.append(link)
            
            
            seen_links = set()
            unique_links = []
            for link in main_links:
                href = link.get('href', '')
                if href not in seen_links:
                    seen_links.add(href)
                    unique_links.append(link)
            
            news_items = []
            seen_ids = set()
            
            for link in unique_links:
                href = link.get('href', '')
                
                
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = f"{self.base_url}{href}"
                else:
                    full_url = f"{self.base_url}/fa/{href}"
                
                
                if '/fa/news/' in full_url:
                    news_id = full_url.split('/fa/news/')[-1].split('/')[0]
                    if news_id.isdigit() and news_id not in seen_ids:
                        seen_ids.add(news_id)
                        title = link.get_text(strip=True)
                        if title and len(title) > 5:
                            news_items.append({
                                'url': full_url,
                                'title': title[:200],
                                'id': news_id
                            })
            
            print(f"[OK] {len(news_items)} خبر از صفحه {page}")
            return news_items
            
        except Exception as e:
            print(f"[ERROR] خطا: {e}")
            return []
    
    def get_news_from_archive_page(self, page=1):
        try:
            
            
            if page == 1:
                url = f"{self.base_url}/fa/archive"
            else:
                url = f"{self.base_url}/fa/archive?page={page}"
            
            print(f"[INFO] در حال دریافت صفحه {page} از آرشیو...")
            print(f"[DEBUG] URL: {url}")
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"[ERROR] خطا در دریافت صفحه: {response.status_code}")
                print(f"URL: {url}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []
            
            
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                
                
                if '/fa/news/' in href or (href.startswith('/') and 'news' in href.lower()):
                    
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = f"{self.base_url}{href}"
                    else:
                        full_url = f"{self.base_url}/fa/{href}"
                    
                    
                    title = link.get_text(strip=True)
                    if not title or len(title) < 10:  
                        
                        parent = link.find_parent(['h2', 'h3', 'div'])
                        if parent:
                            title = parent.get_text(strip=True)
                    
                    
                    date_text = None
                    time_text = None
                    parent_elem = link.find_parent(['article', 'div', 'li'])
                    if parent_elem:
                        
                        parent_text = parent_elem.get_text()
                        date_text, time_text = self.parse_date_and_time_from_text(parent_text)
                    
                    if title and len(title) > 5:  
                        news_items.append({
                            'url': full_url,
                            'title': title[:300],
                            'date_text': date_text,
                            'time_text': time_text
                        })
            
            
            if len(news_items) < 10:
                headings = soup.find_all(['h2', 'h3'])
                for heading in headings:
                    link = heading.find('a', href=True)
                    if link:
                        href = link.get('href', '')
                        if '/fa/news/' in href or '/news/' in href:
                            if href.startswith('http'):
                                full_url = href
                            elif href.startswith('/'):
                                full_url = f"{self.base_url}{href}"
                            else:
                                full_url = f"{self.base_url}/fa/{href}"
                            
                            title = link.get_text(strip=True) or heading.get_text(strip=True)
                            
                            
                            date_text = None
                            time_text = None
                            next_elem = heading.find_next_sibling(['div', 'span', 'p'])
                            if next_elem:
                                date_text, time_text = self.parse_date_and_time_from_text(next_elem.get_text())
                            
                            
                            if not any(item['url'] == full_url for item in news_items) and title:
                                news_items.append({
                                    'url': full_url,
                                    'title': title[:300],
                                    'date_text': date_text,
                                    'time_text': time_text
                                })
            
            
            seen_urls = set()
            unique_items = []
            for item in news_items:
                if item['url'] not in seen_urls:
                    seen_urls.add(item['url'])
                    unique_items.append(item)
            
            
            def sort_key(item):
                date = item.get('date_text', '')
                time = item.get('time_text', '00:00')
                if date and time:
                    return f"{date} {time}"
                elif date:
                    return f"{date} 00:00"
                else:
                    return "0000/00/00 00:00"
            
            unique_items.sort(key=sort_key, reverse=True)
            
            
            if unique_items:
                first_date = unique_items[0].get('date_text', 'N/A')
                first_time = unique_items[0].get('time_text', 'N/A')
                last_date = unique_items[-1].get('date_text', 'N/A')
                last_time = unique_items[-1].get('time_text', 'N/A')
                print(f"[OK] {len(unique_items)} خبر از صفحه {page} پیدا شد")
                print(f"[DEBUG] جدیدترین: {first_date} {first_time}")
                print(f"[DEBUG] قدیمی‌ترین: {last_date} {last_time}")
            else:
                print(f"[WARNING] هیچ خبری در صفحه {page} پیدا نشد!")
            
            return unique_items
            
        except Exception as e:
            print(f"[ERROR] خطا در دریافت صفحه آرشیو: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def crawl_single_news(self, news_url):
        try:
            response = self.session.get(news_url, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            
            news_code = None
            if '/fa/news/' in news_url:
                parts = news_url.split('/fa/news/')
                if len(parts) > 1:
                    code_part = parts[1].split('/')[0]
                    if code_part.isdigit():
                        news_code = code_part
            
            
            if not news_code:
                code_elem = soup.find(string=re.compile(r'کد\s*خبر', re.I))
                if code_elem:
                    parent = code_elem.find_parent()
                    if parent:
                        code_text = parent.get_text()
                        code_match = re.search(r'(\d+)', code_text)
                        if code_match:
                            news_code = code_match.group(1)
            
            
            title = None
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            if not title:
                title = "بدون عنوان"
            
            
            summary = None
            summary_selectors = [
                'div.subtitle',
                'div.lead',
                'div.lead-text',
                'div.summary',
                'div.excerpt',
                'p.lead'
            ]
            
            for selector in summary_selectors:
                summary_elem = soup.select_one(selector)
                if summary_elem:
                    summary = summary_elem.get_text(strip=True)
                    if len(summary) > 50:  
                        break
            
            
            if not summary and title_elem:
                next_p = title_elem.find_next_sibling('p')
                if not next_p:
                    next_p = title_elem.find_next('p')
                if next_p:
                    summary = next_p.get_text(strip=True)
                    if len(summary) < 50:  
                        summary = None
            
            
            text = ""
            content_selectors = [
                'div.news-content',
                'div.content',
                'article',
                'div.text',
                'div.body',
                'div[class*="content"]',
                'div[class*="text"]'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    
                    for unwanted in content_elem(["script", "style", "nav", "header", "footer", "aside"]):
                        unwanted.decompose()
                    
                    
                    for unwanted_class in ['ad', 'advertisement', 'related', 'sidebar', 'tags', 'share']:
                        for elem in content_elem.find_all(class_=re.compile(unwanted_class, re.I)):
                            elem.decompose()
                    
                    text = content_elem.get_text(separator=' ', strip=True)
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    stop_markers = [
                        r'منبع\s*:',
                        r'نظرات\s*کاربران',
                        r'خبر\s*بعد',
                        r'خبر\s*قبل',
                        r'اشتراک\s*گذاری',
                        r'فیلم\s*های\s*دیگر',
                        r'این\s*لحظه\s*با\s*حافظ',
                        r'آپارات\s*عصر\s*ایران'
                    ]
                    
                    for marker in stop_markers:
                        match = re.search(marker, text, re.I)
                        if match:
                            text = text[:match.start()].strip()
                            break
                    
                    if len(text) > 200:  
                        break
            
            
            if not text or len(text) < 200:
                body = soup.find('body')
                if body:
                    for unwanted in body(["script", "style", "nav", "header", "footer", "aside"]):
                        unwanted.decompose()
                    
                    main_content = body.find('main') or body.find('article') or body.find('div', class_=re.compile(r'content|main', re.I))
                    if main_content:
                        text = main_content.get_text(separator=' ', strip=True)
                        text = re.sub(r'\s+', ' ', text).strip()
                        
                        stop_markers = [
                            r'منبع\s*:',
                            r'نظرات\s*کاربران',
                            r'خبر\s*بعد',
                            r'خبر\s*قبل',
                            r'اشتراک\s*گذاری',
                            r'فیلم\s*های\s*دیگر',
                            r'این\s*لحظه\s*با\s*حافظ',
                            r'آپارات\s*عصر\s*ایران'
                        ]
                        
                        for marker in stop_markers:
                            match = re.search(marker, text, re.I)
                            if match:
                                text = text[:match.start()].strip()
                                break
            
            
            if text:
                text = text[:10000]
            else:
                text = "متن خبر در دسترس نیست"
            
            
            date = None
            time_str = None
            
            
            date_text_elem = soup.find(string=re.compile(r'تاریخ\s*(?:انتشار|:)?', re.I))
            if date_text_elem:
                parent = date_text_elem.find_parent()
                if parent:
                    
                    date_text = parent.get_text(strip=True)
                    
                    if not date_text or len(date_text) < 10:
                        next_sibling = parent.find_next_sibling()
                        if next_sibling:
                            date_text = next_sibling.get_text(strip=True)
                    if date_text:
                        date, time_str = self.parse_date_and_time_from_text(date_text)
            
            
            if not date:
                date_elem = soup.find(['time', 'span', 'div'], class_=re.compile(r'date|time|publish', re.I))
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    date, time_str = self.parse_date_and_time_from_text(date_text)
            
            
            if not date:
                all_elements = soup.find_all(['span', 'div', 'p', 'time'])
                for elem in all_elements:
                    elem_text = elem.get_text(strip=True)
                    
                    if re.search(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', elem_text) or re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', elem_text):
                        date, time_str = self.parse_date_and_time_from_text(elem_text)
                        if date:
                            break
            
            
            if not date:
                meta_date = soup.find('meta', property='article:published_time')
                if meta_date:
                    date_str = meta_date.get('content', '')
                    try:
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        date = dt.strftime('%Y/%m/%d')
                        time_str = dt.strftime('%H:%M')
                    except:
                        pass
            
            
            if not date:
                
                url_match = re.search(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', news_url)
                if url_match:
                    year, month, day = url_match.groups()
                    if 1300 <= int(year) <= 1500:
                        date_shamsi = f"{year}/{month.zfill(2)}/{day.zfill(2)}"
                        date = self.persian_to_gregorian(date_shamsi)
            
            
            if not date:
                print(f"[WARNING] نتوانست تاریخ خبر را از {news_url} استخراج کند")
                
                
                return None
            
            
            category = "عمومی"
            
            
            
            service_links = soup.find_all('a', href=re.compile(r'/fa/services/'))
            if service_links:
                for link in service_links:
                    link_text = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if link_text and len(link_text) > 0 and len(link_text) < 50:
                        
                        if link_text not in ['صفحه نخست', 'خانه', 'Home', ''] and not link_text.isdigit():
                            category = link_text
                            print(f"[DEBUG] دسته‌بندی از لینک /fa/services/ استخراج شد: {category} (href: {href})")
                            break
            
            
            if category == "عمومی":
                breadcrumb_text_elem = soup.find(string=re.compile(r'(صفحه\s*نخست|عصرایران\s*دو)', re.I))
                if breadcrumb_text_elem:
                    parent = breadcrumb_text_elem.find_parent()
                    if parent:
                        breadcrumb_text = parent.get_text()
                        
                        if '»' in breadcrumb_text:
                            parts = breadcrumb_text.split('»')
                            if len(parts) > 1:
                                last_part = parts[-1].strip()
                                
                                last_part = re.sub(r'\s+', ' ', last_part).strip()
                                
                                last_part = re.sub(r'کد\s*خبر.*', '', last_part).strip()
                                last_part = re.sub(r'\d+', '', last_part).strip()
                                
                                last_part = re.sub(r'انتشار\s*:?', '', last_part).strip()
                                last_part = re.sub(r'تاریخ\s*انتشار\s*:?', '', last_part).strip()
                                if last_part and len(last_part) > 0 and last_part not in ['صفحه نخست', 'خانه', 'Home', 'عصرایران دو', ''] and len(last_part) < 50:
                                    category = last_part
                                    print(f"[DEBUG] دسته‌بندی از breadcrumb استخراج شد: {category}")
            
            
            if category == "عمومی":
                
                breadcrumb_container = soup.find(['nav', 'div', 'ol', 'ul'], class_=re.compile(r'breadcrumb|bread', re.I))
                if not breadcrumb_container:
                    
                    all_divs = soup.find_all('div')
                    for div in all_divs:
                        div_text = div.get_text()
                        if ('صفحه نخست' in div_text or 'عصرایران دو' in div_text) and '»' in div_text:
                            breadcrumb_container = div
                            break
                
                if breadcrumb_container:
                    
                    all_links = breadcrumb_container.find_all('a')
                    if all_links and len(all_links) > 1:  
                        
                        last_link = all_links[-1]
                        link_text = last_link.get_text(strip=True)
                        href = last_link.get('href', '')
                        
                        if link_text and link_text not in ['صفحه نخست', 'خانه', 'Home', 'عصرایران دو', '']:
                            
                            link_text = re.sub(r'کد\s*خبر.*', '', link_text).strip()
                            link_text = re.sub(r'\d+', '', link_text).strip()
                            link_text = re.sub(r'انتشار\s*:?', '', link_text).strip()
                            if link_text and len(link_text) < 50:
                                category = link_text
                                print(f"[DEBUG] دسته‌بندی از لینک breadcrumb استخراج شد: {category} (href: {href})")
                    else:
                        
                        breadcrumb_text = breadcrumb_container.get_text()
                        if '»' in breadcrumb_text or '›' in breadcrumb_text:
                            parts = re.split(r'[»›]', breadcrumb_text)
                            if len(parts) > 1:
                                last_part = parts[-1].strip()
                                last_part = re.sub(r'\s+', ' ', last_part).strip()
                                last_part = re.sub(r'کد\s*خبر.*', '', last_part).strip()
                                last_part = re.sub(r'\d+', '', last_part).strip()
                                if last_part and last_part not in ['صفحه نخست', 'خانه', 'Home', 'عصرایران دو', ''] and len(last_part) < 50:
                                    category = last_part
            
            
            if category == "عمومی":
                category_links = soup.find_all('a', href=re.compile(r'/(political|economic|sport|culture|social|سیاسی|اقتصاد|ورزش|فرهنگ|اجتماعی)/'))
                if category_links:
                    for link in category_links:
                        link_text = link.get_text(strip=True)
                        if link_text and link_text not in ['صفحه نخست', 'خانه', 'Home'] and len(link_text) < 50:
                            category = link_text
                            break
            
            
            if category == "عمومی":
                if '/political/' in news_url or '/سیاسی/' in news_url:
                    category = "سیاسی"
                elif '/economic/' in news_url or '/اقتصاد/' in news_url:
                    category = "اقتصادی"
                elif '/sport/' in news_url or '/ورزش/' in news_url:
                    category = "ورزشی"
                elif '/culture/' in news_url or '/فرهنگ/' in news_url:
                    category = "فرهنگی"
            
            
            short_url = None
            short_url_elem = soup.find(string=re.compile(r'لینک\s*کوتاه', re.I))
            if short_url_elem:
                parent = short_url_elem.find_parent()
                if parent:
                    
                    link = parent.find('a', href=True)
                    if link:
                        short_url = link.get('href', '')
                        if not short_url.startswith('http'):
                            short_url = f"https://{short_url}" if short_url.startswith('asriran.com') else short_url
            
            
            if not short_url:
                short_input = soup.find('input', {'value': re.compile(r'asriran\.com/[\w]+')})
                if short_input:
                    short_url = short_input.get('value', '')
            
            
            tags = []
            
            
            tags_section = soup.find(['div', 'section'], class_=re.compile(r'tag|tags|label|keyword', re.I))
            if not tags_section:
                tags_section = soup.find(['div', 'section'], id=re.compile(r'tag|tags|label|keyword', re.I))
            
            if tags_section:
                
                tag_links = tags_section.find_all('a', href=re.compile(r'/tag/|/tags/|/keyword/'))
                for tag_link in tag_links:
                    tag_text = tag_link.get_text(strip=True)
                    if tag_text and len(tag_text) > 0 and tag_text not in tags:
                        tags.append(tag_text)
                
                
                if not tag_links:
                    tag_elements = tags_section.find_all(['span', 'div', 'li'], class_=re.compile(r'tag|label', re.I))
                    for tag_elem in tag_elements:
                        tag_text = tag_elem.get_text(strip=True)
                        if tag_text and len(tag_text) > 0 and tag_text not in tags and len(tag_text) < 50:
                            tags.append(tag_text)
            
            
            if not tags:
                meta_tags = soup.find_all('meta', property=re.compile(r'article:tag|tag|keyword', re.I))
                for meta_tag in meta_tags:
                    tag_content = meta_tag.get('content', '')
                    if tag_content and tag_content not in tags:
                        tags.append(tag_content)
            
            
            if not tags:
                all_tag_links = soup.find_all('a', href=re.compile(r'/tag/|/tags/'))
                for tag_link in all_tag_links:
                    tag_text = tag_link.get_text(strip=True)
                    if tag_text and len(tag_text) > 0 and tag_text not in tags and len(tag_text) < 50:
                        tags.append(tag_text)
            
            
            cleaned_tags = []
            for tag in tags:
                tag = tag.strip()
                if tag and len(tag) > 0 and len(tag) < 50 and tag not in ['برچسب', 'Tags', 'Tag', '']:
                    cleaned_tags.append(tag)
            tags = cleaned_tags
            
            
            category = category.strip()
            category = re.sub(r'\s+', ' ', category)  
            
            result = {
                'code': news_code,  
                'title': title,
                'summary': summary,  
                'text': text,  
                'date': date,
                'time': time_str or datetime.now().strftime('%H:%M'),
                'category': category,
                'short_url': short_url,  
                'tags': tags,  
                'url': news_url
            }
            
            print(f"[DEBUG] خبر {news_code}: دسته‌بندی = '{category}', برچسب‌ها = {tags}")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] خطا در کراول {news_url}: {e}")
            return None
    
    def crawl_news(self, start_date_shamsi, end_date_shamsi):
        print(f"[INFO] شروع کراول از {start_date_shamsi} تا {end_date_shamsi} (تاریخ شمسی)")
        
        all_news_urls = []
        seen_ids = set()
        
        print(f"[INFO] جستجو: {start_date_shamsi} تا {end_date_shamsi}")
        
        
        page = 1
        while True:
            news_items = self.get_news_from_advanced_search(start_date_shamsi, end_date_shamsi, page)
            
            
            if not news_items or len(news_items) == 0:
                print(f"[INFO] صفحه {page} خالی - توقف")
                break
            
            
            new_count = 0
            for item in news_items:
                news_id = item.get('id')
                if news_id and news_id not in seen_ids:
                    seen_ids.add(news_id)
                    item['page'] = page  
                    all_news_urls.append(item)
                    new_count += 1
            
            print(f"[INFO] صفحه {page}: {new_count} خبر جدید | مجموع: {len(all_news_urls)}")
            
            
            if new_count == 0:
                print(f"[INFO] همه تکراری - توقف")
                break
            
            
            if page >= 50:
                break
            
            page += 1
            time.sleep(0.3)
        
        print(f"[OK] {len(all_news_urls)} لینک خبر پیدا شد")
        
        if len(all_news_urls) == 0:
            print("[WARNING] هیچ لینک خبری پیدا نشد!")
            return []
        
        
        news_id = 1
        crawled_count = 0
        
        print(f"[INFO] شروع کراول {len(all_news_urls)} لینک خبر...")
        
        for idx, item in enumerate(all_news_urls, 1):
            page_num = item.get('page', '?')
            print(f"[INFO] در حال کراول ({idx}/{len(all_news_urls)}) [صفحه {page_num}]: {item['url'][:70]}...")
            
            news_data = self.crawl_single_news(item['url'])
            
            if news_data:
                
                if item.get('title') and len(item['title']) > len(news_data.get('title', '')):
                    news_data['title'] = item['title']
                
                
                news_date = news_data.get('date', '')
                if not news_date:
                    print(f"[SKIP] خبر رد شد [صفحه {page_num}]: تاریخ پیدا نشد")
                    continue
                
                if news_date:
                    try:
                        
                        parts = news_date.split('/')
                        if len(parts) == 3:
                            year = int(parts[0])
                            
                            
                            if 1300 <= year <= 1500:
                                news_date_shamsi = news_date
                            else:
                                
                                dt_obj = datetime.strptime(news_date, "%Y/%m/%d")
                                j_date = jdatetime.date.fromgregorian(date=dt_obj.date())
                                news_date_shamsi = f"{j_date.year}/{j_date.month:02d}/{j_date.day:02d}"
                            
                            
                            if news_date_shamsi < start_date_shamsi or news_date_shamsi > end_date_shamsi:
                                print(f"[SKIP] خبر رد شد [صفحه {page_num}]: تاریخ {news_date_shamsi} خارج از بازه")
                                continue
                    except Exception as e:
                        
                        print(f"[WARNING] خطا در parse تاریخ {news_date}: {e}")
                
                news_data['id'] = news_id
                self.news_list.append(news_data)
                news_id += 1
                crawled_count += 1
                print(f"[OK] خبر #{news_id-1} [صفحه {page_num}]: {news_data.get('title', '')[:55]}... (تاریخ: {news_date})")
                
                time.sleep(0.5)  
            else:
                print(f"[WARNING] نتوانست خبر را کراول کند: {item['url'][:50]}...")
        
        print("\n" + "="*60)
        print(f"[OK] کراول تمام شد:")
        print(f"     - تعداد لینک‌های یافت شده: {len(all_news_urls)}")
        print(f"     - تعداد اخبار کراول شده: {crawled_count}")
        print(f"     - تعداد اخبار ذخیره شده: {len(self.news_list)}")
        print("="*60 + "\n")
        return self.news_list
    
    def save_to_folder(self, folder_path="news_data"):
        try:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                print(f"[INFO] پوشه {folder_path} ساخته شد")
            
            
            for news in self.news_list:
                file_path = os.path.join(folder_path, f"news_{news['id']}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(news, f, ensure_ascii=False, indent=2)
            
            
            all_news_path = os.path.join(folder_path, "all_news.json")
            with open(all_news_path, 'w', encoding='utf-8') as f:
                json.dump(self.news_list if self.news_list else [], f, ensure_ascii=False, indent=2)
            
            print(f"[OK] اخبار در پوشه {folder_path} ذخیره شد")
            return all_news_path
        except Exception as e:
            print(f"[ERROR] خطا در ذخیره فایل: {e}")
            raise

if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            print("[ERROR] استفاده: python crawler.py START_DATE END_DATE")
            print("مثال: python crawler.py 2024/11/01 2024/11/05")
            sys.exit(1)
        
        start_date = sys.argv[1]
        end_date = sys.argv[2]
        
        print(f"[INFO] شروع کراولر...")
        print(f"[INFO] بازه زمانی: {start_date} تا {end_date}")
        
        crawler = NewsCrawler()
        news_list = crawler.crawl_news(start_date, end_date)
        
        if not news_list or len(news_list) == 0:
            print("[WARNING] هیچ خبری پیدا نشد. در حال ساخت فایل خالی...")
            
            crawler.news_list = []
        
        all_news_file = crawler.save_to_folder()
        
        print(f"[OK] نتیجه: {all_news_file}")
        print(f"[OK] تعداد اخبار: {len(crawler.news_list)}")
        sys.exit(0)
        
    except Exception as e:
        print(f"[ERROR] خطای غیرمنتظره: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
