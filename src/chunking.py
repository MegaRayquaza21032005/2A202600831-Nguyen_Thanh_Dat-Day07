from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks



class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in raw_sentences if s.strip()]

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            
            # Nối các câu trong nhóm bằng một dấu cách và làm sạch khoảng trắng 2 đầu
            chunk_text = " ".join(group).strip()
            chunks.append(chunk_text)

        return chunks



class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Gọi hàm đệ quy để xử lý cắt văn bản
        return self._split(text, self.separators)


    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Tình huống cơ sở: Nếu đoạn text hiện tại đã nhỏ hơn chunk_size, trả về luôn
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Tình huống dự phòng: Nếu đã hết danh sách dấu phân cách mà text vẫn quá dài
        # Cắt cứng (force split) theo từng ký tự
        if not remaining_separators:
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        # BƯỚC 1: TÌM DẤU PHÂN CÁCH PHÙ HỢP
        # Mặc định lấy dấu phân cách cuối cùng (thường là "")
        separator = remaining_separators[-1] 
        next_separators = []

        # Duyệt qua các dấu phân cách còn lại để tìm dấu đầu tiên thực sự xuất hiện trong text
        for i, s in enumerate(remaining_separators):
            if s == "" or s in current_text:
                separator = s
                # Lưu lại các dấu phân cách tiếp theo cho lần đệ quy sau
                next_separators = remaining_separators[i + 1:] 
                break

        # BƯỚC 2: CẮT VĂN BẢN
        if separator == "":
            splits = list(current_text)
        else:
            splits = current_text.split(separator)

        # BƯỚC 3: KIỂM TRA ĐỘ DÀI SAU KHI CẮT VÀ ĐỆ QUY NẾU CẦN
        processed_splits = []
        for s in splits:
            if len(s) <= self.chunk_size:
                processed_splits.append(s)
            else:
                # Nếu có một mảng vừa cắt ra vẫn vượt quá chunk_size,
                # đệ quy gọi lại hàm _split với các dấu phân cách ưu tiên thấp hơn.
                processed_splits.extend(self._split(s, next_separators))

        # BƯỚC 4: GỘP (MERGE) CÁC MẢNH NHỎ LẠI CHO VỪA CHUNK_SIZE
        # Thay vì trả về hàng tá câu ngắn, chúng ta nối chúng lại sao cho 
        # tối đa hóa kích thước chunk (gần với chunk_size nhất có thể).
        chunks = []
        current_chunk = ""

        for s in processed_splits:
            # Xác định phần đệm (là dấu phân cách) để nối lại
            pad = separator if current_chunk else ""
            
            # Nếu gộp mảnh này vào mà vẫn <= chunk_size thì gộp
            if len(current_chunk) + len(pad) + len(s) <= self.chunk_size:
                current_chunk += pad + s
            else:
                # Nếu vượt quá, lưu chunk hiện tại lại và bắt đầu chunk mới
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = s

        # Đừng quên lưu lại chunk cuối cùng
        if current_chunk:
            chunks.append(current_chunk)

        return chunks
        


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_ab = _dot(vec_a, vec_b)
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot_ab / (mag_a * mag_b)



class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        result = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            result[name] = {
                "count": count,
                "avg_length": round(avg_length, 2),
                "chunks": chunks,
            }
        return result
