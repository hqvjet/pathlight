# Frontend Folder Overview 💻

## Folder Purpose 🎯
Next.js 14 application providing the user interface for PathLight.

## Full Directory Tree
```text
frontend/
  ├── .gitignore
  ├── README.md
  ├── eslint.config.mjs
  ├── next.config.ts
  ├── package-lock.json
  ├── package.json
  ├── postcss.config.mjs
  ├── public/
  │   ├── file.svg
  │   ├── globe.svg
  │   ├── next.svg
  │   ├── vercel.svg
  │   └── window.svg
  ├── src/
  │   └── app/
  │       ├── favicon.ico
  │       ├── globals.css
  │       ├── layout.tsx
  │       └── page.tsx
  └── tsconfig.json
```

## Item-by-Item Table
| Path | Role |
| --- | --- |
| .gitignore | Ignore patterns for Node-related files. |
| README.md | Instructions for running the Next.js app. |
| eslint.config.mjs | ESLint rules used during linting. |
| next.config.ts | Next.js configuration and plugins. |
| package-lock.json | Exact dependency versions for npm. |
| package.json | Declares dependencies and scripts. |
| postcss.config.mjs | Tailwind/PostCSS configuration. |
| public/ | Static assets served directly. |
| public/file.svg | SVG icon asset. |
| public/globe.svg | SVG icon asset. |
| public/next.svg | SVG icon asset. |
| public/vercel.svg | SVG icon asset. |
| public/window.svg | SVG icon asset. |
| src/ | Application source code. |
| src/app | Next.js app directory. |
| src/app/favicon.ico | Browser favicon. |
| src/app/globals.css | Global CSS styles. |
| src/app/layout.tsx | Root layout component. |
| src/app/page.tsx | Home page component. |
| tsconfig.json | TypeScript compiler options. |

## Key Workflows / Entry Points
- `npm run dev` launches the development server on port 3000.
- `npm run build` creates an optimized production build.
- `npx next lint` checks code quality using ESLint.

## Example Usage
```bash
cd frontend
npm install
npm run dev
```

## Development Tips
- Ensure Node 18+ is installed for compatibility.
- Tailwind styles live in `globals.css` and the `postcss` config.

## TODO
- TODO: add unit tests and more pages.
