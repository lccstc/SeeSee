# Monorepo Migration Plan for AI Agent

**Objective:** Refactor the current `whatsapp-bookkeeping` single-package Node.js/TypeScript project into an npm workspaces monorepo structure. This will allow sharing the core bookkeeping logic across different platforms (e.g., WhatsApp, WeChat, Web Backend).

**Current Project State:**
- Single package project.
- Core logic (`parser.ts`, `database.ts`) is mixed with platform-specific logic (`whatsapp.ts`, `commands.ts`) in the `src/` directory.
- Root contains `package.json`, `tsconfig.json`, `config.json`, and directories like `data/` and `auth/`.

**Target Architecture (Monorepo):**
```text
/ (Project Root)
├── package.json          (Workspace root)
├── tsconfig.base.json    (Shared TS config)
├── config.json           (Global app config - Namespaced)
├── data/                 (Shared SQLite DB)
├── auth/                 (WhatsApp auth data)
└── packages/
    ├── core/             (Shared business logic: @bookkeeping/core)
    │   ├── package.json
    │   ├── tsconfig.json
    │   └── src/
    │       ├── index.ts
    │       ├── parser.ts
    │       ├── database.ts
    │       ├── config.ts
    │       └── command-handler.ts  <-- NEW: Pure text command logic
    ├── whatsapp/         (WhatsApp bot app: @bookkeeping/whatsapp)
    │   ├── package.json
    │   ├── tsconfig.json
    │   └── src/
    │       ├── index.ts
    │       ├── whatsapp.ts
    │       └── commands.ts         <-- Platform-specific sending only
    └── wechat/           (Future WeChat bot app: @bookkeeping/wechat)
        └── ...
```

---

## Strategic Considerations for WeChat Migration (IMPORTANT)

Before implementing the WeChat package, the developer/agent must address the platform constraints of Personal WeChat:
1. **API Limitations:** Personal WeChat does not have an official open API. The traditional Web protocol is blocked for most accounts created after 2017.
2. **Recommended Solutions:** 
   - **Wechaty with PadLocal/Mac plugins:** Highly stable but often requires a paid token.
   - **WeChatFerry:** Free, hooks into Windows PC WeChat, requires a Windows environment or VM.
3. **Action Item:** Build a tiny standalone 50-line "Hello World" ping-pong bot using the chosen WeChat library *before* integrating it into this monorepo, just to verify the current WeChat account can actually log in and send messages.

---

## Execution Steps for AI Agent

Please execute the following steps precisely. Do not delete the `.git` directory or any existing configuration files (`config.json`, `.env`, etc.) unless explicitly instructed.

### Step 1: Prepare the Root Directory & Config
1.  Create a `packages` directory in the project root.
    *   `mkdir packages`
2.  Rename the existing `tsconfig.json` to `tsconfig.base.json`.
3.  Update `tsconfig.base.json` to be a base configuration. Ensure it does *not* have `include` or `exclude` paths that restrict it to the old `src/` directory.
4.  Rewrite the root `package.json` to configure npm workspaces. Remove all `dependencies` and keep only shared `devDependencies`.
    ```json
    {
      "name": "omni-bookkeeping",
      "private": true,
      "workspaces": [
        "packages/*"
      ],
      "scripts": {
        "build": "npm run build --workspaces",
        "dev:wa": "npm run dev --workspace=@bookkeeping/whatsapp",
        "start:wa": "npm run start --workspace=@bookkeeping/whatsapp"
      },
      "devDependencies": {
        "@types/node": "^20.0.0",
        "tsx": "^4.0.0",
        "typescript": "^5.0.0"
      }
    }
    ```
5. **Update `config.json` structure:** Refactor the global config to use namespaces to prevent platform collision.
    ```json
    {
      "core": {
        "masterPhones": ["..."]
      },
      "whatsapp": {
        "authDir": "./auth"
      },
      "wechat": {
        "puppet": "wechaty-puppet-padlocal",
        "token": "YOUR_TOKEN_HERE"
      },
      "logLevel": "info"
    }
    ```

### Step 2: Extract the `@bookkeeping/core` Package
1.  Create the directory structure: `mkdir -p packages/core/src`
2.  Move core files from the old `src/` directory to `packages/core/src/`:
    *   `mv src/parser.ts packages/core/src/`
    *   `mv src/database.ts packages/core/src/`
    *   `mv src/config.ts packages/core/src/`
3.  **Refactor Command Logic:** Extract the pure text-generation logic from the old `commands.ts` into a new `packages/core/src/command-handler.ts`. This handler should accept pure text inputs (e.g., `/bal`) and return pure string outputs (e.g., `Your balance is 100`), without knowing anything about WhatsApp or Baileys.
4.  Create `packages/core/src/index.ts` to export all core modules:
    ```typescript
    export * from './parser.js';
    export * from './database.js';
    export * from './config.js';
    export * from './command-handler.js';
    ```
5.  Create `packages/core/package.json`:
    ```json
    {
      "name": "@bookkeeping/core",
      "version": "1.0.0",
      "type": "module",
      "main": "dist/index.js",
      "types": "dist/index.d.ts",
      "scripts": {
        "build": "tsc"
      },
      "dependencies": {
        "better-sqlite3": "^11.0.0",
        "@types/better-sqlite3": "^7.6.0",
        "pino": "^9.0.0"
      }
    }
    ```
6.  Create `packages/core/tsconfig.json` that extends the base config:
    ```json
    {
      "extends": "../../tsconfig.base.json",
      "compilerOptions": {
        "outDir": "./dist",
        "rootDir": "./src",
        "declaration": true
      },
      "include": ["src/**/*"]
    }
    ```
7.  **Crucial Fix for `database.ts` & `config.ts`**: Since the file location has moved deeper into `packages/core/src/`, relative paths to the root `data/` and `config.json` might break.
    *   Update `database.ts` to resolve the path to `data/bookkeeping.db` relative to the *process current working directory* (`process.cwd()`) or explicitly navigate up to the root.
    *   Update `config.ts` to read the new namespaced `config.json` from the correct relative path or `process.cwd()`.

### Step 3: Extract the `@bookkeeping/whatsapp` Package
1.  Create the directory structure: `mkdir -p packages/whatsapp/src`
2.  Move the remaining WhatsApp-specific files from the old `src/` directory to `packages/whatsapp/src/`:
    *   `mv src/whatsapp.ts packages/whatsapp/src/`
    *   `mv src/commands.ts packages/whatsapp/src/` (Refactor this to merely act as a bridge between Baileys and the core `command-handler.ts`)
    *   `mv src/index.ts packages/whatsapp/src/`
3.  Delete the now-empty root `src/` directory: `rmdir src`
4.  Create `packages/whatsapp/package.json`:
    ```json
    {
      "name": "@bookkeeping/whatsapp",
      "version": "1.0.0",
      "type": "module",
      "main": "dist/index.js",
      "scripts": {
        "build": "tsc",
        "start": "node dist/index.js",
        "dev": "tsx src/index.ts"
      },
      "dependencies": {
        "@bookkeeping/core": "*",
        "@whiskeysockets/baileys": "^7.0.0-rc.9",
        "qrcode-terminal": "^0.12.0",
        "@types/qrcode-terminal": "^0.12.2"
      }
    }
    ```
5.  Create `packages/whatsapp/tsconfig.json`:
    ```json
    {
      "extends": "../../tsconfig.base.json",
      "compilerOptions": {
        "outDir": "./dist",
        "rootDir": "./src"
      },
      "include": ["src/**/*"],
      "references": [
        { "path": "../core" }
      ]
    }
    ```

### Step 4: Refactor Imports in `@bookkeeping/whatsapp`
Scan all `.ts` files inside `packages/whatsapp/src/` (`whatsapp.ts`, `commands.ts`, `index.ts`).
Replace any relative imports pointing to core modules with the new package name.
*   Change: `import { parseMessage } from './parser.js';`
*   To: `import { parseMessage } from '@bookkeeping/core';`
*   Change: `import { db } from './database.js';`
*   To: `import { db } from '@bookkeeping/core';`
*   Change: `import { config } from './config.js';`
*   To: `import { config } from '@bookkeeping/core';`

### Step 5: Install and Verify
1.  Run `npm install` at the project root to link the workspaces.
2.  Run `npm run build` at the root to ensure both packages compile successfully.
3.  Run `npm run dev:wa` to start the WhatsApp bot in development mode.
4.  Verify that the bot starts, connects to WhatsApp (using existing auth data), and can read/write to the database.

**Completion Condition:**
The project must compile without type errors (`npm run build`), and the `npm run dev:wa` command must successfully start the WhatsApp bot, correctly resolving the local `@bookkeeping/core` package.