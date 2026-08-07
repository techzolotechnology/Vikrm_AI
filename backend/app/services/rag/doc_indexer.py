"""
Documentation Indexer: Index official technology documentation (React, Next.js, Tailwind, FastAPI, Spring Boot,
Node, Express, Docker, Kubernetes, LangChain, LlamaIndex, PyTorch, TensorFlow, MDN).
"""
import logging
from typing import Any, Dict, List

from app.services.embeddings.embedder import CodeEmbedder
try:
    from vector_db.vector_db_manager import VectorDBManager
except ImportError:
    from backend.vector_db.vector_db_manager import VectorDBManager


logger = logging.getLogger(__name__)

OFFICIAL_DOCS_SEED = [
    {
        "tech": "react",
        "title": "React 18 Docs - Hooks, Components, & Server Components",
        "code": "// React 18 useState & useEffect pattern\nimport { useState, useEffect } from 'react';\nexport function useFetch(url) {\n  const [data, setData] = useState(null);\n  useEffect(() => {\n    fetch(url).then(res => res.json()).then(setData);\n  }, [url]);\n  return data;\n}\n",
        "description": "Official React reference for hooks, suspense, hydration, and component lifecycle.",
    },
    {
        "tech": "nextjs",
        "title": "Next.js 14 Docs - App Router, Server Actions, & Route Handlers",
        "code": "// Next.js Server Action pattern\n'use server';\nimport { revalidatePath } from 'next/cache';\nexport async function updateProfile(formData: FormData) {\n  const name = formData.get('name');\n  revalidatePath('/dashboard');\n}\n",
        "description": "Official Next.js reference for App Router layout nesting, metadata, and streaming SSR.",
    },
    {
        "tech": "tailwind",
        "title": "Tailwind CSS v3 Docs - Flexbox, Grid, & Utility Classes",
        "code": "<!-- Glassmorphic card design in Tailwind -->\n<div class='bg-slate-900/60 backdrop-blur-md border border-white/10 p-6 rounded-2xl shadow-2xl hover:border-indigo-500/40 transition-all'>\n  <h2 class='text-xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent'>Card Title</h2>\n</div>\n",
        "description": "Tailwind CSS utility class guidelines, responsiveness breakpoints, and custom animations.",
    },
    {
        "tech": "fastapi",
        "title": "FastAPI Docs - Routing, Pydantic Models, & Async Dependencies",
        "code": "# FastAPI Dependency Injection\nfrom fastapi import Depends, FastAPI\napp = FastAPI()\nasync def get_db(): yield 'db_session'\n@app.get('/items')\nasync def list_items(db = Depends(get_db)): return {'db': db}\n",
        "description": "FastAPI documentation for OpenAPI schema generation, OAuth2 security, and websockets.",
    },
    {
        "tech": "springboot",
        "title": "Spring Boot 3 Docs - REST Controllers, Security, & JPA Repositories",
        "code": "@RestController\n@RequestMapping('/api/users')\npublic class UserController {\n    @Autowired private UserRepository userRepo;\n    @GetMapping public List<User> getAll() { return userRepo.findAll(); }\n}\n",
        "description": "Spring Boot 3 reference for enterprise security, Dependency Injection, and JPA ORM.",
    },
    {
        "tech": "node",
        "title": "Node.js v20 Docs - Async I/O, File System, & Buffer APIs",
        "code": "import { readFile } from 'node:fs/promises';\nasync function loadConfig() {\n  const content = await readFile('config.json', 'utf-8');\n  return JSON.parse(content);\n}\n",
        "description": "Node.js core modules, event loop, worker threads, and streams.",
    },
    {
        "tech": "express",
        "title": "Express.js Docs - Middleware Pipelines & Routing",
        "code": "const express = require('express');\nconst app = express();\napp.use((req, res, next) => { console.log(req.url); next(); });\n",
        "description": "Express.js middleware execution stack, custom error handlers, and router modules.",
    },
    {
        "tech": "docker",
        "title": "Docker & Docker Compose Docs - Containerization",
        "code": "version: '3.8'\nservices:\n  backend:\n    build: .\n    ports: ['8000:8000']\n    environment: [DATABASE_URL=postgresql://user:pass@db:5432/app]\n  db:\n    image: postgres:16-alpine\n",
        "description": "Docker container optimization, multi-stage builds, volume mounts, and network bridges.",
    },
    {
        "tech": "kubernetes",
        "title": "Kubernetes Docs - Pods, Deployments, & Ingress Specs",
        "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: vikrm-app\nspec:\n  replicas: 3\n  template:\n    spec:\n      containers:\n      - name: app\n        image: vikrm-app:latest\n",
        "description": "Kubernetes manifests, horizontal pod autoscaling, configmaps, and secrets management.",
    },
    {
        "tech": "langchain",
        "title": "LangChain Docs - LLM Chains, Agents, & Prompt Templates",
        "code": "from langchain.chains import LLMChain\nfrom langchain.prompts import PromptTemplate\nprompt = PromptTemplate.from_template('Explain {topic}')\n",
        "description": "LangChain abstractions for tool calling, vectorstore retrievers, and structured output parsing.",
    },
    {
        "tech": "llamaindex",
        "title": "LlamaIndex Docs - VectorStoreIndex & Knowledge Graphs",
        "code": "from llama_index.core import VectorStoreIndex, SimpleDirectoryReader\ndocuments = SimpleDirectoryReader('data').load_data()\nindex = VectorStoreIndex.from_documents(documents)\n",
        "description": "LlamaIndex data ingestion, node parsing, and RAG query engines.",
    },
    {
        "tech": "pytorch",
        "title": "PyTorch Docs - Tensors, Neural Networks, & CUDA Acceleration",
        "code": "import torch\nimport torch.nn as nn\nclass Model(nn.Module):\n  def __init__(self): super().__init__(); self.fc = nn.Linear(10, 2)\n  def forward(self, x): return self.fc(x)\n",
        "description": "PyTorch autograd, custom layers, distributed data parallel, and GPU tensor ops.",
    },
    {
        "tech": "tensorflow",
        "title": "TensorFlow 2 Docs - Keras Models & SavedModel Artifacts",
        "code": "import tensorflow as tf\nmodel = tf.keras.Sequential([tf.keras.layers.Dense(64, activation='relu'), tf.keras.layers.Dense(10)])\n",
        "description": "TensorFlow functional Keras APIs, data pipelines, and TensorBoard profiling.",
    },
    {
        "tech": "mdn",
        "title": "MDN Web Docs - HTML5, CSS Grid/Flex, & Modern Web APIs",
        "code": "// MDN Fetch API & Async Generator\nasync function* streamLines(response) {\n  const reader = response.body.getReader();\n  const decoder = new TextDecoder();\n  while (true) {\n    const { done, value } = await reader.read();\n    if (done) break;\n    yield decoder.decode(value);\n  }\n}\n",
        "description": "Mozilla Developer Network standard reference for JavaScript ECMAScript APIs, DOM events, and Web Workers.",
    },
]


class DocumentationIndexer:
    def __init__(self, vector_db: VectorDBManager) -> None:
        self.vector_db = vector_db
        self.embedder = vector_db.embedder

    def index_official_docs(self) -> Dict[str, Any]:
        logger.info("Indexing official tech documentation into vector database...")
        docs_store = self.vector_db.get_store_for_tech("docs")
        indexed_count = 0

        for i, item in enumerate(OFFICIAL_DOCS_SEED):
            doc_id = f"official-doc-{item['tech']}-{i}"
            content = f"Title: {item['title']}\nTech: {item['tech']}\nDescription: {item['description']}\nReference Code:\n{item['code']}"
            vector = self.embedder.embed_query(content)
            metadata = {
                "tech": item["tech"],
                "title": item["title"],
                "description": item["description"],
                "source": "official_documentation",
            }

            # Index in docs collection as well as tech-specific collection
            docs_store.upsert(ids=[doc_id], embeddings=[vector], documents=[content], metadatas=[metadata])
            tech_store = self.vector_db.get_store_for_tech(item["tech"])
            tech_store.upsert(ids=[doc_id], embeddings=[vector], documents=[content], metadatas=[metadata])
            indexed_count += 1

        return {"status": "indexed", "official_docs_count": indexed_count}
