import os
import getpass
from pprint import pprint, pformat
import sys
sys.path.insert(0,".")

from tqdm import tqdm

from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_community.llms import LlamaCpp
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
from langchain_community.document_loaders.merge import MergedDataLoader

from openai import OpenAI
from langchain import PromptTemplate
import asyncio
import glob
import pickle

from doc_dialog.pdf2txt import pdf_to_structured_md_pages_pkl
import shutil


DATA_PATH = "/workspace/data/"
FAISS_VOLUME_PATH = "/workspace/volumes/pdf_ctransformers_faiss/"
class DocumentLoader:
    def __init__(self, faiss_volume_path = FAISS_VOLUME_PATH, pdf_folder_path = DATA_PATH, verbose = False):
        self.verbose = verbose
        self.faiss_volume_path = faiss_volume_path
        self.pdf_folder_path = pdf_folder_path




    def load_documents_from_pdf(self, pdf_path):
        """converts a pdf to structured markdown pages and loads them as documents.

        Args:
            pdf_path (_type_): input pdf path

        Returns:
            _type_: list of documents
        """        
        structured_md_pages_path = pdf_to_structured_md_pages_pkl(pdf_path)
        documents = self.load_documents_from_structured_md_pages_pkl(structured_md_pages_path)
        return documents
    
    def add_documents_from_pdf(self, pdf_path):
        """add a pdf to the vector store.

        Args:
            pdf_path (_type_): path of the pdf
        """        
        documents = self.load_documents_from_pdf(pdf_path)
        self.db.add_documents(documents)
        print(f"added document to db: {pdf_path}")
    
    def remove_document(self, pdf_name):
        """remove a pdf from the vector store

        Args:
            pdf_name (_type_): filename of the pdf without path
        """        
        documents_in_store = self.get_documents_in_store()
        ids_to_be_deleted = documents_in_store[pdf_name]
        self.db.delete(ids = ids_to_be_deleted)
    
    def delete_pdf_from_hd(self, pdf_name):
        """delete a pdf from the volume

        Args:
            pdf_name (_type_): name of the pdf without path
        """        
        pdf_path = f"{self.pdf_folder_path}{pdf_name}"
        os.remove(pdf_path)
        print(f"deleted from hd: {pdf_path}")
    
    def add_pdf_to_hd(self, pdf_path):
        """store a pdf to the volume

        Args:
            pdf_path (_type_): path of the pdf to be stored
        """        
        pdf_name = os.path.basename(pdf_path)
        new_pdf_path = f"{self.pdf_folder_path}{pdf_name}"
        shutil.copyfile(pdf_path, new_pdf_path)
        print(f"added to hd: {pdf_path}")

    def save_db(self):
        """persist the current state of the vector store
        """        
        self.db.save_local(self.faiss_volume_path)

    def load_documents_from_structured_md_pages_pkl(self, structured_md_pages_path):
        """load documents from a structured markdown pickle

        Args:
            structured_md_pages_path (_type_): path to the structured markdown pickle

        Returns:
            _type_: list of documents
        """        
        documents = []
        with open(structured_md_pages_path, "rb") as f:
            md_pages = pickle.load(f)
        for md_page in md_pages:

            num_sections = len(md_page["sections"])
            for idx_section, (section, body) in enumerate(md_page["sections"].items()):
                page_content = "\n".join(body)
                page_content = page_content.replace("NO_TITLE","")
                metadata = md_page["metadata"]
                metadata["section_title"] = section
                metadata["source"] = metadata["file_path"]
                metadata["section_index"] = idx_section
                metadata["section_count"] = num_sections
                doc = Document(
                    page_content=page_content,
                    metadata=metadata
                )
                #pprint(doc)
                documents.append(doc)
        return documents

    def load_documents_from_structured_md_pages(self, structured_md_pages_pkl_folder_path):
        """load documents from a folder containing structured markdown pickles

        Args:
            structured_md_pages_pkl_folder_path (_type_): folder path

        Returns:
            _type_: list of documents
        """        
        documents = []
        for pkl_path in tqdm(glob.glob(f"{structured_md_pages_pkl_folder_path}*.pkl")):
            with open(pkl_path, "rb") as f:
                md_pages = pickle.load(f)
            for md_page in md_pages:
                #pprint(md_page)
                num_sections = len(md_page["sections"])
                for idx_section, (section, body) in enumerate(md_page["sections"].items()):
                    page_content = "\n".join(body)
                    page_content = page_content.replace("NO_TITLE","")
                    metadata = md_page["metadata"]
                    metadata["section_title"] = section
                    metadata["source"] = metadata["file_path"]
                    metadata["section_index"] = idx_section
                    metadata["section_count"] = num_sections
                    doc = Document(
                        page_content=page_content,
                        metadata=metadata
                    )
                    #pprint(doc)
                    documents.append(doc)
        return documents

    def create_db(self, documents):
        """create and save a vector store from documents

        Args:
            documents (_type_): documents to be stored in the vector store
        """        
        texts = documents
        db = FAISS.from_documents(texts, self.embedding_model)
        db.save_local(self.faiss_volume_path )
    


    def load_db(self):
        """load the vectore store
        """        
        self.db = FAISS.load_local(self.faiss_volume_path, self.embedding_model, allow_dangerous_deserialization = True)
        print("loaded DB")

    def retrieve_document_pages(self, question, num_pages):
        """ask a question to the documents in the vector store and receive a list of document pages

        Args:
            question (_type_): question to be asked
            num_pages (_type_): number of documents to be returned

        Returns:
            _type_: list
        """        
        question = question.strip()

        docs_and_scores = self.db.similarity_search_with_score(question, k = num_pages)

        document_pages = []
        for result in docs_and_scores:
            info = []
            info.append(result[1])
            info.append(result[0].metadata["source"])
            info.append(result[0].metadata["page"])
            info.append(result[0].page_content[:50])

            document_pages.append([info,result[0]])
        return document_pages
    
    def get_documents_in_store(self):
        """get the document keys in the store

        Returns:
            _type_: list of keys contained in the store
        """        
        uploaded_files = dict()
        for key, doc in self.db.docstore._dict.items():
            file_name = doc.metadata["source"]
            file_name = os.path.basename(file_name)
            if not file_name  in uploaded_files:
                uploaded_files[file_name] = []

            uploaded_files[file_name] = uploaded_files[file_name] + [key]
        return uploaded_files

