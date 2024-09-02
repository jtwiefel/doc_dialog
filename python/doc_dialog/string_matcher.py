def get_original_text_part(major: str, minor: str, errs: int = 10):
    """Find the closest matching fuzzy substring.

    Args:
        major: the string to search in
        minor: the string to search with
        errs: the total number of errors

    Returns:
        Optional[regex.Match] object
    """
    errs_ = 0
    import regex
    print("matching with 0 errors")
    s = regex.search(f"({minor}){{e<={errs_}}}", major)
    while s is None and errs_ <= errs:
        
        errs_ += 1
        print(f"matching with {errs_} errors")
        s = regex.search(f"({minor}){{e<={errs_}}}", major)
    
    print(errs_)
    print(s)
    if s != None:
        result = s.group()
        return result

from Bio import pairwise2

from Bio.pairwise2 import format_alignment
#import editdistance
from jiwer import wer
def get_original_text_part_bio(major: str, minor: str):
    splitted_major = major.split(" ")
    splitted_minor = minor.split(" ")
    alignments = pairwise2.align.localms(splitted_major,splitted_minor,2,-1,-0.5,-0.1, gap_char=["-"])

    #for a in alignments: 

    #    print(format_alignment(*a))
    
    best_alignment = format_alignment(*alignments[0])
    #print("######")
    #print(best_alignment)
    #print(alignments[0])
    #print(alignments[0].seqA[alignments[0].start:alignments[0].end])
    start_index = alignments[0].start
    for idx, (major_word, minor_word) in enumerate(zip(alignments[0].seqA, alignments[0].seqB)):
        #print(idx, [major_word], [minor_word])
        if minor_word != "-":
            start_index = idx
            break
    #print(start_index)
    end_index = alignments[0].end
    #print("finding the end index")
    for idx, (major_word, minor_word) in enumerate(zip(reversed(alignments[0].seqA), reversed(alignments[0].seqB))):
        #print(idx, [major_word], [minor_word])
        if minor_word != "-":
            end_index = idx
            break
    #print("end index", end_index)
    end_index = len(alignments[0].seqA)-end_index
    #print("end index", end_index)
    found_original_text = alignments[0].seqA[start_index:end_index]
    found_original_text =  list(filter(lambda a: a != "-", found_original_text))
    #print(found_original_text)
    return " ".join(found_original_text)
