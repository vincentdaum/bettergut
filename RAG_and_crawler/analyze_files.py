#!/usr/bin/env python3
"""
File Usage Analyzer - Identifies unused files in the BetterGut AI Pipeline
"""
import os
import ast
import sys
from pathlib import Path
from typing import Set, Dict, List

def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in directory"""
    return list(directory.rglob("*.py"))

def extract_imports(file_path: Path) -> Set[str]:
    """Extract all import statements from a Python file"""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return imports

def analyze_file_usage(base_dir: Path) -> Dict:
    """Analyze which files are used and which are not"""
    python_files = find_python_files(base_dir)
    
    # Create mapping of module names to file paths
    module_to_file = {}
    for file_path in python_files:
        rel_path = file_path.relative_to(base_dir)
        module_name = str(rel_path).replace('/', '.').replace('\\', '.').replace('.py', '')
        module_to_file[module_name] = file_path
    
    # Track which files import which other files
    usage_graph = {}
    all_imports = set()
    
    for file_path in python_files:
        imports = extract_imports(file_path)
        all_imports.update(imports)
        usage_graph[file_path] = imports
    
    # Find entry points (main files that are likely to be executed)
    entry_points = []
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'if __name__ == "__main__"' in content:
                entry_points.append(file_path)
    
    # Add known entry points
    known_entries = ['api.py', 'crawl_health_data.py', 'test_setup.py', 'test_manual.py']
    for entry in known_entries:
        entry_path = base_dir / entry
        if entry_path.exists() and entry_path not in entry_points:
            entry_points.append(entry_path)
    
    return {
        'python_files': python_files,
        'module_to_file': module_to_file,
        'usage_graph': usage_graph,
        'all_imports': all_imports,
        'entry_points': entry_points
    }

def find_unused_files(analysis: Dict) -> List[Path]:
    """Find files that are never imported"""
    used_files = set()
    
    # Start from entry points and traverse the dependency graph
    def traverse_dependencies(file_path: Path, visited: Set[Path]):
        if file_path in visited:
            return
        visited.add(file_path)
        used_files.add(file_path)
        
        imports = analysis['usage_graph'].get(file_path, set())
        for import_name in imports:
            # Try to find corresponding file
            for module_name, module_file in analysis['module_to_file'].items():
                if import_name in module_name or module_name in import_name:
                    traverse_dependencies(module_file, visited)
    
    # Traverse from all entry points
    visited = set()
    for entry_point in analysis['entry_points']:
        traverse_dependencies(entry_point, visited)
    
    # Find unused files
    unused_files = []
    for file_path in analysis['python_files']:
        if file_path not in used_files:
            unused_files.append(file_path)
    
    return unused_files

def categorize_files(base_dir: Path) -> Dict:
    """Categorize files by their purpose"""
    categories = {
        'core_functionality': [],
        'crawlers': [],
        'models': [],
        'configuration': [],
        'testing': [],
        'deployment': [],
        'documentation': [],
        'unused': []
    }
    
    # Core functionality
    core_files = ['api.py', 'crawl_health_data.py']
    for file_name in core_files:
        file_path = base_dir / file_name
        if file_path.exists():
            categories['core_functionality'].append(file_path)
    
    # Crawlers
    crawler_dir = base_dir / 'crawlers'
    if crawler_dir.exists():
        categories['crawlers'].extend(crawler_dir.glob('*.py'))
    
    # Models
    models_dir = base_dir / 'models'
    if models_dir.exists():
        categories['models'].extend(models_dir.glob('*.py'))
    
    # RAG system
    rag_dir = base_dir / 'rag'
    if rag_dir.exists():
        categories['models'].extend(rag_dir.glob('*.py'))
    
    # Configuration
    config_dir = base_dir / 'config'
    if config_dir.exists():
        categories['configuration'].extend(config_dir.glob('*.py'))
    
    # Testing
    test_files = ['test_setup.py', 'test_manual.py']
    for file_name in test_files:
        file_path = base_dir / file_name
        if file_path.exists():
            categories['testing'].append(file_path)
    
    return categories

def main():
    """Analyze file usage in the BetterGut AI Pipeline"""
    base_dir = Path('.')
    
    print("🔍 BetterGut AI Pipeline File Usage Analysis")
    print("=" * 50)
    
    # Analyze file usage
    analysis = analyze_file_usage(base_dir)
    unused_files = find_unused_files(analysis)
    categories = categorize_files(base_dir)
    
    print(f"\n📊 Analysis Results:")
    print(f"Total Python files: {len(analysis['python_files'])}")
    print(f"Entry points found: {len(analysis['entry_points'])}")
    print(f"Potentially unused files: {len(unused_files)}")
    
    # Show entry points
    print(f"\n🚀 Entry Points (Main Executable Files):")
    for entry_point in analysis['entry_points']:
        rel_path = entry_point.relative_to(base_dir)
        print(f"  ✅ {rel_path}")
    
    # Show file categories
    print(f"\n📁 File Categories:")
    for category, files in categories.items():
        if files:
            print(f"\n  {category.replace('_', ' ').title()}:")
            for file_path in files:
                rel_path = file_path.relative_to(base_dir)
                print(f"    • {rel_path}")
    
    # Show potentially unused files
    if unused_files:
        print(f"\n❓ Potentially Unused Files:")
        for file_path in unused_files:
            rel_path = file_path.relative_to(base_dir)
            print(f"  ⚠️ {rel_path}")
    else:
        print(f"\n✅ No unused Python files detected!")
    
    # Analyze non-Python files
    print(f"\n📋 Other Important Files:")
    other_files = [
        'Dockerfile', 'Dockerfile.production', 
        'requirements.txt', 'README.md', 
        '.env.example'
    ]
    
    for file_name in other_files:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ Missing: {file_name}")
    
    # Check for old/legacy directories
    print(f"\n🗂️ Directory Structure:")
    directories = ['crawlers', 'models', 'rag', 'config', 'storage', 'data', 'logs']
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            file_count = len(list(dir_path.rglob('*')))
            print(f"  ✅ {dir_name}/ ({file_count} items)")
        else:
            print(f"  ❌ Missing: {dir_name}/")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if unused_files:
        print(f"  • Consider removing unused files to clean up the project")
        print(f"  • Review unused files to ensure they're not needed for future features")
    
    # Check for old data directory
    old_data_dir = base_dir / 'data'
    new_storage_dir = base_dir / 'storage'
    
    if old_data_dir.exists() and new_storage_dir.exists():
        print(f"  ⚠️ Both 'data/' and 'storage/' directories exist")
        print(f"    Consider migrating content from 'data/' to 'storage/' and removing 'data/'")
    
    # Check for duplicate functionality
    test_files = [f for f in analysis['python_files'] if 'test' in str(f)]
    if len(test_files) > 2:
        print(f"  • Multiple test files found - consider consolidating testing approach")
    
    return analysis, unused_files

if __name__ == "__main__":
    main()
