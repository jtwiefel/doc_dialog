
import gradio as gr
from pprint import pprint
import sys, os
import random
import string
sys.path.insert(0, ".")

config = "bge_m3"

verbose = True



from langchain import PromptTemplate


num_pages = 50

db_path = f"/workspace/volumes/pdf_{config}_faiss/"
pdf_folder_path = "/workspace/volumes/pdf_files/"
structured_md_pages_pkl_folder_path = "/workspace/volumes/structured_md_pages/"


from doc_dialog.document_loader import DocumentLoader
from doc_dialog.embedding_models.bge_m3 import EmbeddingModel
embedding_model = EmbeddingModel(verbose = verbose)
from doc_dialog.large_language_models.llama_3_1_instruct_8b_gptq_int4_remote import LLM
llm = LLM(verbose = verbose)

verbose = True

document_loader = DocumentLoader(faiss_volume_path = db_path, pdf_folder_path = pdf_folder_path, verbose = verbose)

from pathlib import Path
import glob

document_loader.llm = llm
document_loader.embedding_model = embedding_model
if not Path(db_path+"index.faiss").is_file():
    md_pages_dicts = None
    pdf_folder_path = "/workspace/volumes/pdf_files/"
    md_folder_path = "/workspace/volumes/markdown_files/"
    section_folder_path = "/workspace/volumes/section_files/"
    md_pages_pkl_folder_path = "/workspace/volumes/md_pages/"
    structured_md_pages_pkl_folder_path = "/workspace/volumes/structured_md_pages/"
    from doc_dialog.pdf2txt import pdf_to_pages_md_pkl, md_pages_to_dict, save_pkl, load_pkl
    for pdf_path in glob.glob(f"{pdf_folder_path}*.[pP][dD][fF]"):
        print(pdf_path)

        #convert pdf to markdown, save it to a pickle and load the pickle
        md_pages_path = md_pages_pkl_folder_path + Path(pdf_path).stem + ".mdpages.pkl"
        pdf_to_pages_md_pkl(pdf_path, md_pages_path)
        md_pages = load_pkl(md_pages_path)

        #convert markdown pages to a list of dicts containing section titles and section texts, save it as a pickle and load it
        #the "structured md pages" can then be loaded by the data loader and put to a vector store
        md_pages_dicts = md_pages_to_dict(md_pages)
        structured_md_pages_path = structured_md_pages_pkl_folder_path + Path(pdf_path).stem + ".strucmdpages.pkl"
        save_pkl(md_pages_dicts, structured_md_pages_path)
        md_pages_dicts = load_pkl(structured_md_pages_path)

        for page in md_pages_dicts:
            print(f'page: {page["metadata"]["page"]} sections: {len(page["sections"])}')
    if not md_pages_dicts == None:
        docs = document_loader.load_documents_from_structured_md_pages(structured_md_pages_pkl_folder_path)
        document_loader.create_db(docs)


#load the vectore store
document_loader.load_db()

#cache the current documents in the store
documents_in_store = document_loader.get_documents_in_store()
documents_in_store_filenames = list(documents_in_store.keys())

config += "_strucmdpages"


def process_question(question, answer_question):
    """uses the vector store to retrieve the relevant sources for a question to help answer it.
    can also provice an answer to the question

    Args:
        answers (_type_): _description_
        question (_type_): _description_
        answer_question (_type_): _description_

    Returns:
        _type_: _description_
    """    
    print(f"{question=}")
    print(llm)
    num_pages = 50
    #get the sources
    predicted_document_pages = document_loader.retrieve_document_pages(question = question,
                                                                                 num_pages = num_pages)
    formatted_answers = []

    last_context = ""
    context = ""
    context_full = False

    new_answers = []
    for info, document in predicted_document_pages:
        answer = []
        #check if we have enough input tokens left
        if not context_full:
            context = last_context
            #add document text to the context
            if document.metadata["section_title"] != "NO_TITLE":
                context += document.metadata["section_title"]
                context += "\n"
            context += document.page_content
            context += "\n\n"
            prompt = llm.encode(question, context)
            #check if we still have tokens left
            if llm.max_input_tokens < llm.get_prompt_length_in_tokens(prompt):
                context = last_context
                context_full = True
            else:
                last_context = context
            
        print(f"{context_full=}")

        pdf_file_name = os.path.basename(document.metadata["source"])

        #fill the sources
        new_answers.append([document.metadata["section_title"],
                        document.page_content,
                        pdf_file_name,
                        document.metadata["page"]])
    answer = ""
    if answer_question:
        #call the llm with the question and context
        prompt = llm.encode(question, context)
        print("PROMPT:")
        print(prompt)
        print(llm.get_prompt_length_in_tokens(prompt))
        answer = llm.call(prompt)
        print(answer)

    return new_answers, question, answer

files_to_be_stored = []
files_to_be_deleted = []

def remove_from_store(file_name):
    """removes a file from the vector store

    Args:
        file_name (_type_): filename without path

    Returns:
        _type_: returns list of filenames in the vector store
    """    
    global document_loader
    print(f"removing {file_name}")
    document_loader.remove_document(file_name)
    global documents_in_store
    documents_in_store = document_loader.get_documents_in_store()
    global documents_in_store_filenames
    documents_in_store_filenames = list(documents_in_store.keys())
    print("after removing")
    pprint(documents_in_store_filenames)
    global files_to_be_deleted
    files_to_be_deleted.append(file_name)
    return [] + documents_in_store_filenames



with gr.Blocks(title="DocDialog Demo") as demo:
    print("rendering blocks")
    documents_in_store_state = gr.State(documents_in_store_filenames)
    with gr.Tab("Fragen stellen",visible = True):
        answers_state = gr.State([])
        correct_answers_state = gr.State([])


        uploaded_documents_state = gr.State([])
        with gr.Row():
            with gr.Column(scale=1, min_width=50):
                with gr.Group():
                    question_tb = gr.Textbox(lines=3,
                            label = "Frage")
                    with gr.Row():
                        process_btn = gr.Button("Frage verarbeiten")
                    answer_question_cb = gr.Checkbox(label = "Frage beantworten", info = "Die Frage kann direkt beantwortet werden. WARNUNG: Die Antwort ist möglicherweise nicht richtig. Die Verarbeitung kann länger als 60 Sekunden dauern.")
                
                answer_tb = gr.Textbox(label = "Antwort")
                process_btn.click(fn=process_question, inputs=[question_tb, answer_question_cb], outputs=[answers_state, question_tb, answer_tb])
            
            with gr.Column(scale=3, min_width=50):

                @gr.render(inputs=answers_state)
                def render_answers(answers_list):
                    print("rendering answers")
                    print(answers_list)
                    gr.Markdown(f"### Quellen")
                    if len(answers_list) > 0:
                        for answer in answers_list:
                            with gr.Group():
                                with gr.Row():
                                    gr.Markdown(f"### {answer[0]}")
                                with gr.Row():
                                    gr.Markdown(answer[1])
                                with gr.Row():
                                    gr.Markdown(f"*{answer[2]}  Seite: {answer[3]}*")
    with gr.Tab("Dokumente verwalten"):

        upload_file = gr.File(file_count = "multiple", file_types = ["pdf", "PDF"], label = "PDFs hochladen")
        with gr.Row():
            add_to_store_btn = gr.Button("in Datenbank laden")
            def add_to_store(uploaded_files):
                
                print("adding to store:")
                global document_loader
                print(uploaded_files)
                if uploaded_files == None:
                    uploaded_files = []
                for uploaded_file in uploaded_files: 
                    document_loader.add_documents_from_pdf(uploaded_file)
                
                global documents_in_store
                documents_in_store = document_loader.get_documents_in_store()
                print("store after add:")
                print(documents_in_store.keys())
                global documents_in_store_filenames
                documents_in_store_filenames = list(documents_in_store.keys())
                return_val = [] + documents_in_store_filenames
                print(return_val)
                print(id(documents_in_store_filenames))
                print(id(return_val))
                #global files_to_be_stored = {}
                global files_to_be_stored
                files_to_be_stored = files_to_be_stored + uploaded_files

                return None, return_val
            add_to_store_btn.click(fn=add_to_store, inputs=upload_file, outputs=[upload_file, documents_in_store_state])
            persist_changes_btn = gr.Button("Änderungen an Datenbank speichern")
            def persist_changes(uploaded_files):
                print("persisting changes")
                global files_to_be_stored
                global files_to_be_deleted
                print(files_to_be_stored)
                print(files_to_be_deleted)

                global document_loader
                for file_to_be_deleted in files_to_be_deleted:
                    document_loader.delete_pdf_from_hd(file_to_be_deleted)
                
                for file_to_be_stored in files_to_be_stored:
                    document_loader.add_pdf_to_hd(file_to_be_stored)
                document_loader.save_db()
                files_to_be_stored = []
                files_to_be_deleted = []
                print("db changes persisted")
            persist_changes_btn.click(fn=persist_changes, inputs=None, outputs=None)

        @gr.render(inputs=documents_in_store_state)
        def render_documents_in_store(documents_in_store_local):
            print("rendering documents in store")
            print(documents_in_store_local)
            print(documents_in_store_state.value)
            print(documents_in_store_filenames)
            global documents_in_store
            gr.Markdown(f"### Hochgeladene Dokumente")
            for document_in_store in documents_in_store_filenames:
                with gr.Group(elem_id = "selected_answer"):
                    with gr.Row():
                        num_texts = len(documents_in_store[document_in_store])
                        with gr.Column(scale = 5):
                            document_in_store_md = gr.Markdown(f"{document_in_store}")
                        with gr.Column(scale = 1):
                            gr.Markdown(f"{num_texts} Texte")
                        with gr.Column(scale = 1):
                            remove_from_store_btn = gr.Button("aus Datenbank entfernen")
                            remove_from_store_btn.click(fn=remove_from_store, inputs=document_in_store_md, outputs=documents_in_store_state)
    

demo.queue()
demo.launch(show_api=False,
            server_name="0.0.0.0")

