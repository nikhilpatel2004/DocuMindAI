export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const TOKEN_KEY = "documind_token";
const USER_KEY = "documind_user";

// Set VITE_API_URL when the API is hosted on a different origin than the app
// (for example a Hugging Face Space). Falls back to same-origin /api paths.
const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");

function withBase(path) {
  if (!API_BASE || /^https?:\/\//i.test(path)) return path;
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getUser() {
  const raw = localStorage.getItem(USER_KEY);
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setUser(user) {
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_KEY);
  }
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  window.location.href = "/login";
}

export function isAuthenticated() {
  return Boolean(getToken());
}

async function readDetail(res) {
  const data = await res.json().catch(() => ({}));
  return data.detail || data.message || `Request failed (${res.status})`;
}

/** Fetch a JSON endpoint and normalise errors with auto-injected Auth header. */
export async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  options.headers = headers;

  let res;
  try {
    res = await fetch(withBase(path), options);
  } catch {
    throw new ApiError("Network error — make sure the backend is running.", 0);
  }

  if (res.status === 401) {
    // If not already on login/signup, clear token and redirect
    const pathName = window.location.pathname;
    if (pathName !== "/login" && pathName !== "/signup") {
      setToken(null);
      setUser(null);
      window.location.href = "/login";
    }
  }

  if (!res.ok) {
    throw new ApiError(await readDetail(res), res.status);
  }
  if (res.status === 204) return null;
  return res.json().catch(() => ({}));
}

/**
 * Upload a file with real progress reporting and Authorization token.
 * Returns a promise resolving to the parsed response body.
 */
export function uploadFile(path, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", withBase(path));

    const token = getToken();
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      if (onProgress && event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      let data = {};
      try {
        data = JSON.parse(xhr.responseText);
      } catch {
        data = {};
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data);
      } else {
        if (xhr.status === 401) {
          setToken(null);
          setUser(null);
          window.location.href = "/login";
        }
        reject(new ApiError(data.detail || `Upload failed (${xhr.status})`, xhr.status));
      }
    };

    xhr.onerror = () => reject(new ApiError("Network error during upload.", 0));

    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}
