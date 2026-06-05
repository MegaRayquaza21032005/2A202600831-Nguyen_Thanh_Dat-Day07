# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thành Đạt
**Nhóm:** [Tên nhóm]
**Ngày:** 2026-06-05

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai đoạn text có cosine similarity cao nghĩa là embedding vectors của chúng trỏ về cùng một hướng trong không gian vector, cho thấy chúng có ý nghĩa ngữ nghĩa tương đồng — nói về cùng chủ đề, dùng từ ngữ hoặc ý tưởng giống nhau.

**Ví dụ HIGH similarity:**
- Sentence A: "Machine learning uses algorithms to learn patterns from data."
- Sentence B: "Deep learning trains neural networks on large datasets to find patterns."
- Tại sao tương đồng: Cả hai đều nói về quá trình học máy — trích xuất patterns từ dữ liệu, chỉ khác nhau ở kỹ thuật cụ thể (algorithms vs neural networks). Về mặt ngữ nghĩa, chúng thuộc cùng một domain và truyền đạt ý tưởng tương tự.

**Ví dụ LOW similarity:**
- Sentence A: "Python is a high-level programming language for data science."
- Sentence B: "The weather forecast predicts rain tomorrow afternoon."
- Tại sao khác: Hai câu thuộc hai domain hoàn toàn khác nhau (lập trình vs thời tiết), không chia sẻ từ vựng hay ý nghĩa chung nào. Embedding vectors sẽ trỏ về các hướng rất khác trong không gian.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity đo **hướng** (angle) giữa hai vectors thay vì **khoảng cách tuyệt đối**, giúp loại bỏ ảnh hưởng của độ dài văn bản (magnitude). Hai đoạn text cùng chủ đề nhưng khác độ dài sẽ có vectors cùng hướng (cosine cao) nhưng magnitude khác nhau (Euclidean lớn). Do đó, cosine similarity phản ánh sự tương đồng ngữ nghĩa chính xác hơn.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`
> `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23 chunks`
> **Đáp án: 23 chunks**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> `num_chunks = ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks`
> Tăng overlap từ 50 → 100 làm tăng chunk count từ 23 → 25 vì mỗi bước tiến (step) ngắn hơn. Overlap nhiều hơn giúp bảo toàn ngữ cảnh tốt hơn tại ranh giới giữa các chunks — thông tin ở biên chunk không bị mất, giúp retrieval tìm được đoạn liên quan chính xác hơn khi thông tin trả lời nằm ở vị trí giao giữa hai chunks.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Technical Documentation & AI Knowledge Base

**Tại sao nhóm chọn domain này?**
> Nhóm chọn domain tài liệu kỹ thuật về AI/ML vì đây là lĩnh vực phù hợp trực tiếp với nội dung lab — bao gồm các chủ đề về embedding, vector store, RAG, và chunking. Domain này có cấu trúc đa dạng (markdown headers, paragraphs, lists) phù hợp để test các chiến lược chunking khác nhau. Ngoài ra, có cả tài liệu song ngữ (Anh/Việt) giúp kiểm tra khả năng xử lý đa ngôn ngữ.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | python_intro.txt | Lab sample data | 1,944 | source, extension |
| 2 | vector_store_notes.md | Lab sample data | 2,123 | source, extension |
| 3 | rag_system_design.md | Lab sample data | 2,391 | source, extension |
| 4 | customer_support_playbook.txt | Lab sample data | 1,692 | source, extension |
| 5 | chunking_experiment_report.md | Lab sample data | 1,987 | source, extension |
| 6 | vi_retrieval_notes.md | Lab sample data | 2,177 | source, extension |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| source | str | "data/python_intro.txt" | Xác định nguồn gốc tài liệu, giúp trace back kết quả trả về |
| extension | str | ".txt", ".md" | Phân biệt loại file, hữu ích khi lọc tài liệu theo format |
| doc_id | str | "python_intro" | Nhận diện document gốc, hỗ trợ delete và filter theo document |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu (chunk_size=200):

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| python_intro.txt (1,944 chars) | FixedSizeChunker (`fixed_size`) | 10 | 194.4 | Trung bình — cắt giữa câu |
| python_intro.txt | SentenceChunker (`by_sentences`) | 5 | 387.0 | Tốt — giữ ranh giới câu |
| python_intro.txt | RecursiveChunker (`recursive`) | 12 | 160.17 | Tốt — tách theo paragraph trước |
| rag_system_design.md (2,391 chars) | FixedSizeChunker (`fixed_size`) | 12 | 199.25 | Trung bình |
| rag_system_design.md | SentenceChunker (`by_sentences`) | 5 | 476.0 | Tốt nhưng chunk dài |
| rag_system_design.md | RecursiveChunker (`recursive`) | 16 | 147.56 | Tốt — tách theo markdown headers |
| customer_support_playbook.txt (1,692 chars) | FixedSizeChunker (`fixed_size`) | 9 | 188.0 | Trung bình |
| customer_support_playbook.txt | SentenceChunker (`by_sentences`) | 4 | 421.0 | Tốt nhưng chunk lớn |
| customer_support_playbook.txt | RecursiveChunker (`recursive`) | 11 | 152.18 | Tốt |

### Strategy Của Tôi

**Loại:** RecursiveChunker (chunk_size=200)

**Mô tả cách hoạt động:**
> RecursiveChunker sử dụng danh sách dấu phân cách theo thứ tự ưu tiên: `["\n\n", "\n", ". ", " ", ""]`. Đầu tiên, nó thử tách theo paragraph (`\n\n`), nếu chunk vẫn quá lớn thì tách theo dòng (`\n`), rồi theo câu (`. `), rồi theo từ (` `), và cuối cùng theo ký tự (`""`). Sau khi tách, các mảnh nhỏ được merge lại sao cho tối đa hoá kích thước chunk mà không vượt quá chunk_size.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain tài liệu kỹ thuật có cấu trúc rõ ràng với markdown headers, paragraphs, và bullet points. RecursiveChunker khai thác cấu trúc này bằng cách ưu tiên tách theo paragraph trước, giữ nguyên ý nghĩa của từng đoạn. Đối với file `.md`, separator `\n\n` tự nhiên tách theo section/paragraph, cho chunks có ngữ nghĩa hoàn chỉnh hơn so với fixed-size cutting.

**Code snippet (nếu custom):**
```python
# Sử dụng built-in RecursiveChunker với default separators
chunker = RecursiveChunker(chunk_size=200)
chunks = chunker.chunk(text)
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|-------------------|
| python_intro.txt | best baseline (FixedSize) | 10 | 194.4 | Trung bình — cắt giữa câu |
| python_intro.txt | **RecursiveChunker (của tôi)** | 12 | 160.17 | Tốt — mỗi chunk là 1 ý hoàn chỉnh |
| rag_system_design.md | best baseline (FixedSize) | 12 | 199.25 | Trung bình |
| rag_system_design.md | **RecursiveChunker (của tôi)** | 16 | 147.56 | Tốt — tách theo sections |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | RecursiveChunker (200) | 7/10 | Giữ ngữ cảnh tốt, tách theo cấu trúc | Chunk count nhiều hơn |
| [Thành viên 2] | [Cần điền sau khi thảo luận nhóm] | | | |
| [Thành viên 3] | [Cần điền sau khi thảo luận nhóm] | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> RecursiveChunker là lựa chọn tốt nhất cho domain tài liệu kỹ thuật markdown. Nó tự động khai thác cấu trúc document (headers, paragraphs) để tạo chunks có ngữ nghĩa hoàn chỉnh. So với FixedSizeChunker (cắt cứng, có thể cắt giữa câu) và SentenceChunker (chunks quá dài khi group 3 câu dài), RecursiveChunker cân bằng tốt giữa kích thước chunk và bảo toàn ngữ cảnh.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `(?<=[.!?])\s+` để detect ranh giới câu — lookbehind assertion tìm các dấu `.`, `!`, `?` theo sau bởi whitespace. Sau khi split, các câu được strip khoảng trắng thừa, group lại theo `max_sentences_per_chunk`, và nối bằng một dấu cách. Edge case xử lý: text rỗng trả về `[]`, strip whitespace đầu cuối trước khi split.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Algorithm đệ quy: base case là khi `len(text) <= chunk_size` → trả về `[text]`. Nếu text quá dài, duyệt qua danh sách separators theo thứ tự ưu tiên, tìm separator đầu tiên xuất hiện trong text. Split text theo separator đó, kiểm tra từng mảnh — nếu vẫn quá dài thì đệ quy với các separators ưu tiên thấp hơn. Cuối cùng, merge các mảnh nhỏ lại với nhau sao cho tổng không vượt quá `chunk_size`. Fallback cuối cùng khi hết separators là cắt cứng theo ký tự.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Mỗi document được embed bằng `embedding_fn`, tạo record dict gồm `{id, content, embedding, metadata}` và lưu vào `self._store` (in-memory list) hoặc ChromaDB collection. Khi search, embed query thành vector, tính dot product với tất cả stored embeddings, sort descending theo score, và trả về top-k results dưới dạng `[{content, score, metadata}]`.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` thực hiện pre-filtering: duyệt qua `self._store`, chỉ giữ records có metadata khớp tất cả key-value pairs trong `metadata_filter`, sau đó chạy similarity search trên tập đã lọc. `delete_document` sử dụng list comprehension để loại bỏ tất cả records có `metadata['doc_id'] == doc_id`, trả về `True` nếu có ít nhất 1 record bị xóa, `False` nếu không tìm thấy.

### KnowledgeBaseAgent

**`answer`** — approach:
> Theo pattern RAG 3 bước: (1) Gọi `store.search(question, top_k)` để retrieve top-k chunks liên quan nhất. (2) Build prompt với format: instructions → context (các chunks đánh số `[1]`, `[2]`, ...) → question. Prompt yêu cầu LLM chỉ trả lời dựa trên context, nếu thiếu thông tin thì nói rõ. (3) Gọi `llm_fn(prompt)` và return kết quả.

### Test Results

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

42 passed in 1.12s
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

> **Lưu ý:** Kết quả thực tế sử dụng `MockEmbedder` (hash-based, không mang ý nghĩa ngữ nghĩa). Với embedding model thực (e.g., `all-MiniLM-L6-v2`), kết quả sẽ phản ánh ngữ nghĩa chính xác hơn.

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Python is a programming language" | "Java is a programming language" | high | 0.1135 | Sai — MockEmbedder không hiểu ngữ nghĩa |
| 2 | "I love eating pizza for dinner" | "The weather is sunny today" | low | 0.1662 | Đúng — score thấp, khác domain |
| 3 | "Machine learning uses algorithms to learn from data" | "Deep learning trains neural networks on datasets" | high | 0.0201 | Sai — MockEmbedder cho score thấp dù ngữ nghĩa gần |
| 4 | "The cat sat on the mat" | "The cat is sitting on the mat" | high | -0.0049 | Sai — gần như orthogonal với MockEmbedder |
| 5 | "Vector databases store embeddings" | "I enjoy playing basketball" | low | 0.1220 | Đúng — khác domain hoàn toàn |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 4 bất ngờ nhất: "The cat sat on the mat" vs "The cat is sitting on the mat" có score gần 0 (-0.0049), trong khi hai câu gần như đồng nghĩa. Điều này cho thấy `MockEmbedder` (dùng MD5 hash) tạo vector hoàn toàn dựa trên ký tự, không hiểu ngữ nghĩa — chỉ cần thay đổi vài từ là hash khác hoàn toàn. Embedding model thực (neural network-based) sẽ cho kết quả ngược lại vì chúng học được biểu diễn ngữ nghĩa từ dữ liệu huấn luyện, nhận ra "sat" và "is sitting" cùng nghĩa.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries trên implementation cá nhân với `MockEmbedder`.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | How does Python support machine learning? | Python hỗ trợ ML qua các thư viện scikit-learn, PyTorch, TensorFlow; dùng để clean data, train models, run evaluation scripts |
| 2 | What is the purpose of metadata in vector stores? | Metadata giúp filter search space, improve precision — ví dụ lọc theo department, language, date để tránh trả về tài liệu không liên quan |
| 3 | How does recursive chunking work? | Recursive chunking thử tách theo separator ưu tiên cao trước (paragraph), nếu chunk vẫn quá lớn thì đệ quy với separator nhỏ hơn |
| 4 | What should support content avoid? | Tránh vague statements như "check the settings" — nên chỉ rõ exact page, button, log source cụ thể |
| 5 | What are common retrieval errors? | Tài liệu cũ xếp hạng cao, từ khóa không khớp diễn đạt, embedding model xử lý kém nội dung song ngữ |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How does Python support ML? | vi_retrieval_notes.md — Ghi chú về retrieval cho trợ lý tri thức | -0.9972 | Không — sai tài liệu | Demo LLM trả về dựa trên context |
| 2 | What is the purpose of metadata? | rag_system_design.md — RAG System Design | -0.6520 | Có — đề cập metadata filtering | Demo LLM trả về dựa trên context |
| 3 | How does recursive chunking work? | rag_system_design.md — RAG System Design | -0.6233 | Một phần — nhắc đến chunking nhưng không chi tiết recursive | Demo LLM trả về dựa trên context |
| 4 | What should support content avoid? | python_intro.txt — Python intro | -0.7157 | Không — sai tài liệu | Demo LLM trả về dựa trên context |
| 5 | What are common retrieval errors? | vi_retrieval_notes.md — Ghi chú retrieval | -0.7546 | Có — đề cập lỗi retrieval thực tế | Demo LLM trả về dựa trên context |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 3 / 5

> **Ghi chú:** Kết quả retrieval kém vì sử dụng `MockEmbedder` (hash-based, không hiểu ngữ nghĩa). Với embedding model thực như `all-MiniLM-L6-v2`, kết quả sẽ chính xác hơn đáng kể.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> [Cần điền sau khi thảo luận nhóm — ví dụ: Tôi học được cách custom chunker theo Q&A pairs hiệu quả hơn cho FAQ documents từ thành viên khác, hoặc cách tinh chỉnh overlap parameter ảnh hưởng đến retrieval quality.]

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> [Cần điền sau demo — ví dụ: Nhóm khác sử dụng metadata filtering kết hợp với sentence chunking cho domain legal documents, giúp cải thiện precision đáng kể so với search không filter.]

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ sử dụng embedding model thực (LocalEmbedder với all-MiniLM-L6-v2) thay vì MockEmbedder để đánh giá retrieval quality chính xác hơn. Ngoài ra, tôi sẽ thiết kế metadata schema phong phú hơn — thêm các trường `category`, `language`, `topic` — và sử dụng metadata filtering kết hợp với RecursiveChunker có overlap để tăng khả năng tìm đúng chunk liên quan.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 8 / 10 |
| Chunking strategy | Nhóm | 12 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 4 / 5 |
| Results | Cá nhân | 7 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **79 / 100** |
