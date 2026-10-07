# HiMP Project

**HiMP Project** is a desktop application built with **Tkinter** originally designed to help law offices manage clients, cases and documents — but it is intentionally generic and can be adapted to other domains.
Key capabilities:

- Client management (personal data, multiple processes per client)
- Case / process management (statuses, phases, attachments)
- Payments management (status, references, amounts)
- Google Calendar integration for scheduling (create / sync events)
- Automatic document generation from `.docx` templates
- Backed by a **Supabase (PostgreSQL)** database

---

## Table of contents

1. [Requirements](#requirements)
2. [Install Python dependencies](#install-python-dependencies)
3. [Project layout / important files](#project-layout--important-files)
4. [Google Calendar setup (credentials.json)](#google-calendar-setup-credentialsjson)
5. [Supabase (PostgreSQL) setup — database tables](#supabase-postgresql-setup---database-tables)
6. [Environment variables (`.env`) - example](#environment-variables-env---example)
7. [Document generator configuration](#document-generator-configuration)
8. [Application configuration (pagina.py)](#application-configuration-paginapy)
9. [Packaging / building an executable (PyInstaller)](#packaging--building-an-executable-pyinstaller)
10. [Run / Usage](#run--usage)
11. [Troubleshooting & notes](#troubleshooting--notes)
12. [Security, privacy & license notes](#security-privacy--license-notes)

---

## Requirements

- Python 3.10+ (recommend latest stable 3.x)
- Internet access during runtime for Supabase and Google Calendar integration
- A Supabase project with PostgreSQL (tables must be created — see SQL below)
- Google Cloud Console access to create `credentials.json` for Calendar API

### Python libraries

Install the required Python packages:

```bash
pip3 install tkinter google-auth google-auth-oauthlib google-api-python-client pytz python-docx docxtpl pydantic email-validator supabase num2words python-dotenv
```

> Note: `tkinter` is included with many Python distributions; on some Linux systems you may need to install the OS package (for example `sudo apt install python3-tk`).

---

## Install / Setup

1. Clone your repository (or copy files) into a local folder:

```bash
git clone <your-repo-url>
cd <your-project-folder>
```

2. Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows PowerShell
pip install -r requirements.txt  # if you maintain this file; otherwise use the pip line above
```

3. Create a `.env` file in the project root and populate the required environment variables (example below).

4. Create the database tables in your Supabase project using the SQL in the next section.

5. Place the Google Calendar `credentials.json` file inside the `Calendar/` folder.

6. Configure `gerador_documentos.py` and `pagina.py` as described below.

---

## Project layout / important files

```
HIMP_PROJECT/
├── calendar/
│   └── calendar.py                 # Google Calendar integration logic
│
├── gerador_documentos/
│   └── gerador_docs.py             # Document generator configuration & logic
│
├── Home_Page/
│   ├── crud_support.py             # CRUD helper functions for main app
│   └── pagina.py                   # Main application UI (home page)
│
├── Login_Page/
│   ├── loginpage_support.py        # Login utility functions
│   └── loginpage.py                # Login UI
│
├── database.py                     # Supabase/PostgreSQL database connector
├── main.py                         # Application entry point
├── .env                            # Environment variables (Supabase keys, etc.)
└── requirements.txt                # Python dependencies

```

---

## Google Calendar setup (credentials.json)

1. In the Google Cloud Console:

   - Create a project (or use an existing one).
   - Enable the **Google Calendar API** for that project.
   - Under **APIs & Services → Credentials**, create an OAuth 2.0 Client ID (choose Desktop app).
   - Download the JSON file and save it as: `Calendar/credentials.json`.

2. Place `credentials.json` at exactly:
   `Calendar/credentials.json` (relative to project root). The app uses that file to perform OAuth and create tokens to access the Calendar API.

3. On first run, the app will typically open a browser window to complete the OAuth flow and save a token file (commonly `token.json` or similar) — keep that token file in the `Calendar/` folder or as the app expects.

> If you get `scopes` or permissions errors, re-check the OAuth credentials and ensure your OAuth consent screen is configured (external/internal as needed).

---

## Supabase (PostgreSQL) setup — database tables

Create the following tables in your Supabase project. You can paste this SQL into the Supabase SQL editor and run it.

> NOTE: This SQL is provided exactly as given — adjust identifiers or column types if your Supabase/Postgres settings require different naming conventions.

```sql
create table public.cliente (
  passaporte text null,
  nif text null,
  niss text null,
  bi_cc_titulo_residência text null,
  data_nascimento date null,
  nome_completo text null,
  cliente_id integer generated by default as identity not null,
  gênero text null,
  rua text null,
  numero_rua text null,
  complemento text null,
  localidade text null,
  código_postal text null,
  profissão text null,
  validade_passaporte date null,
  validade_bi_cc date null,
  email text null,
  emissão_passaporte date null,
  ddi bigint null,
  contato text null,
  nacionalidade text null,
  local_emissão_passaporte text null,
  naturalidade text null,
  notas_documento text null,
  estado_civil text null,
  emissão_bi_cc date null,
  constraint cliente_pkey primary key (cliente_id),
  constraint cliente_nif_key unique (nif),
  constraint cliente_niss_key unique (niss),
  constraint cliente_passaporte_key unique (passaporte),
  constraint cliente_titulo_residencia_key unique ("bi_cc_titulo_residência")
) TABLESPACE pg_default;

create table public.agendamento (
  evento_id bigint generated by default as identity not null,
  data_inicio timestamp without time zone null,
  duracao text null,
  motivo text null,
  descricao text null,
  google_event_id text null,
  cliente_id integer null,
  titulo text null,
  constraint agendamento_pkey primary key (evento_id),
  constraint agendamento_cliente_id_fkey foreign KEY (cliente_id) references cliente (cliente_id)
) TABLESPACE pg_default;

create table public.documentos_cliente (
  id serial not null,
  cliente_id integer not null,
  documento_nome text not null,
  entregue boolean null default false,
  constraint documentos_cliente_pkey primary key (id),
  constraint documentos_cliente_cliente_id_fkey foreign KEY (cliente_id) references cliente (cliente_id) on delete CASCADE
) TABLESPACE pg_default;

create table public.entidade (
  entidade_id bigint generated by default as identity not null,
  entidade text not null,
  constraint entidade_pkey primary key (entidade_id)
) TABLESPACE pg_default;

create table public.etapa_processo (
  etapa_id bigint generated by default as identity not null,
  processo_id bigint not null,
  fase_id bigint null,
  data_fase date null,
  observação text null,
  constraint etapa_processo_pkey primary key (etapa_id),
  constraint etapa_processo_cliente_processo_id_fkey foreign KEY (processo_id) references processo (processo_id),
  constraint etapa_processo_fase_id_fkey foreign KEY (fase_id) references lista_fases_processo (fase_id)
) TABLESPACE pg_default;

create table public.lista_fases_processo (
  fase_id bigint generated by default as identity not null,
  fase text not null,
  constraint lista_fases_processo_pkey primary key (fase_id)
) TABLESPACE pg_default;

create table public.motivo (
  motivo_id bigint generated by default as identity not null,
  motivo text not null,
  constraint motivo_pkey primary key (motivo_id)
) TABLESPACE pg_default;

create table public.pagamento (
  pagamento_id bigint generated by default as identity not null,
  entidade integer null,
  referencia integer null,
  montante real null,
  data_limite date null,
  data_conclusao date null,
  status_id bigint null,
  motivo_id bigint null,
  cliente_id bigint null,
  constraint pagamento_pkey primary key (pagamento_id),
  constraint pagamento_cliente_id_fkey foreign KEY (cliente_id) references cliente (cliente_id),
  constraint pagamento_motivo_id_fkey foreign KEY (motivo_id) references motivo (motivo_id),
  constraint pagamento_status_id_fkey foreign KEY (status_id) references status_pagamento (status_id)
) TABLESPACE pg_default;

create table public.processo (
  entidade_id bigint null,
  juiz text null,
  processo_anexo_principal text null,
  processo_id bigint generated by default as identity not null,
  numero_processo text null,
  cliente_id bigint not null,
  tipo_do_processo_id bigint null,
  constraint processo_pkey primary key (processo_id),
  constraint processo_numero_processo_key unique (numero_processo),
  constraint processo_cliente_id_fkey foreign KEY (cliente_id) references cliente (cliente_id),
  constraint processo_entidade_id_fkey foreign KEY (entidade_id) references entidade (entidade_id),
  constraint processo_tipo_do_processo_id_fkey foreign KEY (tipo_do_processo_id) references tipo_do_processo (tipo_do_processo_id)
) TABLESPACE pg_default;

create table public.status_pagamento (
  status_id bigint generated by default as identity not null,
  status text not null,
  constraint status_pagamento_pkey primary key (status_id)
) TABLESPACE pg_default;

create table public.tipo_do_processo (
  tipo_do_processo_id bigint generated by default as identity not null,
  tipo_do_processo text not null,
  constraint tipo_do_processo_pkey primary key (tipo_do_processo_id)
) TABLESPACE pg_default;

create table public.users (
  id bigint generated by default as identity not null,
  nif bigint not null,
  password text not null,
  constraint Users_pkey primary key (id),
  constraint Users_nif_key unique (nif)
) TABLESPACE pg_default;
```

After creating tables, insert any needed static lists (e.g., `lista_fases_processo`, `motivo`, `status_pagamento`, `tipo_do_processo`, `entidade`) that your app expects.

---

## Environment variables (`.env`) — example

Create a file named `.env` in the project root and **do not commit it to git**.

Example `.env` template (edit values to match your Supabase project and any other keys used by your app):

```ini
# Supabase
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Google Calendar
# Path to the credentials file (relative to project root)
CALENDAR_CREDENTIALS_PATH=Calendar/credentials.json

```

> Which Supabase key to use:
>
> - For client-side-like operations use the **anon** key.
> - For server-side privileged operations (insert/update that require bypassing RLS / elevated permissions), the **service role** key is required. Check your code to see which key the application uses. Keep the service role key secret.

---

## Document generator configuration

The document generator reads a dictionary `documentos_info` inside `gerador_docs.py`

```python
documentos_info = {
    "Modelo de Documento": {
        "arquivo": "modelo_documento.docx",
        "campos": ["nome", "nif", "endereço"]
    }
}
```

### Steps to add templates

1. Put your `.docx` template in `gerador_documentos/` (for example `gerador_documentos/modelo_documento.docx`).

2. In `gerador_docs.py`, add an entry to `documentos_info` for each template:

   - Key = display name (this is the name shown in the UI)
   - `arquivo` = file name inside the `gerador_documentos/` folder
   - `campos` = list of field names the template expects (these must match the fields you pass when rendering)

3. Example:

```python
documentos_info = {
    "Power of Attorney - Example": {
        "arquivo": "procuracao_example.docx",
        "campos": ["nome", "passaporte", "nif", "endereço", "data_documento"]
    }
}
```

---

## Application configuration (`pagina.py`)

`pagina.py` contains UI configuration and a list of available document templates. You must add the document display name (exactly as used in `documentos_info`) to the `self.modelos_de_documento` list. Example excerpt:

```python
self.modelos_de_documento = [
    "Modelo de Documento"
]
```

### Fixed-value boxes

Some UI boxes contain fixed/default values that are safe to change directly in `pagina.py`. If you need to localize labels or change default values, edit `pagina.py` accordingly. The README can't list every editable box — inspect `pagina.py` for constants and default values and adjust to your needs.

---

## Packaging / Building an executable (PyInstaller)

You can compile the app into a single executable with PyInstaller. Example command:

```bash
python -m PyInstaller --onefile --windowed \
  --add-data "gerador_documentos/modelo_documento.docx;gerador_documentos" \
  --add-data ".env;." \
  --add-data "Calendar/credentials.json;Calendar" \
  main.py
```

Notes:

- On Windows, PyInstaller `--add-data` uses a different separator; the format above works when run inside a bash-like shell. If on Windows native shell, you may need to change the `;` to `;` still but the first path style may need quotes. If packaging on Windows, test and adapt the `--add-data` arguments as PyInstaller docs specify.
- The resulting executable will be in `dist/` (e.g., `dist/main.exe` on Windows or `dist/main` on macOS / Linux).
- You can compile on mac and windows — remember you must compile on each platform or use cross-compilation methods (recommended: build on each target platform).

---

## Run / Usage

While developing or running from source:

```bash
source .venv/bin/activate
python main.py
```

When running the built executable:

- On macOS / Linux:

```bash
./dist/main
```

- On Windows:

Double-click `dist\main.exe` or run in PowerShell / cmd:

```powershell
.\dist\main.exe
```

First run will often require:

- Completing Google OAuth flow (browser will open)
- Confirming / allowing Calendar permissions
- Ensuring `.env` keys are correct and Supabase is reachable

---

## Troubleshooting & common gotchas

- **Missing `credentials.json`**: The calendar functions will fail. Ensure `Calendar/credentials.json` exists and is valid. The app expects it there.
- **Supabase auth / permission errors**: Check which Supabase key you used. If operations require elevated privileges, provide the service role key in `.env`, but keep it secret.
- **Token / OAuth errors**: If Google OAuth fails, delete any saved token files in `Calendar/` (e.g., `token.json`) and re-run to reauthorize.
- **PyInstaller missing files**: If templates or `.env` are not found after building, confirm `--add-data` paths and that runtime code uses relative paths.
- **Database constraints / insertion errors**: The SQL schema includes unique constraints (e.g., `nif`, `niss`, `passaporte`). Ensure data you insert does not violate them.
- **Locale / encoding issues**: Some column names include non-ASCII characters (e.g., `bi_cc_titulo_residência`, `código_postal`, `gênero`, `observação`). If you face issues, consider renaming columns to ASCII-only identifiers and update the code accordingly.
