from setuptools import setup, find_packages

setup(
    name="thinkubator-rag",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "python-multipart",
        "langchain",
        "langchain-community",
        "langchain-openai",
        "pypdf",
        "langchain-google-genai",
        "pytest",
        "google-generativeai",
        "chromadb",
        "python-dotenv",
        "streamlit",
    ],
    extras_require={
        "dev": [
            "pytest",
        ],
    },
)
