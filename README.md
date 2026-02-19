Django Digital Library System with ML Recommendation Engine
Overview

A production-oriented Digital Library System built using Django and PostgreSQL, enhanced with AI-powered book preview generation and a semantic recommendation engine based on vector embeddings.

This project demonstrates backend system design, relational database modeling, AI integration, and containerized deployment using Docker.

Features

Book catalog management (CRUD operations)

PostgreSQL relational database design

Book borrowing and tracking system

AI-generated book previews

Semantic search using embeddings

ML-based recommendation engine

Admin dashboard

Docker and Docker Compose configuration

Secure API key management using environment variables

Tech Stack
Backend

Python

Django

Database

PostgreSQL

AI / ML

OpenAI API (embeddings and preview generation)

Groq API (LLM inference)

DevOps

Docker

Docker Compose

Recommendation Engine Logic

Book descriptions are converted into vector embeddings.

Embeddings are stored in the database.

User queries are embedded using the same model.

Cosine similarity is calculated between vectors.

Top-N most similar books are returned as recommendations.

This enables semantic similarity matching rather than simple keyword-based filtering.

Future Improvements

Add user authentication and role-based access

Convert to REST API using Django REST Framework

Add frontend using React

Deploy to AWS / Render

Add automated testing and CI/CD pipeline
