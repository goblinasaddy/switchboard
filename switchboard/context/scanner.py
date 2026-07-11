import fnmatch
import os
import hashlib
from switchboard.context.models import Language

class GitignoreMatcher:
    """
    Deterministic path matcher replicating gitignore exclusion rules
    without external package dependencies.
    """

    def __init__(self, root_dir: str) -> None:
        self.root_dir = os.path.abspath(root_dir)
        self.patterns: list[str] = [
            ".git/",
            "__pycache__/",
            "*.pyc",
            ".venv/",
            ".pytest_cache/",
            "*.egg-info/",
            "node_modules/",
            "dist/",
            "build/"
        ]
        self._load_gitignore()

    def _load_gitignore(self) -> None:
        git_path = os.path.join(self.root_dir, ".gitignore")
        if os.path.exists(git_path):
            try:
                with open(git_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        self.patterns.append(line)
            except Exception:
                pass

    def is_ignored(self, path: str) -> bool:
        """Check if target path matches any ignore patterns."""
        abs_path = os.path.abspath(path)
        rel_path = os.path.relpath(abs_path, self.root_dir).replace("\\", "/")
        
        # Add trailing slash if it is a directory
        if os.path.isdir(abs_path) and not rel_path.endswith("/"):
            rel_path += "/"
            
        for pat in self.patterns:
            # Normalize pattern for matching
            clean_pat = pat.rstrip("/")
            
            # Absolute matching if pattern starts with /
            if pat.startswith("/"):
                rule = pat[1:]
                if fnmatch.fnmatchcase(rel_path, rule) or fnmatch.fnmatchcase(rel_path, f"{rule}/*"):
                    return True
            else:
                # Segment matching
                if fnmatch.fnmatchcase(rel_path, clean_pat) or fnmatch.fnmatchcase(rel_path, f"*/{clean_pat}") or fnmatch.fnmatchcase(rel_path, f"*/{clean_pat}/*"):
                    return True
                # Check individual directory parts
                for part in rel_path.split("/"):
                    if part and fnmatch.fnmatchcase(part, clean_pat):
                        return True
        return False


def detect_language(filename: str) -> Language:
    """Identify programming language based on file extension."""
    ext = os.path.splitext(filename)[1].lower()
    mapping = {
        ".py": Language.PYTHON,
        ".js": Language.JAVASCRIPT,
        ".ts": Language.TYPESCRIPT,
        ".tsx": Language.TYPESCRIPT,
        ".rs": Language.RUST,
        ".go": Language.GO,
        ".md": Language.MARKDOWN
    }
    return mapping.get(ext, Language.UNKNOWN)


def compute_file_hash(content: str) -> str:
    """Compute sha256 hash representing file content state."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class RepositoryScanner:
    """
    Subsystem component responsible for scanning directory layouts and filtering files.
    """

    def __init__(self, root_path: str) -> None:
        self.root_path = os.path.abspath(root_path)
        self.matcher = GitignoreMatcher(self.root_path)

    def scan(self) -> list[tuple[str, str, Language]]:
        """
        Walks the directory structure recursively and returns non-ignored file records.
        
        Returns:
            List of tuples of (relative_path, absolute_path, detected_language).
        """
        results: list[tuple[str, str, Language]] = []
        
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            # Prune ignored directories in-place to optimize traversal
            ignored_dirs = []
            for d in dirnames:
                full_dpath = os.path.join(dirpath, d)
                if self.matcher.is_ignored(full_dpath):
                    ignored_dirs.append(d)
            for d in ignored_dirs:
                dirnames.remove(d)

            for fname in filenames:
                full_fpath = os.path.join(dirpath, fname)
                if self.matcher.is_ignored(full_fpath):
                    continue
                
                rel_path = os.path.relpath(full_fpath, self.root_path).replace("\\", "/")
                lang = detect_language(fname)
                results.append((rel_path, full_fpath, lang))
                
        return results
