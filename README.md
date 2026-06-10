# Kronos 证券技术分析师（中短线）

基于 Kronos K线大模型 + 6-Agent 多维分析的 A 股技术面分析仪表盘。

## 功能

- **Kronos 预测**：4段预测（10/20/60/120日），基于 AAAI 2026 顶会 Kronos 模型
- **6-Agent 多维分析**：
  - 高阶技术(SMC+ICT+VP)：订单块、FVG、成交量分布
  - 基础技术(MA+RSI+MACD)：经典技术指标
  - 资金面：主力资金流向
  - 情绪面：市场情绪打分
  - 基本面：ROE/PE/营收增长
  - 行业面：板块景气度
- **全市场搜索**：5281 只 A 股，支持中文名称/代码搜索
- **真实K线**：腾讯免费行情数据源

## 快速开始

### 方式一：下载便携版（推荐）
1. 下载最新 `TradingAgent_便携版.zip` 从 [Releases](../../releases)
2. 解压到任意目录
3. 双击 `启动.bat`
4. 浏览器自动打开 `http://localhost:3456`

### 方式二：从源码运行
```bash
pip install numpy pandas
python server.py
# 打开 http://localhost:3456
```

### 方式三：打包为 EXE
```bash
pip install pyinstaller numpy pandas
pyinstaller agent.spec --distpath . --workpath ./build --noconfirm
```

## 数据源

- K线数据：腾讯免费行情（web.ifzq.gtimg.cn）
- 全市场股票列表：内置 5281 只 A 股
- 备选数据：Tushare（需 token，在根目录放 `tushare_token.txt`）

## 模型权重

Kronos 模型权重需单独下载：
```bash
pip install huggingface_hub
huggingface-cli download NeoQuasar/Kronos-small --local-dir kronos_weights/models--NeoQuasar--Kronos-small
huggingface-cli download NeoQuasar/Kronos-Tokenizer-base --local-dir kronos_weights/models--NeoQuasar--Kronos-Tokenizer-base
```

## 项目结构

```
├── server.py              # HTTP 服务器入口
├── index.html             # 前端仪表盘
├── bridge_search.py       # 股票搜索（5281只A股）
├── bridge_chart.py        # K线数据 + Kronos 预测
├── bridge_agent_v4.py     # 6-Agent 多维分析引擎
├── kronos_local/          # Kronos 模型代码
├── kronos_weights/        # 模型权重（需下载）
└── agent.spec             # PyInstaller 打包配置
```

## 技术栈

- Python 3.10+
- Kronos (Hierarchical Tokenizer K-line LLM)
- NumPy / Pandas
- 纯 Python HTTP Server (无框架依赖)

## License

MIT
