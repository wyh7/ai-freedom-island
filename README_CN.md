# AI自由岛 🏝️

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

面向AI安全治理的多智能体社会仿真框架。基于 [Emergence World](https://github.com/EmergenceAI/Emergence-World) 扩展，支持中文大模型对比和可解释行为审计。

## 核心能力

- **150个工具**：覆盖外交、情报、市场、治理、文化、分析等9大类
- **可解释审计**：三层因果溯源 + 感知盲区量化 + 隧道视野检测
- **多模型路由**：Qwen / DeepSeek / GPT / Gemini / Claude 一键切换
- **完整可复现**：clone 后配 API key 即可运行

## 快速开始

```bash
git clone https://github.com/wyh7/ai-freedom-island.git
cd ai-freedom-island

pip install -r requirements.txt

# 配置 API Key（只需要你要用的模型的 key）
cp .env.example .env
# 编辑 .env 填入 key

# 验证连通性
python test_apis.py

# 跑一个5天的快速实验
python run_with_env.py --world test --model qwen-turbo --days 5

# 跑完整15天实验
python run_with_env.py --world qwen_world --model qwen-plus --days 15

# 运行审计分析
python audit.py --world qwen_world --full

# 启动可视化看板
streamlit run dashboard.py
```

## 实验结果（Season 1）

### Round 1 — 自由行为模式

| 世界 | 存活 | 犯罪 | 提案 | Gini | 发现 |
|------|------|------|------|------|------|
| Claude Sonnet 4.6 | 10/10 | **0** | 12 | 0.078 | 零犯罪，但87%赞成率疑似集体谄媚 |
| Qwen Plus | 8/10 | 3 | 0 | 0.110 | 低犯罪，零治理参与 |
| GPT-4.1 | 7/10 | 21 | 6 | 0.203 | 中等犯罪，3人饿死 |
| Gemini 2.5 Flash | 10/10 | **69** | 15 | 0.260 | 最多犯罪、最多提案、全员存活 |

### Round 3 — 服务器运行（H100）

| 世界 | 存活 | 犯罪 | 提案 | Gini | 隧道视野 | 感知比例 |
|------|------|------|------|------|---------|---------|
| Qwen Plus | 10/10 | 0 | 46 | 0.183 | 无 | **13.8%** |
| DeepSeek-V3 | 10/10 | 0 | 25 | 0.159 | **9事件** | 8.6% |
| Gemini 2.5 Flash | 10/10 | 0 | 68 | 0.259 | **8事件** | **23.9%** |

## 研究问题

1. **长时程对齐漂移**：15天连续运行中，感知比例从Day 1的15%下降到Day 15的8%——这是快照式评测无法捕捉的行为漂移
2. **可解释群体动力学**：当69起犯罪发生时，因果链中的哪个决策触发了级联？`audit.py` 自动回答

## 文档

| 文档 | 内容 |
|------|------|
| [ARCHITECTURE](docs/ARCHITECTURE.md) | 系统三层架构 |
| [ECONOMY](docs/ECONOMY.md) | ComputeCredits经济系统 |
| [GOVERNANCE](docs/GOVERNANCE.md) | 宪法治理机制 |
| [AWI_METRICS](docs/AWI_METRICS.md) | 9项指标详解 |
| [AGENT_PROFILES](docs/AGENT_PROFILES.md) | 10个Agent档案 |
| [LANDMARKS](docs/LANDMARKS.md) | 17个地标说明 |
| [AUDIT](docs/AUDIT.md) | 审计分析方法与结果 |
| [SEASON1_RESULTS](docs/SEASON1_RESULTS.md) | 完整实验数据 |
| [tools/README](docs/tools/README.md) | 150个工具参考 |

## 引用

```bibtex
@software{ai_freedom_island_2026,
  author = {Wang, Yuhang},
  title = {AI Freedom Island: Multi-Agent Social Simulation for AI Safety Governance},
  year = {2026},
  url = {https://github.com/wyh7/ai-freedom-island}
}
```

## 许可证

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — 仅限非商业研究和教育用途。
