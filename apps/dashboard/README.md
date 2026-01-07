# AgentTrace Dashboard

Next.js frontend for AgentTrace.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp ../../.env.example .env.local
# Edit .env.local with your configuration
```

3. Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

## Tech Stack

- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- TanStack Query (React Query)
- Zustand (State Management)
- Recharts (Charts)
- NextAuth.js (Authentication)

## Project Structure

```
dashboard/
├── src/
│   ├── app/              # Next.js app router
│   ├── components/       # React components
│   ├── lib/             # Utilities and helpers
│   ├── hooks/           # Custom React hooks
│   └── types/           # TypeScript types
├── public/              # Static assets
└── tests/               # Test files
```

## Testing

```bash
npm test
```

## Building for Production

```bash
npm run build
npm start
```
