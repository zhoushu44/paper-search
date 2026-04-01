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
import html
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
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
PAPER_PROCESS_WORKERS = max(1, int(os.environ.get('PAPER_PROCESS_WORKERS', settings.get('paper_process_workers') or 4)))
FULLTEXT_ANALYSIS_WORKERS = max(1, int(os.environ.get('FULLTEXT_ANALYSIS_WORKERS', settings.get('fulltext_analysis_workers') or 2)))

# API状态
api_status = {
    "SerpAPI": {"available": True, "last_error": None},
    "OpenAlex": {"available": True, "last_error": None},
    "CrossRef": {"available": True, "last_error": None},
    "Semantic Scholar": {"available": True, "last_error": None},
}

oa_enrichment_cache = {}
ieee_doi_resolution_cache = {}

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
                "landing_page_url": loc.get("landing_page_url", "") if isinstance(loc, dict) else "",
                "pdf_url": loc.get("pdf_url", "") if isinstance(loc, dict) else "",
                "primary_location": item.get("primary_location") or {},
                "best_oa_location": item.get("best_oa_location") or {},
                "open_access": item.get("open_access") or {},
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
                "doi_url": f"https://doi.org/{item.get('DOI')}" if item.get('DOI') else "",
                "pdf_url": item.get("link", [{}])[0].get("URL", "") if item.get("link") else "",
                "candidate_urls": [entry.get("URL", "") for entry in item.get("link", []) if entry.get("URL")],
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
            "fields": "title,authors,year,venue,abstract,url,citationCount,openAccessPdf"
        }
        r = requests.get(url, params=params, timeout=30)

        if r.status_code == 429:
            api_status["Semantic Scholar"]["available"] = False
            api_status["Semantic Scholar"]["last_error"] = "Rate limited"
            return papers, "Semantic Scholar", "Rate limited"

        data = r.json()

        for item in data.get("data", []):
            open_access_pdf = item.get("openAccessPdf") if isinstance(item.get("openAccessPdf"), dict) else {}
            papers.append({
                "title": item.get("title", ""),
                "authors": ", ".join([a.get("name", "") for a in item.get("authors", [])]),
                "year": item.get("year"),
                "venue": item.get("venue", ""),
                "abstract": item.get("abstract", ""),
                "url": item.get("url", ""),
                "landing_page_url": item.get("url", ""),
                "pdf_url": open_access_pdf.get("url", ""),
                "open_access": {"pdf_url": open_access_pdf.get("url", "")},
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


def sanitize_note_title(text, fallback="paper"):
    safe = re.sub(r'[\\/:*?"<>|\[\]#\^]+', ' ', (text or '').strip())
    safe = re.sub(r'\s+', ' ', safe)
    safe = safe.strip(' .')
    return safe[:150] or fallback


def build_note_file_identity(paper, notes_dir, reserved_titles=None, fallback_index=None):
    reserved_titles = reserved_titles or set()
    existing_filename = str(paper.get('paper_markdown_filename', '') or '').strip()
    existing_slug = str(paper.get('paper_markdown_slug', '') or '').strip()
    existing_title = str(paper.get('paper_markdown_title', '') or '').strip()

    if existing_filename:
        note_title = existing_title or Path(existing_filename).stem
        filename = existing_filename
        slug = existing_slug or note_title
        return note_title, filename, slug

    if existing_slug and (notes_dir / f"{existing_slug}.md").exists():
        note_title = existing_title or existing_slug
        return note_title, f"{existing_slug}.md", existing_slug

    fallback = f"paper-{fallback_index}" if fallback_index is not None else "paper"
    base_title = sanitize_note_title(existing_title or paper.get('title', ''), fallback=fallback)
    note_title = base_title
    suffix = 2
    while note_title in reserved_titles or (notes_dir / f"{note_title}.md").exists():
        note_title = f"{base_title} ({suffix})"
        suffix += 1

    return note_title, f"{note_title}.md", note_title


def assign_note_identity(paper, notes_dir, reserved_titles=None, fallback_index=None):
    note_title, filename, slug = build_note_file_identity(
        paper,
        notes_dir,
        reserved_titles=reserved_titles,
        fallback_index=fallback_index
    )
    paper['paper_markdown_title'] = note_title
    paper['paper_markdown_filename'] = filename
    paper['paper_markdown_slug'] = slug
    paper['paper_markdown_path'] = str(Path('paper_notes') / filename).replace('\\', '/')
    if reserved_titles is not None:
        reserved_titles.add(note_title)
    return notes_dir / filename


def migrate_existing_note(paper, notes_dir, reserved_titles=None, fallback_index=None):
    reserved_titles = reserved_titles or set()
    fallback = f"paper-{fallback_index}" if fallback_index is not None else "paper"
    desired_title = sanitize_note_title(paper.get('title') or paper.get('paper_markdown_title'), fallback)
    current_filename = str(paper.get('paper_markdown_filename', '') or '').strip()
    current_slug = str(paper.get('paper_markdown_slug', '') or '').strip()
    current_path = notes_dir / current_filename if current_filename else None
    if (not current_path or not current_path.exists()) and current_slug:
        slug_path = notes_dir / f"{current_slug}.md"
        if slug_path.exists():
            current_path = slug_path
    if not current_path or not current_path.exists():
        return None

    target_title = desired_title
    target_path = notes_dir / f"{target_title}.md"
    suffix = 2
    while target_title in reserved_titles or (target_path.exists() and target_path != current_path):
        target_title = f"{desired_title} ({suffix})"
        target_path = notes_dir / f"{target_title}.md"
        suffix += 1

    if current_path != target_path:
        current_path.rename(target_path)

    try:
        content = target_path.read_text(encoding='utf-8')
        if content.startswith('# '):
            content = re.sub(r'^#\s+.*$', f'# {target_title}', content, count=1)
        else:
            content = f"# {target_title}\n\n{content}"
        target_path.write_text(content, encoding='utf-8')
    except Exception:
        pass

    paper['has_fulltext_markdown'] = True
    paper['paper_markdown_title'] = target_title
    paper['paper_markdown_filename'] = target_path.name
    paper['paper_markdown_slug'] = target_title
    paper['paper_markdown_path'] = str(Path('paper_notes') / target_path.name).replace('\\', '/')
    if reserved_titles is not None:
        reserved_titles.add(target_title)
    return target_path


def process_paper_content(paper, keyword, original_keyword):
    relevance_future = None
    fulltext_future = None

    with ThreadPoolExecutor(max_workers=2) as executor:
        relevance_future = executor.submit(check_relevance, paper["title"], paper.get("abstract", ""), keyword)
        fulltext_future = executor.submit(fetch_fulltext_for_paper, paper)

        is_rel, rel_score, reason = relevance_future.result()
        fulltext_result = fulltext_future.result()

    if not is_rel:
        return {
            'status': 'irrelevant',
            'relevance_score': rel_score,
            'relevance_reason_raw': reason,
            'fulltext_result': fulltext_result
        }

    result = generate_analysis(paper["title"], paper.get("abstract", ""), keyword, original_keyword)
    summary, chinese, apps, suggs, rel_stars, rel_reason = result

    processed_paper = dict(paper)
    processed_paper["relevance_score"] = rel_score
    processed_paper["summary"] = summary
    processed_paper["chinese_explanation"] = chinese
    processed_paper["chinese_detail"] = chinese
    processed_paper["applications"] = apps
    processed_paper["suggestions"] = suggs
    processed_paper["relevance_stars"] = rel_stars
    processed_paper["relevance_reason"] = rel_reason
    processed_paper["link"] = processed_paper.get("link") or processed_paper.get("url", "")
    processed_paper["fulltext_status"] = fulltext_result.get("status", "unavailable")
    processed_paper["fulltext_url"] = fulltext_result.get("fulltext_url", "")
    processed_paper["fulltext_source_type"] = fulltext_result.get("fulltext_source_type", "")
    processed_paper["fulltext_attempts"] = fulltext_result.get("fulltext_attempts", [])
    processed_paper["fulltext_error"] = fulltext_result.get("fulltext_error", "")
    processed_paper["fulltext_failure_reason"] = fulltext_result.get("fulltext_failure_reason", "")
    processed_paper["fulltext_failure_details"] = fulltext_result.get("fulltext_failure_details", [])

    return {
        'status': 'ok',
        'paper': processed_paper,
        'relevance_score': rel_score,
        'fulltext_result': fulltext_result
    }


def process_paper_task(index, paper, keyword, original_keyword):
    title = paper.get("title", "")
    year = paper.get("year")
    has_valid_year = year and YEAR_START <= year <= YEAR_END

    if not title or len(title) < 10 or not has_valid_year:
        return {
            'index': index,
            'status': 'invalid',
            'paper': paper,
            'message': '信息不完整'
        }

    processed = process_paper_content(paper, keyword, original_keyword)
    paper_with_score = dict(paper)
    paper_with_score["relevance_score"] = processed.get("relevance_score", 0)

    if processed.get('status') == 'irrelevant':
        return {
            'index': index,
            'status': 'irrelevant',
            'paper': paper_with_score,
            'message': processed.get('relevance_reason_raw', '')
        }

    processed_paper = processed['paper']
    fulltext_result = processed.get('fulltext_result', {})
    if processed_paper.get('fulltext_status') == 'available':
        return {
            'index': index,
            'status': 'ok',
            'paper': processed_paper,
            'fulltext_text': fulltext_result.get('fulltext_text', '')
        }

    processed_paper['has_fulltext_markdown'] = False
    processed_paper['paper_markdown_title'] = ''
    processed_paper['paper_markdown_slug'] = ''
    processed_paper['paper_markdown_path'] = ''
    processed_paper['paper_markdown_filename'] = ''
    processed_paper['fulltext_analysis'] = {}
    return {
        'index': index,
        'status': 'ok',
        'paper': processed_paper,
        'fulltext_text': ''
    }


def strip_html_tags(text):
    text = re.sub(r'<script[\s\S]*?</script>', ' ', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ')
    return html.unescape(text)


def clean_fulltext(text):
    text = strip_html_tags(text or '')
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\x00', ' ')
    return text.strip()


def extract_pdf_text_result(content_bytes):
    if not PdfReader:
        return {'text': '', 'status': 'non_text_pdf', 'page_count': 0, 'non_empty_pages': 0}
    try:
        import io
        reader = PdfReader(io.BytesIO(content_bytes))
        page_count = len(reader.pages)
        texts = []
        non_empty_pages = 0

        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            page_text = clean_fulltext(page_text)
            if page_text:
                non_empty_pages += 1
                texts.append(page_text)

        text = clean_fulltext("\n".join(texts))
        if len(text) >= MIN_FULLTEXT_CHARS:
            status = 'ok'
        elif len(text) < 200 or non_empty_pages == 0:
            status = 'non_text_pdf'
        else:
            status = 'too_short_pdf'

        return {
            'text': text,
            'status': status,
            'page_count': page_count,
            'non_empty_pages': non_empty_pages
        }
    except Exception as e:
        return {'text': '', 'status': 'non_text_pdf', 'page_count': 0, 'non_empty_pages': 0, 'error': str(e)}


def extract_pdf_text(content_bytes):
    return extract_pdf_text_result(content_bytes).get('text', '')


def safe_extract_urls(value):
    urls = []
    if not value:
        return urls
    if isinstance(value, str):
        normalized = normalize_candidate_url(value)
        return [normalized] if normalized else []
    if isinstance(value, dict):
        for key in [
            'url', 'landing_page_url', 'pdf_url', 'doi_url', 'oa_url', 'pdf', 'href',
            'pdf_uri', 'pdfLink', 'full_text_url', 'fulltext_url', 'download_url', 'canonical_url',
            'accepted_oa_url', 'accepted_oa_pdf_url', 'best_oa_url', 'pdf_download_url'
        ]:
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                normalized = normalize_candidate_url(nested)
                if normalized:
                    urls.append(normalized)
            elif isinstance(nested, (dict, list)):
                urls.extend(safe_extract_urls(nested))
        for key in [
            'primary_location', 'best_oa_location', 'open_access', 'locations', 'location', 'oa_locations'
        ]:
            nested = value.get(key)
            if isinstance(nested, (dict, list)):
                urls.extend(safe_extract_urls(nested))
        return urls
    if isinstance(value, list):
        for item in value:
            urls.extend(safe_extract_urls(item))
    return urls


def extract_doi_from_value(value):
    if not value:
        return ''
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ''
        doi_match = re.search(r'(?i)10\.\d{4,9}/[-._;()/:A-Z0-9]+', text)
        return doi_match.group(0).rstrip(').,;]') if doi_match else ''
    if isinstance(value, dict):
        for key in ['doi', 'DOI', 'externalIds', 'external_ids', 'ids', 'identifiers']:
            nested = value.get(key)
            doi = extract_doi_from_value(nested)
            if doi:
                return doi
        return ''
    if isinstance(value, list):
        for item in value:
            doi = extract_doi_from_value(item)
            if doi:
                return doi
    return ''


def extract_paper_doi(paper):
    if not isinstance(paper, dict):
        return ''
    for key in [
        'doi', 'DOI', 'doi_url', 'url', 'link', 'id', 'externalIds', 'external_ids',
        'ids', 'identifiers', 'open_access', 'primary_location', 'best_oa_location'
    ]:
        doi = extract_doi_from_value(paper.get(key))
        if doi:
            return doi
    return ''


def fetch_openalex_oa_urls(doi='', title='', year=None):
    normalized_doi = extract_doi_from_value(doi)
    cache_key = (normalized_doi or normalize_title(title or '')).lower()
    if not cache_key:
        return []
    cached = oa_enrichment_cache.get(cache_key)
    if cached is not None:
        return list(cached)

    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json'
    }

    data = {}
    try:
        if normalized_doi:
            response = requests.get(
                f'https://api.openalex.org/works/https://doi.org/{normalized_doi}',
                headers=headers,
                timeout=20
            )
            response.raise_for_status()
            data = response.json() if response.content else {}
        elif title:
            response = requests.get(
                'https://api.openalex.org/works',
                headers=headers,
                params={'search': title, 'per_page': 5, 'mailto': 'research@example.com'},
                timeout=20
            )
            response.raise_for_status()
            results = response.json().get('results', []) if response.content else []
            target_title = title or ''
            target_year = int(year) if str(year or '').isdigit() else None
            best_item = None
            best_score = 0
            for item in results:
                item_title = item.get('title', '')
                similarity = calc_similarity(target_title, item_title)
                item_year = item.get('publication_year')
                year_penalty = 0 if not target_year or not item_year or abs(int(item_year) - target_year) <= 1 else 0.15
                score = similarity - year_penalty
                if score > best_score:
                    best_item = item
                    best_score = score
            if best_item and best_score >= 0.72:
                data = best_item
    except Exception:
        oa_enrichment_cache[cache_key] = []
        return []

    candidates = []
    for field in [
        data.get('primary_location'),
        data.get('best_oa_location'),
        data.get('open_access'),
        data.get('locations'),
        data.get('oa_locations')
    ]:
        for raw_url in safe_extract_urls(field):
            normalized = normalize_candidate_url(raw_url)
            if normalized and normalized not in candidates:
                candidates.append(normalized)

    oa_enrichment_cache[cache_key] = list(candidates)
    return candidates


def is_openalex_work_url(url):
    normalized = str(url or '').strip()
    if not normalized:
        return False
    parsed = urlparse(normalized)
    host_lower = parsed.netloc.lower()
    path = parsed.path or ''
    return host_lower.endswith('openalex.org') and bool(re.fullmatch(r'/W\d+', path, flags=re.I))


def normalize_candidate_url(url):
    if not url:
        return ""
    url = html.unescape(str(url).strip())
    if not url or url.startswith('https://api.openalex.org/'):
        return ""
    if url.startswith('//'):
        url = f'https:{url}'
    if 'arxiv.org/abs/' in url:
        url = url.replace('/abs/', '/pdf/') + '.pdf'
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return ""

    host_lower = parsed.netloc.lower()
    path = parsed.path or '/'
    if host_lower.startswith('www.'):
        host_lower = host_lower[4:]

    normalized = urlunparse((parsed.scheme, host_lower, path, parsed.params, parsed.query, ''))
    if is_openalex_work_url(normalized):
        return ""
    if host_lower == 'doi.org' and re.search(r'(?i)\.(?:pdf|epub)$', path):
        return ""
    return normalized


def resolve_ieee_document_url(url):
    normalized = normalize_candidate_url(url)
    if not normalized:
        return ''

    cached = ieee_doi_resolution_cache.get(normalized)
    if cached is not None:
        return cached

    parsed = urlparse(normalized)
    host_lower = parsed.netloc.lower()
    path_lower = parsed.path.lower()
    resolved = ''

    if 'doi.org' in host_lower and '/10.1109/' in path_lower:
        try:
            response = requests.get(
                normalized,
                headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,application/pdf;q=0.9,*/*;q=0.8'},
                timeout=20,
                allow_redirects=True
            )
            final_url = normalize_candidate_url(response.url)
            if final_url and 'ieeexplore.ieee.org' in urlparse(final_url).netloc.lower():
                resolved = final_url
        except Exception:
            resolved = ''

    ieee_doi_resolution_cache[normalized] = resolved
    return resolved


def extract_ieee_arnumber(url):
    normalized = str(url or '').strip()
    if not normalized:
        return ''

    parsed = urlparse(normalized)
    host_lower = parsed.netloc.lower()
    path = parsed.path or ''

    if 'ieeexplore.ieee.org' in host_lower:
        match = re.search(r'(?i)/(?:document|abstract/document)/(\d+)', path)
        return match.group(1) if match else ''

    if 'doi.org' in host_lower and '/10.1109/' in path.lower():
        resolved_url = resolve_ieee_document_url(normalized)
        if resolved_url:
            return extract_ieee_arnumber(resolved_url)
    return ''


def looks_like_semanticscholar_challenge(html_text, final_url=''):
    html_text = html_text or ''
    if 'semanticscholar.org' not in str(final_url or '').lower():
        return False
    lower_html = html_text.lower()
    return all(token in lower_html for token in [
        'awswafintegration',
        'challenge.js',
        'gokuprops',
        'pdfs.semanticscholar.org'
    ])


def derive_candidate_variants(url):
    normalized = normalize_candidate_url(url)
    if not normalized:
        return []

    variants = [normalized]
    parsed = urlparse(normalized)
    base_without_query = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, '', ''))
    path_lower = parsed.path.lower()
    host_lower = parsed.netloc.lower()
    path_name = Path(parsed.path).name.lower()
    is_doi_url = host_lower == 'doi.org'
    ieee_arnumber = extract_ieee_arnumber(normalized)
    allow_pdf_derivation = (
        path_lower.endswith('/abstract')
        or '/article/' in path_lower
        or '/content/' in path_lower
        or '/full/' in path_lower
        or any(token in path_name for token in ['article', 'paper', 'fulltext', 'full', 'download'])
    )
    allow_suffix_derivation = not is_doi_url and (
        allow_pdf_derivation
        or '/doi/' in path_lower
    )

    if parsed.query and base_without_query not in variants:
        variants.append(base_without_query)

    if ieee_arnumber:
        for candidate in [
            f'https://ieeexplore.ieee.org/document/{ieee_arnumber}/',
            f'https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={ieee_arnumber}'
        ]:
            normalized_candidate = normalize_candidate_url(candidate)
            if normalized_candidate and normalized_candidate not in variants:
                variants.append(normalized_candidate)

    if allow_suffix_derivation:
        for suffix in ['/pdf', '/full']:
            candidate = normalize_candidate_url(base_without_query.rstrip('/') + suffix)
            if candidate and candidate not in variants:
                variants.append(candidate)
        if path_lower.endswith('/abstract'):
            for replaced in [re.sub(r'/abstract$', '/pdf', base_without_query, flags=re.I), re.sub(r'/abstract$', '/full', base_without_query, flags=re.I)]:
                candidate = normalize_candidate_url(replaced)
                if candidate and candidate not in variants:
                    variants.append(candidate)
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        if ('download', '1') not in query_pairs:
            query_pairs.append(('download', '1'))
            candidate = normalize_candidate_url(urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(query_pairs), '')))
            if candidate and candidate not in variants:
                variants.append(candidate)

    if allow_pdf_derivation and not path_lower.endswith('.pdf') and not path_lower.endswith('/') and '.' not in Path(parsed.path).name:
        pdf_candidate = normalize_candidate_url(base_without_query + '.pdf')
        if pdf_candidate and pdf_candidate not in variants:
            variants.append(pdf_candidate)

    return variants


def collect_fulltext_metadata_urls(paper):
    urls = []
    extra_fields = [
        paper.get('pdf'),
        paper.get('primary_location'),
        paper.get('best_oa_location'),
        paper.get('open_access'),
        paper.get('locations'),
        paper.get('location'),
        paper.get('oa_locations')
    ]
    for field in extra_fields:
        urls.extend(safe_extract_urls(field))

    if str(paper.get('source', '')).lower() in {'semantic scholar', 'openalex'}:
        doi = extract_paper_doi(paper)
        urls.extend(fetch_openalex_oa_urls(doi=doi, title=paper.get('title', ''), year=paper.get('year')))

    normalized_urls = []
    for value in urls:
        normalized = normalize_candidate_url(value)
        if normalized and normalized not in normalized_urls:
            normalized_urls.append(normalized)
    return normalized_urls


def build_fulltext_candidate_urls(paper):
    candidates = []
    source_lower = str(paper.get('source', '')).lower()

    def add_candidate(value):
        for variant in derive_candidate_variants(value):
            if variant and variant not in candidates:
                candidates.append(variant)

    metadata_urls = collect_fulltext_metadata_urls(paper)
    for value in metadata_urls:
        add_candidate(value)

    direct_keys = ['pdf_url', 'link', 'landing_page_url', 'url', 'doi_url']
    if source_lower == 'semantic scholar':
        direct_keys = ['pdf_url', 'doi_url', 'link', 'landing_page_url', 'url']

    for key in direct_keys:
        add_candidate(paper.get(key, ''))

    for value in paper.get('candidate_urls', []) or []:
        add_candidate(value)

    return candidates


def extract_html_main_content(html_text):
    if not html_text:
        return ''

    cleaned_html = re.sub(r'(?is)<(script|style|noscript|svg|canvas|iframe|header|footer|nav|aside|form)[^>]*>.*?</\1>', ' ', html_text)
    snippets = []

    structural_patterns = [
        r'(?is)<article[^>]*>(.*?)</article>',
        r'(?is)<main[^>]*>(.*?)</main>',
        r'(?is)<section[^>]+(?:article|content|main|fulltext|body)[^>]*>(.*?)</section>',
        r'(?is)<div[^>]+(?:article|content|main|fulltext|body)[^>]*>(.*?)</div>'
    ]
    for pattern in structural_patterns:
        for match in re.findall(pattern, cleaned_html):
            text = clean_fulltext(match)
            if len(text) >= 600:
                snippets.append(text)

    if snippets:
        snippets.sort(key=len, reverse=True)
        return clean_fulltext("\n".join(snippets[:3]))

    body_match = re.search(r'(?is)<body[^>]*>(.*?)</body>', cleaned_html)
    return clean_fulltext(body_match.group(1) if body_match else cleaned_html)


def extract_host_aware_second_hop_candidates(html_text, base_url):
    decoded_html = html.unescape(html_text or '').replace('\\/', '/')
    parsed_base = urlparse(base_url or '')
    host_lower = parsed_base.netloc.lower()
    candidates = []

    def add_candidate(raw_url):
        absolute = normalize_candidate_url(urljoin(base_url, raw_url))
        if absolute and absolute not in candidates:
            candidates.append(absolute)

    if 'ieeexplore.ieee.org' in host_lower:
        for pattern in [
            r'(?i)(/iel\d+/[^"\'\s<>]+\.pdf(?:[?#][^"\'\s<>]*)?)',
            r'(?i)(/stamp/stamp\.jsp\?[^"\'\s<>]+)',
            r'(?i)(?:"|\')(?:pdfPath|pdfUrl|xplore-pdf-url|documentLink|ephemeraLink)(?:"|\')\s*[:=]\s*(?:"|\')([^"\']+)(?:"|\')'
        ]:
            for match in re.findall(pattern, decoded_html):
                add_candidate(match)
        arnumber = extract_ieee_arnumber(base_url)
        if not arnumber:
            arnumber_match = re.search(r'(?i)(?:arnumber|articleNumber)(?:"|\')?\s*[:=]\s*(?:"|\')?(\d+)', decoded_html)
            arnumber = arnumber_match.group(1) if arnumber_match else ''
        if arnumber:
            add_candidate(f'/stamp/stamp.jsp?tp=&arnumber={arnumber}')
            add_candidate(f'/document/{arnumber}/')

    if any(token in host_lower for token in ['semanticscholar.org', 'api.semanticscholar.org']):
        for pattern in [
            r'(?i)(https?://pdfs\.semanticscholar\.org/[^"\'\s<>]+)',
            r'(?i)(?:"|\')(?:openAccessPdf|pdfUrl|pdfPath)(?:"|\')\s*[:=]\s*(?:"|\')([^"\']+)(?:"|\')',
            r'(?i)(?:"|\')url(?:"|\')\s*:\s*(?:"|\')(https?://pdfs\.semanticscholar\.org/[^"\']+)(?:"|\')',
            r'(?i)https?:\\/\\/pdfs\.semanticscholar\.org\\/[^"\'\s<>]+'
        ]:
            matches = re.findall(pattern, decoded_html)
            for match in matches:
                if isinstance(match, tuple):
                    for item in match:
                        if item:
                            add_candidate(item.replace('\\/', '/'))
                elif match:
                    add_candidate(str(match).replace('\\/', '/'))

    if any(token in host_lower for token in ['dspace', 'dr.lib.iastate.edu']):
        meta_match = re.search(r'(?is)<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']', decoded_html)
        if meta_match:
            add_candidate(meta_match.group(1))
        for match in re.findall(r'(?i)(/bitstreams?/[^"\'\s<>]+/download(?:[?#][^"\'\s<>]*)?)', decoded_html):
            add_candidate(match)

    return candidates[:5]


def extract_second_hop_candidates(html_text, base_url):
    if not html_text or not base_url:
        return []

    keyword_pattern = re.compile(r'(?i)(download|pdf|full\s*text|fulltext|view\s*pdf|read\s*full|article\s*pdf)')
    href_pattern = re.compile(r'(?i)(\.pdf(?:$|[?#])|/pdf(?:$|[/?#])|download|fulltext|viewarticle|article/download|epdf|pdfviewer|stamp/stamp\.jsp|/bitstreams?/|pdfs\.semanticscholar\.org/)')
    blocked_pattern = re.compile(r'(?i)(/search[/?]|[?&](?:query|q|search|option1)=|/search-results|/advanced-search|/lookup)')
    blocked_extension_pattern = re.compile(r'(?i)(\.(?:css|js|png|jpe?g|gif|svg|ico|woff2?|ttf|eot|json|xml|txt)(?:$|[?#])|/cover\.(?:jpg|jpeg|png)(?:$|[?#]))')
    candidates = []

    def add_candidate(raw_url):
        absolute = normalize_candidate_url(urljoin(base_url, raw_url))
        if not absolute:
            return
        parsed_absolute = urlparse(absolute)
        path_lower = parsed_absolute.path.lower()
        if blocked_pattern.search(absolute) or blocked_extension_pattern.search(absolute):
            return
        if path_lower.startswith(('/css/', '/common/', '/static/', '/assets/')):
            return
        if path_lower.endswith('/full') and not any(token in path_lower for token in ['/fulltext', '/article/full', '/content/pdf']):
            return
        if absolute not in candidates:
            candidates.append(absolute)

    for href in extract_host_aware_second_hop_candidates(html_text, base_url):
        add_candidate(href)

    decoded_html = html.unescape(html_text).replace('\\/', '/')
    meta_refresh_match = re.search(r'(?is)<meta[^>]+http-equiv\s*=\s*["\']?refresh["\']?[^>]+content\s*=\s*["\']([^"\']+)["\']', decoded_html)
    if meta_refresh_match:
        refresh_content = html.unescape(meta_refresh_match.group(1))
        refresh_url_match = re.search(r'(?i)url\s*=\s*[\'\"]?([^\'\";]+)', refresh_content)
        if refresh_url_match:
            add_candidate(refresh_url_match.group(1))
    redirect_input_match = re.search(r'(?is)name=["\']redirectURL["\']\s+value=["\']([^"\']+)["\']', decoded_html)
    key_input_match = re.search(r'(?is)name=["\']key["\']\s+value=["\']([^"\']+)["\']', decoded_html)
    result_input_match = re.search(r'(?is)name=["\']resultName["\']\s+value=["\']([^"\']+)["\']', decoded_html)
    if redirect_input_match and key_input_match and result_input_match:
        redirect_value = html.unescape(redirect_input_match.group(1))
        key_value = html.unescape(key_input_match.group(1))
        result_value = html.unescape(result_input_match.group(1))
        add_candidate(f'/retrieve/{result_value}?Redirect={redirect_value}&key={key_value}')

    link_matches = re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', decoded_html)
    link_tag_matches = re.findall(r'(?is)<link[^>]+href=["\']([^"\']+)["\'][^>]*>', decoded_html)
    attr_matches = re.findall(r'(?is)(?:data-pdf-url|data-download-url|data-fulltext-url|citation_pdf_url|pdfurl|pdfpath)=["\']([^"\']+)["\']', decoded_html)
    meta_matches = []
    for meta_tag in re.findall(r'(?is)<meta[^>]+>', decoded_html):
        name_match = re.search(r'(?is)(?:name|property)=["\']([^"\']+)["\']', meta_tag)
        content_match = re.search(r'(?is)content=["\']([^"\']+)["\']', meta_tag)
        if not name_match or not content_match:
            continue
        meta_name = name_match.group(1).lower()
        if meta_name in {
            'citation_pdf_url', 'citation_fulltext_html_url', 'citation_abstract_html_url',
            'eprints.document_url', 'wkhealth_pdf_url', 'dc.identifier.pdf', 'prism.url'
        }:
            meta_matches.append(content_match.group(1))
    script_matches = re.findall(r'(?is)(?:(?:"|\')(?:pdfPath|pdfUrl|citation_pdf_url|downloadUrl|fullTextUrl|fileUrl|exportPdfDownloadUrl)(?:"|\')\s*[:=]\s*(?:"|\')([^"\']+)(?:"|\'))', decoded_html)
    absolute_url_matches = re.findall(r'(?i)(https?://[^"\'\s<>]+(?:\.pdf(?:[?#][^"\'\s<>]*)?|/download(?:[?#][^"\'\s<>]*)?|/pdf(?:[/?#][^"\'\s<>]*)?|/epdf(?:[/?#][^"\'\s<>]*)?|/fulltext(?:[/?#][^"\'\s<>]*)?|/article/download[^"\'\s<>]*|/bitstreams?/[^"\'\s<>]+|pdfs\.semanticscholar\.org/[^"\'\s<>]+))', decoded_html)
    generic_matches = re.findall(r'(?i)(/[^"\'\s<>]+(?:\.pdf(?:[?#][^"\'\s<>]*)?|/download(?:[?#][^"\'\s<>]*)?|/pdf(?:[/?#][^"\'\s<>]*)?|/epdf(?:[/?#][^"\'\s<>]*)?|/fulltext(?:[/?#][^"\'\s<>]*)?|/article/download[^"\'\s<>]*|/bitstreams?/[^"\'\s<>]+))', decoded_html)

    for href, anchor_html in link_matches:
        anchor_text = clean_fulltext(anchor_html)[:200]
        if not href_pattern.search(href) and not keyword_pattern.search(anchor_text):
            continue
        add_candidate(href)

    for href in link_tag_matches:
        if href_pattern.search(href):
            add_candidate(href)

    for href in attr_matches:
        add_candidate(href)

    for href in meta_matches:
        add_candidate(href)

    for href in script_matches:
        add_candidate(href)

    for href in absolute_url_matches:
        add_candidate(href)

    for href in generic_matches:
        add_candidate(href)

    return candidates[:5]


def looks_like_landing_page(text, html_text=''):
    text = clean_fulltext(text)
    if not text:
        return True

    lower_text = text.lower()
    landing_hits = sum(lower_text.count(token) for token in [
        'abstract', 'doi', 'references', 'supplementary', 'download pdf', 'view pdf',
        'access through your institution', 'purchase pdf', 'rights and permissions', 'cookie'
    ])
    body_hits = sum(lower_text.count(token) for token in [
        'introduction', 'method', 'methods', 'experiment', 'results', 'discussion', 'conclusion'
    ])
    has_pdf_link = bool(re.search(r'(?i)href=["\'][^"\']+\.pdf', html_text or ''))

    if len(text) < MIN_FULLTEXT_CHARS and body_hits < 2 and (landing_hits >= 2 or has_pdf_link):
        return True
    return False


def classify_network_error(exc):
    if isinstance(exc, requests.HTTPError) and getattr(exc, 'response', None) is not None:
        response = exc.response
        status_code = response.status_code
        lower_url = str(getattr(response, 'url', '') or '').lower()
        content_type = str(response.headers.get('Content-Type', '') or '').lower()
        html_text = response.text if 'text/html' in content_type else ''
        lower_html = html_text.lower()

        if status_code in (403, 429):
            if 'semanticscholar.org' in lower_url and looks_like_semanticscholar_challenge(html_text, response.url):
                return 'access_barrier: semanticscholar_waf'
            if 'just a moment' in lower_html or 'cf-browser-verification' in lower_html or 'cloudflare' in lower_html:
                return 'access_barrier: cloudflare_challenge'
            if 'captcha' in lower_html or 'verify you are human' in lower_html:
                return 'access_barrier: anti_bot_challenge'

        return f'network_error: http_{status_code}'
    return f'network_error: {exc.__class__.__name__}'


def classify_html_access_barrier(final_url, html_text):
    final_url = str(final_url or '')
    html_text = html_text or ''
    lower_url = final_url.lower()
    lower_html = html_text.lower()

    if 'semanticscholar.org' in lower_url and looks_like_semanticscholar_challenge(html_text, final_url):
        return 'access_barrier: semanticscholar_waf'

    if any(token in lower_url for token in ['sciencedirect.com', 'linkinghub.elsevier.com']):
        if 'captcha' in lower_html or ('robot' in lower_html and 'challenge' in lower_html):
            return 'access_barrier: anti_bot_challenge'

    if 'ieeexplore.ieee.org' in lower_url:
        if 'request rejected' in lower_html and 'support id' in lower_html:
            return 'access_barrier: ieee_request_rejected'
        if 'captcha' in lower_html or ('bot' in lower_html and 'challenge' in lower_html):
            return 'access_barrier: anti_bot_challenge'
        if 'access through your institution' in lower_html or 'purchase pdf' in lower_html or 'institutional sign in' in lower_html:
            return 'access_barrier: ieee_paywall'
        if 'stamp/stamp.jsp' in lower_url and ('temporarily unavailable' in lower_html or 'document is not accessible' in lower_html or 'access denied' in lower_html):
            return 'access_barrier: ieee_stamp_blocked'

    return ''


def looks_like_js_app_shell(html_text):
    lower_html = str(html_text or '').lower()
    return (
        '<ds-app' in lower_html
        and re.search(r'(?i)<script[^>]+src=["\"][^"\"]*runtime(?:[-._][^"\"])?.*\.js', lower_html)
        and re.search(r'(?i)<script[^>]+src=["\"][^"\"]*main(?:[-._][^"\"])?.*\.js', lower_html)
    )



def fetch_url_text(url, visited_urls=None, hop_depth=0):
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/pdf;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8'
    }
    visited_urls = set(visited_urls or [])
    normalized_request_url = normalize_candidate_url(url) or str(url or '').strip()
    if normalized_request_url:
        visited_urls.add(normalized_request_url)
    try:
        response = requests.get(url, headers=headers, timeout=40, allow_redirects=True)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        final_url = response.url
        if 'text/html' in content_type and looks_like_js_app_shell(response.text):
            retry_headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': headers['Accept']
            }
            retry_response = requests.get(final_url, headers=retry_headers, timeout=40, allow_redirects=True)
            retry_response.raise_for_status()
            retry_content_type = retry_response.headers.get('Content-Type', '').lower()
            if 'text/html' in retry_content_type and len(retry_response.text) > len(response.text):
                response = retry_response
                content_type = retry_content_type
                final_url = response.url
        normalized_final_url = normalize_candidate_url(final_url) or final_url
        if normalized_final_url:
            visited_urls.add(normalized_final_url)
        is_pdf = 'pdf' in content_type or final_url.lower().endswith('.pdf') or response.content[:4] == b'%PDF'

        if is_pdf:
            pdf_result = extract_pdf_text_result(response.content)
            return {
                'status': pdf_result.get('status', 'non_text_pdf'),
                'text': pdf_result.get('text', ''),
                'source_url': final_url,
                'content_type': 'pdf',
                'details': {
                    'page_count': pdf_result.get('page_count', 0),
                    'non_empty_pages': pdf_result.get('non_empty_pages', 0),
                    'text_length': len(pdf_result.get('text', '')),
                    'error': pdf_result.get('error', ''),
                    'hop_depth': hop_depth,
                    'second_hop_candidates': []
                }
            }

        extracted_text = extract_html_main_content(response.text)
        status = 'ok' if len(extracted_text) >= MIN_FULLTEXT_CHARS else 'too_short_html'
        barrier_reason = classify_html_access_barrier(final_url, response.text)
        if barrier_reason:
            status = barrier_reason
        elif status != 'ok' and looks_like_landing_page(extracted_text, response.text):
            status = 'landing_page_only'

        second_hop_candidates = []
        if status in ('landing_page_only', 'too_short_html') and hop_depth == 0:
            for candidate in extract_second_hop_candidates(response.text, final_url):
                normalized_candidate = normalize_candidate_url(candidate)
                if not normalized_candidate or normalized_candidate in visited_urls:
                    continue
                second_hop_candidates.append(normalized_candidate)
                child_result = fetch_url_text(normalized_candidate, visited_urls=visited_urls | {normalized_candidate}, hop_depth=hop_depth + 1)
                child_trace = list(child_result.get('details', {}).get('retry_trace', []))
                child_trace.insert(0, {
                    'candidate_url': normalized_candidate,
                    'final_url': child_result.get('source_url', normalized_candidate),
                    'reason': child_result.get('status', 'network_error'),
                    'content_type': child_result.get('content_type', ''),
                    'error': child_result.get('error', ''),
                    'details': {
                        key: value for key, value in child_result.get('details', {}).items() if key != 'retry_trace'
                    }
                })
                if child_result.get('status') == 'ok':
                    child_details = dict(child_result.get('details', {}))
                    child_details['retry_trace'] = child_trace
                    child_details['second_hop_candidates'] = second_hop_candidates
                    child_details['hop_depth'] = hop_depth + 1
                    child_result['details'] = child_details
                    return child_result
                if len(second_hop_candidates) >= 5:
                    break

        return {
            'status': status,
            'text': extracted_text,
            'source_url': final_url,
            'content_type': 'html',
            'details': {
                'text_length': len(extracted_text),
                'content_type_header': content_type,
                'second_hop_candidates': second_hop_candidates,
                'hop_depth': hop_depth
            }
        }
    except Exception as e:
        error_reason = classify_network_error(e)
        status = error_reason if str(error_reason).startswith('access_barrier:') else 'network_error'
        return {
            'status': status,
            'error': error_reason,
            'source_url': url,
            'content_type': '',
            'details': {'error': str(e), 'hop_depth': hop_depth, 'second_hop_candidates': []}
        }


def summarize_failure_reason(details):
    if not details:
        return 'no_candidates'
    priority = [
        'access_barrier: semanticscholar_waf',
        'access_barrier: ieee_request_rejected',
        'access_barrier: ieee_paywall',
        'access_barrier: ieee_stamp_blocked',
        'access_barrier: cloudflare_challenge',
        'access_barrier: anti_bot_challenge',
        'landing_page_only',
        'non_text_pdf',
        'too_short_pdf',
        'too_short_html',
        'network_error'
    ]
    reasons = [item.get('reason') for item in details if item.get('reason')]
    for reason in priority:
        if reason in reasons:
            return reason
    return reasons[0] if reasons else 'network_error'


def fetch_fulltext_for_paper(paper):
    candidates = build_fulltext_candidate_urls(paper)
    if not candidates:
        return {
            'status': 'unavailable',
            'fulltext_text': '',
            'fulltext_url': '',
            'fulltext_source_type': '',
            'fulltext_attempts': [],
            'fulltext_error': 'no_candidates',
            'fulltext_failure_reason': 'no_candidates',
            'fulltext_failure_details': []
        }

    failure_details = []
    for candidate in candidates:
        result = fetch_url_text(candidate)
        retry_trace = result.get('details', {}).get('retry_trace', [])
        if result['status'] == 'ok':
            return {
                'status': 'available',
                'fulltext_text': result['text'],
                'fulltext_url': result.get('source_url', candidate),
                'fulltext_source_type': result.get('content_type', ''),
                'fulltext_attempts': candidates,
                'fulltext_failure_reason': '',
                'fulltext_failure_details': failure_details
            }

        failure_details.append({
            'candidate_url': candidate,
            'final_url': result.get('source_url', candidate),
            'reason': result.get('status', 'network_error'),
            'content_type': result.get('content_type', ''),
            'error': result.get('error', ''),
            'details': result.get('details', {})
        })
        for retry_item in retry_trace:
            failure_details.append(retry_item)

    failure_reason = summarize_failure_reason(failure_details)
    error_summary = '; '.join([
        f"{item['candidate_url']} => {item['reason']}" for item in failure_details[:5]
    ])
    return {
        'status': 'unavailable',
        'fulltext_text': '',
        'fulltext_url': '',
        'fulltext_source_type': '',
        'fulltext_attempts': candidates,
        'fulltext_error': error_summary,
        'fulltext_failure_reason': failure_reason,
        'fulltext_failure_details': failure_details[:5]
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

    return f"""# {sanitize_note_title(paper.get('paper_markdown_title') or paper.get('title', '未知标题'), '未知标题')}

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

        md += f"| {i} | {level}({score}) | [[{p.get('paper_markdown_title') or p['title'][:35]}]] | {authors} | {p.get('year', '')} | {venue} | {top_mark} | {rel_stars} | {note_status} | {summary} |\n"

    md += generate_visualization(papers, keyword)
    md += "\n---\n\n## 论文详情\n\n"

    for i, p in enumerate(papers, 1):
        is_top, venue_name = is_top_venue(p.get("venue", ""))
        score = p.get("score", 0)
        level = p.get("level", "?")
        level_desc = p.get("level_desc", "")
        rel_stars = p.get("relevance_stars", "★★★☆☆")
        rel_reason = p.get("relevance_reason", "")
        fulltext_status = "已生成单篇全文解读" if p.get('has_fulltext_markdown') else f"未生成（{p.get('fulltext_failure_reason') or '未获取到可解析全文'}）"

        md += f"""### {i}. [[{p.get('paper_markdown_title') or p['title']}]]

**评分**: {level}级 ({score}分) - {level_desc}

**与"{user_keyword}"的相关性**: {rel_stars} {rel_reason}

- **会议**: {p.get('venue', 'N/A')} {f"({venue_name})" if is_top else ""}
- **年份**: {p.get('year', 'N/A')}
- **作者**: {p.get('authors', 'N/A')}
- **引用**: {p.get('citations', 0)}
- **链接**: [{p.get('link') or p.get('url', '')}]({p.get('link') or p.get('url', '')})
- **单篇全文解读**: {fulltext_status}
- **全文失败原因**: {p.get('fulltext_failure_reason', '') or '无'}
- **最后尝试来源**: {(p.get('fulltext_failure_details') or [{}])[0].get('final_url') or (p.get('fulltext_failure_details') or [{}])[0].get('candidate_url') or '无'}

**评分详情**: {p.get('score_details', 'N/A')}

**核心观点**: {p.get('summary', 'N/A')}

**中文详细解读**: {p.get('chinese_explanation', 'N/A')}

**与{user_keyword}相关的应用**: {p.get('applications', 'N/A')}

**阅读建议**: {p.get('suggestions', 'N/A')}

---

"""

    return md


# ==================== 主程序 ====================

def write_search_outputs(valid_papers, keyword, original_keyword, output_dir):
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

    return filename, json_file


def apply_fulltext_analysis(processed_results, notes_dir, reserved_titles, keyword, original_keyword, stats):
    if not processed_results:
        return {
            'papers': [],
            'generated_count': 0,
            'unavailable_count': 0
        }

    ordered_results = sorted(processed_results, key=lambda item: item['index'])
    available_results = [item for item in ordered_results if item['paper'].get('fulltext_status') == 'available']

    if available_results:
        print(f"\n全文解读并发生成中... (并发={FULLTEXT_ANALYSIS_WORKERS})")
        with ThreadPoolExecutor(max_workers=FULLTEXT_ANALYSIS_WORKERS) as executor:
            future_map = {
                executor.submit(
                    generate_fulltext_analysis,
                    item['paper'],
                    keyword,
                    original_keyword,
                    item.get('fulltext_text', '')
                ): item for item in available_results
            }
            for future in as_completed(future_map):
                item = future_map[future]
                idx = item['index']
                try:
                    item['fulltext_analysis'] = future.result()
                except Exception as e:
                    print(f"\n    Fulltext analysis error [{idx + 1}]: {e}")
                    item['fulltext_analysis'] = {
                        'detailed_interpretation': '论文未明确说明',
                        'practical_usage': '论文未明确说明',
                        'evidence_excerpt': [],
                        'evidence_note': '论文未明确说明'
                    }

    valid_papers = []
    generated_count = 0
    unavailable_count = 0
    for item in ordered_results:
        paper = item['paper']
        idx = item['index']

        if paper.get('fulltext_status') == 'available':
            generated_count += 1
            if stats is not None:
                stats['fulltext_available'] += 1
            paper_note_path = assign_note_identity(paper, notes_dir, reserved_titles=reserved_titles, fallback_index=idx + 1)
            note_markdown = build_paper_note_markdown(
                paper,
                keyword,
                original_keyword,
                item.get('fulltext_analysis', {
                    'detailed_interpretation': '论文未明确说明',
                    'practical_usage': '论文未明确说明',
                    'evidence_excerpt': [],
                    'evidence_note': '论文未明确说明'
                })
            )
            with open(paper_note_path, 'w', encoding='utf-8') as f:
                f.write(note_markdown)
            paper['has_fulltext_markdown'] = True
            paper['fulltext_analysis'] = item.get('fulltext_analysis', {})
            paper['fulltext_failure_reason'] = ''
            paper['fulltext_failure_details'] = []
        else:
            unavailable_count += 1
            if stats is not None:
                stats['fulltext_unavailable'] += 1
            paper['has_fulltext_markdown'] = False
            paper['paper_markdown_title'] = ''
            paper['paper_markdown_slug'] = ''
            paper['paper_markdown_path'] = ''
            paper['paper_markdown_filename'] = ''
            paper['fulltext_analysis'] = {}

        valid_papers.append(paper)

    return {
        'papers': valid_papers,
        'generated_count': generated_count,
        'unavailable_count': unavailable_count
    }


def backfill_project_fulltexts(project_dir):
    project_path = Path(project_dir)
    if not project_path.exists():
        raise FileNotFoundError(f"项目目录不存在: {project_dir}")

    notes_dir = project_path / 'paper_notes'
    notes_dir.mkdir(parents=True, exist_ok=True)
    updated_files = []
    processed = 0
    generated = 0
    skipped = 0
    reserved_titles = set()

    for json_file in sorted(project_path.glob('papers_*.json')):
        with open(json_file, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        papers = payload.get('papers', []) or []
        keyword = payload.get('keyword', json_file.stem.replace('papers_', '').replace('_', ' '))
        original_keyword = payload.get('original_keyword') or keyword
        changed = False
        pending_results = []

        print(f"\n回填文件: {json_file.name}")
        print(f"并发处理缺失全文中... (并发={PAPER_PROCESS_WORKERS})")

        with ThreadPoolExecutor(max_workers=PAPER_PROCESS_WORKERS) as executor:
            future_map = {}

            for idx, paper in enumerate(papers):
                processed += 1
                existing_note = notes_dir / str(paper.get('paper_markdown_filename', '') or '')
                if paper.get('has_fulltext_markdown') and existing_note.exists():
                    migrate_existing_note(paper, notes_dir, reserved_titles=reserved_titles, fallback_index=idx + 1)
                    changed = True
                    skipped += 1
                    continue

                note_path = None
                if paper.get('paper_markdown_filename'):
                    note_path = notes_dir / paper['paper_markdown_filename']
                elif paper.get('paper_markdown_slug'):
                    note_path = notes_dir / f"{paper['paper_markdown_slug']}.md"
                if note_path and note_path.exists():
                    migrate_existing_note(paper, notes_dir, reserved_titles=reserved_titles, fallback_index=idx + 1)
                    skipped += 1
                    changed = True
                    continue

                future = executor.submit(fetch_fulltext_for_paper, paper)
                future_map[future] = (idx, paper)

            for future in as_completed(future_map):
                idx, paper = future_map[future]
                try:
                    fulltext_result = future.result()
                except Exception as e:
                    fulltext_result = {
                        'status': 'unavailable',
                        'fulltext_url': '',
                        'fulltext_source_type': '',
                        'fulltext_attempts': [],
                        'fulltext_error': str(e),
                        'fulltext_failure_reason': 'network_error',
                        'fulltext_failure_details': []
                    }

                paper['fulltext_status'] = fulltext_result.get('status', 'unavailable')
                paper['fulltext_url'] = fulltext_result.get('fulltext_url', '')
                paper['fulltext_source_type'] = fulltext_result.get('fulltext_source_type', '')
                paper['fulltext_attempts'] = fulltext_result.get('fulltext_attempts', [])
                paper['fulltext_error'] = fulltext_result.get('fulltext_error', '')
                paper['fulltext_failure_reason'] = fulltext_result.get('fulltext_failure_reason', '')
                paper['fulltext_failure_details'] = fulltext_result.get('fulltext_failure_details', [])
                pending_results.append({
                    'index': idx,
                    'paper': paper,
                    'fulltext_text': fulltext_result.get('fulltext_text', '')
                })
                changed = True

        analysis_result = apply_fulltext_analysis(
            pending_results,
            notes_dir,
            reserved_titles,
            keyword,
            original_keyword,
            stats=None
        )
        generated += analysis_result['generated_count']

        ordered_pending_indices = sorted(item['index'] for item in pending_results)
        for idx, updated_paper in zip(ordered_pending_indices, analysis_result['papers']):
            papers[idx] = updated_paper

        if changed:
            payload['papers'] = papers
            payload['count'] = len(papers)
            payload['timestamp'] = datetime.now().isoformat()
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            md_file, _ = write_search_outputs(papers, keyword, original_keyword, project_path)
            updated_files.append({'json': str(json_file), 'markdown': str(md_file)})

    return {
        'project_dir': str(project_path),
        'processed': processed,
        'generated': generated,
        'skipped': skipped,
        'updated_files': updated_files
    }


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

    stats = {"duplicate": 0, "irrelevant": 0, "invalid": 0, "fulltext_available": 0, "fulltext_unavailable": 0}
    selected_papers = papers[:max_results]
    progress = ProgressBar(len(selected_papers), "处理进度")

    output_dir = Path(project_dir) if project_dir else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    notes_dir = output_dir / 'paper_notes'
    notes_dir.mkdir(parents=True, exist_ok=True)
    reserved_titles = set()

    print(f"并发处理论文中... (并发={PAPER_PROCESS_WORKERS})")
    processed_results = []
    with ThreadPoolExecutor(max_workers=PAPER_PROCESS_WORKERS) as executor:
        future_map = {
            executor.submit(process_paper_task, i, paper, keyword, original_keyword): (i, paper)
            for i, paper in enumerate(selected_papers)
        }

        for future in as_completed(future_map):
            i, paper = future_map[future]
            title_short = paper["title"][:40] + "..." if len(paper["title"]) > 40 else paper["title"]

            try:
                result = future.result()
            except Exception as e:
                print(f"\n[{i+1}/{len(selected_papers)}] {title_short}")
                print(f"  [失败] 处理异常: {e}")
                stats["invalid"] += 1
                progress.update()
                continue

            print(f"\n[{i+1}/{len(selected_papers)}] {title_short}")
            if result['status'] == 'invalid':
                print("  [跳过] 信息不完整")
                stats["invalid"] += 1
                progress.update()
                continue

            if result['status'] == 'irrelevant':
                print(f"  [跳过] 不相关: {result.get('message', '')}")
                stats["irrelevant"] += 1
                progress.update()
                continue

            paper_result = result['paper']
            print("  处理完成")
            if paper_result.get('fulltext_status') == 'available':
                print("  全文获取: 成功")
            else:
                reason = paper_result.get('fulltext_failure_reason') or '未获取到可解析全文'
                print(f"  全文获取: 失败 ({reason})")

            processed_results.append(result)
            progress.update()

    progress.close()

    analysis_result = apply_fulltext_analysis(
        processed_results,
        notes_dir,
        reserved_titles,
        keyword,
        original_keyword,
        stats
    )
    valid_papers = analysis_result['papers']

    print("\n" + "="*50)
    print("生成结果...")
    print("="*50)

    filename, json_file = write_search_outputs(valid_papers, keyword, original_keyword, output_dir)

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
        backfill_project_dir = None

        for arg in args:
            if arg.isdigit():
                max_r = int(arg)
            elif arg.startswith('--original='):
                original_keyword = arg.split('=', 1)[1]
            elif arg.startswith('--project-dir='):
                project_dir = arg.split('=', 1)[1]
            elif arg.startswith('--backfill-project='):
                backfill_project_dir = arg.split('=', 1)[1]
            else:
                keyword_parts.append(arg)

        if backfill_project_dir:
            result = backfill_project_fulltexts(backfill_project_dir)
            print(f"[回填完成] 项目: {result['project_dir']}")
            print(f"  处理论文: {result['processed']}")
            print(f"  新增全文解读: {result['generated']}")
            print(f"  跳过已有: {result['skipped']}")
        else:
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
