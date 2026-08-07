"""
Topological Dependency Graph Resolver for Vikrm AI Platform.
Orders generated files topologically so dependencies (package.json, tsconfig, main.tsx)
are generated and streamed before dependent components, pages, and backends.
"""

from typing import Dict, List, Tuple

class DependencyGraphResolver:
    # Defined topological tier priority (lower tier number = generated earlier)
    TIER_MAP = {
        "package.json": 1,
        "tsconfig.json": 2,
        "vite.config.ts": 3,
        "index.html": 4,
        ".gitignore": 5,
        ".env.example": 6,
        "Dockerfile": 7,
        "docker-compose.yml": 8,
        "src/index.css": 10,
        "src/api/apiClient.ts": 15,
        "src/context/AuthContext.tsx": 20,
        "src/context/CartContext.tsx": 21,
        "src/hooks/": 30,
        "src/components/layout/": 40,
        "src/components/": 45,
        "src/routes/": 50,
        "src/pages/": 60,
        "src/App.tsx": 70,
        "src/main.tsx": 71,
        "server/": 80,
        "README.md": 999
    }

    @classmethod
    def get_tier(cls, filepath: str) -> int:
        if filepath in cls.TIER_MAP:
            return cls.TIER_MAP[filepath]
        
        for prefix, tier in cls.TIER_MAP.items():
            if prefix.endswith("/") and filepath.startswith(prefix):
                return tier
        
        # Default tier for src files
        if filepath.startswith("src/"):
            return 50
        # Default tier for server files
        if filepath.startswith("server/"):
            return 80
        return 100

    @classmethod
    def sort_files(cls, files: Dict[str, str]) -> Dict[str, str]:
        """
        Returns files dict sorted topologically by dependency order.
        Ensures package.json is ALWAYS key #1.
        """
        sorted_pairs = sorted(files.items(), key=lambda item: (cls.get_tier(item[0]), item[0]))
        sorted_dict = dict(sorted_pairs)

        # Force package.json to be absolute first if present
        if "package.json" in sorted_dict:
            pkg_content = sorted_dict.pop("package.json")
            return {"package.json": pkg_content, **sorted_dict}
        
        return sorted_dict
