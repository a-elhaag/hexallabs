from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.services.foundry import complete, _models

router = APIRouter(tags=["test"])


class ChatRequest(BaseModel):
    model: str
    message: str
    system_prompt: str = "You are a helpful assistant."


class ChatResponse(BaseModel):
    model: str
    deployment: str
    response: str


@router.post("/test/chat", response_model=ChatResponse)
async def test_chat(body: ChatRequest):
    deployments = _models()
    response = await complete(
        model=body.model,
        system_prompt=body.system_prompt,
        user_message=body.message,
    )
    return ChatResponse(
        model=body.model,
        deployment=deployments.get(body.model, body.model),
        response=response,
    )


@router.get("/test", response_class=HTMLResponse)
async def test_ui():
    models = list(_models().keys())
    models_json = str(models).replace("'", '"')
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hexallabs — Model Tester</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    background: #fff;
    color: #000;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48px 24px;
  }}
  h1 {{ font-size: 32px; font-weight: 600; margin-bottom: 8px; }}
  p.sub {{ font-size: 14px; color: #6B7280; margin-bottom: 40px; }}

  .card {{
    width: 100%;
    max-width: 720px;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 32px;
    transition: box-shadow 300ms cubic-bezier(0.16,1,0.3,1),
                transform 300ms cubic-bezier(0.16,1,0.3,1);
  }}
  .card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.08);
  }}

  label {{ font-size: 14px; font-weight: 500; display: block; margin-bottom: 6px; }}

  select, textarea {{
    width: 100%;
    font-family: inherit;
    font-size: 14px;
    color: #000;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 10px 12px;
    outline: none;
    transition: border-color 200ms;
    resize: vertical;
  }}
  select:focus, textarea:focus {{ border-color: #000; }}

  .row {{ margin-bottom: 20px; }}

  .models-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
  }}
  .model-chip {{
    padding: 6px 14px;
    border-radius: 999px;
    border: 1px solid #e5e7eb;
    font-size: 13px;
    cursor: pointer;
    background: #fff;
    transition: all 200ms cubic-bezier(0.16,1,0.3,1);
    user-select: none;
  }}
  .model-chip:hover {{ border-color: #000; }}
  .model-chip.active {{ background: #000; color: #fff; border-color: #000; }}

  button {{
    width: 100%;
    padding: 12px;
    background: #000;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: transform 300ms cubic-bezier(0.16,1,0.3,1),
                opacity 200ms;
  }}
  button:hover {{ transform: scale(1.02); }}
  button:active {{ transform: scale(0.98); }}
  button:disabled {{ opacity: 0.4; cursor: not-allowed; transform: none; }}

  .result {{
    margin-top: 28px;
    display: none;
  }}
  .result-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }}
  .result-badge {{
    font-size: 12px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 999px;
    background: #f3f4f6;
    color: #6B7280;
  }}
  .result-text {{
    font-size: 15px;
    line-height: 1.7;
    white-space: pre-wrap;
    border-left: 2px solid #000;
    padding-left: 16px;
  }}

  .spinner {{
    display: none;
    width: 20px; height: 20px;
    border: 2px solid #e5e7eb;
    border-top-color: #000;
    border-radius: 50%;
    animation: spin 800ms linear infinite;
    margin: 0 auto;
  }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
</style>
</head>
<body>
<h1>Model Tester</h1>
<p class="sub">Hexallabs — Azure AI Foundry</p>

<div class="card">
  <div class="row">
    <label>Model</label>
    <div class="models-grid" id="chips"></div>
  </div>

  <div class="row">
    <label for="system">System prompt</label>
    <textarea id="system" rows="2">You are a helpful assistant.</textarea>
  </div>

  <div class="row">
    <label for="msg">Message</label>
    <textarea id="msg" rows="4" placeholder="Ask anything…"></textarea>
  </div>

  <button id="btn" onclick="send()">Send</button>
  <div class="spinner" id="spinner"></div>

  <div class="result" id="result">
    <div class="result-header">
      <span id="result-model" class="result-badge"></span>
      <span id="result-deployment" class="result-badge"></span>
    </div>
    <div class="result-text" id="result-text"></div>
  </div>
</div>

<script>
const MODELS = {models_json};
let selected = MODELS[0];

// Build chips
const grid = document.getElementById('chips');
MODELS.forEach(m => {{
  const chip = document.createElement('div');
  chip.className = 'model-chip' + (m === selected ? ' active' : '');
  chip.textContent = m;
  chip.onclick = () => {{
    selected = m;
    document.querySelectorAll('.model-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
  }};
  grid.appendChild(chip);
}});

async function send() {{
  const msg = document.getElementById('msg').value.trim();
  if (!msg) return;

  const btn = document.getElementById('btn');
  const spinner = document.getElementById('spinner');
  const result = document.getElementById('result');

  btn.disabled = true;
  spinner.style.display = 'block';
  result.style.display = 'none';

  try {{
    const res = await fetch('/test/chat', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        model: selected,
        message: msg,
        system_prompt: document.getElementById('system').value,
      }}),
    }});

    const data = await res.json();

    document.getElementById('result-model').textContent = data.model;
    document.getElementById('result-deployment').textContent = data.deployment;
    document.getElementById('result-text').textContent = data.response;
    result.style.display = 'block';
  }} catch (e) {{
    document.getElementById('result-text').textContent = 'Error: ' + e.message;
    result.style.display = 'block';
  }} finally {{
    btn.disabled = false;
    spinner.style.display = 'none';
  }}
}}

document.getElementById('msg').addEventListener('keydown', e => {{
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send();
}});
</script>
</body>
</html>""")
