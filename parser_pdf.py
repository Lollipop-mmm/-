# парсер который превращает PDF-файлы в txt
import os
from PyPDF2 import PdfReader

def parser_PDFs(original_dir = 'data/laws', final_dir = 'data/law_processed/txt_doc'):
    os.makedirs(final_dir, exist_ok=True)

    for fileName in os.listdir(original_dir):
        if fileName.endswith('.pdf'):
            pdf_path = os.path.join(original_dir, fileName)
            txt_path = os.path.join(final_dir, fileName.replace('.pdf', '.txt'))

            reader = PdfReader(pdf_path)
            text = ''

            for pageNum,  page in enumerate(reader.pages, 1):
                text += f'\n    Страница {pageNum}    \n'
                text += page.extract_text()
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f'Обработан: {fileName}')

if __name__ == '__main__':
    parser_PDFs()

            