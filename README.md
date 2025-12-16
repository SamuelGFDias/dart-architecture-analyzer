# 📊 Dart Architecture Analyzer

Static analysis tool for Flutter/Dart projects that extracts code metrics, complexity, and dependency graphs.

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Features

- 🔍 **Code Metrics**: LOC, Cyclomatic Complexity, Cognitive Complexity
- 🔥 **Hot Spots Detection**: Identifies critical files (high coupling × complexity)
- 🏥 **Code Health Score**: Overall project health assessment (0-100)
- 📊 **Dependency Analysis**: Import/export resolution with barrel file support
- 🤖 **Machine Readable**: JSON output optimized for AI/automation
- 🎨 **jq Integration**: Automatic colorization and filtering support

## 🚀 Quick Start

### Installation

#### Global Installation (Recommended)

**Windows PowerShell:**
```powershell
git clone https://github.com/YOUR_USERNAME/dart-architecture-analyzer.git
cd dart-architecture-analyzer
.\install.ps1
```

**Linux/Mac:**
```bash
git clone https://github.com/YOUR_USERNAME/dart-architecture-analyzer.git
cd dart-architecture-analyzer
chmod +x install.sh
./install.sh
```

After installation, use `dart-analyse` command globally:
```bash
dart-analyse --help
```

#### Manual Usage (Without Installation)

```bash
python analyse.py --help
```

### Basic Usage

```bash
# Full project analysis (saves RELATORIO_ARQUITETURA.json)
dart-analyse

# Markdown report
dart-analyse --format md

# Output to terminal
dart-analyse --output stdout

# Analyze specific files
dart-analyse --files lib/main.dart lib/core/utils/helpers.dart
```

## 🎯 Advanced Usage with jq

The tool automatically detects piped output and sends pure JSON for filtering:

```bash
# Summary metrics
dart-analyse --output stdout | jq '.summary_kpis'

# Code health score
dart-analyse --output stdout | jq '.code_health.health_score'

# Top 5 hotspots
dart-analyse --output stdout | jq '.hotspots_top_10[0:5]'

# Files with high complexity
dart-analyse --output stdout | jq '.files_inventory[] | select(.metrics.complexity > 50)'

# Critical hotspots (risk_score > 1000)
dart-analyse --output stdout | jq '.hotspots_top_10[] | select(.risk_score > 1000) | {path, risk_score}'

# Custom transformation
dart-analyse --output stdout | jq '[.files_inventory[] | {file: .path, loc: .metrics.loc, complexity: .metrics.complexity}]'

# Top 5 most complex files
dart-analyse --output stdout | jq '[.files_inventory | sort_by(.metrics.complexity) | reverse | .[0:5][] | {path, complexity: .metrics.complexity, loc: .metrics.loc}]'
```

## 📊 JSON Output Structure

```json
{
  "meta": {
    "project": "project_name",
    "analysis_date": "2025-12-16T16:00:00",
    "generator": "Static Dart Analyzer v6.0",
    "scope": "Full Project"
  },
  "summary_kpis": {
    "reported_files": 384,
    "total_loc": 37841,
    "avg_complexity": 13.65,
    "avg_cognitive_complexity": 11.86
  },
  "code_health": {
    "high_complexity_files": 26,
    "large_files_count": 27,
    "highly_coupled_files": 47,
    "health_score": 0
  },
  "hotspots_top_10": [...],
  "files_inventory": [...]
}
```

## 🔍 Metrics Explained

### Cyclomatic Complexity
Counts control structures: `if`, `else`, `for`, `while`, `case`, `catch`, logical operators (`&&`, `||`, `??`), ternary operators (`?`).

### Cognitive Complexity
Considers nesting depth - penalizes structures within structures for readability impact.

### Code Health Score
- **100**: Excellent code quality
- **0**: Critical issues
- Penalties:
  - Files with complexity > 50: -10 points each
  - Files with > 300 LOC: -5 points each
  - Files with > 10 references: -3 points each

### Risk Score (Hot Spots)
```
Risk Score = Coupling × Complexity
```
Identifies critical files that are both complex AND heavily used.

## 🛠️ Parameters

| Parameter | Values | Default | Description |
|-----------|---------|---------|-------------|
| `--format` | `json`, `md` | `json` | Output format |
| `--files` | `FILE [FILE ...]` | all | Specific files to analyze |
| `--output` | `file`, `stdout` | `file` | Output destination |

## 💡 Use Cases

### CI/CD - Quality Gate

```bash
# Fail build if health_score < 50
SCORE=$(dart-analyse --output stdout | jq '.code_health.health_score')
if [ $SCORE -lt 50 ]; then
  echo "❌ Code health too low: $SCORE"
  exit 1
fi
```

### Git Hooks - Analyze Changes

```bash
# Analyze only modified files
CHANGED_FILES=$(git diff --name-only HEAD~1 | grep '\.dart$')
dart-analyse --files $CHANGED_FILES --output stdout | jq '.summary_kpis'
```

### Refactoring - Identify Priorities

```bash
# List critical files for refactoring
dart-analyse --output stdout | jq '.hotspots_top_10[] | select(.risk_score > 1000)'
```

### Monitoring - Track Trends

```bash
# Export daily metrics
DATE=$(date +%Y-%m-%d)
dart-analyse --format json
cp RELATORIO_ARQUITETURA.json "metrics/metrics-$DATE.json"
```

## 📋 Requirements

- **Python 3.7+**
- **jq** (optional, for colored terminal output and filtering)
  - Windows: `choco install jq`
  - Mac: `brew install jq`
  - Linux: `apt install jq` or `yum install jq`

## 🔄 Update

To update after modifying `analyse.py`:

**Windows:**
```powershell
.\install.ps1
```

**Linux/Mac:**
```bash
./install.sh
```

## 🗑️ Uninstall

**Windows:**
```powershell
.\uninstall.ps1
```

**Linux/Mac:**
```bash
./uninstall.sh
```

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Bug Reports

If you find a bug, please open an issue with:
- OS and Python version
- Command used
- Expected vs actual behavior
- Minimal reproduction example

## ⭐ Star History

If this tool helps your Flutter/Dart development workflow, consider giving it a star! ⭐
