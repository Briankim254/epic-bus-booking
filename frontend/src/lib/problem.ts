import { isAxiosError } from "axios"
import type { Problem } from "@/client"

/** The API's application/problem+json body, if this error carries one. */
export function toProblem(error: unknown): Problem | null {
  if (!isAxiosError(error)) return null
  const data: unknown = error.response?.data
  if (data && typeof data === "object" && "code" in data && "status" in data) {
    return data as Problem
  }
  return null
}

/** Field errors keyed by the request field, e.g. "body.passenger_name" -> "passenger_name". */
export function fieldErrors(problem: Problem | null): Record<string, string> {
  const out: Record<string, string> = {}
  for (const e of problem?.errors ?? []) {
    const parts = e.field.split(".")
    const field = parts[parts.length - 1] ?? e.field
    out[field] ??= e.message
  }
  return out
}

/** A sentence to show the user. Includes the request id when the server sent one. */
export function problemMessage(error: unknown): string {
  const problem = toProblem(error)
  if (!problem)
    return "Could not reach the server. Check your connection and try again."
  const text = problem.detail ?? problem.title
  return problem.status >= 500 && problem.request_id
    ? `${text} (request id ${problem.request_id})`
    : text
}
