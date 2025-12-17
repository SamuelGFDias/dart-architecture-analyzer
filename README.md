# 📊 Dart Architecture Analyzer

Static analysis tool for Flutter/Dart projects that extracts code metrics, complexity, and dependency graphs.

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Features

### Core Metrics
- 🔍 **Code Metrics**: LOC, Cyclomatic Complexity, Cognitive Complexity
- 🔥 **Hot Spots Detection**: Identifies critical files (high coupling × complexity)
- 📊 **Dependency Analysis**: Import/export resolution with barrel file support

### Advanced Code Smells Detection
- 🏛️ **God Classes**: Detects oversized files with too many responsibilities
- 💀 **Dead Code**: Identifies unused files with no references
- 🔁 **Circular Dependencies**: Finds dependency cycles in your codebase
- 📋 **Duplicate Private Members**: Detects repeated private methods/classes across files
- 🏗️ **Layer Violations**: Identifies architecture boundary violations (e.g., UI → Data)

### Actionable Insights
- 🎯 **Prioritized Recommendations**: Ranked refactoring suggestions with effort estimates
- 💰 **Technical Debt Score**: Quantified debt based on all detected issues
- 🏥 **Code Health Score**: Overall project health assessment (0-100)
- 🤖 **AI-Optimized Output**: JSON format designed for AI agents and automation
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
    "analysis_date": "2025-12-17T10:00:00",
    "generator": "Static Dart Analyzer v2.0",
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
    "god_classes_count": 8,
    "dead_code_candidates": 15,
    "layer_violations_count": 12,
    "circular_dependencies_count": 3,
    "technical_debt_score": 892,
    "health_score": 11
  },
  "code_smells": {
    "god_classes": [...],
    "dead_code_candidates": [...],
    "duplicate_private_members": [...],
    "layer_violations": [...],
    "circular_dependencies": [...]
  },
  "actionable_recommendations": [
    {
      "priority": "CRITICAL",
      "category": "Architecture",
      "issue": "Circular Dependencies Detected",
      "impact": "Prevents proper modularization and testing",
      "affected_count": 3,
      "effort": "High",
      "action": "Break cycles by introducing interfaces/abstractions..."
    }
  ],
  "hotspots_top_10": [...],
  "files_inventory": [...]
}
```

## 🔍 Indicators Explained

### Core Metrics

#### Cyclomatic Complexity
Counts control structures: `if`, `else`, `for`, `while`, `case`, `catch`, logical operators (`&&`, `||`, `??`), ternary operators (`?`).

#### Cognitive Complexity
Considers nesting depth - penalizes structures within structures for readability impact.

### Code Smells

#### God Classes
Files flagged when they exceed thresholds:
- **LOC > 500**: File is too large
- **Classes > 10**: Too many classes in one file
- **Methods > 30**: Too many responsibilities
- **Complexity > 100**: Overly complex logic

#### Dead Code
Files with zero references that are not entry points (main.dart, firebase_options.dart, etc.).

#### Duplicate Private Members
Private methods/classes (`_name`) appearing in multiple files, suggesting need for shared utilities.

#### Layer Violations
Architecture boundary violations, such as:
- UI layer directly importing data sources/repositories
- Presentation importing infrastructure

#### Circular Dependencies
Dependency cycles between files that prevent proper modularization.

### Health Scores

#### Technical Debt Score
Weighted sum of all issues:
- God Classes: 50 points each
- Layer Violations: 30 points each
- High Complexity Files: 15 points each
- High Coupling: 10 points each
- Dead Code: 10 points each
- Duplicates: 5 points each

#### Code Health Score
```
Health Score = max(0, 100 - (Technical Debt Score / 10))
```
- **90-100**: Excellent
- **70-89**: Good
- **50-69**: Needs attention
- **30-49**: Poor
- **0-29**: Critical

#### Risk Score (Hot Spots)
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
# Get prioritized refactoring recommendations
dart-analyse --output stdout | jq '.actionable_recommendations'

# Find all God Classes
dart-analyse --output stdout | jq '.code_smells.god_classes'

# List circular dependencies
dart-analyse --output stdout | jq '.code_smells.circular_dependencies'

# Check for layer violations
dart-analyse --output stdout | jq '.code_smells.layer_violations'

# Find duplicate private members (top candidates for extraction)
dart-analyse --output stdout | jq '.code_smells.duplicate_private_members[0:10]'

# List dead code for cleanup
dart-analyse --output stdout | jq '.code_smells.dead_code_candidates'

# Check technical debt score
dart-analyse --output stdout | jq '.code_health.technical_debt_score'
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
