import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions
import yt_dlp
import logging

def get_youtube_transcript(video_id, languages=['en', 'en-US', 'en-GB']):
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    formatted_transcript = "\n".join([entry['text'] for entry in transcript])
    return formatted_transcript

def generate_notes_from_transcript(genai_model, transcript, prompt):
    response = genai_model.generate_content(prompt + transcript, stream=False)
    return response.text

def save_to_file(filename, text):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)

def load_from_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()

def get_chroma_collection():
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    CHROMA_API_KEY = os.getenv('CHROMA_API_KEY')
    CHROMA_TENANT = os.getenv('CHROMA_TENANT')
    CHROMA_DATABASE = os.getenv('CHROMA_DATABASE')
    if not all([GEMINI_API_KEY, CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE]):
        raise EnvironmentError("Missing one or more required environment variables: GEMINI_API_KEY, CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE")
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=GEMINI_API_KEY)
    chroma_client = chromadb.CloudClient(
        api_key=CHROMA_API_KEY,
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE)
    collection = chroma_client.get_or_create_collection(name='yt_notes', embedding_function=gemini_ef)
    return collection

def upsert_notes_to_chroma(collection, notes, video_id):
    collection.upsert(
        documents=[notes],
        ids=[video_id]
    )

def query_chroma(collection, query_text, n_results=5):
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=['documents', 'distances', 'metadatas'],
    )
    return results

def answer_question_with_context(genai_model, question, context):
    prompt = "Answer the following QUESTION using DOCUMENT as context."
    prompt += f"QUESTION: {question}"
    prompt += f"DOCUMENT: {context}"
    response = genai_model.generate_content(prompt, stream=False)
    return response.text

def get_video_ids_from_playlist(playlist_url):
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            return [entry['id'] for entry in info['entries'] if entry.get('ie_key') == 'Youtube']
    except Exception as e:
        logging.error(f"Failed to fetch playlist with yt-dlp: {e}")
        return []

def main():
    logging.basicConfig(level=logging.INFO)
    playlist_url = 'https://www.youtube.com/playlist?list=PLhjLcvbbPVrVOY5w5Pl7KuSe5fGroQJJD'
    prompt = "Extract key notes from video transcript: "
    video_ids = get_video_ids_from_playlist(playlist_url)
    if not video_ids:
        logging.error("No video IDs found in playlist.")
        return

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=GEMINI_API_KEY)
    genai_model = genai.GenerativeModel('models/gemini-2.5-pro')
    collection = get_chroma_collection()

    for yt_video_id in video_ids:
        try:
            logging.info(f"Processing video: {yt_video_id}")
            transcript = get_youtube_transcript(yt_video_id)
            save_to_file(f"temp_transcript_{yt_video_id}.txt", transcript)
            notes = generate_notes_from_transcript(genai_model, transcript, prompt)
            save_to_file(f"temp_notes_{yt_video_id}.txt", notes)
            upsert_notes_to_chroma(collection, notes, yt_video_id)
        except Exception as e:
            logging.error(f"Error processing video {yt_video_id}: {e}")

    # Example query (can be customized)
    query_text = "who is the best player and why?"
    n_results = 5
    results = query_chroma(collection, query_text, n_results)

    for i in range(len(results['ids'][0])):
        id = results["ids"][0][i]
        document = results['documents'][0][i]
        print("************************************************************************")
        print(f"{i+1}.  https://youtu.be/{id}")
        print("************************************************************************")
        print(document)

    if results['documents'][0]:
        answer = answer_question_with_context(genai_model, query_text, results['documents'][0][0])
        print("\nGemini Answer:")
        print(answer)

if __name__ == "__main__":
    main()