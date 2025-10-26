import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import OpenAI from 'openai';
import fs from 'fs';

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('../frontend'));

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const MODEL = 'gpt-4.1';

const SYSTEM_INSTRUCTIONS = `
	You are "Codex UI Module Generator".
	Return ONLY valid JSON (no prose) that matches:

	{
	"title": "human-friendly title",
	"summary": "one-line summary",
	"html": "<div>...self-contained module markup...</div>"
	}

	Rules:
	- The "html" must be self-contained, no external CSS/JS, no network fetches.
	- You MAY include a <style> tag scoped to the module root and harmless <script> for simple interactivity.
	- Prefer semantic HTML; keep styles minimal; use metric units.
	- Never include <script src>, <link rel>, or inline event handlers that reach the network.
	- If the user requests a chart/plot, render a simple SVG or <canvas>-based static chart without remote assets.
  - Keep modules minimal and small in size.
`;

// Load mock finance facts for context.
const FINANCE_FACTS = fs.readFileSync('./mock_finance_facts.txt', 'utf8');
var memory = "";

app.post('/api/generate-module', async (req, res) => {
  try {
    const { prompt, _ = [] } = req.body;

    const userTask = `
        User prompt: ${prompt}

        CONTEXT FACTS (can invent details as needed):
        [BEGIN_FACTS]
        ${FINANCE_FACTS}
        [END_FACTS]

        MODULES CREATED PREVIOUSLY:
        [BEGIN_PREVIOUS_MODULES]
        ${memory}
        [END_PREVIOUS_MODULES]

        Produce one new module that complements (not repeats) what's already there.
        Return JSON ONLY.
     `;

    const response = await client.responses.create({
      model: MODEL,
      instructions: SYSTEM_INSTRUCTIONS,
      input: userTask
    });

    // DEV: very basic memory of prior modules.
    // This is sample prototype since the dashboard builder remains disconnected from the knowledge network.
    memory += `\n---\n${response.output_text}`;

    const text = response.output_text;
    const payload = JSON.parse(text);

    // Minimal validation
    if (!payload || !payload.title || !payload.html) {
      return res.status(422).json({ error: "Model returned unexpected shape", raw: payload });
    }

    res.json({
      title: payload.title,
      summary: payload.summary || "",
      html: payload.html
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: String(err) });
  }
});

const port = Number(process.env.PORT || 5173);
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
