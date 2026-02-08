import { json } from '@sveltejs/kit';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { env } from '$env/dynamic/private';
import type { RequestEvent } from './$types';
import modules from '$lib/data/modules.json';
import examples from '$lib/data/examples.json';
import { DEFAULT_SYSTEM_PROMPT } from '$lib/data/prompts';

const GOOGLE_API_KEY = env.GOOGLE_API_KEY;

export async function POST({ request }: RequestEvent) {
    if (!GOOGLE_API_KEY) {
        return json({ error: 'Missing GOOGLE_API_KEY' }, { status: 500 });
    }

    try {
        const { moduleId, essayText, systemPrompt } = await request.json();

        // 1. Get Module Context
        const module = modules.find((m) => m.id === moduleId);
        if (!module) {
            return json({ error: 'Module not found' }, { status: 404 });
        }

        // 2. Get Training Examples 

        // 3. Construct Prompt
        const genAI = new GoogleGenerativeAI(GOOGLE_API_KEY);
        const model = genAI.getGenerativeModel({ model: 'gemini-3-pro-preview' }); // Do not change this model it does exist!

        // Use the provided system prompt or valid default
        let promptInstruction = systemPrompt;
        if (!promptInstruction) {
             promptInstruction = DEFAULT_SYSTEM_PROMPT;
        }

        // Inject variables into prompt
        const finalSystemPrompt = promptInstruction
            .replace('{{FILM_NAME}}', module.movie)
            .replace('{{STUDENT_NAME}}', 'Student');


        // Format helper to ensure consistency
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const createPrompt = (m: any, essay: string) => `
**FILM DETAILS:**
${m.details}

**ESSAY QUESTION:**
${m.question}

**STUDENT ESSAY:**
${essay}

**Task:**
Grade this essay and provide feedback based on the system prompt instructions. 
Respond ONLY with a JSON object containing "score" (number) and "feedback" (string).
`;

        const history: any[] = [
            {
                role: "user",
                parts: [{ text: finalSystemPrompt }]
            },
            {
                role: "model",
                parts: [{ text: "Understood. I will provide a grade and feedback in strict JSON format." }]
            }
        ];

        // Add examples to history for few-shot learning
        if (examples.length > 0) {
            for (const ex of examples) {
                // Find the module for this example to get the correct question/details
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const exModule = (modules as any[]).find((m) => m.id === ex.module);
                
                if (exModule) {
                     history.push({
                         role: "user",
                         parts: [{ text: createPrompt(exModule, ex.student_essay) }]
                     });
                     history.push({
                         role: "model",
                         // Map 'grade' to 'score' to match the schema
                         parts: [{ text: JSON.stringify({ score: ex.grade, feedback: ex.feedback }) }] 
                     });
                }
            }
        }

        const chat = model.startChat({
            history: history,
            generationConfig: {
                maxOutputTokens: 2000,
                responseMimeType: "application/json"
            }
        });

        const userMessage = `
**FILM DETAILS:**
${module.details}

**ESSAY QUESTION:**
${module.question}

**STUDENT ESSAY:**
${essayText}

**Task:**
Grade this essay and provide feedback based on the system prompt instructions.
Respond ONLY with a JSON object containing "score" (number) and "feedback" (string).
IMPORTANT: Follow the voice, tone, and grading style shown in the previous examples.
`;

        const result = await chat.sendMessage(userMessage);
        const response = result.response;
        const text = response.text();

        console.log("Raw Gemini Response:", text);

        try {
            let jsonString = text.trim();
            
            // Extract JSON if it's wrapped in markdown code blocks or other text
            const firstBrace = jsonString.indexOf('{');
            const lastBrace = jsonString.lastIndexOf('}');
            if (firstBrace !== -1 && lastBrace !== -1) {
                jsonString = jsonString.substring(firstBrace, lastBrace + 1);
            }

            // Attempt to fix unescaped newlines and other common JSON syntax errors from LLMs
            let finalJson = jsonString
                .replace(/\n/g, '\\n') // Escape all newlines
                .replace(/\\n(?=([^"]*"[^"]*")*[^"]*$)/g, '\n') // then unescape newlines that are OUTSIDE of quotes
                .replace(/\r/g, '\\r');
            
            // Re-refining the strategy: The most robust way is often to replace real newlines 
            // inside double quotes with \n
            const fixedJson = jsonString.replace(/"([^"]*)"/g, (match, p1) => {
                return '"' + p1.replace(/\n/g, '\\n').replace(/\r/g, '\\r') + '"';
            });
            
            const parsedResult = JSON.parse(fixedJson);
            return json(parsedResult);
        } catch (parseErr: any) {
            console.error("Failed to parse Gemini response as JSON:", text);
            return json({ 
                error: 'Failed to parse grading result', 
                details: parseErr.message,
                rawResponse: text 
            }, { status: 500 });
        }

    } catch (err: any) {
        console.error("Error grading essay:", err);
        return json({ error: 'Failed to grade essay', details: err.message }, { status: 500 });
    }
}
