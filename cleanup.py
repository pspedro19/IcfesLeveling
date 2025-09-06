#!/usr/bin/env python3
"""
Script de limpieza y organización del proyecto ICFES Leveling
Elimina archivos temporales, organiza documentación y prepara el proyecto
"""

import os
import shutil
from pathlib import Path
import json
from datetime import datetime

class ProjectCleaner:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        self.archive_dir = self.project_root / "docs" / "archive"
        self.cleanup_report = []
        
    def create_directories(self):
        """Crear estructura de directorios organizada"""
        directories = [
            "docs/archive",
            "docs/reports", 
            "docs/demos",
            "docs/guides",
            "scripts/setup",
            "scripts/migration",
            "data/seeds",
            "data/exports",
            "backups"
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Directorio creado/verificado: {dir_path}")
            
    def organize_documentation(self):
        """Mover archivos de documentación a carpetas apropiadas"""
        doc_files = {
            "reports": ["*REPORT*.md", "*ANALYSIS*.md", "*VERIFICATION*.md"],
            "demos": ["*.html", "*DEMO*.md"],
            "guides": ["GUIA*.md", "*GUIDE*.md", "*README*.md", "*PLAN*.md"],
            "archive": ["*FIXED*.md", "*IMPLEMENTED*.md", "*ERROR*.md"]
        }
        
        for category, patterns in doc_files.items():
            target_dir = self.docs_dir / category
            for pattern in patterns:
                for file in self.project_root.glob(pattern):
                    if file.is_file() and file.parent == self.project_root:
                        target = target_dir / file.name
                        shutil.move(str(file), str(target))
                        self.cleanup_report.append(f"Movido: {file.name} -> docs/{category}/")
                        print(f"📁 Movido: {file.name} -> docs/{category}/")
                        
    def clean_temp_files(self):
        """Eliminar archivos temporales y de caché"""
        temp_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo", 
            "**/*.pyd",
            "**/node_modules",
            "**/.next",
            "**/.pytest_cache",
            "**/*.log",
            "**/.DS_Store",
            "**/Thumbs.db",
            "**/*.swp",
            "**/*.swo",
            "**/dist",
            "**/build",
            "**/.coverage",
            "**/*.egg-info"
        ]
        
        for pattern in temp_patterns:
            for path in self.project_root.glob(pattern):
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                        print(f"🗑️ Eliminado directorio: {path}")
                    else:
                        path.unlink()
                        print(f"🗑️ Eliminado archivo: {path}")
                    self.cleanup_report.append(f"Eliminado: {path}")
                    
    def consolidate_requirements(self):
        """Consolidar todos los requirements en un archivo único"""
        req_files = list(self.project_root.glob("**/requirements*.txt"))
        all_requirements = {}
        
        for req_file in req_files:
            print(f"📝 Procesando: {req_file}")
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extraer nombre del paquete y versión
                        if '==' in line:
                            package, version = line.split('==', 1)
                            if package not in all_requirements or version > all_requirements[package]:
                                all_requirements[package] = version
                        elif '>=' in line:
                            package = line.split('>=')[0]
                            all_requirements[package] = line
                        else:
                            all_requirements[line] = ""
        
        # Escribir requirements consolidado
        consolidated_path = self.project_root / "requirements-all.txt"
        with open(consolidated_path, 'w') as f:
            f.write("# Consolidated Requirements for ICFES Leveling Project\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            
            # Categorizar requirements
            categories = {
                "# Core Framework": ["fastapi", "uvicorn", "next", "react"],
                "# Database": ["sqlalchemy", "psycopg2", "redis", "clickhouse"],
                "# AI/ML": ["openai", "numpy", "pandas", "scikit-learn"],
                "# Testing": ["pytest", "jest", "playwright"],
                "# Utils": []
            }
            
            categorized = {cat: [] for cat in categories}
            
            for package, version in sorted(all_requirements.items()):
                added = False
                for category, keywords in categories.items():
                    if any(kw in package.lower() for kw in keywords):
                        if version:
                            categorized[category].append(f"{package}=={version}")
                        else:
                            categorized[category].append(package)
                        added = True
                        break
                if not added:
                    categorized["# Utils"].append(f"{package}=={version}" if version else package)
            
            for category, packages in categorized.items():
                if packages:
                    f.write(f"\n{category}\n")
                    for pkg in sorted(packages):
                        f.write(f"{pkg}\n")
        
        print(f"✅ Requirements consolidado en: {consolidated_path}")
        self.cleanup_report.append(f"Requirements consolidado: {len(all_requirements)} paquetes")
        
    def create_gitignore(self):
        """Crear un .gitignore completo"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.next/
out/
dist/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# Environment
.env
.env.local
.env.*.local
.env.production

# Logs
*.log
logs/
*.log.*

# Database
*.db
*.sqlite
*.sqlite3

# Uploads
uploads/
temp/

# Docker
docker-compose.override.yml

# Custom
backups/
*.backup
*.bak
.cache/
"""
        
        gitignore_path = self.project_root / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        
        print(f"✅ .gitignore actualizado")
        self.cleanup_report.append(".gitignore actualizado")
        
    def generate_report(self):
        """Generar reporte de limpieza"""
        report_path = self.project_root / "docs" / "reports" / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "actions": self.cleanup_report,
            "summary": {
                "files_moved": len([a for a in self.cleanup_report if "Movido" in a]),
                "files_deleted": len([a for a in self.cleanup_report if "Eliminado" in a]),
                "total_actions": len(self.cleanup_report)
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Reporte generado: {report_path}")
        print(f"   - Archivos movidos: {report['summary']['files_moved']}")
        print(f"   - Archivos eliminados: {report['summary']['files_deleted']}")
        print(f"   - Total de acciones: {report['summary']['total_actions']}")
        
    def run(self):
        """Ejecutar limpieza completa"""
        print("🧹 Iniciando limpieza del proyecto ICFES Leveling...\n")
        
        self.create_directories()
        print()
        
        self.organize_documentation()
        print()
        
        self.clean_temp_files()
        print()
        
        self.consolidate_requirements()
        print()
        
        self.create_gitignore()
        print()
        
        self.generate_report()
        print("\n✨ Limpieza completada exitosamente!")

if __name__ == "__main__":
    cleaner = ProjectCleaner()
    cleaner.run()