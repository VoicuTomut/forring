import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib


class ChunkedProjectAnalyzer:
    """
    Analyzes large projects by breaking them into manageable chunks
    and creating focused summaries for LLM consumption.
    """

    def __init__(self, max_chunk_size: int = 15000):  # ~15k chars per chunk
        self.max_chunk_size = max_chunk_size
        self.buying_keywords = {
            'buy', 'buying', 'purchase', 'offer', 'price', 'bid', 'auction',
            'payment', 'transaction', 'deal', 'contract', 'agreement'
        }
        self.time_keywords = {
            'time', 'schedule', 'deadline', 'expir', 'duration', 'timeout',
            'timer', 'countdown', 'week', 'day', 'hour', 'minute'
        }
        self.validation_keywords = {
            'notary', 'agent', 'buyer', 'validate', 'validation', 'verify',
            'approve', 'confirm', 'document', 'signature', 'legal'
        }

    def scan_and_prioritize(self, root_path: str) -> Dict[str, any]:
        """Scan project and create prioritized file analysis."""

        print("🔍 Scanning project for buying process relevance...")

        # Get all relevant files
        files_data = self._scan_files(root_path)

        # Prioritize files
        prioritized_files = self._prioritize_files(files_data)

        # Create different analysis chunks
        analysis = {
            'project_overview': self._create_project_overview(prioritized_files),
            'high_priority_files': self._create_high_priority_chunk(prioritized_files),
            'buying_process_files': self._create_buying_process_chunk(prioritized_files),
            'validation_workflow_files': self._create_validation_chunk(prioritized_files),
            'utility_and_config_files': self._create_utility_chunk(prioritized_files),
            'recommendations': self._generate_recommendations(prioritized_files)
        }

        return analysis

    def _scan_files(self, root_path: str) -> List[Dict]:
        """Scan all relevant files in the project."""

        root_path = Path(root_path).resolve()
        files_data = []

        exclude_dirs = {
            '__pycache__', '.git', '.svn', '.hg', 'node_modules',
            '.venv', 'venv', '.env', 'env', '.pytest_cache',
            '.mypy_cache', '.tox', 'dist', 'build', '.egg-info'
        }

        target_extensions = {'.py', '.json', '.md', '.txt', '.yml', '.yaml'}

        for file_path in root_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in target_extensions:
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    relative_path = file_path.relative_to(root_path)

                    file_info = {
                        'path': str(relative_path),
                        'content': content,
                        'size': len(content),
                        'extension': file_path.suffix,
                        'relevance_score': self._calculate_relevance(str(relative_path), content)
                    }

                    files_data.append(file_info)

                except Exception as e:
                    print(f"⚠️  Skipped {file_path}: {e}")

        return files_data

    def _calculate_relevance(self, path: str, content: str) -> int:
        """Calculate relevance score for buying process."""

        score = 0
        path_lower = path.lower()
        content_lower = content.lower()

        # Path-based scoring
        path_keywords = {
            'buy': 100, 'purchase': 100, 'offer': 90, 'price': 80,
            'notary': 90, 'agent': 85, 'buyer': 85,
            'validation': 70, 'validate': 70, 'verify': 65,
            'time': 60, 'schedule': 60, 'deadline': 70,
            'document': 50, 'contract': 60, 'agreement': 55
        }

        for keyword, weight in path_keywords.items():
            if keyword in path_lower:
                score += weight

        # Content-based scoring (limited to avoid processing huge files)
        content_sample = content_lower[:2000]  # First 2k chars

        for keyword in self.buying_keywords:
            score += content_sample.count(keyword) * 10

        for keyword in self.time_keywords:
            score += content_sample.count(keyword) * 8

        for keyword in self.validation_keywords:
            score += content_sample.count(keyword) * 6

        # Boost important file types
        if 'class' in path_lower or 'model' in path_lower:
            score += 40
        if 'utils' in path_lower or 'helper' in path_lower:
            score += 30
        if 'config' in path_lower or 'setting' in path_lower:
            score += 25

        return score

    def _prioritize_files(self, files_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Organize files by priority levels."""

        # Sort by relevance score
        files_data.sort(key=lambda x: x['relevance_score'], reverse=True)

        high_priority = []
        medium_priority = []
        low_priority = []

        for file_info in files_data:
            score = file_info['relevance_score']
            if score >= 100:
                high_priority.append(file_info)
            elif score >= 50:
                medium_priority.append(file_info)
            else:
                low_priority.append(file_info)

        return {
            'high': high_priority,
            'medium': medium_priority,
            'low': low_priority,
            'all': files_data
        }

    def _create_project_overview(self, prioritized_files: Dict) -> str:
        """Create a high-level project overview."""

        total_files = len(prioritized_files['all'])
        high_count = len(prioritized_files['high'])
        medium_count = len(prioritized_files['medium'])

        # Get file structure overview
        directories = set()
        file_types = {}

        for file_info in prioritized_files['all']:
            path_parts = Path(file_info['path']).parts
            if len(path_parts) > 1:
                directories.add(path_parts[0])

            ext = file_info['extension']
            file_types[ext] = file_types.get(ext, 0) + 1

        overview = f"""# PROJECT OVERVIEW - BUYING PROCESS ANALYSIS

## 📊 Statistics
- Total relevant files: {total_files}
- High priority (buying process): {high_count} files
- Medium priority: {medium_count} files
- Main directories: {', '.join(sorted(directories))}
- File types: {', '.join(f'{ext}({count})' for ext, count in file_types.items())}

## 🎯 High Priority Files (Top 10)
"""

        for i, file_info in enumerate(prioritized_files['high'][:10]):
            overview += f"- {file_info['path']} (Score: {file_info['relevance_score']})\n"

        overview += f"""
## 🔍 Analysis Focus
This analysis focuses on:
1. Time-limited buying offers (2-week expiration)
2. Multi-party validation (buyer-agent-notary)
3. Document validation workflows
4. Price and offer management
"""

        return overview

    def _create_high_priority_chunk(self, prioritized_files: Dict) -> str:
        """Create chunk with highest priority files."""

        chunk = "# HIGH PRIORITY FILES - CORE BUYING PROCESS\n\n"
        current_size = len(chunk)

        for file_info in prioritized_files['high']:
            file_content = f"## File: {file_info['path']}\n"
            file_content += f"**Relevance Score:** {file_info['relevance_score']}\n"
            file_content += f"**Size:** {file_info['size']} chars\n\n"
            file_content += "```python\n" if file_info['extension'] == '.py' else "```\n"
            file_content += file_info['content']
            file_content += "\n```\n\n"

            if current_size + len(file_content) > self.max_chunk_size:
                break

            chunk += file_content
            current_size += len(file_content)

        return chunk

    def _create_buying_process_chunk(self, prioritized_files: Dict) -> str:
        """Create chunk focused on buying process files."""

        chunk = "# BUYING PROCESS SPECIFIC FILES\n\n"
        current_size = len(chunk)

        # Filter files related to buying process
        buying_files = [f for f in prioritized_files['all']
                        if any(keyword in f['path'].lower()
                               for keyword in ['buy', 'purchase', 'offer', 'price'])]

        for file_info in buying_files:
            file_content = f"## {file_info['path']}\n"

            # Extract key functions/classes (for Python files)
            if file_info['extension'] == '.py':
                key_parts = self._extract_key_parts(file_info['content'])
                file_content += key_parts
            else:
                file_content += f"```\n{file_info['content'][:1000]}...\n```\n"

            if current_size + len(file_content) > self.max_chunk_size:
                break

            chunk += file_content + "\n"
            current_size += len(file_content)

        return chunk

    def _create_validation_chunk(self, prioritized_files: Dict) -> str:
        """Create chunk for validation and workflow files."""

        chunk = "# VALIDATION & WORKFLOW FILES\n\n"
        current_size = len(chunk)

        validation_files = [f for f in prioritized_files['all']
                            if any(keyword in f['path'].lower()
                                   for keyword in ['notary', 'validation', 'workflow', 'agent'])]

        for file_info in validation_files:
            if current_size > self.max_chunk_size:
                break

            summary = self._create_file_summary(file_info)
            chunk += summary + "\n"
            current_size += len(summary)

        return chunk

    def _create_utility_chunk(self, prioritized_files: Dict) -> str:
        """Create chunk for utility and configuration files."""

        chunk = "# UTILITY & CONFIGURATION FILES\n\n"
        current_size = len(chunk)

        utility_files = [f for f in prioritized_files['all']
                         if any(keyword in f['path'].lower()
                                for keyword in ['util', 'helper', 'config', 'database'])]

        for file_info in utility_files:
            if current_size > self.max_chunk_size:
                break

            summary = self._create_file_summary(file_info)
            chunk += summary + "\n"
            current_size += len(summary)

        return chunk

    def _extract_key_parts(self, content: str) -> str:
        """Extract key functions and classes from Python code."""

        lines = content.split('\n')
        key_parts = []

        for i, line in enumerate(lines):
            if line.strip().startswith(('def ', 'class ', 'async def ')):
                # Get function/class definition + a few lines
                part = []
                for j in range(i, min(i + 10, len(lines))):
                    part.append(lines[j])
                    if j > i and lines[j].strip() and not lines[j].startswith(' '):
                        break
                key_parts.append('\n'.join(part))

        if key_parts:
            return "**Key Components:**\n```python\n" + '\n\n'.join(key_parts) + "\n```\n"
        else:
            return f"```python\n{content[:500]}...\n```\n"

    def _create_file_summary(self, file_info: Dict) -> str:
        """Create a summary of a file."""

        summary = f"## {file_info['path']} (Score: {file_info['relevance_score']})\n"

        if file_info['extension'] == '.py':
            # Extract docstrings and key info
            content = file_info['content']
            lines = content.split('\n')

            # Get module docstring
            if '"""' in content or "'''" in content:
                docstring_start = -1
                for i, line in enumerate(lines[:10]):
                    if '"""' in line or "'''" in line:
                        docstring_start = i
                        break

                if docstring_start >= 0:
                    summary += f"**Purpose:** {lines[docstring_start][:100]}...\n"

            # Get key functions
            functions = [line.strip() for line in lines
                         if line.strip().startswith('def ')][:3]
            if functions:
                summary += f"**Key Functions:** {', '.join(f.split('(')[0].replace('def ', '') for f in functions)}\n"

        else:
            summary += f"**Content Preview:** {file_info['content'][:200]}...\n"

        return summary

    def _generate_recommendations(self, prioritized_files: Dict) -> str:
        """Generate recommendations based on the analysis."""

        recommendations = """# RECOMMENDATIONS FOR BUYING PROCESS IMPROVEMENT

## 🎯 Based on Code Analysis

### Missing Components Analysis:
"""

        # Check for specific components
        all_content = ' '.join(f['content'].lower() for f in prioritized_files['all'])

        missing_components = []

        if 'datetime' not in all_content and 'time' not in all_content:
            missing_components.append("⏰ Time management system")

        if '2 week' not in all_content and 'fourteen' not in all_content:
            missing_components.append("📅 2-week offer expiration logic")

        if 'workflow' not in all_content:
            missing_components.append("🔄 Multi-party workflow system")

        if all_content.count('notary') < 5:
            missing_components.append("👨‍⚖️ Comprehensive notary validation")

        for component in missing_components:
            recommendations += f"- {component}\n"

        recommendations += """
### Priority Implementation Order:
1. **Time Management System** - Add datetime handling for 2-week expiration
2. **Offer Workflow** - Create buyer→agent→notary approval chain
3. **Document Validation** - Implement notary document verification
4. **Expiration Tracking** - Auto-expire offers after 2 weeks
5. **Notification System** - Alert all parties of status changes

### Suggested File Structure Improvements:
- `models/offer.py` - Time-limited offer management
- `workflows/buying_process.py` - Multi-party workflow orchestration
- `services/notification.py` - Status change notifications
- `utils/time_management.py` - Deadline and expiration utilities
"""

        return recommendations

    def save_analysis_chunks(self, analysis: Dict, output_dir: str = "analysis_chunks"):
        """Save analysis chunks as separate files."""

        os.makedirs(output_dir, exist_ok=True)

        for chunk_name, content in analysis.items():
            filename = f"{output_dir}/{chunk_name}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"💾 Saved: {filename}")

        # Create index file
        index_content = f"""# PROJECT ANALYSIS INDEX
Generated: {datetime.now().isoformat()}

## Available Analysis Chunks:

"""
        for chunk_name in analysis.keys():
            index_content += f"- [{chunk_name.replace('_', ' ').title()}]({chunk_name}.md)\n"

        with open(f"{output_dir}/README.md", 'w', encoding='utf-8') as f:
            f.write(index_content)

        print(f"📋 Created index: {output_dir}/README.md")


# Usage example
if __name__ == "__main__":
    print("🚀 CHUNKED PROJECT ANALYZER")
    print("Breaking large project into manageable chunks for LLM analysis")
    print("=" * 60)

    analyzer = ChunkedProjectAnalyzer(max_chunk_size=15000)

    # Analyze project
    analysis = analyzer.scan_and_prioritize(".")

    # Save chunks
    analyzer.save_analysis_chunks(analysis)

    print(f"\n✅ Analysis complete!")
    print(f"📂 Check 'analysis_chunks' directory for organized files")
    print(f"💡 Start with 'project_overview.md' then 'high_priority_files.md'")