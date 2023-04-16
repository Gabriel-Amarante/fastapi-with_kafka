import nltk
nltk.download('stopwords')

import numpy as np
import cv2
from PIL import Image
import sys
import os
import pytesseract
import pdfplumber
from pdf2image import convert_from_path
from unidecode import unidecode
from difflib import SequenceMatcher



class DocumentExtractor():
    def __init__(self, path):
        self.dir_path = path

    def deskew(self, image):
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated

    def similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def get_text_from_pdf(self, conf=0):
        pages = convert_from_path(self.path, 300, fmt='jpeg')
        extracted_text = []
        for img in pages:
            img = np.array(img)
            if conf == 1:
                img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                kernel = np.ones((2, 2), np.uint8)
                img = cv2.dilate(img, kernel, iterations=1)
                img = cv2.erode(img, kernel, iterations=1)
                img = cv2.adaptiveThreshold(cv2.bilateralFilter(img, 9, 75, 75), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
                img = self.deskew(img)
            img = Image.fromarray(img)
            text = pytesseract.image_to_string(img, lang='por')
            extracted_text.append(text)
        return (extracted_text)

    def get_text_from_pdf_rot(self, conf=2):
        pages = convert_from_path(self.path, 300, fmt='jpeg')
        extracted_text = []
        for img in pages:
            img = np.array(img)
            altura, largura = img.shape[:2]
            ponto = (largura / 2, altura / 2) #ponto no centro da figura
            rotacao = cv2.getRotationMatrix2D(ponto, 180, 1.0)
            img = cv2.warpAffine(img, rotacao, (largura, altura))
            if conf == 1:
                img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                kernel = np.ones((2, 2), np.uint8)
                img = cv2.dilate(img, kernel, iterations=1)
                img = cv2.erode(img, kernel, iterations=1)
                img = cv2.adaptiveThreshold(cv2.bilateralFilter(img, 9, 75, 75), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
                img = self.deskew(img)
            img = Image.fromarray(img)
            text = pytesseract.image_to_string(img, lang='por')
            extracted_text.append(text)
        return (extracted_text)

    def read_file(self, config=0):
        pdf = pdfplumber.open(self.path)
        text = []
        for page in pdf.pages:
            text.append(page.extract_text())
        if None in text or '' in text:
            print("Handling file as image...")
            text = self.get_text_from_pdf(conf=config)
        if config == 2:
            print("Handling file as 180 degrees rotated image ...")
            text = self.get_text_from_pdf_rot(conf=config)
        text = ' (NEWPAGE) '.join(text)
        return text

    def clean_text(self, text, remove_stop_words=True):
        stop_words = nltk.corpus.stopwords.words("portuguese")
        text_by_words = text.replace('\n', ' ').split(' ')
        if remove_stop_words:
            formated_text = [unidecode(word.lower()) for word in text_by_words if (len(word) >= 1) & (word.lower() not in stop_words)]
        else:
            formated_text = [unidecode(word.lower()) for word in text_by_words if (len(word) >= 1)]
        return formated_text

    def get_prazo_clauses(self, text):
        sentences = []
        for idx, i in enumerate(text):
            if self.similar('clausula', i) > 0.7:
                clause = text[idx:]
                if any(test in clause[:10] for test in ['prazo', 'vigencia']):
                    for j in range(1, len(clause)):
                        if self.similar('clausula', clause[j]) > 0.7:
                            clause = clause[:j]
                            break
                    # print(' '.join(clause))
                    sentences.append(' '.join(clause))
        return sentences

    def read_all_documents(self):
        prazos = []
        if os.path.isdir(self.dir_path):
            for file in sorted(os.listdir(self.dir_path)):
                print('Reading File {}'.format(file))
                self.path = '{}/{}'.format(self.dir_path, file)
                text = self.read_file(config=1)
                print('Cleaning Texts')
                text = self.clean_text(text, remove_stop_words=False)
                print('Getting Prazos')
                sentences = self.get_prazo_clauses(text)
                if len(sentences) == 0:
                    print('Trying different configuration...')
                    print('Reading File {}'.format(self.dir_path))
                    self.path = '{}/{}'.format(self.dir_path, file)
                    text = self.read_file(config=0)
                    print('Cleaning Texts')
                    text = self.clean_text(text, remove_stop_words=False)
                    print('Getting Prazos')
                    sentences = self.get_prazo_clauses(text)
                if len(sentences) == 0:
                    print('Trying different configuration... rotating file')
                    print('Reading File {}'.format(self.dir_path))
                    self.path = '{}/{}'.format(self.dir_path, file)
                    text = self.read_file(config=2)
                    print('Cleaning Texts')
                    text = self.clean_text(text, remove_stop_words=False)
                    print('Getting Prazos')
                    sentences = self.get_prazo_clauses(text)
                prazos.append(sentences)
                print('\n')
        else:
            print('Reading File {}'.format(self.dir_path))
            self.path = self.dir_path
            text = self.read_file(config=0)
            print('Cleaning Texts')
            text = self.clean_text(text, remove_stop_words=False)
            print('Getting Prazos')
            sentences = self.get_prazo_clauses(text)
            if len(sentences) == 0:
                print('Trying different configuration...')
                print('Reading File {}'.format(self.dir_path))
                self.path = self.dir_path
                text = self.read_file(config=1)
                print('Cleaning Texts')
                text = self.clean_text(text, remove_stop_words=False)
                print('Getting Prazos')
                sentences = self.get_prazo_clauses(text)
            if len(sentences) == 0:
                print('Trying different configuration... rotating file')
                print('Reading File {}'.format(self.dir_path))
                self.path = self.dir_path
                text = self.read_file(config=2)
                print('Cleaning Texts')
                text = self.clean_text(text, remove_stop_words=False)
                print('Getting Prazos')
                sentences = self.get_prazo_clauses(text)
            prazos.append(sentences)
            print('\n')
        return prazos

    def write_prazos(self, path, prazos):
        erros = []
        with open(os.path.join(path, 'output.txt'), 'w') as f:
            for i in range(len(prazos)):
                f.write('FILE: {}\n'.format(i))
                if len(prazos) == 0:
                    erros.append(i)
                    f.write('NONE FOUND! \n')
                for _string in prazos[i]:
                    f.write(str(_string) + '\n')
                f.write('\n')

def main(path):
    pathpdf = os.path.join(path, "pdf", "")
    # path = './documents/contratante/00.pdf'
    extractor = DocumentExtractor(pathpdf)
    prazos = extractor.read_all_documents()
    extractor.write_prazos(path, prazos)


#if __name__ == "__main__":
#    path = sys.argv[1]
#    # path = './documents/contratante/00.pdf'
#    extractor = DocumentExtractor(path)
#    prazos = extractor.read_all_documents()
#    extractor.write_prazos(prazos)
