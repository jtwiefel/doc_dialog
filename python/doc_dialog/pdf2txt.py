import fitz  # PyMuPDF
import re
import os,sys
from collections import OrderedDict
sys.path.insert(0,".")
from pathlib import Path
import pickle 
import logging
import pymupdf4llm
from jiwer import wer

from codetiming import Timer

l = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
l.addHandler(handler)
l.setLevel(logging.DEBUG)
l.setLevel(logging.INFO)
l.debug("Hello from DEBUG logger")
l.info("Hello from INFO logger")
l.warning("Hello from WARNING logger")
l.error("Hello from ERROR logger")
print("Hello from print")

pdf_folder_path = "/workspace/volumes/pdf_files/"
md_folder_path = "/workspace/volumes/markdown_files/"
section_folder_path = "/workspace/volumes/section_files/"
md_pages_pkl_folder_path = "/workspace/volumes/md_pages/"
structured_md_pages_pkl_folder_path = "/workspace/volumes/structured_md_pages/"

def remove_header_footer(lines, header_lines=2, footer_lines=2):
    """removes the header and footer lines

    Args:
        lines (_type_): lines of text or markdown
        header_lines (int, optional): number of lines to be removed at the beginning. Defaults to 2.
        footer_lines (int, optional): number of lines to be removed at the end. Defaults to 2.

    Returns:
        _type_: _description_
    """    
    if len(lines) > header_lines + footer_lines:
        return lines[header_lines: -footer_lines]
    return lines

def md_page_to_dict(page_dict):
    """
    converts a markdown page to a dictionary. the keys are section titles and the values are section texts.

    Args:
        page_dict (_type_): a markdown page dict

    Returns:
        _type_: a markdown page dict enriched with the key "sections" containing a dictionary
    """    
    pages = []
    current_page = -1
    current_title = "NO_TITLE"
    no_title_index = 0
    new_title_started = False
    new_title = []
    new_content = []
    
    #get the text of the markdown page
    lines = page_dict["text"].split("\n")

    #remove headers
    lines =  remove_header_footer(lines, header_lines=2, footer_lines=2)
    sections = OrderedDict()
    for line in lines:
        #ignore empty lines
        if line.strip() == "":
            continue
        l.debug(f"line: {line}")
        #check if a new section title was started. this has to be done because section titles can span multiple lines
        if new_title_started:
            #check if the line start is bold, which could mean it is a section title
            if line.startswith("**"):
                l.debug(f"found continuing title: {line}")
                #get the title
                title = line.split("**")[1]
                new_title.append(title)
            #if this is a normal line not starting with bold, this means, the title ended
            else:
                # store the current title
                current_title = " ".join(new_title)
                #reset everything else
                new_title = []
                new_content = []
                new_title_started = False
                #store this line to the content
                new_content.append(line)
        #check if there is a bold start, meaning a title starts
        elif line.startswith("**"):
            #if the line also ends with bold, this should be a title
            if line.strip().endswith("**"):
                #if we did not store any content yet, we ignore this lines
                if current_title == "NO_TITLE" and len(new_content) == 0:
                    l.debug(f"ignoring line: {line}")
                    continue
                #if we did store something already
                else:
                    l.debug(f"storing content for title: {current_title}")
                    #save the content of the previous section
                    sections[current_title] = new_content
                #indicate we have a new title started
                new_title_started = True
                l.debug(f"found title: {line}")
                #remove bold markers and duplicate spaces
                title = " ".join(line.split("**")).strip()
                title = ' '.join(title.split())
                l.debug(f"starting title {title}")
                #append the new title
                new_title = []
                new_title.append(title)
            #this line did not end with a bold marker, which should mean it is regular text
            else:
                #save it to our content
                new_content.append(line)
        # regular line, add it to our content of the current section
        else:
            new_content.append(line)
    l.debug(f"storing content for title (at end): {current_title}")
    l.debug(f"content:\n{new_content}")
    #save the last content and section
    sections[current_title] = new_content
    #update page dict
    page_dict["sections"] = sections
    return page_dict

def md_pages_to_dict(md_pages):
    """
    converts a list of markdown pages to a list of dictionaries.
    the keys are the names of the sections and the values are the texts of the sections.

    Args:
        md_pages (_type_): list of markdown pages

    Returns:
        _type_: list of dictionaries
    """    
    md_pages_dicts = []
    for md_page in md_pages:
        md_page_dict = md_page_to_dict(md_page)
        md_pages_dicts.append(md_page_dict)
    return md_pages_dicts


def pdf_to_pages_md_pkl(pdf_path, pkl_path):
    """
    converts a pdf to markdown and saves the pagewise markdown as a pickle

    Args:
        pdf_path (_type_): path to the input pdf
        pkl_path (_type_): path to the output pickle
    """    
    md_pages = pymupdf4llm.to_markdown(pdf_path, page_chunks=True)
    with open(pkl_path, "wb") as f:
        pickle.dump(md_pages, f)

def save_pkl(data,pkl_path):
    """
    saves data to a pickle

    Args:
        data (_type_): the data to be saved
        pkl_path (_type_): the path of the pickle
    """    
    with open(pkl_path, "wb") as f:
        pickle.dump(data, f)

def load_pkl(pkl_path):
    """load a pickle

    Args:
        pkl_path (_type_): path to the pickle

    Returns:
        _type_: data inside the pickle
    """    
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    return data


def pdf_to_structured_md_pages_pkl(pdf_path):
    """
    Converts a pdf to markdown pagewise and saves it as a pickle.
    Then, then it extracts the section titles and section texts at saves
    it as a list of dictionaries in pickle.

    Args:
        pdf_path (_type_): input pdf

    Returns:
        _type_: path to the pickle
    """    
    md_pages_path = md_pages_pkl_folder_path + Path(pdf_path).stem + ".mdpages.pkl"
    pdf_to_pages_md_pkl(pdf_path, md_pages_path)
    md_pages = load_pkl(md_pages_path)
    md_pages_dicts = md_pages_to_dict(md_pages)
    structured_md_pages_path = structured_md_pages_pkl_folder_path + Path(pdf_path).stem + ".strucmdpages.pkl"
    save_pkl(md_pages_dicts, structured_md_pages_path)
    return structured_md_pages_path
    


from pprint import pprint
import glob

if __name__ == "__main__":
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
        









