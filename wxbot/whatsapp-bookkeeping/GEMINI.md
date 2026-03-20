# WhatsApp Bookkeeping

## Project Overview

WhatsApp Bookkeeping is a standalone WhatsApp group bookkeeping bot. It is entirely rule-based with zero AI overhead, designed to handle transaction records, balance queries, settlements, and more within WhatsApp groups. 

**Key Technologies:**
*   **Language:** TypeScript / Node.js
*   **WhatsApp API:** `@whiskeysockets/baileys`
*   **Database:** `better-sqlite3`
*   **Logging:** `pino`

**Architecture Overview:**
*   The application connects to WhatsApp using Baileys and listens for messages.
*   It parses incoming messages (often in specific formats like `+100rmb` or `-50rg 5.3`) using rule-based logic (`src/parser.ts`).
*   Data such as transactions, group assignments, balances, and exchange rates are stored in a local SQLite database (`src/database.ts`).
*   It supports features like multi-currency (RMB and NGN), delayed payment reminders, and broadcast messaging to specific group categories.
*   Authentication state for WhatsApp is persisted in the `auth/` directory to maintain login sessions across restarts.

## Building and Running

The project relies on standard npm scripts for its lifecycle:

*   **Install Dependencies:**
    ```bash
    npm install
    ```
*   **Build (Compile TypeScript to JavaScript):**
    ```bash
    npm run build
    ```
*   **Start the Application (Production mode):**
    ```bash
    npm start
    ```
    *Note: On the first run, a QR code will be displayed in the terminal for WhatsApp authentication.*
*   **Run in Development Mode (using `tsx`):**
    ```bash
    npm run dev
    ```
*   **Run Tests:**
    ```bash
    npm test
    ```

## Development Conventions

*   **Configuration:** The main application settings are stored in `config.json` at the project root. This file includes the master phone numbers for admin access and the path to the authentication directory.
*   **Source Structure:** The source code is organized within the `src/` directory:
    *   `index.ts`: The main entry point.
    *   `whatsapp.ts`: Handles WhatsApp connection and event listeners.
    *   `commands.ts`: Implements the logic for various bot commands (e.g., `/bal`, `/mx`, `/js`).
    *   `parser.ts`: Contains the logic for parsing transaction messages.
    *   `database.ts`: Manages SQLite database interactions.
    *   `config.ts`: Handles loading and validating configuration.
*   **Data Storage:** 
    *   The SQLite database is typically stored in the `data/` directory (e.g., `data/bookkeeping.db`).
    *   WhatsApp authentication files are stored in the `auth/` directory (configured via `config.json`).
*   **Testing:** Tests are executed using `tsx` (e.g., `src/parser.test.ts`), focusing on the critical parsing logic.
