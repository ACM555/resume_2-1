import type { OcrResponse, SuggestionsResponse } from "../types";

// 【关键修复点】从环境变量中读取后端真实地址
// 如果读取不到（比如本地开发且没配环境变量），则退回到本地默认值
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function ocrResume(file: File): Promise<OcrResponse> {
  const form = new FormData();
  form.append("file", file);

  // 【关键修复点】使用模板字符串拼接完整的后端 URL
  const resp = await fetch(`${API_BASE_URL}/api/ocr`, {
    method: "POST",
    body: form,
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`OCR 请求失败：${resp.status} ${text || resp.statusText}`);
  }
  return (await resp.json()) as OcrResponse;
}

export async function generateSuggestions(resumeId: number): Promise<SuggestionsResponse> {
  // 【关键修复点】使用模板字符串拼接完整的后端 URL
  const resp = await fetch(`${API_BASE_URL}/api/suggestions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ resumeId }),
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`生成建议失败：${resp.status} ${text || resp.statusText}`);
  }
  return (await resp.json()) as SuggestionsResponse;
}
