# 论文搜索与展示系统

基于 Flask 的论文搜索与项目管理工具。支持用中文关键词创建项目、自动扩展英文检索词、汇总论文结果，并在 `projects/` 下保存项目数据与单篇全文解读。

## 功能

- 多源搜索论文
- 自动识别顶会/顶级期刊
- 生成论文简介与中文解读
- 项目化管理搜索结果
- 导出项目 ZIP 与单篇 Markdown 解读
- Web 界面实时显示搜索进度

## 目录说明

- `app.py`：Flask Web 入口
- `paper_search.py`：论文搜索与生成脚本
- `projects/`：项目数据目录
- `projects.json`：项目索引
- `settings.json`：运行配置

新生成的数据以 `projects/` 为准；根目录 `papers_*.md/json` 与 `.meta_*.json` 不再作为推荐工作流。

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Web 应用

```bash
python app.py
```

默认监听：`0.0.0.0:5055`

浏览器访问：

- `http://127.0.0.1:5055`
- 或你的服务器 IP 对应的 `5055` 端口

### 3. 命令行模式

```bash
python paper_search.py "transformer attention"
python paper_search.py "large language model" 100
```

## 配置

应用优先读取 `settings.json` 中的配置；如果未设置，则回退到环境变量：

- `PAPER_SEARCH_API_KEY`
- `PAPER_SEARCH_API_BASE`
- `PAPER_SEARCH_MODEL`

## Docker 部署

### 拉取已发布镜像

```bash
docker pull zhoushu1/paper-search:latest
```

如果拉取时出现类似下面的错误：

```text
Error response from daemon: Get "https://registry-1.docker.io/v2/": net/http: request canceled while waiting for connection (Client.Timeout exceeded while awaiting headers)
```

这通常是本机到 Docker Hub 的网络连接超时，不是镜像名错误。可以优先检查：

- 本机网络是否能访问 `https://registry-1.docker.io`
- Docker Desktop / Docker daemon 是否正常联网
- 是否需要代理或镜像加速器
- 防火墙、公司网络或地区网络是否拦截 Docker Hub

### 本地构建镜像

```bash
docker build -t paper-search2 .
```

### 运行容器

```bash
docker run --rm -p 5055:5055 \
  -e PAPER_SEARCH_API_KEY=your_api_key \
  -e PAPER_SEARCH_API_BASE=https://your-api-base/v1 \
  -e PAPER_SEARCH_MODEL=gpt-5.4 \
  -v $(pwd)/projects:/app/projects \
  -v $(pwd)/projects.json:/app/projects.json \
  -v $(pwd)/settings.json:/app/settings.json \
  paper-search2
```

如果本地尚未创建 `projects.json` 或 `settings.json`，可以先创建空文件后再挂载。

## GitHub Actions

仓库已包含 `.github/workflows/docker.yml`，在以下场景触发：

- push 到 `master`
- 手动触发 `workflow_dispatch`

工作流会登录镜像仓库、构建镜像并推送 `latest` 和 `${GITHUB_SHA}` 两个 tag。

### 需要的 Secrets

- `DOCKER_HUB_USERNAME`
- `DOCKER_HUB_TOKEN`

### 可选的 Repository Variables

- `DOCKER_REGISTRY`：默认 `docker.io`
- `DOCKER_IMAGE_NAME`：默认使用 `${DOCKER_HUB_USERNAME}/paper-search`

## 说明

- 不要把运行产物提交到仓库根目录。
- `.gitignore` 已忽略缓存、调试文件、根目录论文导出产物和本地工具目录。
- 生产或容器环境请使用环境变量或挂载的 `settings.json` 提供 API 配置。
