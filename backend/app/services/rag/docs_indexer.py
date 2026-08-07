"""
RAG Documentation Engine.

Pre-indexed reference documentation signatures for major frameworks, libraries,
and APIs to provide grounding before AI code generation.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DocEntry:
    framework: str
    topic: str
    content: str
    url: str


OFFICIAL_DOCS: List[DocEntry] = [
    DocEntry("React", "Hooks & State", "React 19 features useActionState, useOptimistic, and use hook for async data loading.", "https://react.dev/reference/react"),
    DocEntry("Next.js", "App Router", "Next.js 15 App Router uses Server Components by default. Use 'use client' for interactive components.", "https://nextjs.org/docs"),
    DocEntry("Tailwind CSS", "Design Tokens & Glassmorphism", "Tailwind v3/v4 backdrop-blur, bg-white/10, border-white/20, shadow-glass utilities.", "https://tailwindcss.com/docs"),
    DocEntry("Spring Boot", "REST & Data JPA", "Spring Boot 3.x with Jakarta EE, @RestController, @Autowired, Spring Data JPA repositories.", "https://spring.io/projects/spring-boot"),
    DocEntry("FastAPI", "Async & Pydantic v2", "FastAPI async endpoints with Pydantic v2 BaseModel and Depends dependency injection.", "https://fastapi.tiangolo.com"),
    DocEntry("Node.js", "Async I/O & ES Modules", "Node.js native ES modules, async/await, fs/promises, and worker_threads.", "https://nodejs.org/docs"),
    DocEntry("Express.js", "Middleware Routing", "Express 4/5 router middleware, req/res lifecycle, async error handlers.", "https://expressjs.com"),
    DocEntry("Flutter", "State Management & Widgets", "Flutter 3.x MaterialApp, Stateless/StatefulWidget, Provider and Riverpod.", "https://docs.flutter.dev"),
    DocEntry("Docker", "Containerization", "Multi-stage Dockerfile builds with lightweight alpine/slim images and docker-compose.", "https://docs.docker.com"),
    DocEntry("Kubernetes", "Deployments & Ingress", "Kubernetes Pod, Deployment, Service, and NGINX Ingress Controller YAML specifications.", "https://kubernetes.io/docs"),
    DocEntry("LangChain", "LLM Chains & Agents", "LangChain LCEL (LangChain Expression Language) for prompt templates and output parsers.", "https://python.langchain.com/docs"),
    DocEntry("LlamaIndex", "Vector Indexes", "LlamaIndex VectorStoreIndex, SimpleDirectoryReader, and QueryEngine for RAG.", "https://docs.llamaindex.ai"),
    DocEntry("PyTorch", "Tensors & Neural Nets", "PyTorch torch.nn.Module, DataLoader, Autograd, and GPU CUDA acceleration.", "https://pytorch.org/docs"),
    DocEntry("TensorFlow", "Keras Models", "TensorFlow 2.x tf.keras Sequential, Model compilation, and fit training pipeline.", "https://www.tensorflow.org/api_docs"),
    DocEntry("Hugging Face", "Transformers", "Hugging Face transformers AutoModelForCausalLM and AutoTokenizer pipeline execution.", "https://huggingface.co/docs"),
    DocEntry("MDN Web Docs", "JavaScript & Web APIs", "MDN standard APIs for Web Speech, Fetch API, WebSockets, and Storage.", "https://developer.mozilla.org"),
]


class RAGDocsEngine:
    @staticmethod
    def search_docs(query: str, framework: Optional[str] = None) -> List[DocEntry]:
        lower_q = query.lower()
        results = []

        for doc in OFFICIAL_DOCS:
            if framework and framework.lower() not in doc.framework.lower():
                continue
            if any(term in doc.content.lower() or term in doc.topic.lower() or term in doc.framework.lower() for term in lower_q.split()):
                results.append(doc)

        return results if results else OFFICIAL_DOCS[:5]
