# summarizer.py

def generate_summary(transcript_list):
    full_text = " ".join(transcript_list)
    summary = full_text[:500] + "..." if len(full_text) > 500 else full_text
    return summary