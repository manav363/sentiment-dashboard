import axios from "axios";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

const client = axios.create({
  baseURL: BASE ? `${BASE}/api` : "/api",
  timeout: 180_000,
  headers: { "Content-Type": "application/json" },
});

let modelReady = false;

async function waitForModel(retries = 30, intervalMs = 2000): Promise<void> {
  for (let i = 0; i < retries; i++) {
    try {
      const { data } = await axios.get(`${BASE}/health`, { timeout: 5000 });
      if (data?.model_loaded) {
        modelReady = true;
        return;
      }
    } catch {
      // backend not yet reachable — keep retrying
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  // Exhausted retries — let the actual request proceed and fail naturally
}

client.interceptors.request.use(async (config) => {
  if (!modelReady && config.url?.includes("/analyze")) {
    await waitForModel();
  }
  return config;
});

export default client;