# AI-Assisted University Student Complaint Management

A small Streamlit MVP for university staff.

## MVP capabilities

- AI complaint classification
- AI priority/urgency recommendation
- AI department routing recommendation
- Human review and override
- Staff-confirmed status/resolution information
- AI response drafting
- Response editing and approval
- Manual sending
- Basic case record and audit history
- AI failure fallback

## Core product rule

**AI recommends. Staff decides.**

The application does not automatically route complaints, resolve complaints, or send AI-generated responses.

## Repository structure

```text
ai-university-complaint-management/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── .streamlit/
│   └── secrets.toml.example
│
├── src/
│   ├── ai_service.py
│   └── case_store.py
│
└── data/
    └── .gitkeep
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

For AI processing, create `.streamlit/secrets.toml` locally using the example file and add your provider credentials.

## Streamlit deployment

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud.
3. Select the repository and `app.py` as the entry point.
4. Add your secrets in the Streamlit Secrets section using the keys in `secrets.toml.example`.
5. Deploy.

## Security warning

Never put an API key in `app.py`, frontend code, GitHub, screenshots, or documentation.

Use Streamlit Secrets.

## Prototype storage warning

This starter stores cases in a local JSON file for simplicity. That is useful for learning and demos, but it is **not a production storage solution for real student complaint data**. Streamlit-hosted apps should use an approved persistent database before real institutional deployment.

Do not put real student complaint data into GitHub.

## Current AI configuration

The app uses a configurable OpenAI-compatible chat-completions endpoint. The values are read from Streamlit Secrets:

- `GROQ_API_KEY`
- `AI_MODEL`
- `AI_BASE_URL`

The model name is intentionally configurable.

## Scope

This repository intentionally does not include:

- WhatsApp integration
- Email integration
- Student chatbot
- Automatic response sending
- Automatic complaint resolution
- Advanced analytics
- Mobile application
- Complex university integrations
