# ChromaDB Learning Journey

This repository documents my personal log dump on [ChromaDB](https://www.trychroma.com/) and vector databases.

## Project Structure

```
chromadb-labs/
│
├── README.md                # Project overview and setup instructions
├── requirements.txt         # Python dependencies
└── scripts/                 # Python scripts for experiments and learning
```

## Getting Started

1. **Clone the repo**
   ```sh
   git clone https://github.com/kevinjosephh/chromadb-labs
   cd chromadb-labs
   ```

2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Create a `.env` file in the project root and add:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     CHROMA_API_KEY=your_chromadb_api_key_here
     CHROMA_TENANT=your_chromadb_tenant_here
     CHROMA_DATABASE=your_chromadb_database_here
     ```

4. **Run scripts**
   - Navigate to the `scripts/` directory and run the desired Python script, for example:
     ```sh
     python scripts/chroma_ingest.py
     ```

## References

- [ChromaDB Learning Playlist](https://www.youtube.com/playlist?list=PL58zEckBH8fA-R1ifTjTIjrdc3QKSk6hI)
- [Specific Video: ChromaDB Tutorial](https://www.youtube.com/watch?v=QSW2L8dkaZk&list=PL58zEckBH8fA-R1ifTjTIjrdc3QKSk6hI&index=2)

## License

MIT 