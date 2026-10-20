import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AppNav from "../components/AppNav";
import MarkdownMessage from "../components/MarkdownMessage";
import { apiFetch } from "../api";

const SUGGESTIONS = [
  "Summarise the key points of this document.",
  "What are the main conclusions?",
  "List any numbers, dates, or figures mentioned.",
  "Explain this in simple terms.",
];

function statusClass(status) {
  return `badge badge-${status || "uploaded"}`;
}

function describeAskError(err) {
  if (err.status === 503) {
    return err.message || "The AI answering service is unavailable right now. Please check your KIE API configuration.";
  }
  if (err.status === 422 && /vector|qdrant|embedding/i.test(err.message)) {
    return `${err.message} — check the vector store settings (QDRANT_LOCAL_PATH or QDRANT_URL).`;
  }
  return err.message || "An unexpected error occurred.";
}

export default function Chat() {
  const threadRef = useRef(null);
  const [searchParams] = useSearchParams();
  const requestedDoc = searchParams.get("doc");

  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const readyDocs = documents.filter((doc) => doc.status === "ready");

  const loadDocuments = useCallback(async () => {
    setLoadingDocs(true);
    setError("");
    try {
      const data = await apiFetch("/api/v1/documents");
      const docs = data.documents || [];
      setDocuments(docs);
      const ready = docs.filter((doc) => doc.status === "ready").map((doc) => doc.id);
      setSelectedDocs(
        requestedDoc
          ? ready.includes(requestedDoc)
            ? [requestedDoc]
            : ready
          : ready
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingDocs(false);
    }
  }, [requestedDoc]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    const node = threadRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [messages, loading]);

  const toggleDoc = (id) => {
    setSelectedDocs((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]));
  };

  const selectAll = () => setSelectedDocs(readyDocs.map((doc) => doc.id));
  const clearAll = () => setSelectedDocs([]);

  const send = async (questionOverride) => {
    const question = (questionOverride ?? input).trim();
    if (!question || loading) return;
    if (!selectedDocs.length) {
      setError("Select at least one document to ask questions about.");
      return;
    }

    setError("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const data = await apiFetch("/api/v1/chat/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, document_ids: selectedDocs }),
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer || "", sources: data.citations || [] },
      ]);
    } catch (err) {
      const message = describeAskError(err);
      setError(message);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: message, sources: [], isError: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  };

  return (
    <div className="app-shell">
      <AppNav />
      <main className="app-main">
        <div className="page-header">
          <h1 className="page-title">Chat with your documents</h1>
          <p className="page-subtitle">
            Answers are grounded in your uploaded PDFs and cite the source pages.
          </p>
        </div>

        {error && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: 16 }}>
            {error}
          </div>
        )}

        <div className="chat-layout">
          <aside className="chat-side card">
            <div className="chat-side-head">
              <span className="stat-label">Documents</span>
              {selectedDocs.length > 0 && (
                <button type="button" className="btn btn-ghost btn-sm" onClick={clearAll}>
                  Clear
                </button>
              )}
            </div>

            {loadingDocs ? (
              <p className="page-subtitle" style={{ margin: 0 }}>
                Loading…
              </p>
            ) : documents.length === 0 ? (
              <div className="empty-state" style={{ padding: "18px 4px" }}>
                <div className="empty-state-title">No documents</div>
                <p>
                  <Link to="/upload">Upload a PDF</Link> to get started.
                </p>
              </div>
            ) : (
              <>
                <label className={"doc-chip" + (selectedDocs.length === readyDocs.length && readyDocs.length ? " selected" : "")}>
                  <input
                    type="checkbox"
                    checked={readyDocs.length > 0 && selectedDocs.length === readyDocs.length}
                    onChange={(e) => (e.target.checked ? selectAll() : clearAll())}
                  />
                  <span className="doc-chip-name">Select all ready</span>
                </label>
                {documents.map((doc) => {
                  const isReady = doc.status === "ready";
                  return (
                    <label
                      key={doc.id}
                      className={
                        "doc-chip" +
                        (selectedDocs.includes(doc.id) ? " selected" : "") +
                        (isReady ? "" : " doc-chip-disabled")
                      }
                      title={isReady ? doc.original_name : `${doc.original_name} — ${doc.status}`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedDocs.includes(doc.id)}
                        disabled={!isReady}
                        onChange={() => toggleDoc(doc.id)}
                      />
                      <span className="doc-chip-name">{doc.original_name}</span>
                      {!isReady && <span className={statusClass(doc.status)}>{doc.status}</span>}
                    </label>
                  );
                })}
              </>
            )}
          </aside>

          <section className="chat-panel card">
            <div className="chat-thread" ref={threadRef}>
              {messages.length === 0 ? (
                <div>
                  <div className="empty-state" style={{ paddingBottom: 14 }}>
                    <div className="empty-state-title">Hey! 👋 Kya scene hai?</div>
                    <p>
                      {selectedDocs.length
                        ? `${selectedDocs.length} document${selectedDocs.length === 1 ? "" : "s"} selected. Ab kuch bhi poocho — answers sirf inhi documents se aayenge.`
                        : "Left side se PDF select karo, phir sawaal daalna shuru karo."}
                    </p>
                  </div>
                  {SUGGESTIONS.map((text) => (
                    <button
                      key={text}
                      type="button"
                      className="suggestion"
                      onClick={() => send(text)}
                      disabled={loading || !selectedDocs.length}
                    >
                      {text}
                    </button>
                  ))}
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div key={index} className={"msg " + (msg.role === "user" ? "msg-user" : "msg-assistant")}>
                    <div
                      className="msg-bubble"
                      style={msg.isError ? { background: "#fef3f2", borderColor: "#fecdca", color: "#b42318" } : undefined}
                    >
                      {msg.isError || msg.role === "user" ? (
                        msg.content
                      ) : (
                        <MarkdownMessage content={msg.content} />
                      )}
                    </div>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="msg-sources">
                        {msg.sources.map((source, sourceIndex) => (
                          <span className="source-chip" key={sourceIndex} title={source.source_filename}>
                            {source.source_filename} · p.{source.page_number}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}

              {loading && (
                <div className="msg msg-assistant">
                  <div className="msg-bubble">
                    <span className="typing">
                      <span className="spinner" />
                      Searching your documents… 🔍
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="chat-composer">
              <textarea
                className="chat-input"
                placeholder={
                  selectedDocs.length
                    ? "Ask a question… (Enter to send, Shift+Enter for a new line)"
                    : "Select a document to start asking…"
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={loading}
              />
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => send()}
                disabled={loading || !input.trim() || !selectedDocs.length}
              >
                Send
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
