import os
import json
import re

# удаляет мусор (колонтитулы, номера страниц, URL, даты, оглавление и тд) после парсинга
def clean_text(text):
    # удаляем колонтитулы ФЗ: "ФЗ от 18.07.2011 № 223-ФЗ, официальный текст, актуальная"
    text = re.sub(r'ФЗ от\s+\d{2}\.\d{2}\.\d{4}\s+№\s*\d+-ФЗ[^\n]*', '', text)
    
    # удаляем URL
    text = re.sub(r'https?://[^\s]+', '', text)
    
    # удаляем "Стр. N из M"
    text = re.sub(r'Стр\.\s+\d+\s+из\s+\d+', '', text)
    
    # удаляем даты-времени "22.10.2026, 17:48"
    text = re.sub(r'\d{2}\.\d{2}\.\d{4},\s+\d{2}:\d{2}', '', text)
    
    # удаляем дублирующиеся номера страниц типа "252 252"
    text = re.sub(r'\b(\d+)\s+\1\b', r'\1', text)
    
    # удаляем оглавление (блок со строками типа "1 Область применения......1")
    # ищем паттерн: число + текст + много точек + число в конце строки
    text = re.sub(r'^\s*\d+\s+[^\n]{2,60}\.{3,}[^\n]*\d+\s*$', '', text, flags=re.MULTILINE)
    
    # удаляем слово "Содержание" как заголовок
    text = re.sub(r'^\s*Содержание\s*$', '', text, flags=re.MULTILINE)
    
    # удаляем "Предисловие" как заголовок (для ГОСТ)
    text = re.sub(r'^\s*Предисловие\s*$', '', text, flags=re.MULTILINE)
    
    # удаляем множественные переносы строк (более 2 подряд)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

# определяем тип дока по имени файла
def detect_document_type(file_name):
    name_lower = file_name.lower()
    
    if 'fz' in name_lower or 'фз' in name_lower:
        return 'fz'
    
    if name_lower.startswith('gost') or name_lower.startswith('гост'):
        return 'gost'
    
    if name_lower.startswith('polozhenie') or name_lower.startswith('положение'):
        return 'regulation'
    
    return 'unknown'

# разбитие ФЗ по статьям
def split_by_articles(text):
    # паттерн: начало строки + "Статья" + пробелы + число (возможно с точками) + точка/пробел/перенос
    pattern = r'(?=(?:^|\n)\s*Статья\s+\d+(?:\.\d+)*\s*[.\n])'
    parts = re.split(pattern, text)
    return [p.strip() for p in parts if p.strip()]

# разбиение ГОСТ по разделам
def split_by_sections_gost(text):
    # число + возможные подпункты + пробел + заглавная буква
    pattern = r'(?=(?:^|\n)\s*\d+(?:\.\d+)*\s+[А-ЯA-Z])'
    parts = re.split(pattern, text)
    return [p.strip() for p in parts if p.strip()]

# разбиение Положения по пунктам/главам
def split_by_sections_regulation(text):
    # сначала пытаемся разбить по "Глава/Раздел"
    pattern_chapter = r'(?=(?:^|\n)\s*(?:Глава|Раздел)\s+)'
    parts = re.split(pattern_chapter, text)
    
    # если нашли главы — используем их
    if len(parts) > 1:
        return [p.strip() for p in parts if p.strip()]
    
    # иначе разбиваем по пунктам с точкой
    pattern = r'(?=(?:^|\n)\s*\d+\.\d*\s+[А-ЯA-Z])'
    parts = re.split(pattern, text)
    return [p.strip() for p in parts if p.strip()]

# выбор способа разбиения по типу доку
def split_into_logical_blocks(text, doc_type):
    if doc_type == 'fz':
        return split_by_articles(text)
    elif doc_type == 'gost':
        return split_by_sections_gost(text)
    elif doc_type == 'regulation':
        return split_by_sections_regulation(text)
    else:
        # если тип не определили — разбиваем по абзацам
        return [p.strip() for p in text.split('\n\n') if p.strip()]

# извлечение короткого заголовка блока, статьи, раздела
def extract_section_title(block, doc_type):
    # ФЗ
    if doc_type == 'fz':
        match = re.match(r'(Статья\s+\d+(?:\.\d+)*)', block)
        if match:
            return match.group(1).strip()
    
    # ГОСТ/Положение
    first_line = block.split('\n')[0].strip()
    return first_line[:80]

# обновление страницы, иначе наследуем последний
def get_page_for_chunk(chunk_text, current_page):
    match = re.search(r'[Сс]траница\s+(\d+)', chunk_text)
    if match:
        return int(match.group(1))
    return current_page

# обработка
def process_one_file(file_path, output_dir):
    """
    1. Читает текст
    2. Очищает от мусора
    3. Разбивает на полные статьи/разделы
    4. Сохраняет в JSON
    """
    file_name = os.path.basename(file_path)
    
    # чтение файла
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # очищстка от мусора
    text = clean_text(text)
    
    # определение типа
    doc_type = detect_document_type(file_name)
    
    # разбиение на логические блоки (каждый блок = статья)
    blocks = split_into_logical_blocks(text, doc_type)
    
    print(f'  Тип: {doc_type}')
    print(f'  Найдено блоков (статей/разделов): {len(blocks)}')
    
    all_chunks = []
    chunk_counter = 0
    current_page = 0
    
    for block in blocks:
        # номер стр
        current_page = get_page_for_chunk(block, current_page)

        clean_block = re.sub(r'\s*Страница\s+\d+\s*', '\n', block).strip()

        # извлечение заголовока блока
        section_title = extract_section_title(clean_block, doc_type)
        
        # создание чанка — весь блок целиком, без деления
        chunk_data = {
            'id': f"chunk_{chunk_counter}",
            'text': clean_block,
            'source_file': file_name,
            'section_title': section_title,
            'doc_type': doc_type,
            'page': current_page,
            'chunk_number': chunk_counter
        }
        all_chunks.append(chunk_data)
        chunk_counter += 1
    
    # сохр в JSON 
    base_name = os.path.splitext(file_name)[0]
    output_path = os.path.join(output_dir, f"{base_name}_chunks.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    print(f'  Создано чанков: {len(all_chunks)}')
    print(f'  Сохранено: {output_path}')
    
    return len(all_chunks)

# обработка txtшек для каждой свой JSON
def process_all_files():
    # пути относительно расположения скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, 'data', 'law_processed', 'txt_doc')
    output_dir = os.path.join(script_dir, 'data', 'law_processed', 'chunks_doc')
    
    # папка резов
    os.makedirs(output_dir, exist_ok=True)
    
    print(f'=== Начало обработки ===\n')
    
    total_chunks = 0
    processed_files = 0
    
    for file_name in sorted(os.listdir(input_dir)):
        if file_name.endswith('.txt'):
            file_path = os.path.join(input_dir, file_name)
            
            print(f'Файл: {file_name}')

            count = process_one_file(file_path, output_dir)
            total_chunks += count
            processed_files += 1
            
            print()
    
    print(f'=== Готово! Файлов: {processed_files}, чанков: {total_chunks} ===')
    
    return processed_files


if __name__ == '__main__':
    process_all_files()