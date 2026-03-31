# -*- coding: utf-8 -*-
"""Flask论文搜索与展示系统"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import re
import html
import markdown
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, abort, url_for
import subprocess
import threading
from pathlib import Path

app = Flask(__name__)

APP_HOST = '0.0.0.0'
APP_PORT = 5055

# 数据目录
DATA_DIR = Path(__file__).parent
MARKDOWN_DIR = DATA_DIR
JSON_DIR = DATA_DIR
PROJECTS_DIR = DATA_DIR / 'projects'
PROJECTS_FILE = DATA_DIR / 'projects.json'
SETTINGS_FILE = DATA_DIR / 'settings.json'

# 确保项目目录存在
if not PROJECTS_DIR.exists():
    PROJECTS_DIR.mkdir(exist_ok=True)

# 默认API配置
DEFAULT_API_KEY = os.environ.get('PAPER_SEARCH_API_KEY', '')
DEFAULT_API_BASE = os.environ.get('PAPER_SEARCH_API_BASE', '')
DEFAULT_MODEL = os.environ.get('PAPER_SEARCH_MODEL', 'gpt-5.4')
DEFAULT_SEARCH_COUNT = 15

OPENAI_API_KEY = DEFAULT_API_KEY
OPENAI_API_BASE = DEFAULT_API_BASE
OPENAI_MODEL = DEFAULT_MODEL

# 加载设置
def load_settings():
    """加载系统设置"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_settings(settings):
    """保存系统设置"""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def get_api_config():
    """获取当前API配置"""
    settings = load_settings()
    return {
        'api_key': settings.get('api_key') or DEFAULT_API_KEY,
        'api_url': settings.get('api_url') or DEFAULT_API_BASE,
        'model': settings.get('model') or DEFAULT_MODEL,
        'search_count': settings.get('search_count') or DEFAULT_SEARCH_COUNT
    }

# 中文关键词翻译映射表
KEYWORD_TRANSLATIONS = {
    # 电商相关
    "电商": "e-commerce",
    "电子商务": "e-commerce",
    "点击率": "click-through rate CTR",
    "转化率": "conversion rate",
    "用户行为": "user behavior",
    "推荐系统": "recommender system recommendation",
    "推荐算法": "recommendation algorithm",
    "商品推荐": "product recommendation",
    "销量预测": "sales prediction forecasting",
    "用户画像": "user profiling user representation",
    "个性化推荐": "personalized recommendation",
    "协同过滤": "collaborative filtering",
    "内容推荐": "content-based recommendation",
    "点击预测": "click prediction",

    # 深度学习
    "深度学习": "deep learning",
    "神经网络": "neural network",
    "卷积神经网络": "CNN convolutional neural network",
    "循环神经网络": "RNN recurrent neural network",
    "注意力机制": "attention mechanism",
    "自注意力": "self-attention",
    "Transformer": "transformer",
    "BERT": "BERT language model",
    "GPT": "GPT language model",
    "预训练模型": "pre-trained model",
    "知识图谱": "knowledge graph",
    "图神经网络": "graph neural network GNN",

    # NLP
    "自然语言处理": "natural language processing NLP",
    "文本分类": "text classification",
    "情感分析": "sentiment analysis",
    "命名实体识别": "named entity recognition NER",
    "机器翻译": "machine translation",
    "问答系统": "question answering",
    "对话系统": "dialogue system conversational AI",
    "文本生成": "text generation",
    "摘要生成": "text summarization",

    # 计算机视觉
    "计算机视觉": "computer vision",
    "图像分类": "image classification",
    "目标检测": "object detection",
    "图像分割": "image segmentation",
    "人脸识别": "face recognition",
    "图像生成": "image generation",
    "生成对抗网络": "GAN generative adversarial network",
    "扩散模型": "diffusion model",

    # 强化学习
    "强化学习": "reinforcement learning",
    "策略梯度": "policy gradient",
    "Q学习": "Q-learning",
    "多智能体": "multi-agent",

    # 数据挖掘
    "数据挖掘": "data mining",
    "聚类": "clustering",
    "分类": "classification",
    "回归": "regression",
    "异常检测": "anomaly detection",
    "时序预测": "time series prediction forecasting",
    "推荐": "recommendation",

    # 其他常用
    "优化算法": "optimization algorithm",
    "迁移学习": "transfer learning",
    "联邦学习": "federated learning",
    "模型压缩": "model compression",
    "量化": "quantization",
    "蒸馏": "knowledge distillation",
    "多模态": "multimodal",
    "因果推断": "causal inference",
}


def translate_keyword(chinese_keyword):
    """将中文关键词翻译为英文，并生成相关关键词"""
    result = {
        'original': chinese_keyword,
        'translated': [],
        'expanded': []
    }

    # 直接匹配翻译
    words = chinese_keyword.replace("的", " ").replace("与", " ").replace("和", " ").split()
    translated_words = []

    for word in words:
        word = word.strip()
        if not word:
            continue

        # 查找翻译
        found = False
        for cn, en in KEYWORD_TRANSLATIONS.items():
            if cn in word or word in cn:
                translated_words.append(en)
                found = True
                break

        if not found:
            translated_words.append(word)

    result['translated'] = translated_words

    # 生成扩展关键词
    base_keyword = ' '.join(translated_words)

    # 根据主题生成相关关键词
    expanded = []

    if any(w in chinese_keyword for w in ['电商', '点击率', '转化率', '推荐']):
        expanded = [
            f"{base_keyword}",
            f"{base_keyword} prediction",
            f"{base_keyword} deep learning",
            "CTR prediction e-commerce",
            "click-through rate estimation",
            "user behavior modeling",
            "recommendation system"
        ]
    elif any(w in chinese_keyword for w in ['图像', '视觉', '检测', '分割']):
        expanded = [
            f"{base_keyword}",
            f"{base_keyword} deep learning",
            f"{base_keyword} CNN",
            "computer vision",
            "image recognition"
        ]
    elif any(w in chinese_keyword for w in ['文本', '语言', 'NLP', '对话']):
        expanded = [
            f"{base_keyword}",
            f"{base_keyword} BERT transformer",
            f"{base_keyword} deep learning",
            "natural language processing",
            "text analysis"
        ]
    else:
        expanded = [
            f"{base_keyword}",
            f"{base_keyword} deep learning",
            f"{base_keyword} neural network",
            f"{base_keyword} survey review"
        ]

    result['expanded'] = list(set(expanded))[:8]

    return result


def translate_keyword_by_ai(chinese_keyword):
    """使用AI翻译关键词"""
    prompt = f"""Translate the Chinese keyword to English for academic paper search, and generate 5-8 related English keywords.

Chinese keyword: {chinese_keyword}

Return JSON format:
{{"main_translation": "main English keyword", "related_keywords": ["keyword1", "keyword2", ...]}}

Only return the JSON, no other text."""

    try:
        r = requests.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': OPENAI_MODEL,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3,
                'max_tokens': 300
            },
            timeout=30
        )

        content = r.json()['choices'][0]['message']['content']
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"AI translation error: {e}")

    return None

# 顶会列表
TOP_VENUES = {
    'NeurIPS', 'ICML', 'ICLR', 'AAAI', 'IJCAI',  # AI/ML
    'ACL', 'EMNLP', 'NAACL',  # NLP
    'CVPR', 'ICCV', 'ECCV',  # CV
    'OSDI', 'SOSP', 'NSDI', 'SIGCOMM',  # System
    'IEEE S&P', 'CCS', 'USENIX Security',  # Security
    'SIGMOD', 'VLDB', 'ICDE',  # DB
    'KDD', 'SIGIR', 'WWW',  # Data Mining/IR
    'Nature', 'Science', 'Cell',  # Top Journals
    'JAMA', 'NEJM', 'Lancet'  # Medical
}

# 会议/期刊中文分类
VENUE_CATEGORIES = {
    # AI/ML - 人工智能/机器学习顶会
    'NeurIPS': '人工智能顶会',
    'ICML': '人工智能顶会',
    'ICLR': '人工智能顶会',
    'AAAI': '人工智能顶会',
    'IJCAI': '人工智能顶会',
    'AISTATS': '人工智能顶会',
    'UAI': '人工智能顶会',

    # NLP - 自然语言处理顶会
    'ACL': '自然语言顶会',
    'EMNLP': '自然语言顶会',
    'NAACL': '自然语言顶会',
    'COLING': '自然语言顶会',
    'LREC': '自然语言顶会',
    'EACL': '自然语言顶会',

    # CV - 计算机视觉顶会
    'CVPR': '计算机视觉顶会',
    'ICCV': '计算机视觉顶会',
    'ECCV': '计算机视觉顶会',
    'WACV': '计算机视觉顶会',
    'BMVC': '计算机视觉顶会',
    'SIGGRAPH': '图形学顶会',

    # System - 系统顶会
    'OSDI': '系统顶会',
    'SOSP': '系统顶会',
    'NSDI': '网络顶会',
    'SIGCOMM': '网络顶会',
    'ASPLOS': '系统顶会',
    'EuroSys': '系统顶会',
    'ATC': '系统顶会',

    # Security - 安全顶会
    'IEEE S&P': '安全顶会',
    'CCS': '安全顶会',
    'USENIX Security': '安全顶会',
    'NDSS': '安全顶会',

    # DB - 数据库顶会
    'SIGMOD': '数据库顶会',
    'VLDB': '数据库顶会',
    'ICDE': '数据库顶会',
    'CIDR': '数据库顶会',

    # SE - 软件工程顶会
    'ICSE': '软件工程顶会',
    'FSE': '软件工程顶会',
    'ASE': '软件工程顶会',

    # DM/IR - 数据挖掘/信息检索顶会
    'KDD': '数据挖掘顶会',
    'ICDM': '数据挖掘顶会',
    'SDM': '数据挖掘顶会',
    'SIGIR': '信息检索顶会',
    'WSDM': '信息检索顶会',
    'WWW': '互联网顶会',
    'CIKM': '信息检索顶会',

    # Recommender - 推荐系统
    'RecSys': '推荐系统顶会',

    # MM - 多媒体
    'ACM MM': '多媒体顶会',
    'ICME': '多媒体顶会',

    # HCI - 人机交互
    'CHI': '人机交互顶会',
    'UIST': '人机交互顶会',
    'CSCW': '人机交互顶会',

    # Robotics - 机器人
    'ICRA': '机器人顶会',
    'IROS': '机器人顶会',
    'RSS': '机器人顶会',

    # Top Journals - 顶级期刊
    'Nature': '顶级期刊',
    'Science': '顶级期刊',
    'Cell': '顶级期刊',
    'JMLR': '机器学习期刊',
    'TPAMI': '人工智能期刊',
    'TACL': '自然语言期刊',
    'TOIS': '信息检索期刊',
    'TKDE': '数据工程期刊',

    # Medical - 医学
    'JAMA': '医学顶刊',
    'NEJM': '医学顶刊',
    'Lancet': '医学顶刊',
}

def get_venue_category(venue):
    """获取会议/期刊的中文分类"""
    if not venue:
        return ""
    venue_upper = venue.upper()
    for key, category in VENUE_CATEGORIES.items():
        if key.upper() in venue_upper:
            return category
    return ""


def is_top_venue(venue):
    """判断是否为顶会"""
    if not venue:
        return False, ""
    venue_upper = venue.upper()
    for top in TOP_VENUES:
        if top.upper() in venue_upper:
            return True, top
    return False, ""


def load_projects():
    """加载项目列表"""
    if PROJECTS_FILE.exists():
        with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_projects(projects):
    """保存项目列表"""
    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)


def save_project_meta(project_id, project_data):
    """同步保存单个项目元数据"""
    project_dir = PROJECTS_DIR / project_id
    if not project_dir.exists():
        return
    with open(project_dir / 'meta.json', 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)


def compute_project_stats(project_id):
    """根据项目目录中的实际文件计算项目统计信息"""
    papers = get_project_papers(project_id)
    return {
        'total_papers': len(papers),
        'top_papers': sum(1 for p in papers if is_top_venue(p.get('venue', ''))[0])
    }


def update_project_registry(project_id, status=None, persist=True):
    """根据项目实际内容更新 projects.json 与 meta.json 中的项目状态"""
    projects = load_projects()
    if project_id not in projects:
        return None

    stats = compute_project_stats(project_id)
    projects[project_id]['total_papers'] = stats['total_papers']
    projects[project_id]['top_papers'] = stats['top_papers']
    if status is not None:
        projects[project_id]['status'] = status

    if persist:
        save_projects(projects)
        save_project_meta(project_id, projects[project_id])

    return projects[project_id]


def create_project(keyword):
    """创建新项目"""
    projects = load_projects()
    safe_keyword = re.sub(r'[\\/:*?"<>|]+', '_', keyword).strip(' ._') or 'project'
    project_id = f"proj_{safe_keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 翻译关键词
    translation = translate_keyword(keyword)

    projects[project_id] = {
        'name': keyword,
        'created': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'search_keywords': translation['expanded'][:5],
        'total_papers': 0,
        'top_papers': 0,
        'status': 'searching'
    }
    save_projects(projects)

    # 创建项目目录
    project_dir = PROJECTS_DIR / project_id
    project_dir.mkdir(exist_ok=True)

    # 保存项目元数据
    save_project_meta(project_id, projects[project_id])

    return project_id, translation['expanded'][:5]


def get_project_papers(project_id):
    """获取项目内所有论文"""
    project_dir = PROJECTS_DIR / project_id
    all_papers = []

    if project_dir.exists():
        for f in project_dir.iterdir():
            if f.name.startswith('papers_') and f.suffix == '.md':
                data = parse_markdown_file(str(f))
                for p in data['papers']:
                    p['source_file'] = f.name
                    p['project_id'] = project_id
                all_papers.extend(data['papers'])

    # 按评分排序
    def get_score(p):
        s = p.get('score', 'D(0)')
        if isinstance(s, (int, float)):
            return int(s)
        s = str(s or 'D(0)')
        match = re.search(r'\((\d+)\)', s)
        return int(match.group(1)) if match else 0

    all_papers.sort(key=get_score, reverse=True)
    return all_papers


def format_failure_reason(reason):
    reason_map = {
        'network_error': '网络请求失败',
        'non_text_pdf': 'PDF 可下载但无法提取正文',
        'landing_page_only': '仅获取到摘要/落地页',
        'too_short_pdf': 'PDF 正文过短',
        'too_short_html': 'HTML 正文过短',
        'no_candidates': '缺少可尝试的全文链接'
    }
    return reason_map.get(reason, reason or '')


def summarize_failure_detail(detail):
    if not isinstance(detail, dict):
        return ''
    reason = format_failure_reason(detail.get('reason')) or detail.get('reason', '')
    final_url = detail.get('final_url') or detail.get('candidate_url') or ''
    extra = detail.get('error') or ''
    summary = reason
    if final_url:
        summary += f' | {final_url}'
    if extra:
        summary += f' | {extra}'
    return summary


app.jinja_env.globals.update(format_failure_reason=format_failure_reason)
app.jinja_env.globals.update(is_top_venue=is_top_venue)


def build_project_paper_note_path(project_id, paper):
    """构建项目内单篇全文解读文件路径"""
    relative_path = str(paper.get('paper_markdown_path', '') or '').strip()
    filename = str(paper.get('paper_markdown_filename', '') or '').strip()
    slug = str(paper.get('paper_markdown_slug', '') or '').strip()
    project_dir = PROJECTS_DIR / project_id

    candidate = None
    if relative_path:
        candidate = project_dir / relative_path
    elif filename:
        candidate = project_dir / 'paper_notes' / filename
    elif slug:
        candidate = project_dir / 'paper_notes' / f'{slug}.md'

    return candidate


def get_project_paper_note_url(project_id, paper):
    """获取项目内单篇全文解读链接"""
    if not paper.get('has_fulltext_markdown'):
        return None

    candidate = build_project_paper_note_path(project_id, paper)
    if not candidate or not candidate.exists() or candidate.suffix.lower() != '.md':
        return None

    slug = str(paper.get('paper_markdown_slug', '') or '').strip()
    if slug:
        return url_for('project_paper_note', project_id=project_id, slug=slug)

    return url_for('project_paper_note_file', project_id=project_id, filename=candidate.name)


app.jinja_env.globals.update(get_project_paper_note_url=get_project_paper_note_url)


def parse_markdown_file(filepath):
    """解析markdown文件，提取论文信息"""
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    papers = []

    keyword_match = re.search(r'\*\*关键词\*\*:\s*(.+?)\n', content)
    date_match = re.search(r'\*\*日期\*\*:\s*(.+?)\n', content)
    keyword = keyword_match.group(1).strip() if keyword_match else Path(filepath).stem.replace('papers_', '').replace('_', ' ')
    date = date_match.group(1).strip() if date_match else 'Unknown'

    json_path = Path(filepath).with_suffix('.json')
    papers_from_json = []
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as jf:
                json_data = json.load(jf)
            papers_from_json = json_data.get('papers', []) or []
        except Exception:
            papers_from_json = []

    table_section = re.search(r'## 汇总表.*?\n\n(.+?)\n##', content, re.DOTALL)
    if table_section:
        table_content = table_section.group(1)
        rows = table_content.split('\n')[2:]

        for row in rows:
            if '|' not in row:
                continue
            parts = [p.strip() for p in row.split('|')]
            if len(parts) >= 8:
                papers.append({
                    'rank': parts[1],
                    'score': parts[2],
                    'title': parts[3].replace('[[', '').replace(']]', ''),
                    'authors': parts[4],
                    'year': parts[5],
                    'venue': parts[6],
                    'is_top': parts[7],
                    'summary': parts[9] if len(parts) > 9 else (parts[8] if len(parts) > 8 else '')
                })

    detail_section = re.split(r'### \d+\.\s*', content)
    for detail in detail_section:
        if not detail.strip():
            continue

        title_match = re.search(r'\[\[(.+?)\]\]', detail)
        if not title_match:
            continue
        title = title_match.group(1)

        for paper in papers:
            paper_title = paper['title']
            if title in paper_title or paper_title in title:
                score_match = re.search(r'\*\*评分\*\*:\s*(.+?)\n', detail)
                if score_match:
                    paper['score_full'] = score_match.group(1).strip()

                venue_match = re.search(r'\*\*会议\*\*:\s*([^\n]*)', detail)
                if venue_match:
                    venue_val = venue_match.group(1).strip()
                    if venue_val and not venue_val.startswith('- **'):
                        paper['venue'] = venue_val

                year_match = re.search(r'\*\*年份\*\*:\s*(.+?)\n', detail)
                if year_match:
                    paper['year'] = year_match.group(1).strip()

                authors_match = re.search(r'\*\*作者\*\*:\s*(.+?)\n', detail)
                if authors_match:
                    paper['authors'] = authors_match.group(1).strip()

                citations_match = re.search(r'\*\*引用\*\*:\s*(.+?)\n', detail)
                if citations_match:
                    paper['citations'] = citations_match.group(1).strip()

                link_match = re.search(r'\*\*链接\*\*:\s*\[(.+?)\]\((.+?)\)', detail)
                if link_match:
                    paper['link_text'] = link_match.group(1).strip()
                    paper['link'] = link_match.group(2).strip()

                chinese_match = re.search(r'\*\*中文详细解读\*\*:\s*(.+?)(?=\*\*与|\*\*阅读建议\*\*|---|$)', detail, re.DOTALL)
                if chinese_match:
                    paper['chinese_detail'] = chinese_match.group(1).strip()

                apps_match = re.search(r'\*\*与.+?相关的应用\*\*:\s*(.+?)(?=\*\*阅读建议\*\*|---|$)', detail, re.DOTALL)
                if apps_match:
                    paper['applications'] = apps_match.group(1).strip()

                suggs_match = re.search(r'\*\*阅读建议\*\*:\s*(.+?)(?=\n---|\n##|$)', detail, re.DOTALL)
                if suggs_match:
                    paper['suggestions'] = suggs_match.group(1).strip()

                fulltext_status_match = re.search(r'\*\*单篇全文解读\*\*:\s*(.+?)\n', detail)
                if fulltext_status_match:
                    paper['fulltext_markdown_status'] = fulltext_status_match.group(1).strip()

                failure_reason_match = re.search(r'\*\*全文失败原因\*\*:\s*(.+?)\n', detail)
                if failure_reason_match:
                    paper['fulltext_failure_reason'] = failure_reason_match.group(1).strip()

                last_attempt_match = re.search(r'\*\*最后尝试来源\*\*:\s*(.+?)\n', detail)
                if last_attempt_match:
                    paper['fulltext_last_attempt'] = last_attempt_match.group(1).strip()

                paper['full_detail'] = detail.strip()
                break

    if papers_from_json:
        merged = []
        used = set()
        for paper in papers:
            matched = None
            for idx, item in enumerate(papers_from_json):
                item_title = str(item.get('title', ''))
                if idx in used:
                    continue
                if item_title == paper.get('title') or item_title.startswith(paper.get('title', '')) or paper.get('title', '').startswith(item_title):
                    matched = dict(item)
                    used.add(idx)
                    break
            if matched is None:
                matched = {}
            merged_paper = dict(matched)
            merged_paper.update({k: v for k, v in paper.items() if v not in ('', None, [])})
            merged.append(merged_paper)
        for idx, item in enumerate(papers_from_json):
            if idx not in used:
                merged.append(item)
        papers = merged

    return {
        'keyword': keyword,
        'date': date,
        'papers': papers
    }


def get_all_markdown_files_grouped():
    """获取按中文关键词分组的项目文件列表"""
    files = get_all_markdown_files()

    grouped = {}
    for f in files:
        orig_kw = f['data'].get('original_keyword', f['data']['keyword'])
        if orig_kw not in grouped:
            grouped[orig_kw] = {
                'original_keyword': orig_kw,
                'files': [],
                'total_papers': 0
            }
        grouped[orig_kw]['files'].append(f)
        grouped[orig_kw]['total_papers'] += len(f['data']['papers'])

    return list(grouped.values())


def get_all_markdown_files():
    """获取所有项目内markdown论文文件（原始格式）"""
    files = []

    for project_dir in sorted(PROJECTS_DIR.iterdir(), key=lambda item: item.name) if PROJECTS_DIR.exists() else []:
        if not project_dir.is_dir():
            continue
        for f in sorted(project_dir.glob('papers_*.md')):
            data = parse_markdown_file(str(f))
            data['original_keyword'] = data.get('original_keyword', data['keyword'])
            for paper in data['papers']:
                paper['project_id'] = project_dir.name
                paper['source_file'] = f.name
            files.append({
                'filename': f.name,
                'project_id': project_dir.name,
                'data': data
            })

    return files


@app.route('/project/<project_id>')
def project_detail(project_id):
    """项目详情页"""
    projects = load_projects()
    if project_id not in projects:
        return "项目不存在", 404

    project = projects[project_id]
    papers = get_project_papers(project_id)
    for paper in papers:
        paper['fulltext_failure_reason_display'] = format_failure_reason(paper.get('fulltext_failure_reason', ''))
        failure_details = paper.get('fulltext_failure_details') or []
        paper['fulltext_last_attempt'] = summarize_failure_detail(failure_details[0]) if failure_details else paper.get('fulltext_last_attempt', '')

    return render_template('project_detail.html',
                          project_id=project_id,
                          project=project,
                          papers=papers)


@app.route('/api/create_project', methods=['POST'])
def api_create_project():
    """创建新项目并开始搜索"""
    global search_status_store

    keyword = request.json.get('keyword', '').strip()
    if not keyword:
        return jsonify({'success': False, 'error': '请输入关键词'})

    # 获取搜索数量配置
    config = get_api_config()
    search_count = config.get('search_count', 15)

    # 创建项目
    project_id, search_keywords = create_project(keyword)

    # 更新搜索状态
    update_search_status(
        searching=True,
        progress=5,
        status='正在翻译关键词...',
        reset_logs=True,
        project_id=project_id,
        original_keyword=keyword
    )

    # 后台搜索
    import subprocess
    import sys
    import threading

    def run_search():
        global search_status_store
        project_dir = PROJECTS_DIR / project_id
        total = len(search_keywords)

        for idx, kw in enumerate(search_keywords):
            try:
                update_search_status(
                    status=f'正在搜索 ({idx+1}/{total}): {kw[:20]}...',
                    progress=5 + int((idx / total) * 90),
                    log_message=f'第 {idx+1}/{total} 步：搜索关键词 {kw}'
                )

                # 切换到DATA_DIR执行搜索，确保文件生成在正确位置
                original_cwd = os.getcwd()
                os.chdir(DATA_DIR)

                try:
                    # 传递原始中文关键词
                    cmd = [
                        sys.executable,
                        str(DATA_DIR / 'paper_search.py'),
                        kw,
                        str(search_count),
                        f'--original={keyword}',
                        f'--project-dir={project_dir}'
                    ]
                    result = subprocess.run(
                        cmd,
                        capture_output=True, text=True, timeout=300
                    )
                    if result.stderr:
                        print(f"搜索错误 [{kw}]: {result.stderr[:200]}")
                finally:
                    os.chdir(original_cwd)

                # 文件现在直接生成到项目目录，无需再从根目录搬运

            except Exception as e:
                print(f"搜索错误 [{kw}]: {e}")

        update_project_registry(project_id, status='completed')

        update_search_status(
            searching=False,
            progress=100,
            status='搜索完成',
            log_message='搜索完成，正在刷新结果'
        )

    thread = threading.Thread(target=run_search)
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'project_id': project_id,
        'message': f'项目"{keyword}"已创建，正在后台搜索...'
    })


@app.route('/api/delete_project', methods=['POST'])
def api_delete_project():
    """删除项目"""
    project_id = request.json.get('project_id', '')
    if not project_id:
        return jsonify({'success': False, 'error': '项目ID不能为空'})

    # 删除项目文件
    project_dir = PROJECTS_DIR / project_id
    if project_dir.exists():
        import shutil
        shutil.rmtree(project_dir)

    # 从项目列表移除
    projects = load_projects()
    if project_id in projects:
        del projects[project_id]
        save_projects(projects)

    # 如果当前全局状态指向该项目，同时清空进度状态，避免前端残留
    if search_status_store.get('project_id') == project_id:
        update_search_status(
            searching=False,
            progress=0,
            status='',
            logs=[],
            reset_logs=True,
            task_id=None,
            original_keyword='',
            project_id=None
        )

    return jsonify({'success': True})


def run_project_backfill(project_id):
    project_dir = PROJECTS_DIR / project_id
    projects = load_projects()
    if project_id in projects:
        projects[project_id]['status'] = 'searching'
        save_projects(projects)
        save_project_meta(project_id, projects[project_id])

    update_search_status(
        searching=True,
        progress=5,
        status='正在补生成缺失全文解读...',
        reset_logs=True,
        log_message=f'开始回填项目 {project_id}',
        project_id=project_id,
        task_id=f'backfill:{project_id}'
    )

    try:
        cmd = [
            sys.executable,
            str(DATA_DIR / 'paper_search.py'),
            f'--backfill-project={project_dir}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        output = '\n'.join([part for part in [result.stdout.strip(), result.stderr.strip()] if part]).strip()

        update_project_registry(project_id, status='completed')

        if result.returncode == 0:
            update_search_status(
                searching=False,
                progress=100,
                status='缺失全文解读补生成完成',
                log_message=output or '补生成完成，正在刷新结果',
                project_id=project_id,
                task_id=f'backfill:{project_id}'
            )
        else:
            update_search_status(
                searching=False,
                progress=100,
                status='补生成失败',
                log_message=output or '补生成失败',
                project_id=project_id,
                task_id=f'backfill:{project_id}'
            )
    except Exception as e:
        update_search_status(
            searching=False,
            progress=100,
            status='补生成失败',
            log_message=str(e),
            project_id=project_id,
            task_id=f'backfill:{project_id}'
        )


@app.route('/api/project/<project_id>/backfill_fulltext', methods=['POST'])
def api_project_backfill_fulltext(project_id):
    projects = load_projects()
    if project_id not in projects:
        return jsonify({'success': False, 'error': '项目不存在'})

    thread = threading.Thread(target=run_project_backfill, args=(project_id,))
    thread.daemon = True
    thread.start()
    return jsonify({'success': True, 'message': '已开始补生成缺失全文解读'})


@app.route('/api/continue_search', methods=['POST'])
def api_continue_search():
    """继续搜索 - 追加到项目"""
    global search_status_store

    project_id = request.json.get('project_id', '')
    keyword = request.json.get('keyword', '').strip()

    if not project_id:
        return jsonify({'success': False, 'error': '参数错误'})

    projects = load_projects()
    if project_id not in projects:
        return jsonify({'success': False, 'error': '项目不存在'})

    # 获取项目原始关键词
    original_keyword = projects[project_id].get('name', '')

    # 获取搜索数量配置
    config = get_api_config()
    search_count = config.get('search_count', 15)

    # 获取或生成搜索关键词
    if keyword:
        # 用户输入了新关键词，翻译它
        translation = translate_keyword(keyword)
        new_keywords = translation['expanded'][:3]
    else:
        # 没有输入，自动扩展搜索范围
        existing = projects[project_id].get('search_keywords', [])
        # 基于现有关键词扩展
        new_keywords = []
        for kw in existing[:2]:
            new_keywords.append(kw + ' survey review')
            new_keywords.append(kw + ' deep learning')
        new_keywords = list(set(new_keywords))[:4]

    if not new_keywords:
        return jsonify({'success': False, 'error': '无法生成搜索关键词'})

    # 追加到项目
    projects[project_id]['search_keywords'].extend(new_keywords)
    projects[project_id]['status'] = 'searching'
    save_projects(projects)
    save_project_meta(project_id, projects[project_id])

    # 更新搜索状态
    update_search_status(
        searching=True,
        progress=5,
        status='正在扩展搜索...',
        reset_logs=True,
        project_id=project_id,
        original_keyword=original_keyword
    )

    import subprocess
    import sys
    import threading

    def run_search():
        global search_status_store
        project_dir = PROJECTS_DIR / project_id
        total = len(new_keywords)

        for idx, kw in enumerate(new_keywords):
            try:
                update_search_status(
                    status=f'搜索 ({idx+1}/{total}): {kw[:25]}...',
                    progress=5 + int((idx / total) * 90),
                    log_message=f'第 {idx+1}/{total} 步：扩展搜索 {kw}'
                )

                # 切换到DATA_DIR执行搜索
                original_cwd = os.getcwd()
                os.chdir(DATA_DIR)

                try:
                    # 传递原始中文关键词
                    cmd = [
                        sys.executable,
                        str(DATA_DIR / 'paper_search.py'),
                        kw,
                        str(search_count),
                        f'--original={original_keyword}',
                        f'--project-dir={project_dir}'
                    ]
                    result = subprocess.run(
                        cmd,
                        capture_output=True, text=True, timeout=300
                    )
                    if result.stderr:
                        print(f"搜索错误 [{kw}]: {result.stderr[:200]}")
                finally:
                    os.chdir(original_cwd)

                # 文件现在直接生成到项目目录，无需再从根目录搬运

            except Exception as e:
                print(f"搜索错误 [{kw}]: {e}")

        # 更新状态和论文计数
        update_project_registry(project_id, status='completed')

        update_search_status(
            searching=False,
            progress=100,
            status='搜索完成',
            log_message='扩展搜索完成，正在刷新结果'
        )

    thread = threading.Thread(target=run_search)
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'message': f'正在搜索 {len(new_keywords)} 个关键词...'})


# 英文关键词翻译为中文
ENGLISH_TO_CHINESE = {
    'conversion rate prediction': '转化率预测',
    'user behavior modeling': '用户行为建模',
    'recommendation algorithm': '推荐算法',
    'click prediction deep learning': '点击预测深度学习',
    'collaborative filtering': '协同过滤',
    'content-based recommendation': '内容推荐',
    'deep recommendation': '深度推荐',
    'personalization': '个性化',
    'e-commerce user behavior': '电商用户行为',
    'online shopping prediction': '在线购物预测',
    'product recommendation': '商品推荐',
    'customer churn prediction': '客户流失预测',
    'survey': '综述',
    'review': '综述',
    'deep learning': '深度学习',
    'neural network': '神经网络',
    'prediction': '预测',
    'optimization': '优化',
    'ctr prediction': 'CTR预测',
    'attention mechanism': '注意力机制',
    'transformer': 'Transformer',
    'knowledge graph': '知识图谱',
    'graph neural network': '图神经网络',
}


@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """获取或保存设置"""
    if request.method == 'GET':
        settings = load_settings()
        # 不返回完整的API key
        if settings.get('api_key'):
            settings['api_key'] = settings['api_key'][:8] + '...' if len(settings['api_key']) > 8 else '***'
        return jsonify(settings)

    elif request.method == 'POST':
        data = request.json
        settings = load_settings()

        # 更新设置（如果提供了新的完整API key才更新）
        if data.get('api_key') and not data['api_key'].endswith('...'):
            settings['api_key'] = data['api_key']
        if data.get('api_url'):
            settings['api_url'] = data['api_url']
        if data.get('model'):
            settings['model'] = data['model']
        if data.get('search_count'):
            settings['search_count'] = int(data['search_count'])

        save_settings(settings)
        return jsonify({'success': True, 'message': '设置已保存'})


@app.route('/api/suggest_keywords/<project_id>')
def api_suggest_keywords(project_id):
    """推荐继续搜索的关键词（返回中文）"""
    projects = load_projects()
    if project_id not in projects:
        return jsonify({'keywords': []})

    project = projects[project_id]
    existing = project.get('search_keywords', [])
    name = project.get('name', '')

    # 英文关键词列表
    english_suggestions = []

    if '点击率' in name or 'CTR' in str(existing).upper():
        english_suggestions.extend([
            'conversion rate prediction',
            'user behavior modeling',
            'recommendation algorithm',
            'click prediction deep learning'
        ])

    if '推荐' in name or 'recommendation' in str(existing).lower():
        english_suggestions.extend([
            'collaborative filtering',
            'content-based recommendation',
            'deep recommendation',
            'personalization'
        ])

    if '电商' in name or 'e-commerce' in str(existing).lower():
        english_suggestions.extend([
            'e-commerce user behavior',
            'online shopping prediction',
            'product recommendation',
            'customer churn prediction'
        ])

    # 通用扩展
    expansions = ['survey', 'review', 'deep learning', 'optimization']
    for kw in existing[:2]:
        for exp in expansions[:2]:
            english_suggestions.append(f"{kw} {exp}")

    # 去重
    english_suggestions = list(set(english_suggestions))[:6]

    # 转换为中文
    chinese_suggestions = []
    for kw in english_suggestions:
        chinese_kw = ENGLISH_TO_CHINESE.get(kw, kw)
        # 如果没有精确匹配，尝试部分匹配
        if chinese_kw == kw:
            for eng, chn in ENGLISH_TO_CHINESE.items():
                if eng in kw.lower():
                    chinese_kw = kw.replace(eng, chn)
                    break
        chinese_suggestions.append(chinese_kw)

    return jsonify({'keywords': chinese_suggestions})


@app.route('/download_project/<project_id>')
def download_project(project_id):
    """下载项目 - 打包为ZIP"""
    projects = load_projects()
    if project_id not in projects:
        return "项目不存在", 404

    project = projects[project_id]
    project_dir = PROJECTS_DIR / project_id

    import io
    import zipfile

    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('项目信息.txt', f"""项目名称: {project['name']}
创建时间: {project['created']}
论文总数: {project['total_papers']}
顶会论文: {project['top_papers']}
""")

        for f in sorted(project_dir.iterdir(), key=lambda item: item.name):
            if f.name == 'meta.json':
                zf.write(f, f.name)
                continue

            if f.is_file() and f.suffix in {'.md', '.json'} and f.name.startswith('papers_'):
                zf.write(f, f'原始数据/{f.name}')

        paper_notes_dir = project_dir / 'paper_notes'
        if paper_notes_dir.exists():
            for note_file in sorted(paper_notes_dir.rglob('*')):
                if note_file.is_file():
                    arcname = note_file.relative_to(project_dir).as_posix()
                    zf.write(note_file, arcname)

    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{project["name"]}_论文汇总.zip'
    )


@app.route('/api/project_summary/<project_id>')
def api_project_summary(project_id):
    """获取项目汇总 - 大表格格式"""
    projects = load_projects()
    if project_id not in projects:
        return jsonify({'error': '项目不存在'}), 404

    project = projects[project_id]
    papers = get_project_papers(project_id)
    original_keyword = project.get('name', '')

    def esc(value):
        return html.escape(str(value if value is not None else '--'))

    def format_multiline_text(value):
        text = esc(value)
        return text.replace('\n', '<br>') if text else ''

    top_count = sum(1 for p in papers if is_top_venue(p.get('venue', ''))[0])

    html_content = f'''
    <div class="summary-stats">
        <span>共 <strong>{len(papers)}</strong> 篇论文</span>
        <span>顶会论文 <strong>{top_count}</strong> 篇</span>
        <span>关键词: <strong>{esc(original_keyword)}</strong></span>
    </div>
    <table class="summary-table-xlarge">
        <thead>
            <tr>
                <th style="width:50px">排名</th>
                <th style="width:80px">评分</th>
                <th style="width:320px">论文标题</th>
                <th style="width:120px">作者</th>
                <th style="width:60px">年份</th>
                <th style="width:200px">会议/期刊</th>
                <th style="width:120px">相关性</th>
                <th style="width:800px">核心观点与应用</th>
            </tr>
        </thead>
        <tbody>
    '''

    for i, p in enumerate(papers, 1):
        is_top, venue_name = is_top_venue(p.get('venue', ''))
        venue_category = get_venue_category(p.get('venue', ''))

        if is_top:
            top_html = f'<span class="badge-top">{esc(venue_category or venue_name)}</span>'
        else:
            top_html = '--'

        score = str(p.get('score', '--'))
        score_class = 'score-high' if 'A' in score or 'S' in score else ''

        summary = p.get('summary', '') or p.get('chinese_explanation', '')
        abstract = p.get('abstract', '')
        if abstract:
            abstract = re.sub(r'<[^>]+>', '', str(abstract)).strip()

        applications = p.get('applications', '')
        suggestions = p.get('suggestions', '')

        if summary:
            detail_content = format_multiline_text(summary)
        elif abstract:
            abstract_preview = abstract[:400] + '...' if len(abstract) > 400 else abstract
            detail_content = f'<span style="color:#60a5fa;">【摘要】</span>{format_multiline_text(abstract_preview)}'
        else:
            detail_content = '<span style="color:#94a3b8;">暂无概述</span>'

        if applications:
            detail_content += f'<br><br><span style="color:#10b981;">📌 <b>应用场景:</b></span> {format_multiline_text(applications)}'

        if suggestions:
            detail_content += f'<br><span style="color:#f59e0b;">💡 <b>阅读建议:</b></span> {format_multiline_text(suggestions)}'

        if p.get('has_fulltext_markdown'):
            title_url = get_project_paper_note_url(project_id, p)
            if title_url:
                title_html = f'<a href="{esc(title_url)}" target="_blank" rel="noopener noreferrer">{esc(p.get("title", "--"))}</a>'
            else:
                title_html = f'{esc(p.get("title", "--"))}<div class="note-unavailable">全文解读文件缺失</div>'
        else:
            title_html = f'{esc(p.get("title", "--"))}<div class="note-unavailable">未生成单篇全文解读</div>'

        relevance_stars = '★★★★★' if is_top else ('★★★★☆' if 'A' in score else '★★★☆☆')

        venue = str(p.get('venue', '--'))[:25]
        if venue_category:
            venue_display = f'{esc(venue)}<br><span style="color:#f59e0b;font-size:11px;">{esc(venue_category)}</span>'
        else:
            venue_display = esc(venue)

        html_content += f'''
            <tr>
                <td class="rank">{i}</td>
                <td><span class="score-badge {score_class}">{esc(score)}</span></td>
                <td class="title-cell">{title_html}</td>
                <td>{esc(str(p.get('authors', '--'))[:18])}</td>
                <td>{esc(p.get('year', '--'))}</td>
                <td>{venue_display}<br>{top_html}</td>
                <td class="relevance-cell"><span class="relevance-stars">{relevance_stars}</span></td>
                <td class="summary-cell" style="font-size:15px;line-height:1.8;">{detail_content}</td>
            </tr>
        '''

    html_content += '</tbody></table>'

    return jsonify({
        'name': project['name'],
        'total': len(papers),
        'html': html_content
    })


@app.route('/project/<project_id>/paper_note/<slug>')
def project_paper_note(project_id, slug):
    """渲染项目内单篇全文解读 Markdown"""
    projects = load_projects()
    if project_id not in projects:
        abort(404)

    project_dir = PROJECTS_DIR / project_id
    note_path = project_dir / 'paper_notes' / f'{slug}.md'
    if not note_path.exists() or note_path.suffix.lower() != '.md':
        abort(404)

    with open(note_path, 'r', encoding='utf-8') as f:
        content = f.read()

    rendered_html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
    title = content.splitlines()[0].lstrip('# ').strip() if content.strip() else '单篇全文解读'

    return render_template(
        'markdown_view.html',
        title=title,
        content=rendered_html,
        project_id=project_id,
        project_name=projects[project_id].get('name', ''),
        is_project_note=True
    )


@app.route('/project/<project_id>/paper_note_file/<path:filename>')
def project_paper_note_file(project_id, filename):
    """按文件名兜底访问项目内单篇全文解读 Markdown"""
    projects = load_projects()
    if project_id not in projects:
        abort(404)

    safe_filename = Path(filename).name
    note_path = PROJECTS_DIR / project_id / 'paper_notes' / safe_filename
    if not note_path.exists() or note_path.suffix.lower() != '.md':
        abort(404)

    return send_file(note_path)


@app.route('/')
def index():
    """主页 - 显示项目列表"""
    projects = load_projects()
    registry_changed = False

    # 更新每个项目的论文统计
    for pid in list(projects.keys()):
        project = projects[pid]
        synced = update_project_registry(pid, status=project.get('status'), persist=False)
        if synced and (
            project.get('total_papers') != synced.get('total_papers')
            or project.get('top_papers') != synced.get('top_papers')
            or project.get('status') != synced.get('status')
        ):
            projects[pid] = synced
            registry_changed = True

    if registry_changed:
        save_projects(projects)
        for pid, project in projects.items():
            save_project_meta(pid, project)

    total_papers = sum(p.get('total_papers', 0) for p in projects.values())
    total_top = sum(p.get('top_papers', 0) for p in projects.values())

    return render_template('index.html',
                          projects=projects,
                          total_papers=total_papers,
                          total_top=total_top)


@app.route('/project/<project_id>/paper/<filename>/<int:index>')
def paper_detail(project_id, filename, index):
    """项目内论文详情页"""
    safe_filename = Path(filename).name
    filepath = PROJECTS_DIR / project_id / safe_filename
    if not filepath.exists() or filepath.suffix.lower() != '.md':
        return "论文不存在", 404

    data = parse_markdown_file(str(filepath))

    if index < 0 or index >= len(data['papers']):
        return "论文不存在", 404

    paper = data['papers'][index]
    paper['fulltext_failure_reason_display'] = format_failure_reason(paper.get('fulltext_failure_reason', ''))
    failure_details = paper.get('fulltext_failure_details') or []
    paper['fulltext_last_attempt'] = summarize_failure_detail(failure_details[0]) if failure_details else paper.get('fulltext_last_attempt', '')

    full_content = ''
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    detail_pattern = rf'### {index + 1}\.\s*\[\[{re.escape(paper["title"])}\]\](.+?)(?=\n### \d+\.|\n##|$)'
    detail_match = re.search(detail_pattern, content, re.DOTALL)
    if detail_match:
        full_content = detail_match.group(0)

    return render_template('paper_detail.html',
                          paper=paper,
                          keyword=data['keyword'],
                          date=data['date'],
                          full_detail=full_content,
                          project_id=project_id)


@app.route('/search', methods=['GET', 'POST'])
def search():
    """搜索页面"""
    keyword = request.args.get('keyword', '').strip()

    files = get_all_markdown_files()
    results = []

    for f in files:
        data = f['data']
        if keyword:
            if keyword.lower() in data['keyword'].lower():
                results.append(f)
        else:
            results.append(f)

    return render_template('search.html',
                          keyword=keyword,
                          results=results,
                          total_files=len(results))


@app.route('/api/papers')
def api_papers():
    """API - 获取所有论文数据"""
    files = get_all_markdown_files()
    all_papers = []

    for f in files:
        data = f['data']
        for paper in data['papers']:
            all_papers.append({
                'keyword': data['keyword'],
                'date': data['date'],
                'filename': f['filename'],
                'project_id': f.get('project_id'),
                'title': paper.get('title', ''),
                'authors': paper.get('authors', ''),
                'year': paper.get('year', ''),
                'venue': paper.get('venue', ''),
                'is_top': is_top_venue(paper.get('venue', ''))[0],
                'score': paper.get('score', ''),
                'summary': paper.get('summary', ''),
                'chinese_detail': paper.get('chinese_detail', ''),
                'applications': paper.get('applications', ''),
                'suggestions': paper.get('suggestions', ''),
                'link': paper.get('link', '')
            })

    return jsonify({
        'total': len(all_papers),
        'papers': all_papers
    })


@app.route('/export', methods=['POST'])
def export_papers():
    """批量导出论文为Markdown"""
    selected_papers = request.json.get('papers', [])

    if not selected_papers:
        return jsonify({'error': '没有选择论文'}), 400

    exported = []
    for item in selected_papers:
        project_id = item.get('project_id')
        filename = Path(item.get('filename', '')).name
        if not project_id or not filename:
            continue

        filepath = PROJECTS_DIR / project_id / filename
        if not filepath.exists():
            continue

        data = parse_markdown_file(str(filepath))
        index = item.get('index', -1)
        if not isinstance(index, int) or not (0 <= index < len(data['papers'])):
            continue

        paper = data['papers'][index]

        md_content = f"""# {paper['title']}

## 基本信息

- **关键词**: {data['keyword']}
- **搜索日期**: {data['date']}
- **年份**: {paper.get('year', 'Unknown')}
- **会议/期刊**: {paper.get('venue', 'Unknown')}
- **作者**: {paper.get('authors', 'Unknown')}
- **评分**: {paper.get('score', 'Unknown')}
- **引用**: {paper.get('citations', 'Unknown')}

---

## 核心概述

{paper.get('summary', '暂无概述')}

---

## 中文详细解读

{paper.get('chinese_detail', '暂无详细解读')}

---

## 相关应用场景

基于搜索关键词「{data['keyword']}」的实际运用：

{paper.get('applications', '暂无应用场景信息')}

---

## 阅读建议

{paper.get('suggestions', '暂无阅读建议')}

---

## 论文链接

{paper.get('link', '暂无链接')}

---
*导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        exported.append({
            'filename': f"paper_{index}_{data['keyword'].replace(' ', '_')}.md",
            'content': md_content,
            'title': paper['title']
        })

    return jsonify({'exported': exported})


@app.route('/timeline/<keyword>')
def timeline_view(keyword):
    """时间线视图 - 按年份展示论文"""
    files = get_all_markdown_files()

    all_papers = []
    for f in files:
        data = f['data']
        if keyword.lower() in data['keyword'].lower():
            for idx, paper in enumerate(data['papers']):
                timeline_paper = dict(paper)
                timeline_paper['filename'] = f['filename']
                timeline_paper['project_id'] = f.get('project_id')
                timeline_paper['paper_index'] = idx
                timeline_paper['search_keyword'] = data['keyword']
                all_papers.append(timeline_paper)

    timeline = {}
    for paper in all_papers:
        year = paper.get('year', 'Unknown')
        if year not in timeline:
            timeline[year] = []
        timeline[year].append(paper)

    sorted_years = sorted([y for y in timeline.keys() if y != 'Unknown'], reverse=True)
    if 'Unknown' in timeline:
        sorted_years.append('Unknown')

    return render_template('timeline.html',
                          keyword=keyword,
                          timeline=timeline,
                          sorted_years=sorted_years,
                          total_papers=len(all_papers))


# 全局搜索状态存储
search_status_store = {
    'searching': False,
    'progress': 0,
    'status': '',
    'task_id': None,
    'original_keyword': '',  # 原始中文关键词
    'logs': []
}


def append_search_log(message):
    """追加搜索日志，仅保留最近5条"""
    if not message:
        return
    logs = search_status_store.setdefault('logs', [])
    logs.append(message)
    search_status_store['logs'] = logs[-5:]



def update_search_status(status=None, progress=None, searching=None, reset_logs=False, log_message=None, logs=None, **extra_fields):
    """统一更新搜索状态，并维护最近日志"""
    if reset_logs:
        search_status_store['logs'] = []

    if searching is not None:
        search_status_store['searching'] = searching
    if progress is not None:
        search_status_store['progress'] = progress
    if status is not None:
        search_status_store['status'] = status

    for key, value in extra_fields.items():
        search_status_store[key] = value

    if logs is not None:
        search_status_store['logs'] = list(logs)[-5:]

    message = log_message if log_message is not None else status
    if logs is None:
        append_search_log(message)


@app.route('/api/search_status')
def api_search_status():
    """获取搜索状态"""
    # 确保状态一致性：如果progress=100但searching仍为True，强制修正
    if search_status_store['progress'] >= 100 and search_status_store['searching']:
        search_status_store['searching'] = False
    return jsonify(search_status_store)


@app.route('/api/search_status/update', methods=['POST'])
def api_update_search_status():
    """更新搜索状态（内部调用）"""
    global search_status_store
    data = request.json
    update_search_status(
        searching=data.get('searching', False),
        progress=data.get('progress', 0),
        status=data.get('status', ''),
        log_message=data.get('log_message'),
        logs=data.get('logs'),
        reset_logs=data.get('reset_logs', False),
        task_id=data.get('task_id', search_status_store.get('task_id')),
        original_keyword=data.get('original_keyword', search_status_store.get('original_keyword', '')),
        project_id=data.get('project_id', search_status_store.get('project_id'))
    )
    return jsonify({'success': True})


if __name__ == '__main__':
    # 确保templates目录存在
    templates_dir = os.path.join(DATA_DIR, 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        print(f"创建templates目录: {templates_dir}")

    print("=" * 60)
    print("论文搜索与展示系统")
    print("=" * 60)
    print(f"数据目录: {DATA_DIR}")
    print(f"Markdown文件: {len(get_all_markdown_files())} 个")
    print("=" * 60)
    print("启动Web服务器...")
    print(f"访问地址: http://127.0.0.1:{APP_PORT}")
    print(f"监听地址: http://{APP_HOST}:{APP_PORT}")
    print("=" * 60)

    app.run(host=APP_HOST, port=APP_PORT, debug=False)
