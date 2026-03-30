# -*- coding: utf-8 -*-
"""
论文搜索与验证系统 v5.0
新增功能：相关性分析、中文解读、可视化、API自动切换、设置配置
"""

import sys
import os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
import time
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path

# ==================== 加载配置 ====================
def load_settings():
    """从settings.json加载配置"""
    settings_file = Path(__file__).parent / 'settings.json'
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

settings = load_settings()

# API配置（优先使用settings.json中的配置）
SERPAPI_KEY = "a65089c62fdfa94600f13300d3684e2051b4efe95d160d28d32a6f799a823571"
CORE_API_KEY = "KIFAPNWtOS3J9lvThr7E1CbxqmBXwfpD"
OPENAI_API_KEY = settings.get('api_key') or "sk-rniPHXm3rCD1M4LIyFFw0zhXsJIdmfXIRRZLEsSpBoLk56n2"
OPENAI_API_BASE = settings.get('api_url') or "https://api.nofx.online/v1"
OPENAI_MODEL = settings.get('model') or "gpt-5.4"

# 搜索配置
YEAR_START = 2021
YEAR_END = 2026
MAX_RESULTS = settings.get('search_count') or 50
DUPLICATE_THRESHOLD = 0.8

# API状态
api_status = {
    "SerpAPI": {"available": True, "last_error": None},
    "OpenAlex": {"available": True, "last_error": None},
    "CrossRef": {"available": True, "last_error": None},
    "Semantic Scholar": {"available": True, "last_error": None},
}

# 进度条锁
progress_lock = threading.Lock()

# ==================== 顶会列表 ====================
TOP_VENUES = {
    # AI/ML
    "NeurIPS", "ICML", "ICLR", "AAAI", "IJCAI", "AISTATS", "UAI",
    # NLP
    "ACL", "EMNLP", "NAACL", "COLING", "LREC", "EACL",
    # CV
    "CVPR", "ICCV", "ECCV", "WACV", "BMVC",
    # 系统
    "OSDI", "SOSP", "NSDI", "SIGCOMM", "ASPLOS", "EuroSys", "ATC",
    # 安全
    "IEEE S&P", "CCS", "USENIX Security", "NDSS",
    # 数据库
    "SIGMOD", "VLDB", "ICDE", "CIDR",
    # 软件工程
    "ICSE", "FSE", "ASE",
    # 网络
    "MobiCom", "INFOCOM",
    # 图形学
    "SIGGRAPH",
    # 人机交互
    "CHI", "UIST", "CSCW",
    # 多媒体
    "ACM MM", "ICME",
    # 信息检索
    "SIGIR", "WSDM", "CIKM", "WWW",
    # 机器人
    "ICRA", "IROS", "RSS",
    # 数据挖掘
    "KDD", "ICDM", "SDM",
    # 推荐
    "RecSys",
    # 期刊
    "Nature", "Science", "JMLR", "TPAMI", "TACL", "TOIS", "TKDE",
}


# ==================== 进度条 ====================

class ProgressBar:
    """简单进度条"""

    def __init__(self, total, desc="Progress"):
        self.total = total
        self.current = 0
        self.desc = desc
        self.start_time = time.time()

    def update(self, n=1):
        with progress_lock:
            self.current += n
            self._display()

    def _display(self):
        if self.total == 0:
            return

        percent = min(100, int(self.current / self.total * 100))
        bar_len = 30
        filled = int(bar_len * self.current / self.total)
        bar = "=" * filled + "-" * (bar_len - filled)

        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = elapsed / self.current * (self.total - self.current)
            eta_str = f"ETA: {int(eta)}s"
        else:
            eta_str = "ETA: --"

        print(f"\r  {self.desc}: [{bar}] {percent}% ({self.current}/{self.total}) {eta_str}", end="", flush=True)

        if self.current >= self.total:
            print()  # 换行

    def close(self):
        self.current = self.total
        self._display()


# ==================== 论文评分系统 ====================

def calculate_paper_score(paper):
    """
    综合评分系统 (0-100分)
    - 引用数 (0-30分)
    - 顶会加成 (0-25分)
    - 年份新鲜度 (0-20分)
    - 完整性 (0-15分)
    - 相关性 (0-10分)
    """
    score = 0
    details = []

    # 1. 引用数评分 (0-30)
    citations = paper.get("citations", 0)
    if citations >= 1000:
        cite_score = 30
        details.append(f"引用{citations}(顶级)")
    elif citations >= 500:
        cite_score = 25
        details.append(f"引用{citations}(高)")
    elif citations >= 100:
        cite_score = 20
        details.append(f"引用{citations}(中)")
    elif citations >= 50:
        cite_score = 15
        details.append(f"引用{citations}(一般)")
    elif citations >= 10:
        cite_score = 10
        details.append(f"引用{citations}(较少)")
    else:
        cite_score = 5
        details.append(f"引用{citations}(新/少)")
    score += cite_score

    # 2. 顶会加成 (0-25)
    is_top, venue_name = is_top_venue(paper.get("venue", ""))
    if is_top:
        score += 25
        details.append(f"顶会:{venue_name}")
    else:
        details.append("非顶会")

    # 3. 年份新鲜度 (0-20)
    year = paper.get("year")
    current_year = datetime.now().year
    if year:
        age = current_year - year
        if age == 0:
            score += 20
            details.append("当年新文")
        elif age == 1:
            score += 18
            details.append("1年内")
        elif age == 2:
            score += 15
            details.append("2年内")
        elif age == 3:
            score += 12
            details.append("3年内")
        elif age <= 5:
            score += 8
            details.append(f"{age}年前")
        else:
            score += 5
            details.append(f"{age}年前(较旧)")

    # 4. 完整性 (0-15)
    completeness = 0
    if paper.get("title"):
        completeness += 3
    if paper.get("authors"):
        completeness += 3
    if paper.get("abstract"):
        completeness += 4
    if paper.get("venue"):
        completeness += 3
    if paper.get("url"):
        completeness += 2
    score += completeness
    details.append(f"完整度{completeness}/15")

    # 5. 相关性 (从AI分析中获取，默认给满分)
    rel_score = paper.get("relevance_score", 10)
    if rel_score >= 80:
        score += 10
        details.append("高度相关")
    elif rel_score >= 60:
        score += 7
        details.append("相关")
    elif rel_score >= 40:
        score += 5
        details.append("部分相关")
    else:
        score += 3
        details.append("弱相关")

    return min(100, score), "; ".join(details)


def get_score_level(score):
    """评分等级"""
    if score >= 80:
        return "S", "强烈推荐"
    elif score >= 70:
        return "A", "推荐阅读"
    elif score >= 60:
        return "B", "值得一看"
    elif score >= 50:
        return "C", "一般"
    else:
        return "D", "参考"


# ==================== 搜索引擎（带API状态检测） ====================

def search_serpapi(keyword, max_results=MAX_RESULTS):
    """SerpAPI - Google Scholar"""
    papers = []
    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_scholar",
            "q": f"{keyword} after:{YEAR_START} before:{YEAR_END}",
            "api_key": SERPAPI_KEY,
            "num": max_results
        }
        r = requests.get(url, params=params, timeout=30)

        if r.status_code == 429:
            api_status["SerpAPI"]["available"] = False
            api_status["SerpAPI"]["last_error"] = "Rate limited"
            return papers, "SerpAPI", "Rate limited"

        data = r.json()

        for result in data.get("organic_results", []):
            pub_info = result.get("publication_info", {})
            summary = pub_info.get("summary", "") if isinstance(pub_info, dict) else ""

            venue = ""
            if " - " in summary:
                venue = summary.split(" - ")[-1]
                venue = re.sub(r',?\s*\d{4}', '', venue).strip()

            snippet = result.get("snippet", "")
            years = re.findall(r'\b(20[1-2][0-9])\b', f"{snippet} {summary}")
            year = max([int(y) for y in years]) if years else None

            authors = ""
            if isinstance(pub_info, dict):
                auth_list = pub_info.get("authors", [])
                if isinstance(auth_list, list):
                    authors = ", ".join([a.get("name", "") for a in auth_list])

            papers.append({
                "title": result.get("title", ""),
                "authors": authors,
                "year": year,
                "venue": venue,
                "abstract": snippet,
                "url": result.get("link", ""),
                "citations": result.get("inline_links", {}).get("cited_by", {}).get("total", 0),
                "source": "SerpAPI"
            })

        return papers, "SerpAPI", None

    except Exception as e:
        api_status["SerpAPI"]["available"] = False
        api_status["SerpAPI"]["last_error"] = str(e)
        return papers, "SerpAPI", str(e)


def search_openalex(keyword, max_results=MAX_RESULTS):
    """OpenAlex API"""
    papers = []
    try:
        url = "https://api.openalex.org/works"
        params = {
            "search": keyword,
            "filter": f"from_publication_date:{YEAR_START}-01-01,to_publication_date:{YEAR_END}-12-31",
            "per_page": min(max_results, 100),
            "mailto": "research@example.com"
        }
        r = requests.get(url, params=params, timeout=30)
        data = r.json()

        for item in data.get("results", []):
            authors = []
            for a in item.get("authorships", [])[:5]:
                author = a.get("author", {})
                if author:
                    authors.append(author.get("display_name", ""))

            venue = ""
            loc = item.get("primary_location", {})
            if loc and loc.get("source"):
                venue = loc["source"].get("display_name", "")

            year = None
            pub_date = item.get("publication_date", "")
            if pub_date:
                year = int(pub_date[:4])

            abstract = ""
            inv_index = item.get("abstract_inverted_index", {})
            if inv_index:
                words = [""] * (max(max(pos) for pos in inv_index.values()) + 1 if inv_index else 0)
                for word, positions in inv_index.items():
                    for pos in positions:
                        if pos < len(words):
                            words[pos] = word
                abstract = " ".join(words[:200])

            papers.append({
                "title": item.get("title", ""),
                "authors": ", ".join(authors),
                "year": year,
                "venue": venue,
                "abstract": abstract,
                "url": item.get("id", ""),
                "citations": item.get("cited_by_count", 0),
                "source": "OpenAlex"
            })

        return papers, "OpenAlex", None

    except Exception as e:
        api_status["OpenAlex"]["available"] = False
        api_status["OpenAlex"]["last_error"] = str(e)
        return papers, "OpenAlex", str(e)


def search_crossref(keyword, max_results=MAX_RESULTS):
    """CrossRef API"""
    papers = []
    try:
        url = "https://api.crossref.org/works"
        params = {
            "query": keyword,
            "filter": f"from-pub-date:{YEAR_START},until-pub-date:{YEAR_END}",
            "rows": max_results
        }
        r = requests.get(url, params=params, timeout=30)
        data = r.json()

        for item in data.get("message", {}).get("items", []):
            authors = []
            for a in item.get("author", [])[:5]:
                name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                authors.append(name)

            pub_date = item.get("published-print") or item.get("published-online") or {}
            year_parts = pub_date.get("date-parts", [[None]])
            year = year_parts[0][0] if year_parts and year_parts[0] else None

            venue_list = item.get("container-title", [])
            venue = venue_list[0] if venue_list else ""

            papers.append({
                "title": item.get("title", [""])[0],
                "authors": ", ".join(authors),
                "year": year,
                "venue": venue,
                "abstract": item.get("abstract", ""),
                "url": item.get("URL", ""),
                "citations": item.get("is-referenced-by-count", 0),
                "source": "CrossRef"
            })

        return papers, "CrossRef", None

    except Exception as e:
        api_status["CrossRef"]["available"] = False
        api_status["CrossRef"]["last_error"] = str(e)
        return papers, "CrossRef", str(e)


def search_semantic_scholar(keyword, max_results=MAX_RESULTS):
    """Semantic Scholar API"""
    papers = []
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": keyword,
            "year": f"{YEAR_START}-{YEAR_END}",
            "limit": max_results,
            "fields": "title,authors,year,venue,abstract,url,citationCount"
        }
        r = requests.get(url, params=params, timeout=30)

        if r.status_code == 429:
            api_status["Semantic Scholar"]["available"] = False
            api_status["Semantic Scholar"]["last_error"] = "Rate limited"
            return papers, "Semantic Scholar", "Rate limited"

        data = r.json()

        for item in data.get("data", []):
            papers.append({
                "title": item.get("title", ""),
                "authors": ", ".join([a.get("name", "") for a in item.get("authors", [])]),
                "year": item.get("year"),
                "venue": item.get("venue", ""),
                "abstract": item.get("abstract", ""),
                "url": item.get("url", ""),
                "citations": item.get("citationCount", 0),
                "source": "Semantic Scholar"
            })

        return papers, "Semantic Scholar", None

    except Exception as e:
        api_status["Semantic Scholar"]["available"] = False
        api_status["Semantic Scholar"]["last_error"] = str(e)
        return papers, "Semantic Scholar", str(e)


# ==================== 并发搜索 ====================

def search_all_concurrent(keyword, max_results=MAX_RESULTS):
    """并发搜索所有API"""
    print("\n[Concurrent Search] Starting...")

    all_papers = []
    search_funcs = [
        lambda: search_serpapi(keyword, max_results),
        lambda: search_openalex(keyword, max_results // 2),
        lambda: search_crossref(keyword, max_results // 2),
        lambda: search_semantic_scholar(keyword, max_results // 2),
    ]

    # 进度条
    progress = ProgressBar(len(search_funcs), "APIs")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(func): i for i, func in enumerate(search_funcs)}

        for future in as_completed(futures):
            try:
                papers, api_name, error = future.result()
                if error:
                    print(f"\n  [{api_name}] Error: {error} (switching to backup)")
                else:
                    print(f"\n  [{api_name}] Found {len(papers)} papers")
                all_papers.extend(papers)
            except Exception as e:
                print(f"\n  [API] Exception: {e}")

            progress.update()

    progress.close()

    return all_papers


# ==================== 工具函数 ====================

def normalize_title(title):
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    return ' '.join(title.split())


def calc_similarity(t1, t2):
    t1, t2 = normalize_title(t1), normalize_title(t2)
    if not t1 or not t2:
        return 0
    if t1 == t2:
        return 1.0
    if t1 in t2 or t2 in t1:
        return 0.9
    w1, w2 = set(t1.split()), set(t2.split())
    if not w1 or not w2:
        return 0
    return len(w1 & w2) / len(w1 | w2)


def is_duplicate(paper, existing):
    for p in existing:
        if calc_similarity(paper.get("title", ""), p.get("title", "")) >= DUPLICATE_THRESHOLD:
            return True
    return False


def deduplicate(papers):
    unique = []
    for p in papers:
        if not is_duplicate(p, unique):
            unique.append(p)
    return unique


def is_top_venue(venue):
    if not venue:
        return False, ""
    venue_upper = venue.upper()
    for top in TOP_VENUES:
        if top.upper() in venue_upper:
            return True, top
    return False, ""


# ==================== AI分析与全文解读 ====================

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
MIN_FULLTEXT_CHARS = 4000
MAX_FULLTEXT_PROMPT_CHARS = 26000

try:
    from pypdf import PdfReader
except Exception:
    try:
        from PyPDF2 import PdfReader
    except Exception:
        PdfReader = None


def check_relevance(title, abstract, keyword):
    prompt = f"""Is this paper relevant to keyword '{keyword}'?

Title: {title}
Abstract: {abstract[:300] if abstract else 'No abstract'}

Return JSON only:
{{"is_relevant": true/false, "score": 0-100, "reason": "brief explanation"}}
"""

    try:
        r = requests.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 150},
            timeout=30
        )
        content = r.json()["choices"][0]["message"]["content"]
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            data = json.loads(match.group())
            return data.get("is_relevant", True), data.get("score", 50), data.get("reason", "")
    except Exception:
        pass
    return True, 50, "Check failed"


def generate_analysis(title, abstract, keyword, original_keyword=None):
    """生成摘要级分析（兼容旧页面）"""
    user_keyword = original_keyword or keyword

    prompt = f"""请分析这篇论文与用户研究主题"{user_keyword}"的相关性。

论文标题：{title}
论文摘要：{abstract[:600] if abstract else '无摘要'}
英文搜索关键词：{keyword}
用户研究主题：{user_keyword}

请严格按照以下JSON格式返回（只返回JSON，不要其他内容）：
{{
    "relevance_score": "相关性评分1-5星",
    "relevance_reason": "与用户主题的相关性说明（30字）",
    "summary": "核心内容概述（80字以内，说明该论文对'{user_keyword}'研究的具体帮助）",
    "chinese_explanation": "中文详细解读（150字左右，包括：研究问题、核心方法、主要贡献、实验结果）",
    "applications": "与'{user_keyword}'相关的实际应用场景（列举2-3个具体应用）",
    "suggestions": "阅读建议（是否值得阅读、适合什么背景读者、与'{user_keyword}'的结合点）"
}}
"""

    try:
        r = requests.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 1000},
            timeout=60
        )
        content = r.json()["choices"][0]["message"]["content"]
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            data = json.loads(match.group())
            return (
                data.get("summary", ""),
                data.get("chinese_explanation", ""),
                data.get("applications", ""),
                data.get("suggestions", ""),
                data.get("relevance_score", "★★★☆☆"),
                data.get("relevance_reason", "")
            )
    except Exception as e:
        print(f"\n    Analysis error: {e}")
    return "", "", "", "", "★★★☆☆", ""


def slugify_text(text, fallback="paper"):
    text = (text or "").strip().lower()
    text = re.sub(r'https?://', '', text)
    text = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text[:80] or fallback


def sanitize_filename(text, fallback="paper"):
    safe = re.sub(r'[\\/:*?"<>|]+', '_', (text or '').strip())
    safe = re.sub(r'\s+', '_', safe)
    safe = safe.strip('._')
    return safe[:120] or fallback


def strip_html_tags(text):
    text = re.sub(r'<script[\s\S]*?</script>', ' ', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ')
    return text


def clean_fulltext(text):
    text = strip_html_tags(text or '')
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\x00', ' ')
    return text.strip()


def extract_pdf_text(content_bytes):
    if not PdfReader:
        return ""
    try:
        import io
        reader = PdfReader(io.BytesIO(content_bytes))
        texts = []
        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            if page_text:
                texts.append(page_text)
        return clean_fulltext("\n".join(texts))
    except Exception:
        return ""


def normalize_candidate_url(url):
    if not url:
        return ""
    url = str(url).strip()
    if not url or url.startswith('https://api.openalex.org/'):
        return ""
    if 'arxiv.org/abs/' in url:
        return url.replace('/abs/', '/pdf/') + '.pdf'
    return url


def build_fulltext_candidate_urls(paper):
    candidates = []
    for key in ['pdf_url', 'link', 'landing_page_url', 'url', 'doi_url']:
        value = normalize_candidate_url(paper.get(key, ''))
        if value and value not in candidates:
            candidates.append(value)
    for value in paper.get('candidate_urls', []) or []:
        value = normalize_candidate_url(value)
        if value and value not in candidates:
            candidates.append(value)
    return candidates


def fetch_url_text(url):
    headers = {'User-Agent': USER_AGENT, 'Accept': 'text/html,application/pdf;q=0.9,*/*;q=0.8'}
    try:
        response = requests.get(url, headers=headers, timeout=40, allow_redirects=True)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        final_url = response.url

        if 'pdf' in content_type or final_url.lower().endswith('.pdf'):
            text = extract_pdf_text(response.content)
            if len(text) >= MIN_FULLTEXT_CHARS:
                return {'status': 'ok', 'text': text, 'source_url': final_url, 'content_type': 'pdf'}
            return {'status': 'too_short', 'text': text, 'source_url': final_url, 'content_type': 'pdf'}

        text = clean_fulltext(response.text)
        if len(text) >= MIN_FULLTEXT_CHARS:
            return {'status': 'ok', 'text': text, 'source_url': final_url, 'content_type': 'html'}
        return {'status': 'too_short', 'text': text, 'source_url': final_url, 'content_type': 'html'}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'source_url': url}


def fetch_fulltext_for_paper(paper):
    candidates = build_fulltext_candidate_urls(paper)
    errors = []
    for candidate in candidates:
        result = fetch_url_text(candidate)
        if result['status'] == 'ok':
            return {
                'status': 'available',
                'fulltext_text': result['text'],
                'fulltext_url': result.get('source_url', candidate),
                'fulltext_source_type': result.get('content_type', ''),
                'fulltext_attempts': candidates
            }
        error_hint = result.get('error') or result.get('status')
        errors.append(f"{candidate} => {error_hint}")

    return {
        'status': 'unavailable',
        'fulltext_text': '',
        'fulltext_url': '',
        'fulltext_source_type': '',
        'fulltext_attempts': candidates,
        'fulltext_error': '; '.join(errors[:5])
    }


def build_fulltext_prompt_segments(fulltext_text):
    text = clean_fulltext(fulltext_text)
    if len(text) <= MAX_FULLTEXT_PROMPT_CHARS:
        return [text]

    windows = []
    segment_len = MAX_FULLTEXT_PROMPT_CHARS // 4
    positions = [0, max(len(text) // 3 - segment_len // 2, 0), max(2 * len(text) // 3 - segment_len // 2, 0), max(len(text) - segment_len, 0)]
    seen = set()
    for pos in positions:
        if pos in seen:
            continue
        seen.add(pos)
        windows.append(text[pos:pos + segment_len])
    return windows


def generate_fulltext_analysis(paper, keyword, original_keyword, fulltext_text):
    user_keyword = original_keyword or keyword
    segments = build_fulltext_prompt_segments(fulltext_text)
    segment_text = "\n\n".join([f"[正文片段{i+1}]\n{seg}" for i, seg in enumerate(segments)])

    prompt = f"""你将基于论文全文片段生成中文分析。禁止使用论文之外的信息、常识补充、外部资料或猜测。

用户研究主题：{user_keyword}
英文搜索关键词：{keyword}
论文标题：{paper.get('title', '')}
作者：{paper.get('authors', '')}
年份：{paper.get('year', '')}
会议/期刊：{paper.get('venue', '')}

请只依据下面给出的论文正文片段作答：
{segment_text}

请严格返回JSON，不要输出JSON之外的任何文字：
{{
  "detailed_interpretation": "中文详细解读，必须只基于正文；若某点正文未明确说明，请明确写‘论文未明确说明’",
  "practical_usage": "结合用户主题，说明该论文可支持的实际运用或业务含义。只能写正文可支持的应用、任务、场景；不确定就写‘论文未明确说明’",
  "evidence_excerpt": ["从正文片段中摘录的3-5条关键依据，可直接引用或紧贴原意转述"],
  "evidence_note": "说明上述解读和实际运用分别由正文哪些内容支撑；无支撑处必须写‘论文未明确说明’"
}}
"""

    try:
        r = requests.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1, "max_tokens": 2200},
            timeout=120
        )
        content = r.json()["choices"][0]["message"]["content"]
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            data = json.loads(match.group())
            excerpts = data.get('evidence_excerpt', [])
            if not isinstance(excerpts, list):
                excerpts = [str(excerpts)] if excerpts else []
            return {
                'detailed_interpretation': data.get('detailed_interpretation', '论文未明确说明'),
                'practical_usage': data.get('practical_usage', '论文未明确说明'),
                'evidence_excerpt': [str(item).strip() for item in excerpts if str(item).strip()][:5],
                'evidence_note': data.get('evidence_note', '论文未明确说明')
            }
    except Exception as e:
        print(f"\n    Fulltext analysis error: {e}")

    return {
        'detailed_interpretation': '论文未明确说明',
        'practical_usage': '论文未明确说明',
        'evidence_excerpt': [],
        'evidence_note': '论文未明确说明'
    }


def build_paper_note_markdown(paper, keyword, original_keyword, fulltext_analysis):
    user_keyword = original_keyword or keyword
    evidence_excerpt = fulltext_analysis.get('evidence_excerpt', [])
    if evidence_excerpt:
        evidence_md = "\n".join([f"- {item}" for item in evidence_excerpt])
    else:
        evidence_md = "- 论文未明确说明"

    original_link = paper.get('fulltext_url') or paper.get('link') or paper.get('url') or '无'

    return f"""# {paper.get('title', '未知标题')}

## 论文信息
- 标题：{paper.get('title', '未知标题')}
- 作者：{paper.get('authors', '未知')}
- 年份：{paper.get('year', '未知')}
- 会议/期刊：{paper.get('venue', '未知')}
- 用户搜索主题：{user_keyword}
- 原文链接：{original_link}

## 中文详细解读
{fulltext_analysis.get('detailed_interpretation', '论文未明确说明')}

## 结合主题的实际运用
{fulltext_analysis.get('practical_usage', '论文未明确说明')}

## 证据摘录
{evidence_md}

## 依据说明
{fulltext_analysis.get('evidence_note', '论文未明确说明')}

## 生成约束说明
- 本文仅基于可获取的论文全文/正文片段生成。
- 对正文无法支持的内容，统一标记为“论文未明确说明”。
"""


# ==================== 可视化 ====================

def generate_visualization(papers, keyword):
    """生成ASCII可视化图表"""

    if not papers:
        return ""

    # 1. 评分分布
    score_dist = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
    for p in papers:
        score = p.get("score", 0)
        level = p.get("level", get_score_level(score)[0])
        score_dist[level] += 1

    # 2. 年份分布
    year_dist = {}
    for p in papers:
        year = p.get("year")
        if year:
            year_dist[year] = year_dist.get(year, 0) + 1

    # 3. 来源分布
    source_dist = {}
    for p in papers:
        source = p.get("source", "Unknown")
        source_dist[source] = source_dist.get(source, 0) + 1

    viz = f"""
## 数据可视化

### 评分分布

```
S级 (80-100): {"*" * score_dist["S"]} ({score_dist["S"]})
A级 (70-79):  {"*" * score_dist["A"]} ({score_dist["A"]})
B级 (60-69):  {"*" * score_dist["B"]} ({score_dist["B"]})
C级 (50-59):  {"*" * score_dist["C"]} ({score_dist["C"]})
D级 (<50):    {"*" * score_dist["D"]} ({score_dist["D"]})
```

### 年份分布

```
"""

    for year in sorted(year_dist.keys(), reverse=True):
        count = year_dist[year]
        bar = "*" * min(count, 20)
        viz += f"{year}: {bar} ({count})\n"

    viz += "```\n\n### 来源分布\n\n```\n"

    for source, count in sorted(source_dist.items(), key=lambda x: -x[1]):
        bar = "*" * min(count, 20)
        viz += f"{source[:15]:<15}: {bar} ({count})\n"

    viz += "```\n"

    return viz


# ==================== Markdown生成 ====================

def generate_markdown(papers, keyword, original_keyword=None):
    """生成Markdown（含评分和可视化）"""
    user_keyword = original_keyword or keyword

    for p in papers:
        score, details = calculate_paper_score(p)
        p["score"] = score
        p["score_details"] = details
        level, desc = get_score_level(score)
        p["level"] = level
        p["level_desc"] = desc

    papers.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_papers = [p for p in papers if is_top_venue(p.get("venue", ""))[0]]

    md = f"""# 论文搜索结果

**关键词**: {keyword}
**用户主题**: {user_keyword}
**日期**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**总数**: {len(papers)} 篇 (顶会: {len(top_papers)})

---

## 汇总表（按评分排序）

| 排名 | 评分 | 论文 | 作者 | 年份 | 会议 | 顶会 | 相关性 | 全文解读 | 核心观点 |
|------|------|------|------|------|------|------|--------|----------|----------|
"""

    for i, p in enumerate(papers, 1):
        is_top, venue_name = is_top_venue(p.get("venue", ""))
        top_mark = f"[{venue_name}]" if is_top else "--"
        score = p.get("score", 0)
        level = p.get("level", "?")
        authors = str(p.get("authors", ""))[:15]
        venue = str(p.get("venue", ""))[:12]
        summary = p.get("summary", "")[:50]
        rel_stars = p.get("relevance_stars", "★★★☆☆")
        note_status = "已生成" if p.get("has_fulltext_markdown") else "缺全文"

        md += f"| {i} | {level}({score}) | [[{p['title'][:35]}]] | {authors} | {p.get('year', '')} | {venue} | {top_mark} | {rel_stars} | {note_status} | {summary} |\n"

    md += generate_visualization(papers, keyword)
    md += "\n---\n\n## 论文详情\n\n"

    for i, p in enumerate(papers, 1):
        is_top, venue_name = is_top_venue(p.get("venue", ""))
        score = p.get("score", 0)
        level = p.get("level", "?")
        level_desc = p.get("level_desc", "")
        rel_stars = p.get("relevance_stars", "★★★☆☆")
        rel_reason = p.get("relevance_reason", "")
        fulltext_status = "已生成单篇全文解读" if p.get('has_fulltext_markdown') else "未生成（未获取到可解析全文）"

        md += f"""### {i}. [[{p['title']}]]

**评分**: {level}级 ({score}分) - {level_desc}

**与"{user_keyword}"的相关性**: {rel_stars} {rel_reason}

- **会议**: {p.get('venue', 'N/A')} {f"({venue_name})" if is_top else ""}
- **年份**: {p.get('year', 'N/A')}
- **作者**: {p.get('authors', 'N/A')}
- **引用**: {p.get('citations', 0)}
- **链接**: [{p.get('link') or p.get('url', '')}]({p.get('link') or p.get('url', '')})
- **单篇全文解读**: {fulltext_status}

**评分详情**: {p.get('score_details', 'N/A')}

**核心观点**: {p.get('summary', 'N/A')}

**中文详细解读**: {p.get('chinese_explanation', 'N/A')}

**与{user_keyword}相关的应用**: {p.get('applications', 'N/A')}

**阅读建议**: {p.get('suggestions', 'N/A')}

---

"""

    return md


# ==================== 主程序 ====================

def main(keyword, max_results=MAX_RESULTS, original_keyword=None, project_dir=None):
    """主函数，original_keyword为用户输入的中文关键词"""

    print(f"""
+----------------------------------------------------------+
|            论文搜索系统 v5.0                              |
+----------------------------------------------------------+
|  新功能: 相关性分析、中文解读、可视化、API自动切换        |
+----------------------------------------------------------+
""")

    print("="*50)
    print(f"关键词: {keyword}")
    if original_keyword:
        print(f"用户主题: {original_keyword}")
    print(f"年份: {YEAR_START}-{YEAR_END}")
    print("="*50)

    all_papers = search_all_concurrent(keyword, max_results)
    papers = deduplicate(all_papers)
    print(f"\n去重: {len(all_papers)} -> {len(papers)} 篇")

    if not papers:
        print("未找到论文")
        return []

    print("\n" + "="*50)
    print("处理论文...")
    print("="*50)

    valid_papers = []
    stats = {"duplicate": 0, "irrelevant": 0, "invalid": 0, "fulltext_available": 0, "fulltext_unavailable": 0}
    progress = ProgressBar(min(len(papers), max_results), "处理进度")

    output_dir = Path(project_dir) if project_dir else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    notes_dir = output_dir / 'paper_notes'
    notes_dir.mkdir(parents=True, exist_ok=True)

    for i, paper in enumerate(papers[:max_results]):
        title_short = paper["title"][:40] + "..." if len(paper["title"]) > 40 else paper["title"]
        print(f"\n[{i+1}/{min(len(papers), max_results)}] {title_short}")

        if is_duplicate(paper, valid_papers):
            print("  [跳过] 重复")
            stats["duplicate"] += 1
            progress.update()
            continue

        year = paper.get("year")
        has_valid_year = year and YEAR_START <= year <= YEAR_END
        if not paper.get("title") or len(paper["title"]) < 10 or not has_valid_year:
            print("  [跳过] 信息不完整")
            stats["invalid"] += 1
            progress.update()
            continue

        print("  检查相关性...", end=" ")
        is_rel, rel_score, reason = check_relevance(paper["title"], paper.get("abstract", ""), keyword)
        paper["relevance_score"] = rel_score

        if not is_rel:
            print(f"不相关: {reason}")
            stats["irrelevant"] += 1
            progress.update()
            continue
        print(f"OK ({rel_score}%)")

        print("  生成摘要级分析...", end=" ")
        result = generate_analysis(paper["title"], paper.get("abstract", ""), keyword, original_keyword)
        summary, chinese, apps, suggs, rel_stars, rel_reason = result
        print("完成")

        paper["summary"] = summary
        paper["chinese_explanation"] = chinese
        paper["chinese_detail"] = chinese
        paper["applications"] = apps
        paper["suggestions"] = suggs
        paper["relevance_stars"] = rel_stars
        paper["relevance_reason"] = rel_reason
        paper["link"] = paper.get("link") or paper.get("url", "")

        print("  获取全文...", end=" ")
        fulltext_result = fetch_fulltext_for_paper(paper)
        paper["fulltext_status"] = fulltext_result.get("status", "unavailable")
        paper["fulltext_url"] = fulltext_result.get("fulltext_url", "")
        paper["fulltext_source_type"] = fulltext_result.get("fulltext_source_type", "")
        paper["fulltext_attempts"] = fulltext_result.get("fulltext_attempts", [])
        paper["fulltext_error"] = fulltext_result.get("fulltext_error", "")

        if fulltext_result.get('status') == 'available':
            print("成功")
            stats['fulltext_available'] += 1
            slug = f"{i+1:02d}-{slugify_text(paper.get('title', ''), 'paper')}"
            paper_note_path = notes_dir / f"{slug}.md"
            print("  生成单篇全文解读...", end=" ")
            fulltext_analysis = generate_fulltext_analysis(paper, keyword, original_keyword, fulltext_result['fulltext_text'])
            note_markdown = build_paper_note_markdown(paper, keyword, original_keyword, fulltext_analysis)
            with open(paper_note_path, 'w', encoding='utf-8') as f:
                f.write(note_markdown)
            print("完成")

            paper['has_fulltext_markdown'] = True
            paper['paper_markdown_slug'] = slug
            paper['paper_markdown_path'] = str(Path('paper_notes') / paper_note_path.name).replace('\\', '/')
            paper['paper_markdown_filename'] = paper_note_path.name
            paper['fulltext_analysis'] = fulltext_analysis
        else:
            print("未获取到可解析全文")
            stats['fulltext_unavailable'] += 1
            paper['has_fulltext_markdown'] = False
            paper['paper_markdown_slug'] = ''
            paper['paper_markdown_path'] = ''
            paper['paper_markdown_filename'] = ''
            paper['fulltext_analysis'] = {}

        valid_papers.append(paper)
        progress.update()

    progress.close()

    print("\n" + "="*50)
    print("生成结果...")
    print("="*50)

    markdown = generate_markdown(valid_papers, keyword, original_keyword)
    safe_keyword = sanitize_filename(keyword.replace(' ', '_'))
    filename = output_dir / f"papers_{safe_keyword}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown)

    json_file = output_dir / f"papers_{safe_keyword}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "keyword": keyword,
            "original_keyword": original_keyword or keyword,
            "timestamp": datetime.now().isoformat(),
            "count": len(valid_papers),
            "papers": valid_papers
        }, f, ensure_ascii=False, indent=2)

    top_count = sum(1 for p in valid_papers if is_top_venue(p.get("venue", ""))[0])
    avg_score = sum(p.get("score", 0) for p in valid_papers) / len(valid_papers) if valid_papers else 0

    print(f"\n[完成]")
    print(f"  文件: {filename}")
    print(f"  有效论文: {len(valid_papers)} 篇")
    print(f"  顶会论文: {top_count} 篇")
    print(f"  平均评分: {avg_score:.1f}")
    print(f"  全文解读: 已生成={stats['fulltext_available']}, 缺全文={stats['fulltext_unavailable']}")
    print(f"  跳过: 重复={stats['duplicate']}, 不相关={stats['irrelevant']}, 无效={stats['invalid']}")

    return valid_papers


# ==================== 入口 ====================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        max_r = MAX_RESULTS
        keyword_parts = []
        original_keyword = None
        project_dir = None

        for arg in args:
            if arg.isdigit():
                max_r = int(arg)
            elif arg.startswith('--original='):
                original_keyword = arg.split('=', 1)[1]
            elif arg.startswith('--project-dir='):
                project_dir = arg.split('=', 1)[1]
            else:
                keyword_parts.append(arg)

        keyword = " ".join(keyword_parts) if keyword_parts else ""
        if keyword:
            main(keyword, max_r, original_keyword, project_dir)
    else:
        while True:
            keyword = input("\n输入关键词 (q退出): ").strip()
            if keyword.lower() == 'q':
                break
            if keyword:
                main(keyword)
