/**
 * Loading State Component
 * Displays loading skeleton for benchmark pages
 */

export function LoadingState({ rows = 10 }: { rows?: number }) {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Header skeleton */}
      <div className="h-8 bg-gray-200 rounded w-1/3"></div>
      <div className="h-4 bg-gray-200 rounded w-1/4"></div>

      {/* Table skeleton */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        {/* Table header */}
        <div className="bg-gray-50 border-b border-gray-200 p-4">
          <div className="flex gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-300 rounded flex-1"></div>
            ))}
          </div>
        </div>

        {/* Table rows */}
        {[...Array(rows)].map((_, i) => (
          <div key={i} className="border-b border-gray-200 p-4">
            <div className="flex gap-4">
              {[...Array(6)].map((_, j) => (
                <div key={j} className="h-4 bg-gray-200 rounded flex-1"></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ChartLoadingState({ height = 400 }: { height?: number }) {
  return (
    <div
      className="bg-gray-100 rounded-lg animate-pulse flex items-center justify-center"
      style={{ height }}
    >
      <div className="text-gray-400 text-sm">Loading chart...</div>
    </div>
  );
}
