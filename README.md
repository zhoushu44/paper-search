# 论文搜索与验证系统

## 功能

- 🔍 多源搜索论文（Google Scholar、Semantic Scholar、CrossRef）
- 🏆 自动识别顶会/顶级期刊
- 📝 生成论文简介和中文详细解释
- ✅ AI验证论文真实性
- 📊 导出Markdown表格

## 安装

```bash
pip install requests beautifulsoup4
```

可选（本地LLM）：
```bash
# 1. 安装Ollama: https://ollama.com
# 2. 拉取模型
ollama pull qwen2:7b
# 或
ollama pull llama3
```

## 使用方法

### 命令行模式

```bash
python paper_search.py "transformer attention"
python paper_search.py "large language model" 100
```

### 交互模式

```bash
python paper_search.py
```

## API说明

| API | 状态 | 限制 |
|-----|------|------|
| SerpAPI (Google Scholar) | ✓ 已配置 | 100次/月（免费） |
| Semantic Scholar | 免费 | 100次/5分钟 |
| CrossRef | 免费 | 无限制 |
| Ollama | 可选 | 本地运行 |

## 输出格式

文件：`papers_关键词.md`

包含：
- 汇总表格（所有论文）
- 顶会论文详情
- 论文简介
- 中文详细解释

## 顶会列表

- AI/ML: NeurIPS, ICML, ICLR, AAAI, IJCAI
- NLP: ACL, EMNLP, NAACL
- CV: CVPR, ICCV, ECCV
- 系统: OSDI, SOSP, NSDI, SIGCOMM
- 安全: IEEE S&P, CCS, USENIX Security
- 数据库: SIGMOD, VLDB, ICDE
- 等等...
