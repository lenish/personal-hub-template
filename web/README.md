# Personal Hub - Web

Next.js 15 frontend for Personal Hub.

## 🏗️ Status: Template

This directory is intentionally minimal. You should implement:

- `src/app/` - Next.js App Router pages
- `src/components/` - React components
- `src/lib/` - Utility functions
- `package.json` - Dependencies

## 📚 Example Structure

```
web/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── auth/
│   │   ├── dash/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx        # Dashboard home
│   │   │   ├── health/         # Health metrics
│   │   │   └── intel/          # Intel reports
│   │   └── api/
│   │       └── auth/           # Auth.js routes
│   ├── components/
│   │   ├── ui/                 # Radix UI components
│   │   ├── health/             # Health widgets
│   │   └── charts/             # Chart components
│   └── lib/
│       ├── auth.ts             # Auth.js config
│       ├── api.ts              # API client
│       └── utils.ts
└── public/
    └── images/
```

## 🚀 Getting Started

See the full Personal Hub repository for a complete implementation example.

## 📖 Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [Auth.js Documentation](https://authjs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Radix UI Documentation](https://www.radix-ui.com/docs)
