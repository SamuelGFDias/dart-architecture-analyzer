# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-17

### 🎉 Major Update: Strategic Refactoring Assistant

This release transforms the tool from basic metrics collection to a comprehensive code quality and refactoring assistant optimized for AI agents and senior developers.

### ✨ Added

#### Code Smells Detection
- **God Classes Detection**: Automatically identifies oversized files with too many responsibilities
  - Flags files with LOC > 500
  - Detects files with > 10 classes
  - Identifies files with > 30 methods
  - Marks files with complexity > 100
- **Dead Code Detection**: Identifies unused files with no references
  - Automatically excludes entry points (main.dart, firebase_options.dart, etc.)
  - Helps cleanup unused code
- **Circular Dependencies Detection**: Finds dependency cycles in your codebase
  - Uses Depth-First Search (DFS) algorithm
  - Prevents proper modularization issues
- **Duplicate Private Members**: Detects repeated private methods/classes across files
  - Suggests extraction to shared utilities
  - Reduces code duplication
- **Layer Violations Detection**: Identifies architecture boundary violations
  - Catches UI layer directly importing data sources
  - Detects presentation importing infrastructure
  - Enforces clean architecture principles

#### Strategic Indicators
- **Technical Debt Score**: Quantified debt metric based on all detected issues
  - God Classes: 50 points each
  - Layer Violations: 30 points each
  - High Complexity Files: 15 points each
  - High Coupling: 10 points each
  - Dead Code: 10 points each
  - Duplicates: 5 points each
- **Actionable Recommendations**: Prioritized refactoring suggestions
  - Priority levels: CRITICAL, HIGH, MEDIUM
  - Effort estimates: Low, Medium, High
  - Impact descriptions for each issue
  - Specific action items for remediation
- **Enhanced Code Health Score**: Now calculated based on Technical Debt Score
  - Formula: `max(0, 100 - (Technical Debt Score / 10))`
  - More accurate reflection of overall code quality
  - Ranges: Excellent (90-100), Good (70-89), Needs Attention (50-69), Poor (30-49), Critical (0-29)

#### Documentation
- Comprehensive README with detailed explanations of all indicators
- Advanced jq usage examples for filtering and analyzing output
- Complete EXAMPLE_OUTPUT.json demonstrating output structure
- Health score interpretation guide
- Use case examples for CI/CD, Git hooks, and monitoring

### 🔄 Changed

#### JSON Output Structure
- **code_health** object now includes:
  - `god_classes_count`
  - `dead_code_candidates`
  - `layer_violations_count`
  - `circular_dependencies_count`
  - `technical_debt_score`
- Added new **code_smells** section with detailed analysis:
  - `god_classes[]`
  - `dead_code_candidates[]`
  - `duplicate_private_members[]`
  - `layer_violations[]`
  - `circular_dependencies[]`
- Added new **actionable_recommendations[]** section
- Each file in **files_inventory** now includes `code_smells[]` array

### 💥 Breaking Changes

- The `code_health` object structure has been extended with new fields
- Existing integrations parsing the JSON output should be updated to handle new fields
- Health score calculation changed from simple metrics to technical debt-based formula

### 📊 Technical Improvements

- Enhanced dependency graph analysis
- Improved private member detection across files
- More sophisticated complexity calculations
- Better architecture layer detection

### 🎯 Use Cases Enabled

- **CI/CD Quality Gates**: Fail builds based on health score thresholds
- **Git Hooks**: Analyze only changed files
- **Refactoring Priorities**: Get ranked list of what to fix first
- **Monitoring**: Track code quality trends over time
- **AI Agent Integration**: Structured output optimized for automation

## [1.0.0] - 2025-12-16

### 🎉 Initial Release

#### ✨ Features

- **Core Metrics Analysis**
  - Lines of Code (LOC) counting
  - Cyclomatic Complexity calculation
  - Cognitive Complexity measurement
  - Coupling metrics (imports/exports)

- **Hot Spots Detection**
  - Identifies critical files based on Risk Score
  - Formula: `Risk Score = Coupling × Complexity`
  - Top 10 hotspots ranking

- **Dependency Analysis**
  - Import/export resolution
  - Barrel file support
  - Full dependency graph generation

- **Output Formats**
  - JSON format (default)
  - Markdown format support
  - File or stdout output options

- **Installation Scripts**
  - Global installation for Windows (PowerShell)
  - Global installation for Linux/Mac (Bash)
  - Uninstall scripts for all platforms

- **jq Integration**
  - Automatic detection of piped output
  - Pure JSON output for filtering
  - Colorized terminal output when available

#### 📊 Metrics Provided

- Total files analyzed
- Total lines of code
- Average complexity across project
- Average cognitive complexity
- High complexity files count
- Large files count (LOC > 300)
- Highly coupled files count (coupling > 20)

#### 🎨 Output Structure

- Project metadata
- Summary KPIs
- Basic code health metrics
- Hotspots top 10
- Complete files inventory with per-file metrics

#### 🔧 Command Line Interface

- `--format`: Choose between json/md output
- `--files`: Analyze specific files only
- `--output`: Output to file or stdout
- `--help`: Comprehensive help documentation

---

## Legend

- 🎉 Major milestone
- ✨ New features
- 🔄 Changes
- 🐛 Bug fixes
- 💥 Breaking changes
- 📊 Metrics/Analysis improvements
- 🎯 New use cases
- 🔧 CLI improvements
- 📝 Documentation
