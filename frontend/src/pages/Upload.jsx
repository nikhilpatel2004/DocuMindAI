import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import AppNav from "../components/AppNav";
import { apiFetch, uploadFile } from "../api";

const MAX_UPLOAD_MB = 20;

function formatBytes(bytes) {
  if (bytes === null || bytes === undefined) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value) {
  if (!value) return "—";
  const normalized = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(value)
    ? `${value.replace(" ", "T")}Z`
    : value;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function describeUploadError(err) {
  if (err.status === 415) return "Only PDF files are accepted.";
  if (err.status === 413) return `That file is larger than the ${MAX_UPLOAD_MB} MB limit.`;
  if (err.status === 503) {
    return "Document processing is unavailable right now. Please try again in a moment.";
  }
  if (err.status === 422 && /vector|qdrant|embedding/i.test(err.message)) {
    return `${err.message} — check the vector store settings (QDRANT_LOCAL_PATH or QDRANT_URL).`;
  }
  return err.message;
}

function statusClass(status) {
  return `badge badge-${status || "uploaded"}`;
}

export default function Upload() {
  const inputRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [deletingId, setDeletingId] = useState("");
  const [pendingDelete, setPendingDelete] = useState(null);
  const [celebrate, setCelebrate] = useState(null);

  const loadDocuments = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const data = await apiFetch("/api/v1/documents");
      setDocuments(data.documents || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    if (!pendingDelete) return undefined;
    const onKeyDown = (event) => {
      if (event.key === "Escape" && !deletingId) setPendingDelete(null);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [pendingDelete, deletingId]);

  useEffect(() => {
    if (!celebrate) return undefined;
    const timer = window.setTimeout(() => setCelebrate(null), 4000);
    return () => window.clearTimeout(timer);
  }, [celebrate]);

  const chooseFile = (candidate) => {
    setError("");
    setNotice("");
    if (!candidate) return;
    if (!candidate.name.toLowerCase().endsWith(".pdf")) {
      setFile(null);
      setError("Only PDF files are accepted.");
      return;
    }
    if (candidate.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setFile(null);
      setError(`That file is ${formatBytes(candidate.size)} — the limit is ${MAX_UPLOAD_MB} MB.`);
      return;
    }
    setFile(candidate);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files?.[0]);
  };

  const handleUpload = async () => {
    if (!file || uploading) return;
    setError("");
    setNotice("");
    setUploading(true);
    setProgress(0);
    setProcessing(false);
    try {
      const data = await uploadFile("/api/v1/documents", file, (percent) => {
        setProgress(percent);
        if (percent >= 100) setProcessing(true);
      });
      const uploadedName = data.original_name || file.name;
      setNotice(`${uploadedName} was uploaded and is ready to query.`);
      setCelebrate({ name: uploadedName });
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      await loadDocuments();
    } catch (err) {
      setError(describeUploadError(err));
    } finally {
      setUploading(false);
      setProcessing(false);
      setProgress(0);
    }
  };

  const requestDelete = (doc) => {
    setError("");
    setNotice("");
    setPendingDelete(doc);
  };

  const confirmDelete = async () => {
    const doc = pendingDelete;
    if (!doc || deletingId) return;
    setError("");
    setNotice("");
    setDeletingId(doc.id);
    try {
      await apiFetch(`/api/v1/documents/${doc.id}`, { method: "DELETE" });
      setDocuments((prev) => prev.filter((item) => item.id !== doc.id));
      setNotice(`Deleted "${doc.original_name}".`);
      setPendingDelete(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId("");
    }
  };

  return (
    <div className="app-shell">
      <AppNav />
      <main className="app-main">
        <div className="page-header">
          <h1 className="page-title">Upload a PDF</h1>
          <p className="page-subtitle">
            Your PDF is stored on this machine. Retrieved excerpts are sent to KIE to generate grounded answers.
          </p>
        </div>

        {error && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: 16 }}>
            {error}
          </div>
        )}
        {notice && (
          <div className="alert alert-success" role="status" style={{ marginBottom: 16 }}>
            {notice}
          </div>
        )}

        <div
          className={"dropzone" + (dragging ? " dragging" : "")}
          role="button"
          tabIndex={0}
          onClick={() => !uploading && inputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              if (!uploading) inputRef.current?.click();
            }
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <div className="dropzone-icon">+</div>
          <div className="dropzone-title">
            {dragging ? "Drop your PDF here" : "Drag and drop a PDF, or click to browse"}
          </div>
          <div className="dropzone-hint">PDF only, up to {MAX_UPLOAD_MB} MB</div>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            hidden
            onChange={(e) => chooseFile(e.target.files?.[0])}
          />
        </div>

        {file && (
          <div className="file-row">
            <div style={{ minWidth: 0 }}>
              <div className="file-row-name">{file.name}</div>
              <div className="file-row-meta">{formatBytes(file.size)}</div>
            </div>
            <div className="file-row-spacer" />
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => {
                setFile(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
              disabled={uploading}
            >
              Remove
            </button>
            <button type="button" className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
              {uploading ? (processing ? "Processing…" : `Uploading ${progress}%`) : "Upload"}
            </button>
          </div>
        )}

        {uploading && (
          <div className="progress" aria-hidden="true">
            <div className="progress-bar" style={{ width: `${processing ? 100 : progress}%` }} />
          </div>
        )}
        {processing && (
          <p className="page-subtitle" style={{ marginTop: 8 }}>
            Extracting text and building embeddings — this can take a moment.
          </p>
        )}

        <section className="card card-pad section-gap">
          <div className="chat-side-head">
            <h2 className="card-title" style={{ margin: 0 }}>
              Your documents
            </h2>
            <button type="button" className="btn btn-ghost btn-sm" onClick={loadDocuments} disabled={loadingDocs}>
              {loadingDocs ? "Refreshing…" : "Refresh"}
            </button>
          </div>

          {loadingDocs ? (
            <div className="empty-state">
              <div className="empty-state-title">Loading documents…</div>
            </div>
          ) : documents.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-title">No documents yet</div>
              <p>Upload your first PDF to start asking questions about it.</p>
            </div>
          ) : (
            <div className="doc-list">
              {documents.map((doc) => (
                <div className="doc-item" key={doc.id}>
                  <div className="doc-item-body">
                    <div className="doc-item-name">
                      <span title={doc.original_name}>{doc.original_name}</span>
                      <span className={statusClass(doc.status)}>{doc.status}</span>
                    </div>
                    <div className="doc-item-meta">
                      {formatBytes(doc.file_size)} · {doc.page_count ?? "—"} pages ·{" "}
                      {doc.chunk_count ?? "—"} chunks · {formatDate(doc.created_at)}
                    </div>
                  </div>
                  <Link className="btn btn-sm" to="/chat">
                    Ask
                  </Link>
                  <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    onClick={() => requestDelete(doc)}
                    disabled={deletingId === doc.id}
                  >
                    {deletingId === doc.id ? "Deleting…" : "Delete"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      {pendingDelete && (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={() => {
            if (!deletingId) setPendingDelete(null);
          }}
        >
          <div
            className="modal-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-dialog-title"
            aria-describedby="delete-dialog-desc"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="delete-dialog-title" className="modal-title">
              Delete document?
            </h2>
            <p id="delete-dialog-desc" className="modal-text">
              Are you sure you want to delete{" "}
              <strong>{pendingDelete.original_name}</strong>? This also removes its
              indexed content and cannot be undone.
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setPendingDelete(null)}
                disabled={!!deletingId}
                autoFocus
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-danger-solid"
                onClick={confirmDelete}
                disabled={!!deletingId}
              >
                {deletingId ? "Deleting…" : "Yes, delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {celebrate && (
        <div className="upload-toast" role="status" aria-live="polite">
          <span className="upload-confetti" aria-hidden="true">
            {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
              <span
                key={i}
                className="upload-confetti-piece"
                style={{ animationDelay: `${i * 45}ms`, left: `${8 + i * 12}%` }}
              />
            ))}
          </span>
          <span className="upload-toast-icon" aria-hidden="true">
            ✓
          </span>
          <span className="upload-toast-copy">
            <strong>Uploaded!</strong>
            <span className="upload-toast-file">{celebrate.name}</span>
          </span>
          <button
            type="button"
            className="upload-toast-close"
            onClick={() => setCelebrate(null)}
            aria-label="Dismiss upload notification"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
