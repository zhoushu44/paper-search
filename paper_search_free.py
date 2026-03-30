# -*- coding: utf-8 -*-
"""
论文搜索与验证系统 - 完全免费版
功能：通过免费API搜索论文，判断是否顶会，生成Markdown表格

免费API使用：
1. Semantic Scholar API - 免费，无需key，100次/5分钟
2. arXiv API - 免费，无限制
3. Ollama本地LLM - 完全免费（需安装）

如果不想用Ollama，可以手动填写简介
"""

import requests
import xml.etree.ElementTree as ET
import time
import re
import json
from datetime import datetime

# ==================== 配置区 ====================
YEAR_START = 2021
YEAR_END = 2026
MAX_RESULTS = 50

# Ollama配置（本地LLM，完全免费）
OLLAMA_URL = "http://localhost:11434"  # 默认地址
OLLAMA_MODEL = "qwen2:7b"  # 或 "llama3", "deepseek-coder" 等

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
    "IEEE S&P", "S&P", "CCS", "USENIX Security", "NDSS",
    # 数据库
    "SIGMOD", "VLDB", "ICDE", "CIDR",
    # 软件工程
    "ICSE", "FSE", "ASE", "ISSTA",
    # 网络
    "SIGCOMM", "MobiCom", "INFOCOM",
    # 图形学
    "SIGGRAPH", "Eurographics",
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
}

# ==================== 方法1: Semantic Scholar搜索 (免费) ====================
def search_semantic_scholar(keyword, year_start=YEAR_START, year_end=YEAR_END, limit=MAX_RESULTS):
    """
    Semantic Scholar API - 完全免费，无需API Key
    限制：100次/5分钟
    """
    print(f"\n[Semantic Scholar] 搜索: {keyword}")

    papers = []

    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": keyword,
        "year": f"{year_start}-{year_end}",
        "limit": limit,
        "fields": "title,authors,year,venue,abstract,url,citationCount,publicationVenue,externalIds"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        if "data" in data:
            for item in data["data"]:
                paper = {
                    "title": item.get("title", ""),
                    "authors": ", ".join([a.get("name", "") for a in item.get("authors", [])]),
                    "year": item.get("year"),
                    "venue": extract_venue_from_semantic(item),
                    "abstract": item.get("abstract", ""),
                    "url": item.get("url", ""),
                    "citations": item.get("citationCount", 0),
                    "source": "Semantic Scholar"
                }
                papers.append(paper)

        print(f"找到 {len(papers)} 篇论文")

    except Exception as e:
        print(f"Semantic Scholar搜索出错: {e}")

    return papers


def extract_venue_from_semantic(item):
    """从Semantic Scholar结果提取会议名称"""
    # 方式1: publicationVenue字段
    pub_venue = item.get("publicationVenue", {})
    if pub_venue:
        if isinstance(pub_venue, dict):
            return pub_venue.get("name", "") or pub_venue.get("venue", "")
        return str(pub_venue)

    # 方式2: 从venue字段
    venue = item.get("venue", "")
    if venue:
        return venue

    # 方式3: 从externalIds推断
    ext_ids = item.get("externalIds", {})
    if "DOI" in ext_ids:
        doi = ext_ids["DOI"]
        # DOI通常包含会议信息，如 10.1145/... 表示ACM会议
        pass

    return ""


# ==================== 方法2: arXiv搜索 (免费) ====================
def search_arxiv(keyword, year_start=YEAR_START, year_end=YEAR_END, max_results=MAX_RESULTS):
    """
    arXiv API - 完全免费，无限制
    注意：arXiv主要是预印本，不是顶会
    """
    print(f"\n[arXiv] 搜索: {keyword}")

    papers = []

    # arXiv API
    base_url = "http://export.arxiv.org/api/query"

    # 构建查询
    query = f"all:{keyword}"

    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }

    try:
        response = requests.get(base_url, params=params, timeout=60)
        root = ET.fromstring(response.content)

        # 定义命名空间
        ns = {"atom": "http://www.w3.org/2005/Atom",
              "arxiv": "http://arxiv.org/schemas/atom"}

        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip()
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]

            # 提取年份
            published = entry.find("atom:published", ns).text
            year = int(published[:4])

            # 筛选年份
            if year_start <= year <= year_end:
                paper = {
                    "title": title,
                    "authors": ", ".join(authors),
                    "year": year,
                    "venue": "arXiv",
                    "abstract": entry.find("atom:summary", ns).text.strip(),
                    "url": entry.find("atom:id", ns).text,
                    "citations": 0,
                    "source": "arXiv"
                }
                papers.append(paper)

        print(f"找到 {len(papers)} 篇论文")

    except Exception as e:
        print(f"arXiv搜索出错: {e}")

    return papers


# ==================== 方法3: CrossRef搜索 (免费) ====================
def search_crossref(keyword, year_start=YEAR_START, year_end=YEAR_END, rows=MAX_RESULTS):
    """
    CrossRef API - 完全免费，无限制
    包含期刊和会议论文
    """
    print(f"\n[CrossRef] 搜索: {keyword}")

    papers = []

    url = "https://api.crossref.org/works"

    params = {
        "query": keyword,
        "filter": f"from-pub-date:{year_start},until-pub-date:{year_end}",
        "rows": rows,
        "select": "title,author,published-print,published-online,container-title,abstract,URL,is-referenced-by-count"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        if "message" in data and "items" in data["message"]:
            for item in data["message"]["items"]:
                title_list = item.get("title", [])
                title = title_list[0] if title_list else ""

                authors = []
                for author in item.get("author", []):
                    name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                    authors.append(name)

                # 获取年份
                pub_date = item.get("published-print") or item.get("published-online") or {}
                year_info = pub_date.get("date-parts", [[None]])
                year = year_info[0][0] if year_info and year_info[0] else None

                paper = {
                    "title": title,
                    "authors": ", ".join(authors),
                    "year": year,
                    "venue": item.get("container-title", [""])[0] if item.get("container-title") else "",
                    "abstract": item.get("abstract", ""),
                    "url": item.get("URL", ""),
                    "citations": item.get("is-referenced-by-count", 0),
                    "source": "CrossRef"
                }
                papers.append(paper)

        print(f"找到 {len(papers)} 篇论文")

    except Exception as e:
        print(f"CrossRef搜索出错: {e}")

    return papers


# ==================== 综合搜索 ====================
def search_all_sources(keyword, max_per_source=20):
    """使用所有免费API搜索"""
    all_papers = []

    # Semantic Scholar (推荐，有顶会信息)
    papers = search_semantic_scholar(keyword, limit=max_per_source)
    all_papers.extend(papers)
    time.sleep(1)  # 避免限流

    # CrossRef (期刊和会议)
    papers = search_crossref(keyword, rows=max_per_source)
    all_papers.extend(papers)
    time.sleep(1)

    # arXiv (预印本，可选)
    # papers = search_arxiv(keyword, max_results=max_per_source)
    # all_papers.extend(papers)

    # 去重
    seen = set()
    unique_papers = []
    for paper in all_papers:
        title_lower = paper["title"].lower()
        if title_lower not in seen:
            seen.add(title_lower)
            unique_papers.append(paper)

    print(f"\n总共找到 {len(unique_papers)} 篇唯一论文")
    return unique_papers


# ==================== 顶会匹配 ====================
def is_top_venue(venue):
    """判断是否为顶级会议/期刊"""
    if not venue:
        return False, ""

    venue_upper = venue.upper()

    for top in TOP_VENUES:
        if top.upper() in venue_upper or top in venue:
            return True, top

    return False, ""


# ==================== LLM生成 (Ollama本地) ====================
def check_ollama_available():
    """检查Ollama是否可用"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def generate_with_ollama(title, abstract):
    """使用Ollama本地LLM生成简介"""
    if not abstract:
        abstract = "无摘要信息"

    prompt = f"""分析以下论文，用JSON格式返回结果：

标题：{title}
摘要：{abstract[:500]}

返回格式：
{{
    "summary": "一句话简介（50字内，英文）",
    "chinese_explanation": "中文详细解释（150字，包括研究问题、方法、贡献）"
}}

只返回JSON，不要其他内容。"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        result = response.json()
        content = result.get("response", "")

        # 解析JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("summary", ""), data.get("chinese_explanation", "")

    except Exception as e:
        print(f"Ollama生成出错: {e}")

    return "", ""


def generate_without_llm(title, abstract):
    """无LLM时的简化处理"""
    summary = f"论文研究{title[:50]}..."
    chinese = f"该论文标题为《{title}》，" + (f"摘要：{abstract[:150]}..." if abstract else "暂无详细摘要。")
    return summary, chinese


# ==================== 真实性验证 ====================
def validate_paper(paper):
    """验证论文真实性"""
    confidence = 0
    reasons = []

    # 1. 标题有效性
    if paper.get("title") and len(paper["title"]) > 10:
        confidence += 25
        reasons.append("标题有效")

    # 2. 年份有效性
    year = paper.get("year")
    if year and YEAR_START <= year <= YEAR_END:
        confidence += 20
        reasons.append(f"年份有效({year})")

    # 3. 作者信息
    if paper.get("authors"):
        confidence += 15
        reasons.append("有作者")

    # 4. 会议/期刊
    if paper.get("venue"):
        confidence += 15
        reasons.append("有发表场所")

    # 5. 引用数
    citations = paper.get("citations", 0)
    if citations > 0:
        confidence += min(citations, 25)
        reasons.append(f"引用{citations}次")

    # 6. 摘要
    if paper.get("abstract"):
        confidence += 10
        reasons.append("有摘要")

    return confidence >= 50, confidence, "; ".join(reasons)


# ==================== 生成Markdown表格 ====================
def generate_markdown(papers, keyword):
    """生成Markdown表格"""
    md = f"""# 论文搜索结果

**关键词**: {keyword}
**时间范围**: {YEAR_START}-{YEAR_END}
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**论文数量**: {len(papers)}

---

| 序号 | 论文名 | 作者 | 年份 | 会议 | 顶会 | 相关简介 | 中文详细解释 |
|------|--------|------|------|------|------|----------|-------------|
"""

    for i, p in enumerate(papers, 1):
        is_top, venue_name = is_top_venue(p.get("venue", ""))
        top_mark = f"✓ {venue_name}" if is_top else "✗"

        md += f"| {i} | {p['title']} | {p['authors'][:30]} | {p['year']} | {p['venue'][:20]} | {top_mark} | {p.get('summary', '')} | {p.get('chinese_explanation', '')} |\n"

    # 添加顶会统计
    top_count = sum(1 for p in papers if is_top_venue(p.get("venue", ""))[0])
    md += f"\n---\n**统计**: 共 {len(papers)} 篇，其中顶会 {top_count} 篇\n"

    return md


# ==================== 主程序 ====================
def main(keyword, max_results=50):
    """主函数"""

    print("=" * 60)
    print("论文搜索与验证系统 (免费版)")
    print("=" * 60)

    # 检查Ollama
    ollama_ok = check_ollama_available()
    if ollama_ok:
        print(f"✓ Ollama可用 (模型: {OLLAMA_MODEL})")
    else:
        print(f"✗ Ollama不可用，将使用简化模式")
        print("  提示: 安装Ollama可获得更好的简介生成效果")

    # Step 1: 搜索
    papers = search_all_sources(keyword, max_per_source=max_results//2)

    if not papers:
        print("\n未找到论文")
        return

    # Step 2-4: 处理每篇论文
    valid_papers = []

    print(f"\n处理 {len(papers)} 篇论文...")

    for i, paper in enumerate(papers):
        print(f"\n[{i+1}/{len(papers)}] {paper['title'][:50]}...")

        # 验证
        is_valid, conf, reason = validate_paper(paper)
        print(f"  可信度: {conf}% - {reason}")

        if not is_valid:
            print("  [跳过] 可信度不足")
            continue

        # 生成简介
        if ollama_ok:
            summary, chinese = generate_with_ollama(paper["title"], paper.get("abstract", ""))
        else:
            summary, chinese = generate_without_llm(paper["title"], paper.get("abstract", ""))

        paper["summary"] = summary
        paper["chinese_explanation"] = chinese
        valid_papers.append(paper)

        time.sleep(0.5)

    # Step 5: 生成结果
    print(f"\n生成结果...")
    markdown = generate_markdown(valid_papers, keyword)

    # 保存
    filename = f"papers_{keyword.replace(' ', '_')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"\n✓ 完成! 保存至: {filename}")
    print(f"✓ 有效论文: {len(valid_papers)} 篇")

    return valid_papers


# ==================== 交互入口 ====================
if __name__ == "__main__":
    import sys

    print("""
╔══════════════════════════════════════════════════════════╗
║           论文搜索与验证系统 (完全免费版)                  ║
╠══════════════════════════════════════════════════════════╣
║  使用API:                                                ║
║  - Semantic Scholar (免费)                               ║
║  - CrossRef (免费)                                       ║
║  - Ollama本地LLM (可选，免费)                            ║
╚══════════════════════════════════════════════════════════╝
""")

    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        max_r = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        main(keyword, max_r)
    else:
        while True:
            keyword = input("\n输入搜索关键词 (q退出): ").strip()
            if keyword.lower() == 'q':
                break
            if keyword:
                main(keyword)
