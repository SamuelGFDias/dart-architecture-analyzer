import os
import re
import sys
import json
import argparse
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# --- CONFIGURAÇÃO ---
DEFAULT_IGNORED_SUFFIXES = (
    '.g.dart', 
    '.freezed.dart', 
    '.gen.dart', 
    '.config.dart', 
    '_web.dart'
)
DEFAULT_OUTPUT_NAME = "RELATORIO_ARQUITETURA"
# --------------------

def load_ignore_patterns(root_path):
    """Carrega padrões de ignore do arquivo .analyseignore"""
    ignore_file = root_path / '.analyseignore'
    patterns = list(DEFAULT_IGNORED_SUFFIXES)
    
    if ignore_file.exists():
        try:
            with open(ignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Ignora linhas vazias e comentários
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception as e:
            print(f"Aviso: Erro ao ler .analyseignore: {e}", file=sys.stderr)
    
    return tuple(patterns)

def should_ignore_file(filename, ignore_patterns):
    """Verifica se um arquivo deve ser ignorado baseado nos padrões"""
    for pattern in ignore_patterns:
        if pattern.startswith('*'):
            # Pattern com wildcard (ex: *.test.dart)
            if filename.endswith(pattern[1:]):
                return True
        elif filename.endswith(pattern):
            return True
    return False

class DartFile:
    def __init__(self, path, package_name, root_path):
        self.path = Path(path).resolve()
        self.root_path = root_path
        try:
            self.rel_path = self.path.relative_to(root_path)
        except ValueError:
            self.rel_path = self.path
            
        self.package_name = package_name
        
        self.raw_imports = []
        self.raw_exports = []
        self.resolved_imports = set()
        self.resolved_exports = set()
        self.used_by = set()
        
        # Métricas
        self.lines_of_code = 0
        self.num_classes = 0
        self.num_functions = 0
        self.num_widgets = 0
        self.cyclomatic_complexity = 0
        self.cognitive_complexity = 0
        
        # Code Smells Detection
        self.private_members = []  # Lista de nomes de membros privados (_nome)
        self.class_names = []  # Lista de nomes de classes
        self.is_god_class = False
        self.god_class_reasons = []

    @property
    def filename(self):
        return self.path.name

    def parse(self):
        with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            self.raw_imports = re.findall(r"^\s*import\s+['\"](.+?)['\"]", content, re.MULTILINE)
            self.raw_exports = re.findall(r"^\s*export\s+['\"](.+?)['\"]", content, re.MULTILINE)
            self._analyze_complexity(content)
    
    def _analyze_complexity(self, content):
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith(('//', '/*', '*')):
                self.lines_of_code += 1
        
        # Extrai nomes de classes
        class_matches = re.findall(r'\bclass\s+(\w+)', content)
        self.class_names = class_matches
        self.num_classes = len(class_matches)
        
        self.num_widgets = len(re.findall(r'\bclass\s+\w+\s+extends\s+(StatelessWidget|StatefulWidget|ConsumerWidget|HookWidget|ConsumerStatefulWidget)', content))
        self.num_functions = len(re.findall(r'\b(void|Future|String|int|bool|double|Widget|List|Map|Set)\s+\w+\s*\([^)]*\)\s*(async\s*)?\{', content))
        
        # Extrai membros privados (classes, métodos, variáveis que começam com _)
        self.private_members = list(set(re.findall(r'\b(_\w+)', content)))
        
        # Complexidade Ciclomática simples
        self.cyclomatic_complexity += len(re.findall(r'\bif\b', content))
        self.cyclomatic_complexity += len(re.findall(r'\belse\b', content))
        self.cyclomatic_complexity += len(re.findall(r'\bfor\b', content))
        self.cyclomatic_complexity += len(re.findall(r'\bwhile\b', content))
        self.cyclomatic_complexity += len(re.findall(r'\bcase\b', content))
        self.cyclomatic_complexity += len(re.findall(r'\bcatch\b', content))
        self.cyclomatic_complexity += len(re.findall(r'\?\?', content))
        self.cyclomatic_complexity += len(re.findall(r'&&', content))
        self.cyclomatic_complexity += len(re.findall(r'\|\|', content))
        self.cyclomatic_complexity += content.count('?')
        
        # Complexidade Cognitiva (Nesting)
        nesting_depth = 0
        max_nesting = 0
        for line in lines:
            stripped = line.strip()
            if any(kw in stripped for kw in ['if ', 'for ', 'while ', 'switch ']):
                nesting_depth += 1
                max_nesting = max(max_nesting, nesting_depth)
                self.cognitive_complexity += nesting_depth
            if stripped.endswith('}'):
                nesting_depth = max(0, nesting_depth - 1)
        self.cognitive_complexity += max_nesting
        
        # Detecção de God Class
        self._detect_god_class()
    
    def _detect_god_class(self):
        """Detecta se o arquivo é uma God Class baseado em múltiplos critérios"""
        reasons = []
        
        if self.lines_of_code > 500:
            reasons.append(f"Arquivo muito grande ({self.lines_of_code} LOC)")
        
        if self.num_classes > 10:
            reasons.append(f"Muitas classes em um arquivo ({self.num_classes})")
        
        if self.num_functions > 30:
            reasons.append(f"Muitos métodos/funções ({self.num_functions})")
        
        if self.cyclomatic_complexity > 100:
            reasons.append(f"Complexidade ciclomática muito alta ({self.cyclomatic_complexity})")
        
        if reasons:
            self.is_god_class = True
            self.god_class_reasons = reasons

    def resolve_paths(self, all_files_map):
        self._resolve_list(self.raw_imports, self.resolved_imports, all_files_map)
        self._resolve_list(self.raw_exports, self.resolved_exports, all_files_map)

    def _resolve_list(self, raw_list, target_set, all_files_map):
        for item in raw_list:
            resolved_path = None
            if item.startswith(f'package:{self.package_name}/'):
                relative_part = item.replace(f'package:{self.package_name}/', '')
                lib_root = self.root_path / 'lib'
                if lib_root.exists():
                    resolved_path = (lib_root / relative_part).resolve()
            elif not item.startswith('package:') and not item.startswith('dart:'):
                resolved_path = (self.path.parent / item).resolve()

            if resolved_path and resolved_path in all_files_map:
                target_set.add(resolved_path)

    def to_dict(self):
        """Serializa o objeto para JSON"""
        result = {
            "path": str(self.rel_path).replace('\\', '/'),
            "metrics": {
                "loc": self.lines_of_code,
                "complexity": self.cyclomatic_complexity,
                "cognitive_complexity": self.cognitive_complexity,
                "classes": self.num_classes,
                "widgets": self.num_widgets,
                "methods": self.num_functions,
            },
            "dependency_graph": {
                "imports_count": len(self.resolved_imports),
                "used_by_count": len(self.used_by),
                "used_by": [str(p.relative_to(self.root_path)).replace('\\', '/') for p in self.used_by]
            },
            "code_smells": {
                "is_god_class": self.is_god_class,
                "god_class_reasons": self.god_class_reasons if self.is_god_class else []
            }
        }
        return result

def get_package_name(root_path):
    pubspec_path = root_path / 'pubspec.yaml'
    if not pubspec_path.exists():
        return None
    try:
        with open(pubspec_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('name:'):
                    return line.split(':')[1].strip()
    except:
        pass
    return None

def generate_recommendations(god_classes, dead_code, duplicates, violations, circular_deps, highly_coupled, high_complexity):
    """Gera recomendações priorizadas e acionáveis para refatoração"""
    recommendations = []
    
    # Prioridade 1: Circular Dependencies (bloqueadores críticos)
    if circular_deps:
        recommendations.append({
            "priority": "CRITICAL",
            "category": "Architecture",
            "issue": "Circular Dependencies Detected",
            "impact": "Prevents proper modularization and testing",
            "affected_count": len(circular_deps),
            "effort": "High",
            "action": "Break cycles by introducing interfaces/abstractions or restructuring module boundaries"
        })
    
    # Prioridade 2: Layer Violations (problemas arquiteturais)
    if violations:
        recommendations.append({
            "priority": "HIGH",
            "category": "Architecture",
            "issue": "Layer Violations",
            "impact": "Breaks clean architecture principles, increases coupling",
            "affected_count": len(violations),
            "effort": "Medium",
            "action": "Refactor UI to depend on domain abstractions instead of data implementations"
        })
    
    # Prioridade 3: God Classes (refatoração urgente)
    if god_classes:
        recommendations.append({
            "priority": "HIGH",
            "category": "Code Quality",
            "issue": "God Classes Detected",
            "impact": "Hard to maintain, test, and understand",
            "affected_count": len(god_classes),
            "effort": "High",
            "action": f"Split large classes into focused modules. Start with: {god_classes[0].rel_path}"
        })
    
    # Prioridade 4: Dead Code (quick wins)
    if len(dead_code) > 5:
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Cleanup",
            "issue": "Dead Code Accumulation",
            "impact": "Increases maintenance burden and confusion",
            "affected_count": len(dead_code),
            "effort": "Low",
            "action": "Remove unused files after verifying they're not dynamic imports"
        })
    
    # Prioridade 5: Duplicate Private Members (oportunidade de modularização)
    if len(duplicates) > 10:
        recommendations.append({
            "priority": "MEDIUM",
            "category": "DRY Principle",
            "issue": "Duplicate Private Members",
            "impact": "Code duplication, inconsistent behavior across modules",
            "affected_count": len(duplicates),
            "effort": "Medium",
            "action": "Extract common private members to shared utilities or base classes"
        })
    
    # Prioridade 6: High Complexity (refatoração gradual)
    if high_complexity > 5:
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Code Quality",
            "issue": "High Complexity Files",
            "impact": "Difficult to understand and prone to bugs",
            "affected_count": high_complexity,
            "effort": "Medium",
            "action": "Simplify complex logic, extract methods, reduce nesting"
        })
    
    return recommendations

def generate_json_report(files_to_report, root_path, package_name, ignored_count, is_partial_analysis, circular_deps, output_mode='file', output_file=None):
    """Gera o relatório em formato JSON otimizado para IA"""
    
    if output_file is None:
        output_file = DEFAULT_OUTPUT_NAME
    
    # Prepara os dados
    files_list = [f.to_dict() for f in files_to_report.values()]
    
    # Identifica Hotspots para a IA (apenas dentro do escopo analisado)
    hotspots = []
    for f in files_to_report.values():
        risk = len(f.used_by) * f.cyclomatic_complexity
        if risk > 100:
            hotspots.append({
                "path": str(f.rel_path).replace('\\', '/'),
                "risk_score": risk,
                "reason": f"High coupling ({len(f.used_by)}) x Complexity ({f.cyclomatic_complexity})"
            })
    
    hotspots.sort(key=lambda x: x['risk_score'], reverse=True)
    
    # Code Health Metrics
    total_files = len(files_to_report)
    total_loc = sum(f.lines_of_code for f in files_to_report.values())
    avg_complexity = total_loc and sum(f.cyclomatic_complexity for f in files_to_report.values()) / total_files or 0
    avg_cognitive = total_files and sum(f.cognitive_complexity for f in files_to_report.values()) / total_files or 0
    
    # Thresholds for health assessment
    high_complexity_files = sum(1 for f in files_to_report.values() if f.cyclomatic_complexity > 50)
    large_files = sum(1 for f in files_to_report.values() if f.lines_of_code > 300)
    highly_coupled = sum(1 for f in files_to_report.values() if len(f.used_by) > 10)
    
    # Code Smells Detection
    god_classes = [f for f in files_to_report.values() if f.is_god_class]
    
    # Dead Code Detection (whitelist de entry points comuns)
    entry_points_whitelist = ['main.dart', 'firebase_options.dart', 'bootstrap.dart', 'app.dart']
    dead_code_candidates = []
    for f in files_to_report.values():
        if len(f.used_by) == 0 and f.filename not in entry_points_whitelist:
            dead_code_candidates.append({
                "path": str(f.rel_path).replace('\\', '/'),
                "reason": "No references found (potential dead code)"
            })
    
    # Detecção de duplicação de membros privados
    private_members_map = {}
    for f in files_to_report.values():
        for member in f.private_members:
            if member not in private_members_map:
                private_members_map[member] = []
            private_members_map[member].append(str(f.rel_path).replace('\\', '/'))
    
    duplicate_private_members = []
    for member, files in private_members_map.items():
        if len(files) > 1:
            duplicate_private_members.append({
                "member_name": member,
                "occurrences": len(files),
                "files": files,
                "suggestion": "Consider extracting to shared utility or base class"
            })
    
    # Ordena por número de ocorrências
    duplicate_private_members.sort(key=lambda x: x['occurrences'], reverse=True)
    
    # Layer Violations Detection (simplified)
    layer_violations = []
    for f in files_to_report.values():
        file_path = str(f.rel_path).replace('\\', '/')
        
        # Detecta se é UI layer
        is_ui_layer = any(pattern in file_path for pattern in ['/presentation/', '/ui/', '/screens/', '/pages/', '/widgets/'])
        
        if is_ui_layer:
            # Verifica se importa diretamente data sources ou repositories
            for imp in f.raw_imports:
                if any(pattern in imp for pattern in ['data_source', 'datasource', '/data/', 'repository', '/repo/']):
                    # Verifica se não é um import de domain (permitido)
                    if '/domain/' not in imp:
                        layer_violations.append({
                            "file": file_path,
                            "violation": f"UI layer importing data layer: {imp}",
                            "severity": "high",
                            "suggestion": "UI should depend on domain layer abstractions, not data implementations"
                        })
    
    # Technical Debt Score calculation
    tech_debt_score = 0
    tech_debt_score += len(god_classes) * 50  # God classes são muito custosas
    tech_debt_score += len(dead_code_candidates) * 10
    tech_debt_score += len(duplicate_private_members) * 5
    tech_debt_score += len(layer_violations) * 30
    tech_debt_score += high_complexity_files * 15
    tech_debt_score += highly_coupled * 10

    report_data = {
        "meta": {
            "project": package_name,
            "analysis_date": datetime.now().isoformat(),
            "generator": "Static Dart Analyzer v0.0.1",
            "scope": "Partial (Selected Files)" if is_partial_analysis else "Full Project"
        },
        "summary_kpis": {
            "reported_files": total_files,
            "total_loc": total_loc,
            "avg_complexity": avg_complexity,
            "avg_cognitive_complexity": avg_cognitive
        },
        "code_health": {
            "high_complexity_files": high_complexity_files,
            "large_files_count": large_files,
            "highly_coupled_files": highly_coupled,
            "god_classes_count": len(god_classes),
            "dead_code_candidates": len(dead_code_candidates),
            "layer_violations_count": len(layer_violations),
            "circular_dependencies_count": len(circular_deps),
            "technical_debt_score": tech_debt_score,
            "health_score": max(0, 100 - (tech_debt_score // 10))
        },
        "code_smells": {
            "god_classes": [{
                "path": str(f.rel_path).replace('\\', '/'),
                "reasons": f.god_class_reasons,
                "metrics": {
                    "loc": f.lines_of_code,
                    "complexity": f.cyclomatic_complexity,
                    "classes": f.num_classes,
                    "methods": f.num_functions
                },
                "suggestion": "Split into smaller, focused modules with single responsibilities"
            } for f in god_classes],
            "dead_code_candidates": dead_code_candidates,
            "duplicate_private_members": duplicate_private_members[:20],  # Top 20
            "layer_violations": layer_violations,
            "circular_dependencies": circular_deps
        },
        "actionable_recommendations": generate_recommendations(
            god_classes, dead_code_candidates, duplicate_private_members, 
            layer_violations, circular_deps, highly_coupled, high_complexity_files
        ),
        "hotspots_top_10": hotspots[:10],
        "files_inventory": files_list
    }

    if output_mode == 'stdout':
        import sys
        json_str = json.dumps(report_data, indent=2)
        
        # Detecta se stdout está sendo redirecionado (pipe)
        # Se sim, envia JSON puro para permitir pipe com jq externo
        is_piped = not sys.stdout.isatty()
        
        if is_piped:
            # Saída está sendo redirecionada/pipe - envia JSON puro
            print(json_str)
        elif shutil.which('jq'):
            # Terminal interativo com jq disponível - usa colorização
            try:
                process = subprocess.Popen(
                    ['jq', '.'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=json_str)
                if process.returncode == 0:
                    print(stdout, end='')
                else:
                    print(json_str)
            except Exception:
                print(json_str)
        else:
            # Terminal interativo sem jq - JSON puro
            print(json_str)
    else:
        output_path = root_path / f"{output_file}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        print(f"Relatório JSON gerado: {output_path}")

def generate_markdown_report(files_to_report, root_path, package_name, ignored_count, is_partial_analysis, output_mode='file', output_file=None):
    if output_file is None:
        output_file = DEFAULT_OUTPUT_NAME
    
    sorted_by_usage = sorted(files_to_report.values(), key=lambda x: len(x.used_by), reverse=True)
    top_critical = sorted_by_usage[:15]
    
    orphans = []
    whitelist = ['main.dart', 'firebase_options.dart', 'bootstrap.dart']
    for f in sorted_by_usage:
        if len(f.used_by) == 0 and f.filename not in whitelist:
            orphans.append(f)

    # Gera o conteúdo markdown
    content = []
    content.append(f"# Relatório de Arquitetura: {package_name}\n")
    content.append(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    content.append(f"**Escopo:** {'Análise Parcial (Arquivos Selecionados)' if is_partial_analysis else 'Projeto Completo'}\n\n")
    
    content.append("## 🤖 Contexto\n")
    content.append("Este relatório foca apenas nos arquivos solicitados, mas calcula referências globais (quem usa estes arquivos).\n\n")

    content.append("## 🔥 Arquivos Críticos (no escopo selecionado)\n")
    if top_critical:
        for f in top_critical:
            content.append(f"- `{f.rel_path}` (**{len(f.used_by)}** refs | Complexidade: {f.cyclomatic_complexity})\n")
    else:
        content.append("Nenhum arquivo no escopo.\n")
        
    content.append(f"\n## 📑 Detalhamento ({len(files_to_report)} arquivos)\n")
    sorted_alpha = sorted(files_to_report.values(), key=lambda x: str(x.rel_path))
    
    for f in sorted_alpha:
        usage = len(f.used_by)
        content.append(f"### `{f.rel_path}`\n")
        content.append(f"- **Métricas:** LOC: {f.lines_of_code} | Ciclo: {f.cyclomatic_complexity} | Cognitiva: {f.cognitive_complexity}\n")
        if usage > 0:
            content.append(f"- **Usado por ({usage}):**\n")
            # Limita a 10 refs para não poluir
            for consumer in sorted(list(f.used_by))[:10]:
                try:
                    consumer_rel = Path(consumer).relative_to(root_path)
                    content.append(f"  - `{consumer_rel}`\n")
                except:
                    content.append(f"  - `{consumer}`\n")
            if usage > 10:
                content.append(f"  - ... e mais {usage - 10}\n")
        else:
            content.append("- _Sem referências diretas._\n")
        content.append("\n")

    markdown_content = ''.join(content)
    
    if output_mode == 'stdout':
        # Para Windows PowerShell: usa UTF-8 com errors='replace'
        import sys
        if sys.platform == 'win32':
            sys.stdout.reconfigure(encoding='utf-8')
        print(markdown_content)
    else:
        output_path = root_path / f"{output_file}.md"
        with open(output_path, 'w', encoding='utf-8') as md:
            md.write(markdown_content)
        print(f"Relatório Markdown gerado: {output_path}")

def detect_circular_dependencies(all_files):
    """Detecta dependências circulares no grafo de dependências"""
    circular_deps = []
    
    def find_cycle(start_path, current_path, visited, stack):
        """DFS para encontrar ciclos"""
        if current_path in stack:
            # Encontrou ciclo
            cycle_start = stack.index(current_path)
            cycle = stack[cycle_start:] + [current_path]
            return cycle
        
        if current_path in visited:
            return None
        
        visited.add(current_path)
        stack.append(current_path)
        
        if current_path in all_files:
            current_file = all_files[current_path]
            for imported_path in current_file.resolved_imports:
                cycle = find_cycle(start_path, imported_path, visited, stack[:])
                if cycle:
                    return cycle
        
        return None
    
    checked = set()
    for file_path in all_files.keys():
        if file_path not in checked:
            cycle = find_cycle(file_path, file_path, set(), [])
            if cycle:
                # Converte paths para strings relativos
                cycle_str = []
                for p in cycle:
                    try:
                        cycle_str.append(str(Path(p).relative_to(all_files[file_path].root_path)).replace('\\', '/'))
                    except:
                        cycle_str.append(str(p))
                
                # Evita adicionar o mesmo ciclo múltiplas vezes
                cycle_signature = tuple(sorted(cycle_str))
                if cycle_signature not in checked:
                    circular_deps.append({
                        "cycle": cycle_str,
                        "severity": "high",
                        "suggestion": "Break circular dependency by introducing interfaces or restructuring"
                    })
                    checked.add(cycle_signature)
    
    return circular_deps

def analyze_project(root_path_str, output_format='md', target_files=None, output_mode='file'):
    root_path = Path(root_path_str).resolve()
    package_name = get_package_name(root_path)
    
    if not package_name:
        print("Erro: pubspec.yaml não encontrado.", file=sys.stderr if output_mode == 'stdout' else sys.stdout)
        return

    # Carrega padrões de ignore
    ignore_patterns = load_ignore_patterns(root_path)
    
    print(f"Iniciando análise completa para resolver dependências...", file=sys.stderr if output_mode == 'stdout' else sys.stdout)
    
    # 1. SCAN GLOBAL (Sempre necessário para resolver dependências reversas corretamente)
    all_files = {}
    ignored_count = 0
    lib_path = root_path / 'lib'
    
    if not lib_path.exists():
        print("Erro: Pasta /lib não encontrada.", file=sys.stderr if output_mode == 'stdout' else sys.stdout)
        return

    for root, dirs, files in os.walk(lib_path):
        for file in files:
            if file.endswith('.dart'):
                if should_ignore_file(file, ignore_patterns):
                    ignored_count += 1
                    continue
                full_path = Path(root) / file
                dart_file = DartFile(full_path, package_name, root_path)
                all_files[full_path.resolve()] = dart_file

    # 2. Parse Global
    for f in all_files.values():
        f.parse()
    for f in all_files.values():
        f.resolve_paths(all_files)

    # 3. Propagação de Exports Global
    effective_exports = {path: obj.resolved_exports.copy() for path, obj in all_files.items()}
    changed = True
    while changed:
        changed = False
        for path, exports in effective_exports.items():
            to_add = set()
            for exported_path in exports:
                if exported_path in effective_exports:
                    to_add.update(effective_exports[exported_path])
            if len(to_add.difference(exports)) > 0:
                exports.update(to_add)
                changed = True

    # 4. Cruzamento Global (Used By)
    for consumer_path, consumer_obj in all_files.items():
        for imported_path in consumer_obj.resolved_imports:
            if imported_path in all_files:
                all_files[imported_path].used_by.add(consumer_path)
            if imported_path in effective_exports:
                for deep_exported_path in effective_exports[imported_path]:
                    if deep_exported_path in all_files:
                        all_files[deep_exported_path].used_by.add(consumer_path)
    
    # 4.5. Detecção de Circular Dependencies
    circular_deps = detect_circular_dependencies(all_files)

    # 5. FILTRAGEM (Selecionar apenas o que o usuário pediu para relatar)
    files_to_report = {}
    is_partial_analysis = False

    if target_files:
        is_partial_analysis = True
        print(f"Filtrando saída para {len(target_files)} arquivos...", file=sys.stderr if output_mode == 'stdout' else sys.stdout)
        for t_file in target_files:
            # Tenta resolver o caminho passado (relativo ou absoluto)
            try:
                # Remove aspas extras se houver e resolve caminho
                clean_path = t_file.strip().strip("'").strip('"')
                target_path = Path(clean_path).resolve()
                
                if target_path in all_files:
                    files_to_report[target_path] = all_files[target_path]
                else:
                    print(f"Aviso: Arquivo solicitado não encontrado ou ignorado: {clean_path}", file=sys.stderr)
            except Exception as e:
                print(f"Erro ao processar caminho {t_file}: {e}", file=sys.stderr)
    else:
        files_to_report = all_files

    # 6. Output
    return files_to_report, root_path, package_name, ignored_count, is_partial_analysis, circular_deps

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Analisador de Arquitetura Flutter - Extrai métricas de código e dependências',
        epilog='''
Exemplos de uso:

  Análise completa (exibe no terminal):
    dart-analyse

  Salvar em arquivo (nome padrão):
    dart-analyse --output file

  Salvar com nome customizado:
    dart-analyse --output file --output-file meu_relatorio

  Análise parcial (arquivos específicos):
    dart-analyse --files lib/main.dart lib/core/utils/helpers.dart

  Saída no terminal:
    dart-analyse --output stdout

  Integração com jq (filtros e transformações):
    dart-analyse --output stdout | jq '.summary_kpis'
    dart-analyse --output stdout | jq '.hotspots_top_10[0:5]'
    dart-analyse --output stdout | jq '.code_health.health_score'
    
  Filtros avançados:
    # Arquivos com alta complexidade
    dart-analyse --output stdout | jq '.files_inventory[] | select(.metrics.complexity > 50)'
    
    # Top 5 arquivos mais complexos com formato customizado
    dart-analyse --output stdout | jq '[.files_inventory | sort_by(.metrics.complexity) | reverse | .[0:5][] | {path, complexity: .metrics.complexity, loc: .metrics.loc}]'
    
    # Estatísticas por hotspot
    dart-analyse --output stdout | jq '.hotspots_top_10[] | select(.risk_score > 1000)'

Nota: Quando --output stdout é usado, o jq é automaticamente aplicado para colorização
      em terminal interativo. Para pipes, o JSON puro é enviado.
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--format', 
                        choices=['md', 'json'], 
                        default='json', 
                        help='Formato de saída: md (Markdown) ou json (JSON para IA/automação)')
    
    parser.add_argument('--files', 
                        nargs='+', 
                        metavar='FILE',
                        help='Lista de arquivos .dart para analisar (caminhos relativos à raiz do projeto)')
    
    parser.add_argument('--output',
                        choices=['file', 'stdout'],
                        default='stdout',
                        help='Destino: file (salva arquivo) ou stdout (exibe no terminal)')
    
    parser.add_argument('--output-file',
                        metavar='NAME',
                        default=None,
                        help='Nome do arquivo de saída (sem extensão). Padrão: RELATORIO_ARQUITETURA')
    
    args = parser.parse_args()
    
    files_to_report, root_path, package_name, ignored_count, is_partial, circular_deps = analyze_project(
        os.getcwd(), args.format, args.files, args.output
    )
    
    # Gera o relatório no formato e destino especificados
    if args.format == 'json':
        generate_json_report(files_to_report, root_path, package_name, ignored_count, is_partial, circular_deps, args.output, args.output_file)
    else:
        generate_markdown_report(files_to_report, root_path, package_name, ignored_count, is_partial, args.output, args.output_file)