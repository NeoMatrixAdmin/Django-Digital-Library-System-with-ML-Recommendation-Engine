# Django Digital Library System with ML Recommendation Engine

## Overview

A production-oriented Digital Library System built using Django and PostgreSQL, enhanced with AI-powered book preview generation and a semantic recommendation engine based on vector embeddings.

This project demonstrates backend system design, relational database modeling, AI integration, and containerized deployment using Docker.

---

## Features

- Book catalog management (CRUD operations)
- PostgreSQL relational database integration
- Book borrowing and tracking system
- AI-generated book previews
- Semantic search using embeddings
- ML-based recommendation engine
- Admin dashboard
- Docker and Docker Compose setup
- Secure API key handling using environment variables

---

## Tech Stack

### Backend
- Python
- Django

### Database
- PostgreSQL

### AI / Machine Learning
- OpenAI API (embeddings and preview generation)
- Groq API (LLM inference)

### DevOps
- Docker
- Docker Compose

---

## Recommendation Engine Design

1. Book descriptions are converted into vector embeddings.
2. Embeddings are stored in the database.
3. User queries are embedded using the same model.
4. Cosine similarity is computed between vectors.
5. Top-N most similar books are returned as recommendations.

This enables semantic similarity matching instead of keyword-based filtering.

---
