CREATE TABLE files (
    file_id INTEGER PRIMARY KEY,
    path TEXT NOT NULL,
    type TEXT,
    subtype TEXT,
    size_bytes INTEGER,
    mtime INTEGER,
    content_hash TEXT,
    status TEXT,
    meta_json TEXT
);

CREATE TABLE chunks (
    chunk_id INTEGER PRIMARY KEY,
    file_id INTEGER,
    modality TEXT,
    level INTEGER,
    token_len INTEGER,
    text TEXT,
    meta_json TEXT,
    FOREIGN KEY (file_id) REFERENCES files (file_id)
);

CREATE TABLE embeddings (
    embedding_id INTEGER PRIMARY KEY,
    chunk_id INTEGER,
    modality TEXT,
    model TEXT,
    dim INTEGER,
    vector BLOB,
    FOREIGN KEY (chunk_id) REFERENCES chunks (chunk_id)
);

CREATE TABLE images (
    image_id INTEGER PRIMARY KEY,
    file_id INTEGER,
    phash TEXT,
    width INTEGER,
    height INTEGER,
    meta_json TEXT,
    clip_vector_ref INTEGER,
    FOREIGN KEY (file_id) REFERENCES files (file_id)
);

CREATE TABLE tables_meta (
    table_id INTEGER PRIMARY KEY,
    file_id INTEGER,
    sheet_name TEXT,
    n_rows INTEGER,
    n_cols INTEGER,
    profile_json TEXT,
    FOREIGN KEY (file_id) REFERENCES files (file_id)
);

CREATE TABLE entities (
    entity_id INTEGER PRIMARY KEY,
    surface_form TEXT,
    canonical_form TEXT,
    type TEXT,
    freq INTEGER,
    meta_json TEXT
);

CREATE TABLE entity_chunk (
    entity_id INTEGER,
    chunk_id INTEGER,
    count INTEGER,
    PRIMARY KEY (entity_id, chunk_id),
    FOREIGN KEY (entity_id) REFERENCES entities (entity_id),
    FOREIGN KEY (chunk_id) REFERENCES chunks (chunk_id)
);

CREATE TABLE clusters (
    cluster_id INTEGER PRIMARY KEY,
    level INTEGER,
    modality TEXT,
    member_chunk_ids TEXT,
    meta_json TEXT
);

CREATE TABLE summaries (
    summary_id INTEGER PRIMARY KEY,
    cluster_id INTEGER,
    level INTEGER,
    text TEXT,
    model TEXT,
    token_len INTEGER,
    provenance_chunk_ids TEXT,
    FOREIGN KEY (cluster_id) REFERENCES clusters (cluster_id)
);

CREATE TABLE llm_cache (
    cache_id INTEGER PRIMARY KEY,
    key_hash TEXT,
    request_json TEXT,
    response_text TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    created_at INTEGER
);

CREATE TABLE capsules (
    capsule_id INTEGER PRIMARY KEY,
    task_hash TEXT,
    created_at INTEGER,
    token_len INTEGER,
    text TEXT,
    section_index_json TEXT
);

CREATE TABLE stubs (
    stub_id INTEGER PRIMARY KEY,
    capsule_id INTEGER,
    reference_type TEXT,
    reference_id INTEGER,
    description TEXT,
    FOREIGN KEY (capsule_id) REFERENCES capsules (capsule_id)
);

CREATE TABLE evaluation_runs (
    run_id INTEGER PRIMARY KEY,
    capsule_id INTEGER,
    metrics_json TEXT,
    created_at INTEGER,
    FOREIGN KEY (capsule_id) REFERENCES capsules (capsule_id)
);
