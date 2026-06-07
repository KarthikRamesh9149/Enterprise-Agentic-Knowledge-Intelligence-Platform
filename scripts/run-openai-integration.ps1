$ErrorActionPreference = "Stop"

$baseUrl = $env:API_URL
if (-not $baseUrl) {
  $baseUrl = "http://localhost:8000"
}

$root = Split-Path -Parent $PSScriptRoot
$docs = @(
  "demo-data/ai-research-paper-summary.md",
  "demo-data/company-annual-report-ai-risk.md",
  "demo-data/company-annual-report-ai-investment.md",
  "demo-data/agentic-ai-governance-notes.md",
  "demo-data/rag-limitations-research-notes.md"
)

foreach ($doc in $docs) {
  $full = Join-Path $root $doc
  if (-not (Test-Path -LiteralPath $full)) {
    throw "Missing integration document: $doc"
  }
}

function Invoke-JsonPost {
  param(
    [string]$Uri,
    [hashtable]$Headers,
    [object]$Body
  )
  Invoke-RestMethod -Method Post -Uri $Uri -Headers $Headers -ContentType "application/json" -Body ($Body | ConvertTo-Json -Depth 8)
}

$health = Invoke-RestMethod "$baseUrl/health"
if ($health.status -ne "ok") {
  throw "Backend health failed"
}

$login = Invoke-JsonPost "$baseUrl/auth/login" @{} @{
  email = "admin@example.com"
  password = "LocalAdmin123!"
}

$headers = @{ Authorization = "Bearer $($login.access_token)" }
$uploaded = @()

foreach ($doc in $docs) {
  $full = Join-Path $root $doc
  $uploadRaw = curl.exe -s -X POST "$baseUrl/documents/upload" -H "Authorization: Bearer $($login.access_token)" -F "file=@$full"
  $upload = $uploadRaw | ConvertFrom-Json
  if (-not $upload.id) {
    throw "Upload failed for $doc`: $uploadRaw"
  }
  $processed = Invoke-RestMethod -Method Post -Uri "$baseUrl/documents/$($upload.id)/process" -Headers $headers
  if ($processed.status -ne "processed") {
    throw "Processing failed for $doc with status $($processed.status): $($processed.error_message)"
  }
  $chunks = Invoke-RestMethod -Method Get -Uri "$baseUrl/documents/$($upload.id)/chunks" -Headers $headers
  if ($chunks.Count -lt 1) {
    throw "No chunks created for $doc"
  }
  $uploaded += [pscustomobject]@{
    file = $upload.original_filename
    status = $processed.status
    chunks = $chunks.Count
  }
}

$questions = @(
  "Summarize the main AI infrastructure risks across the uploaded annual reports.",
  "Compare how the companies describe AI-related investment.",
  "What does the uploaded research say about RAG limitations?",
  "Which parts of the evidence suggest agentic AI outputs should route to human review?",
  "Give a board-level summary of AI opportunities and risks from these documents."
)

$answers = @()
foreach ($question in $questions) {
  $chat = Invoke-JsonPost "$baseUrl/chat/query" $headers @{ question = $question; top_k = 8 }
  if (-not $chat.answer -or $chat.answer.Length -lt 120) {
    throw "Answer too short for question: $question"
  }
  if ($chat.citations.Count -lt 1) {
    throw "No citations returned for question: $question"
  }
  if ($chat.trace.Count -lt 10) {
    throw "Trace did not include all workflow nodes for question: $question"
  }
  if ($chat.confidence_score -lt 0 -or $chat.confidence_score -gt 1) {
    throw "Invalid confidence score for question: $question"
  }
  $answers += [pscustomobject]@{
    question = $question
    answerLength = $chat.answer.Length
    citations = $chat.citations.Count
    confidence = $chat.confidence_score
    confidenceBand = $chat.confidence_band
    status = $chat.status
    traceSteps = $chat.trace.Count
    reviewRequired = $chat.human_review_required
  }
}

$reviews = Invoke-RestMethod -Method Get -Uri "$baseUrl/review/items" -Headers $headers
$analytics = Invoke-RestMethod -Method Get -Uri "$baseUrl/admin/analytics" -Headers $headers
$evalRun = Invoke-JsonPost "$baseUrl/evals/run" $headers @{ name = "OpenAI integration smoke"; dataset_name = "local-openai-smoke" }

[pscustomobject]@{
  health = $health.status
  uploadedDocuments = $uploaded
  answers = $answers
  reviewItems = $reviews.Count
  analytics = $analytics
  evalRun = $evalRun
} | ConvertTo-Json -Depth 8

