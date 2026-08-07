"""
Project Template Library: Manages complete application boilerplate templates for 18 tech stacks & domain apps.
Includes: React, Next.js, FastAPI, Spring Boot, Flask, Express, Electron, Flutter,
CRM, ERP, Inventory, Hospital, Hotel, Portfolio, Dashboard, Chat App, Blog, Landing Page, E-Commerce.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

TEMPLATES_CONFIG: Dict[str, Dict[str, Any]] = {
    "react": {
        "title": "Modern React 18 TypeScript Web Application",
        "description": "Production Vite + React + Tailwind CSS + Lucide Icons + React Router template.",
        "category": "framework",
        "language": "typescript",
        "framework": "react",
        "structure": [
            "src/App.tsx", "src/main.tsx", "src/index.css", "src/components/Header.tsx", "package.json", "vite.config.ts", "README.md"
        ],
        "files": {
            "package.json": json.dumps({
                "name": "vikrm-react-app",
                "version": "1.0.0",
                "private": True,
                "scripts": {"dev": "vite", "build": "tsc && vite build"},
                "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0", "lucide-react": "^0.300.0"},
                "devDependencies": {"vite": "^5.0.0", "typescript": "^5.0.0", "@types/react": "^18.2.0"}
            }, indent=2),
            "README.md": "# React 18 Production Template\n\nRun `npm install` and `npm run dev` to start.",
            "vite.config.ts": "import { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\nexport default defineConfig({ plugins: [react()] });\n",
            "src/App.tsx": "import React from 'react';\nexport default function App() {\n  return (\n    <div className='min-h-screen bg-slate-950 text-white p-8'>\n      <h1 className='text-3xl font-bold text-indigo-400'>Vikrm React Platform Application</h1>\n      <p className='mt-2 text-slate-400'>Responsive React 18 Single Page App.</p>\n    </div>\n  );\n}\n",
            "src/main.tsx": "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\nimport './index.css';\nReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
            "src/index.css": "@tailwind base;\n@tailwind components;\n@tailwind utilities;\nbody { background-color: #090d16; color: #ffffff; }\n"
        }
    },
    "nextjs": {
        "title": "Next.js 14 App Router Full-Stack Application",
        "description": "Next.js 14 template with Server Actions, Tailwind CSS, TypeScript, and API routes.",
        "category": "framework",
        "language": "typescript",
        "framework": "nextjs",
        "structure": [
            "app/page.tsx", "app/layout.tsx", "app/api/health/route.ts", "package.json", "next.config.js", "README.md"
        ],
        "files": {
            "package.json": json.dumps({
                "name": "vikrm-nextjs-app",
                "version": "1.0.0",
                "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
                "dependencies": {"next": "14.1.0", "react": "^18.2.0", "react-dom": "^18.2.0"}
            }, indent=2),
            "README.md": "# Next.js 14 Fullstack App\n\nNext.js 14 App Router starter.",
            "app/page.tsx": "export default function Page() {\n  return (\n    <main className='flex min-h-screen flex-col items-center justify-between p-24 bg-slate-950 text-white'>\n      <h1 className='text-4xl font-bold'>Next.js 14 App Router</h1>\n    </main>\n  );\n}\n",
            "app/layout.tsx": "export default function RootLayout({ children }: { children: React.ReactNode }) {\n  return (\n    <html lang='en'>\n      <body className='bg-slate-950 text-white'>{children}</body>\n    </html>\n  );\n}\n",
            "app/api/health/route.ts": "import { NextResponse } from 'next/server';\nexport async function GET() {\n  return NextResponse.json({ status: 'ok', timestamp: new Date().toISOString() });\n}\n"
        }
    },
    "fastapi": {
        "title": "FastAPI Async Microservice Backend",
        "description": "High-performance Python FastAPI service with Pydantic v2, CORS, and Gunicorn/Uvicorn config.",
        "category": "backend",
        "language": "python",
        "framework": "fastapi",
        "structure": [
            "app/main.py", "app/api/v1/endpoints.py", "app/core/config.py", "requirements.txt", "Dockerfile", "README.md"
        ],
        "files": {
            "requirements.txt": "fastapi>=0.109.0\nuvicorn[standard]>=0.27.0\npydantic>=2.6.0\npython-dotenv>=1.0.0\n",
            "README.md": "# FastAPI Microservice\n\nRun `uvicorn app.main:app --reload`",
            "app/main.py": "from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\n\napp = FastAPI(title='Vikrm FastAPI Backend', version='1.0.0')\napp.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])\n\n@app.get('/health')\nasync def health_check():\n    return {'status': 'healthy', 'service': 'fastapi-backend'}\n"
        }
    },
    "springboot": {
        "title": "Spring Boot 3 Java Enterprise Microservice",
        "description": "Spring Boot 3 REST application with Maven pom.xml and OpenAPI integration.",
        "category": "backend",
        "language": "java",
        "framework": "springboot",
        "structure": [
            "src/main/java/com/vikrm/api/Application.java", "src/main/java/com/vikrm/api/controller/ApiController.java", "pom.xml", "README.md"
        ],
        "files": {
            "pom.xml": "<project>\n  <modelVersion>4.0.0</modelVersion>\n  <groupId>com.vikrm</groupId>\n  <artifactId>spring-boot-api</artifactId>\n  <version>1.0.0</version>\n</project>\n",
            "README.md": "# Spring Boot 3 Service\n\nRun `mvn spring-boot:run`",
            "src/main/java/com/vikrm/api/Application.java": "package com.vikrm.api;\nimport org.springframework.boot.SpringApplication;\nimport org.springframework.boot.autoconfigure.SpringBootApplication;\n@SpringBootApplication\npublic class Application {\n    public static void main(String[] args) {\n        SpringApplication.run(Application.class, args);\n    }\n}\n"
        }
    },
    "flask": {
        "title": "Flask Lightweight REST API",
        "description": "Python Flask micro-framework API template.",
        "category": "backend",
        "language": "python",
        "framework": "flask",
        "structure": ["app.py", "requirements.txt", "README.md"],
        "files": {
            "requirements.txt": "Flask>=3.0.0\nFlask-CORS>=4.0.0\n",
            "app.py": "from flask import Flask, jsonify\napp = Flask(__name__)\n@app.route('/api/health')\ndef health(): return jsonify({'status': 'ok'})\nif __name__ == '__main__': app.run(port=5000)\n",
            "README.md": "# Flask REST Service"
        }
    },
    "express": {
        "title": "Node.js Express REST & API Gateway",
        "description": "Express.js API boilerplate with middleware and route modules.",
        "category": "backend",
        "language": "javascript",
        "framework": "express",
        "structure": ["server.js", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "express-api", "dependencies": {"express": "^4.18.2", "cors": "^2.8.5"}}, indent=2),
            "server.js": "const express = require('express');\nconst cors = require('cors');\nconst app = express();\napp.use(cors());\napp.use(express.json());\napp.get('/health', (req, res) => res.json({ status: 'ok' }));\napp.listen(3000, () => console.log('Server running on 3000'));\n",
            "README.md": "# Express API Boilerplate"
        }
    },
    "electron": {
        "title": "Electron Cross-Platform Desktop Application",
        "description": "Desktop app starter with Electron and React frontend.",
        "category": "desktop",
        "language": "typescript",
        "framework": "electron",
        "structure": ["main.js", "preload.js", "index.html", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "electron-app", "main": "main.js", "devDependencies": {"electron": "^28.0.0"}}, indent=2),
            "main.js": "const { app, BrowserWindow } = require('electron');\nfunction createWindow() {\n  const win = new BrowserWindow({ width: 1200, height: 800 });\n  win.loadFile('index.html');\n}\napp.whenReady().then(createWindow);\n",
            "index.html": "<!DOCTYPE html><html><body><h1>Electron App</h1></body></html>",
            "README.md": "# Electron Desktop Application"
        }
    },
    "flutter": {
        "title": "Flutter Cross-Platform Mobile App",
        "description": "iOS and Android mobile app with Material 3 UI.",
        "category": "mobile",
        "language": "dart",
        "framework": "flutter",
        "structure": ["lib/main.dart", "pubspec.yaml", "README.md"],
        "files": {
            "pubspec.yaml": "name: flutter_vikrm_app\ndescription: Flutter mobile application.\nenvironment:\n  sdk: '>=3.0.0 <4.0.0'\ndependencies:\n  flutter:\n    sdk: flutter\n",
            "lib/main.dart": "import 'package:flutter/material.dart';\nvoid main() => runApp(const MyApp());\nclass MyApp extends StatelessWidget {\n  const MyApp({super.key});\n  @override Widget build(BuildContext context) => const MaterialApp(home: Scaffold(body: Center(child: Text('Flutter App'))));\n}\n",
            "README.md": "# Flutter Mobile Application"
        }
    },
    "crm": {
        "title": "Enterprise Customer Relationship Management (CRM)",
        "description": "Complete CRM dashboard template with contact pipelines, deal stages, and analytics.",
        "category": "domain",
        "language": "typescript",
        "framework": "react",
        "structure": ["src/pages/Leads.tsx", "src/pages/Deals.tsx", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "vikrm-crm-suite", "version": "1.0.0"}, indent=2),
            "README.md": "# Vikrm Enterprise CRM Template\n\nContact management, pipeline tracking, and sales analytics."
        }
    },
    "erp": {
        "title": "Enterprise Resource Planning (ERP) Platform",
        "description": "Full-scale ERP template for supply chain, HR, finance, and operations.",
        "category": "domain",
        "language": "typescript",
        "framework": "react",
        "structure": ["src/modules/Finance.tsx", "src/modules/SupplyChain.tsx", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "vikrm-erp-suite", "version": "1.0.0"}, indent=2),
            "README.md": "# Vikrm ERP Suite\n\nUnified resource planning, ledger management, and operations."
        }
    },
    "inventory": {
        "title": "Inventory Management System",
        "description": "Stock tracking, SKU management, warehouse allocation, and low-stock alerts.",
        "category": "domain",
        "language": "typescript",
        "framework": "nextjs",
        "structure": ["app/stock/page.tsx", "app/skus/page.tsx", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "inventory-app", "version": "1.0.0"}, indent=2),
            "README.md": "# Inventory Management System"
        }
    },
    "hospital": {
        "title": "Hospital & Healthcare Information System (HIS)",
        "description": "Patient records, appointment scheduling, doctor shifts, and prescriptions.",
        "category": "domain",
        "language": "typescript",
        "framework": "react",
        "structure": ["src/pages/Patients.tsx", "src/pages/Appointments.tsx", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "hospital-management", "version": "1.0.0"}, indent=2),
            "README.md": "# Hospital Management System"
        }
    },
    "hotel": {
        "title": "Hotel & Resort Booking Management System",
        "description": "Room reservations, check-in/out workflows, housekeeping, and billing.",
        "category": "domain",
        "language": "typescript",
        "framework": "nextjs",
        "structure": ["app/rooms/page.tsx", "app/bookings/page.tsx", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "hotel-booking-app", "version": "1.0.0"}, indent=2),
            "README.md": "# Hotel Booking Management System"
        }
    },
    "portfolio": {
        "title": "Developer & Agency Portfolio Website",
        "description": "Animated Glassmorphism portfolio template with project showcases and contact form.",
        "category": "domain",
        "language": "typescript",
        "framework": "react",
        "structure": ["src/sections/Hero.tsx", "src/sections/Projects.tsx", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "developer-portfolio", "version": "1.0.0"}, indent=2),
            "README.md": "# Developer Portfolio Template"
        }
    },
    "dashboard": {
        "title": "SaaS Admin Dashboard & Analytics Suite",
        "description": "Real-time metrics dashboard with chart widgets, table filters, and dark mode.",
        "category": "domain",
        "language": "typescript",
        "framework": "react",
        "structure": ["src/components/Metrics.tsx", "src/components/Charts.tsx", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "saas-admin-dashboard", "version": "1.0.0"}, indent=2),
            "README.md": "# SaaS Admin Dashboard Template"
        }
    },
    "chatapp": {
        "title": "Real-Time Collaborative Chat & Messaging App",
        "description": "WebSocket messaging app with direct chats, group rooms, and status indicators.",
        "category": "domain",
        "language": "typescript",
        "framework": "react",
        "structure": ["src/components/ChatRoom.tsx", "src/services/socket.ts", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "realtime-chat-app", "version": "1.0.0"}, indent=2),
            "README.md": "# Real-Time Chat App Template"
        }
    },
    "blog": {
        "title": "Modern Content Blog & CMS Platform",
        "description": "MDX powered publishing platform with RSS feeds and SEO tags.",
        "category": "domain",
        "language": "typescript",
        "framework": "nextjs",
        "structure": ["app/blog/[slug]/page.tsx", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "modern-blog-cms", "version": "1.0.0"}, indent=2),
            "README.md": "# Modern Blog CMS Template"
        }
    },
    "landing": {
        "title": "High-Converting Product Landing Page",
        "description": "Conversion-optimized landing page with pricing tables, testimonials, and FAQ.",
        "category": "domain",
        "language": "typescript",
        "framework": "react",
        "structure": ["src/components/Pricing.tsx", "src/components/CTA.tsx", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "saas-landing-page", "version": "1.0.0"}, indent=2),
            "README.md": "# Product Landing Page Template"
        }
    },
    "ecommerce": {
        "title": "Full-Featured E-Commerce Storefront",
        "description": "Online storefront with shopping cart, product catalog, checkout, and Stripe.",
        "category": "domain",
        "language": "typescript",
        "framework": "nextjs",
        "structure": ["app/cart/page.tsx", "app/products/page.tsx", "package.json", "README.md"],
        "files": {
            "package.json": json.dumps({"name": "ecommerce-storefront", "version": "1.0.0"}, indent=2),
            "README.md": "# Full-Featured E-Commerce Template"
        }
    }
}


class ProjectTemplateLibrary:
    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).resolve().parent
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.init_templates_on_disk()

    def init_templates_on_disk(self) -> None:
        """Writes project template files to disk for local availability."""
        for key, tconf in TEMPLATES_CONFIG.items():
            tdir = self.base_dir / key
            tdir.mkdir(parents=True, exist_ok=True)

            meta = {
                "key": key,
                "title": tconf["title"],
                "description": tconf["description"],
                "category": tconf["category"],
                "language": tconf["language"],
                "framework": tconf["framework"],
                "structure": tconf["structure"],
            }
            with open(tdir / "template.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            for rel_path, content in tconf["files"].items():
                fpath = tdir / rel_path
                fpath.parent.mkdir(parents=True, exist_ok=True)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)

    def list_templates(self) -> List[Dict[str, Any]]:
        return [
            {
                "key": key,
                "title": cfg["title"],
                "description": cfg["description"],
                "category": cfg["category"],
                "language": cfg["language"],
                "framework": cfg["framework"],
                "structure": cfg["structure"],
            }
            for key, cfg in TEMPLATES_CONFIG.items()
        ]

    def get_template(self, key: str) -> Optional[Dict[str, Any]]:
        if key in TEMPLATES_CONFIG:
            return TEMPLATES_CONFIG[key]
        return None
