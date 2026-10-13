# streamlit-placeholder

Placeholder Streamlit app for testing, deployable as a Keboola data app.

## Run locally

```bash
uv run streamlit run app.py
```

## Keboola deployment

`keboola-config/` holds the runtime config: `setup.sh` installs deps with `uv sync`,
supervisord runs Streamlit on port 8501, and nginx proxies it on port 8888.
