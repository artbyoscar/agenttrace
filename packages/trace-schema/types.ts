/**
 * AgentTrace TypeScript Type Definitions
 *
 * OpenTelemetry-compatible trace and span types with AI agent extensions.
 * Used by the dashboard for type-safe trace visualization and analysis.
 *
 * Generated from the AgentTrace schema specification.
 */

/**
 * AI agent framework identification
 */
export type Framework =
  | 'langchain'
  | 'crewai'
  | 'autogen'
  | 'openai_agents'
  | 'llamaindex'
  | 'semantic_kernel'
  | 'haystack'
  | 'custom'
  | 'unknown';

/**
 * Classification of span types for AI agent operations
 */
export type SpanType =
  // LLM Operations
  | 'llm_call' // Direct LLM API call
  | 'embedding' // Embedding generation
  // Agent Operations
  | 'agent_step' // Single agent reasoning/action step
  | 'chain' // Chain or workflow execution
  | 'workflow' // Multi-step workflow
  // Tool Operations
  | 'tool_call' // External tool invocation
  | 'retrieval' // Vector store or database retrieval
  | 'search' // Web or document search
  // Data Operations
  | 'preprocessing' // Input preprocessing
  | 'postprocessing' // Output postprocessing
  | 'transformation' // Data transformation
  // Memory Operations
  | 'memory_read' // Reading from agent memory
  | 'memory_write' // Writing to agent memory
  // Generic
  | 'span' // Generic span for custom operations
  | 'root'; // Root span of a trace

/**
 * Execution status of a span (OpenTelemetry-compatible)
 */
export type SpanStatus = 'unset' | 'ok' | 'error';

/**
 * Role of a message in LLM conversation
 */
export type MessageRole = 'system' | 'user' | 'assistant' | 'function' | 'tool';

/**
 * Deployment environment
 */
export type Environment = 'development' | 'staging' | 'production' | 'test';

/**
 * Represents a single message in an LLM conversation
 */
export interface Message {
  /** Role of the message */
  role: MessageRole;
  /** Message content */
  content: string;
  /** Name of the function/tool (if role is function/tool) */
  name?: string;
  /** Function call data (deprecated, use tool_calls) */
  function_call?: Record<string, any>;
  /** Tool calls data (new format) */
  tool_calls?: Array<Record<string, any>>;
}

/**
 * Token usage statistics for LLM calls
 */
export interface TokenUsage {
  /** Tokens in the prompt */
  prompt_tokens: number;
  /** Tokens in the completion */
  completion_tokens: number;
  /** Total tokens used */
  total_tokens: number;
}

/**
 * LLM-specific metadata for LLM_CALL spans
 *
 * Captures all relevant information about an LLM API call for
 * debugging, replay, and cost analysis.
 */
export interface LLMCall {
  // Model information
  /** Model name (e.g., 'gpt-4', 'claude-2') */
  model: string;
  /** Provider (e.g., 'openai', 'anthropic') */
  provider?: string;

  // Request parameters
  /** Conversation messages */
  messages: Message[];
  /** Sampling temperature (0-2) */
  temperature?: number;
  /** Maximum tokens to generate */
  max_tokens?: number;
  /** Nucleus sampling parameter (0-1) */
  top_p?: number;
  /** Frequency penalty (-2 to 2) */
  frequency_penalty?: number;
  /** Presence penalty (-2 to 2) */
  presence_penalty?: number;
  /** Stop sequences */
  stop_sequences?: string[];

  // Response data
  /** Generated response text */
  response?: string;
  /** Why generation stopped */
  finish_reason?: 'stop' | 'length' | 'function_call' | 'tool_calls' | 'content_filter';

  // Usage statistics
  /** Token usage */
  usage?: TokenUsage;

  // Function/Tool calling
  /** Available functions */
  functions?: Array<Record<string, any>>;
  /** Function call result */
  function_call?: Record<string, any>;
  /** Available tools (new format) */
  tools?: Array<Record<string, any>>;
  /** Tool choice strategy */
  tool_choice?: string | Record<string, any>;

  // Cost tracking
  /** Estimated cost in USD */
  cost_usd?: number;
}

/**
 * Tool-specific metadata for TOOL_CALL spans
 */
export interface ToolCall {
  /** Name of the tool */
  tool_name: string;
  /** Input parameters */
  tool_input?: Record<string, any>;
  /** Output result */
  tool_output?: any;
  /** Error message if failed */
  tool_error?: string;
  /** Additional tool metadata */
  tool_metadata?: Record<string, any>;
}

/**
 * Retrieval-specific metadata for RETRIEVAL spans
 *
 * Captures vector search and retrieval operations, common in RAG systems.
 */
export interface RetrievalCall {
  /** Query text or embedding */
  query: string;
  /** Collection/index name */
  collection?: string;
  /** Number of results requested */
  top_k?: number;
  /** Minimum similarity score (0-1) */
  score_threshold?: number;
  /** Query filters */
  filters?: Record<string, any>;

  // Results
  /** Actual number of results */
  num_results?: number;
  /** Retrieved documents */
  results?: Array<Record<string, any>>;
  /** Similarity scores (0-1) */
  scores?: number[];
}

/**
 * An event that occurred during span execution
 *
 * Based on OpenTelemetry span events.
 */
export interface SpanEvent {
  /** Event name */
  name: string;
  /** When the event occurred (ISO 8601) */
  timestamp: string;
  /** Event attributes */
  attributes: Record<string, any>;
}

/**
 * Link to another span
 *
 * Based on OpenTelemetry span links.
 */
export interface SpanLink {
  /** Linked trace ID */
  trace_id: string;
  /** Linked span ID */
  span_id: string;
  /** Link attributes */
  attributes: Record<string, any>;
}

/**
 * Error information for failed spans
 */
export interface SpanError {
  /** Error type/class name */
  type: string;
  /** Error message */
  message: string;
  /** Stack trace */
  traceback?: string;
}

/**
 * Represents a single operation in a trace
 *
 * Based on OpenTelemetry span specification with AI agent-specific extensions.
 */
export interface Span {
  // OpenTelemetry-compatible fields
  /** Unique identifier for the trace */
  trace_id: string;
  /** Unique identifier for this span */
  span_id: string;
  /** Parent span ID (null for root) */
  parent_span_id?: string | null;
  /** Human-readable span name */
  name: string;
  /** When span started (ISO 8601) */
  start_time: string;
  /** When span ended (ISO 8601) */
  end_time?: string | null;
  /** Duration in seconds */
  duration?: number | null;
  /** Execution status */
  status: SpanStatus;
  /** Additional status info */
  status_message?: string;

  // AI agent-specific fields
  /** Type of operation */
  span_type: SpanType;
  /** Framework that generated this span */
  framework: Framework;

  // Input/Output for replay
  /** Input to the operation */
  input?: any;
  /** Output from the operation */
  output?: any;

  // Type-specific metadata
  /** LLM call metadata (if span_type is llm_call) */
  llm?: LLMCall;
  /** Tool call metadata (if span_type is tool_call) */
  tool?: ToolCall;
  /** Retrieval metadata (if span_type is retrieval) */
  retrieval?: RetrievalCall;

  // OpenTelemetry attributes and context
  /** Custom attributes */
  attributes: Record<string, any>;
  /** Span events (logs) */
  events: SpanEvent[];
  /** Links to other spans */
  links: SpanLink[];

  // Error tracking
  /** Error information if status is error */
  error?: SpanError;

  // Metadata
  /** Tags for filtering */
  tags: string[];
  /** Additional metadata */
  metadata: Record<string, any>;
}

/**
 * Represents a complete trace (collection of spans)
 *
 * A trace represents an end-to-end execution of an agent operation.
 */
export interface Trace {
  // Trace identification
  /** Unique identifier for the trace */
  trace_id: string;
  /** Human-readable trace name */
  name: string;
  /** Project this trace belongs to */
  project_id: string;

  // Temporal information
  /** When trace started (ISO 8601) */
  start_time: string;
  /** When trace ended (ISO 8601) */
  end_time?: string | null;
  /** Total trace duration in seconds */
  duration?: number | null;

  // Status
  /** Overall trace status */
  status: SpanStatus;

  // Classification
  /** Primary framework used */
  framework: Framework;
  /** Tags for filtering */
  tags: string[];
  /** Environment (dev, staging, prod) */
  environment: Environment;

  // Metadata
  /** Custom metadata */
  metadata: Record<string, any>;
  /** User who triggered the trace */
  user_id?: string;
  /** Session identifier */
  session_id?: string;

  // Spans
  /** All spans in the trace */
  spans: Span[];

  // Summary statistics
  /** Total tokens across all LLM calls */
  total_tokens?: number | null;
  /** Total cost across all LLM calls */
  total_cost?: number | null;
  /** Number of spans with errors */
  error_count: number;
}

/**
 * Trace list item (summary view)
 *
 * Lighter version of Trace for list views, without full span details.
 */
export interface TraceSummary {
  trace_id: string;
  name: string;
  project_id: string;
  start_time: string;
  end_time?: string | null;
  duration?: number | null;
  status: SpanStatus;
  framework: Framework;
  tags: string[];
  environment: Environment;
  total_tokens?: number | null;
  total_cost?: number | null;
  error_count: number;
  span_count: number;
  user_id?: string;
  session_id?: string;
}

/**
 * Query parameters for fetching traces
 */
export interface TraceQueryParams {
  /** Project ID to filter by */
  project_id?: string;
  /** Framework to filter by */
  framework?: Framework;
  /** Status to filter by */
  status?: SpanStatus;
  /** Environment to filter by */
  environment?: Environment;
  /** Tags to filter by (AND logic) */
  tags?: string[];
  /** User ID to filter by */
  user_id?: string;
  /** Session ID to filter by */
  session_id?: string;
  /** Start time range (ISO 8601) */
  start_time_gte?: string;
  /** End time range (ISO 8601) */
  start_time_lte?: string;
  /** Minimum duration in seconds */
  duration_gte?: number;
  /** Maximum duration in seconds */
  duration_lte?: number;
  /** Search query (name, metadata) */
  search?: string;
  /** Page number (1-indexed) */
  page?: number;
  /** Page size */
  page_size?: number;
  /** Sort field */
  sort_by?: 'start_time' | 'duration' | 'total_tokens' | 'total_cost';
  /** Sort order */
  sort_order?: 'asc' | 'desc';
}

/**
 * Paginated trace list response
 */
export interface TraceListResponse {
  /** List of trace summaries */
  traces: TraceSummary[];
  /** Total number of traces matching query */
  total: number;
  /** Current page (1-indexed) */
  page: number;
  /** Page size */
  page_size: number;
  /** Total number of pages */
  total_pages: number;
  /** Whether there are more pages */
  has_next: boolean;
  /** Whether there are previous pages */
  has_previous: boolean;
}

/**
 * Analytics aggregation result
 */
export interface TraceAnalytics {
  /** Time period for analytics */
  period: {
    start: string;
    end: string;
  };
  /** Total number of traces */
  total_traces: number;
  /** Total tokens used */
  total_tokens: number;
  /** Total cost in USD */
  total_cost: number;
  /** Average duration in seconds */
  avg_duration: number;
  /** Error rate (0-1) */
  error_rate: number;
  /** Breakdown by framework */
  by_framework: Record<Framework, number>;
  /** Breakdown by span type */
  by_span_type: Record<SpanType, number>;
  /** Time series data points */
  timeseries?: Array<{
    timestamp: string;
    trace_count: number;
    token_count: number;
    cost: number;
    avg_duration: number;
    error_count: number;
  }>;
}

/**
 * Type guards for runtime type checking
 */
export const isLLMSpan = (span: Span): span is Span & { llm: LLMCall } => {
  return span.span_type === 'llm_call' && span.llm !== undefined;
};

export const isToolSpan = (span: Span): span is Span & { tool: ToolCall } => {
  return span.span_type === 'tool_call' && span.tool !== undefined;
};

export const isRetrievalSpan = (span: Span): span is Span & { retrieval: RetrievalCall } => {
  return span.span_type === 'retrieval' && span.retrieval !== undefined;
};

export const isRootSpan = (span: Span): boolean => {
  return span.parent_span_id === null || span.parent_span_id === undefined;
};

export const hasError = (span: Span): boolean => {
  return span.status === 'error';
};

/**
 * Utility functions for working with traces
 */
export const getSpanDurationMs = (span: Span): number | null => {
  return span.duration ? span.duration * 1000 : null;
};

export const getTraceDurationMs = (trace: Trace): number | null => {
  return trace.duration ? trace.duration * 1000 : null;
};

export const getRootSpan = (trace: Trace): Span | undefined => {
  return trace.spans.find(isRootSpan);
};

export const getChildSpans = (trace: Trace, parentSpanId: string): Span[] => {
  return trace.spans.filter((span) => span.parent_span_id === parentSpanId);
};

export const getSpanById = (trace: Trace, spanId: string): Span | undefined => {
  return trace.spans.find((span) => span.span_id === spanId);
};

export const formatCost = (cost?: number | null): string => {
  if (cost === undefined || cost === null) return '-';
  return `$${cost.toFixed(4)}`;
};

export const formatTokens = (tokens?: number | null): string => {
  if (tokens === undefined || tokens === null) return '-';
  return tokens.toLocaleString();
};

export const formatDuration = (duration?: number | null): string => {
  if (duration === undefined || duration === null) return '-';
  if (duration < 1) return `${(duration * 1000).toFixed(0)}ms`;
  if (duration < 60) return `${duration.toFixed(2)}s`;
  return `${(duration / 60).toFixed(2)}m`;
};
