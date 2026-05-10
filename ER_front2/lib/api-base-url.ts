export function getApiBaseUrl() {
  if (process.env.NODE_ENV === "production") {
    return ""
  }

  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080"
}
