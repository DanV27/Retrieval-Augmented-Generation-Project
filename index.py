from sentence_transformers import SentenceTransformer



def n_tokens(text: str) -> int:
    return len(tok.encode(text, add_special_tokens=False))
model = SentenceTransformer("all-MiniLM-L6-v2")
tok = model.tokenizer
MAX_MODEL_TOKENS = model.max_seq_length - 2      # reserve [CLS] and [SEP]
assert CHUNK_SIZE <= MAX_MODEL_TOKENS, (
    f"CHUNK_SIZE={CHUNK_SIZE} exceeds model window {MAX_MODEL_TOKENS}; "
    f"chunks will be silently truncated at embed time"
)

if __name__ == "__main__":
    print(model.max_seq_length)