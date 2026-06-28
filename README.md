# 钽铌矿计价计算器

钽矿 (Ta₂O₅) 和铌矿 (Nb₂O₅) 国际计价工具，支持实时汇率和增值税计算。

## 计价公式

```
国际到岸价 ($/吨) = 国际价格 ($/磅) × 2204.6226 × 品位(%)
国内税前价格 (¥/吨) = 国际到岸价 × 汇率
国内税后价格 (¥/吨) = 国内税前 × (1 + 增值税率)
含税吨度价格 (¥/吨度) = 国内税后 ÷ 品位(%)
```

## 部署方式

### 方式一：GitHub Pages（推荐，免费）

1. 将 `tantalum_calculator.html` 推送到 GitHub 仓库
2. 在仓库 Settings → Pages 中开启 GitHub Pages
3. 选择部署分支和目录（建议设为 `/ (root)` 或 `/docs`）

纯静态降级模式：无需任何后端，用户手动输入国际价格即可使用。

### 方式二：本地开发

```powershell
# 双击启动或命令行运行
启动计算器.bat

# 或手动启动
python price_server.py
# 浏览器打开 http://localhost:8765
```

### 方式三：Cloudflare Workers（有实时价格）

部署 `price_server.py` 逻辑到 Cloudflare Worker，修改 HTML 中的 API_ENDPOINTS 数组。

## 文件清单

| 文件 | 用途 |
|------|------|
| `tantalum_calculator.html` | 主页面，部署到 GitHub Pages |
| `price_server.py` | Python 本地后端 |
| `启动计算器.bat` | Windows 本地一键启动 |

## 矿链通系列

- 铜矿石套保计算器
- 铅锌矿计价计算器
- 锂辉石计价计算器
- **钽铌矿计价计算器** ← 本项目

---

矿链通1.0 - 佛山鑫善源
