import os
import json
import chromadb
from chromadb.utils import embedding_functions

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'db', 'laws_db')
CHUNKS_DIR = os.path.join(SCRIPT_DIR, 'data', 'law_processed', 'chunks_doc')
COLLECTION_NAME = 'laws_collection'

# создает векторную базу данных ChromaDB, возвращает клиент и коллекцию
def create_database(db_path=DB_PATH):
    client = chromadb.PersistentClient(path=db_path)

    ru_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ru_ef,
        metadata={"hnsw:space": "cosine"}  # косинусное расстояние для поиска
    )

    print(f'База данных: {os.path.abspath(db_path)}')
    print(f'Коллекция: {collection.name}')
    print(f'Документов в базе: {collection.count()}')

    return client, collection

# читает все *_chunks.json файлы из папки и возвращает список кусочков
def load_chunks_from_json(chunks_dir=CHUNKS_DIR):
    all_chunks = []

    for file_name in sorted(os.listdir(chunks_dir)):
        if file_name.endswith('_chunks.json'):
            file_path = os.path.join(chunks_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)

            print(f' {file_name}: {len(chunks)} кусочков')
            all_chunks.extend(chunks)

    print(f'\n Всего кусочков для загрузки: {len(all_chunks)}')
    return all_chunks

# сохр куски в коллекцию ChromaDB, ChromaDB сам создаст векторы (эмбеддинги) из текста
def save_to_database(chunks, collection):
    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        source_file = chunk['source_file']
        base_name = os.path.splitext(source_file)[0]
        ids.append(f"{base_name}_{chunk['id']}")
        documents.append(chunk['text'])
        metadatas.append({
            'source_file': str(source_file),
            'page_number': int(chunk['page']),
            'section_title': str(chunk['section_title']),
            'doc_type': str(chunk['doc_type']),
            'chunk_number': int(chunk['chunk_number'])
        })

    if collection.count() > 0:
        print(f' Очищаю коллекцию ({collection.count()} документов)...')
        collection.delete(where={})

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f' Сохранено в базу: {len(ids)} кусочков')
    print(f' Всего документов в базе: {collection.count()}')

def main():
    """
    1. Создаёт/открывает базу данных
    2. Загружает кусочки из JSON
    3. Сохраняет в базу
    4. Делает тестовый поиск
    """
    print("=== Сохранение в векторную базу данных ===\n")
    
    client, collection = create_database()
    print()
    
    chunks = load_chunks_from_json()
    print()
    
    save_to_database(chunks, collection)


if __name__ == '__main__':
    main()