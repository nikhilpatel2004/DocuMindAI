import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppNav from "../components/AppNav";
import { apiFetch, getUser } from "../api";

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const currentUser = getUser();
  const displayName =
    currentUser?.username ||
    (currentUser?.email ? currentUser.email.split("@")[0] : "there");

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch("/api/v1/documents");
      setDocuments(data.documents || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const readyCount = documents.filter((doc) => doc.status === "ready").length;
  const processingCount = documents.filter((doc) => doc.status === "processing").length;
  const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunk_count || 0), 0);

  return (
    <div className="app-shell">
      <AppNav />
      <main className="app-main">
        <div className="page-header">
          <h1 className="page-title">Welcome back, {displayName}</h1>
          <p className="page-subtitle">
            Upload PDFs, then ask questions and get grounded answers with source citations.
          </p>
        </div>

        {error && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: 16 }}>
            {error}
          </div>
        )}

        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-value">{loading ? "—" : documents.length}</div>
            <div className="stat-label">Documents</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{loading ? "—" : readyCount}</div>
            <div className="stat-label">Ready to query</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{loading ? "—" : processingCount}</div>
            <div className="stat-label">Processing</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{loading ? "—" : totalChunks}</div>
            <div className="stat-label">Indexed chunks</div>
          </div>
        </div>

        <section className="section-gap">
          <h2 className="card-title">Get started</h2>
          <div className="action-grid">
            <Link className="action-card" to="/upload">
              <h3>Upload a PDF</h3>
              <p>Add a document — it is chunked and embedded locally for retrieval.</p>
            </Link>
            <Link className="action-card" to="/chat">
              <h3>Ask your documents</h3>
              <p>Query your knowledge base and see which pages each answer came from.</p>
            </Link>
          </div>
        </section>

        <section className="card card-pad section-gap">
          <div className="chat-side-head" style={{ marginBottom: 12 }}>
            <h2 className="card-title" style={{ margin: 0 }}>
              Recent documents
            </h2>
            <Link className="btn btn-ghost btn-sm" to="/upload">
              Manage
            </Link>
          </div>

          {loading ? (
            <div className="empty-state">
              <div className="empty-state-title">Loading…</div>
            </div>
          ) : documents.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-title">No documents yet</div>
              <p>
                <Link to="/upload">Upload your first PDF</Link> to get started.
              </p>
            </div>
          ) : (
            <div className="doc-list">
              {documents.slice(0, 5).map((doc) => (
                <div className="doc-item" key={doc.id}>
                  <div className="doc-item-body">
                    <div className="doc-item-name">
                      <span title={doc.original_name}>{doc.original_name}</span>
                      <span className={`badge badge-${doc.status || "uploaded"}`}>{doc.status}</span>
                    </div>
                    <div className="doc-item-meta">
                      {doc.page_count ?? "—"} pages · {doc.chunk_count ?? "—"} chunks
                    </div>
                  </div>
                  {doc.status === "ready" && (
                    <Link
                      className="btn btn-sm"
                      to={`/chat?doc=${encodeURIComponent(doc.id)}`}
                    >
                      Ask
                    </Link>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
