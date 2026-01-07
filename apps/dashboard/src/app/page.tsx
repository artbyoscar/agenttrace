export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-4">AgentTrace Dashboard</h1>
        <p className="text-xl text-gray-600">
          AI Agent Observability Platform
        </p>
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-bold mb-2">Traces</h2>
            <p className="text-gray-600">View and analyze agent execution traces</p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-bold mb-2">Analytics</h2>
            <p className="text-gray-600">Monitor performance and usage metrics</p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-bold mb-2">Projects</h2>
            <p className="text-gray-600">Manage your agent projects</p>
          </div>
        </div>
      </div>
    </main>
  )
}
