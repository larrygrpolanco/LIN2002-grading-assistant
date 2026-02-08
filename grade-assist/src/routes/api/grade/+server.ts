import { json } from '@sveltejs/kit';
import { GoogleGenerativeAI, SchemaType } from '@google/generative-ai';
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

        // Calculate word count to help LLM accuracy
        const wordCount = essayText.trim().split(/\s+/).filter((w: string) => w.length > 0).length;

        // 1. Get Module Context
        const module = modules.find((m) => m.id === moduleId);
        if (!module) {
            return json({ error: 'Module not found' }, { status: 404 });
        }

        // 2. Get Training Examples 

        // 3. Construct Prompt
        const genAI = new GoogleGenerativeAI(GOOGLE_API_KEY);
        const model = genAI.getGenerativeModel({ model: 'gemini-3-pro-preview' }); // Never change this model, this is the most stable modern model!

        // Use the provided system prompt or valid default
        let promptInstruction = systemPrompt;
        if (!promptInstruction) {
             promptInstruction = DEFAULT_SYSTEM_PROMPT;
        }

        // Inject variables into prompt
        const finalSystemPrompt = promptInstruction
            .replace('{{FILM_NAME}}', module.movie)
            .replace('{{STUDENT_NAME}}', '[student]');


        // Format helper to ensure consistency
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const createPrompt = (m: any, essay: string, count: number) => `
**ESSAY QUESTION:**
${m.question}

**STUDENT ESSAY (OFFICIAL WORD COUNT: ${count} - DO NOT VERIFY):**
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
                     const exWordCount = ex.student_essay.trim().split(/\s+/).filter(w => w.length > 0).length;
                     history.push({
                         role: "user",
                         parts: [{ text: createPrompt(exModule, ex.student_essay, exWordCount) }]
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
                maxOutputTokens: 2000, // Increased to ensure full JSON response
                responseMimeType: "application/json",
                topP: 0.8, // use 0.5 to reduce chance of early STOP token causing truncation
                // Strict schema enforcement prevents truncation and malformed JSON
                responseSchema: {
                    type: SchemaType.OBJECT,
                    properties: {
                        score: { type: SchemaType.NUMBER },
                        feedback: { type: SchemaType.STRING }
                    },
                    required: ["score", "feedback"]
                }
            }
        });

        const userMessage = `
**FILM DETAILS:**
${module.details}

**ESSAY QUESTION:**
${module.question}

**STUDENT ESSAY (Word Count: ${wordCount}):**
${essayText}

**Rubric:**
1. Length (10 pts)
Excellent: Appropriate length (within 10% of the required length).
Needs improvement: Too short or long (by more than 20% of the required word count).
Insufficient: Too short or long (by more than 35% of the required word count).
Failing: Not submitted.

2. Time Stamp (20 pts)
Excellent: Film scene and time stamp included and convincing as evidence for point.
Needs improvement: Film scene and time stamp included but only marginally convincing as evidence for point.
Insufficient: Film scene included but no time stamp.
Failing: Not submitted or no film scene and time stamp included.

3. Quality of Expression (20 pts)
Excellent: Good grammar and accurate spelling; appropriate phrasing and style according to academic conventions.
Sufficient: Few grammar and spelling errors; slight mistakes in phrasing and style.
Needs improvement: Various grammar and spelling errors; noticeable problems with proper phrasing and style.
Failing: Not submitted or grammar and spelling errors overwhelm and inhibit comprehension.

4. Content (50 pts)
Excellent: Excellent points and relevant references; original ideas and excellent insight into topic; opinions corroborated with relevant evidence; no generalizations or unsubstantiated claims; obvious connection to topic/film/culture.
Good to sufficient: Good points and mostly relevant references; some original ideas and insight into topic; opinions mostly corroborated with relevant evidence; very few generalizations and/or unsubstantiated claims; noticeable connection to topic/film/culture.
Needs improvement: Few points and little to no relevant references; lacking original ideas; only superficial insight into topic; opinions corroborated with little to no relevant evidence (unconvincing ideas); some generalizations and/or unsubstantiated claims; certain degree of disconnect to topic/film/culture.
Failing: No relevant argumentation or original ideas; no serious effort of engaging with topic and/or producing insightful, original, or meaningful comments; no connection to topic/film/culture."

**Task:**
Grade this essay and provide feedback based on the system prompt instructions.
Respond ONLY with a JSON object containing "score" (number) and "feedback" (string).
IMPORTANT: Follow the voice, tone, and grading style shown in the previous examples.
`;

        // Helper function to clean and parse response
        const cleanAndParse = (responseText: string) => {
            let cleaned = responseText;
            // Remove markdown code blocks if present
            if (cleaned.startsWith('```json')) {
                cleaned = cleaned.replace(/^```json\s*/, '').replace(/\s*```$/, '');
            } else if (cleaned.startsWith('```')) {
                cleaned = cleaned.replace(/^```\s*/, '').replace(/\s*```$/, '');
            }
            return JSON.parse(cleaned);
        };

        let result = await chat.sendMessage(userMessage);
        let response = result.response;
        let text = response.text();

        console.log("Raw Gemini Response:", text);

        let parsedResult;
        let retryAttempted = false;

        try {
            // With responseSchema, the text should be valid JSON.
            // We just need a simple parse.
            parsedResult = cleanAndParse(text);
        } catch (parseErr: any) {
            console.warn("Initial parse failed, attempting retry...", parseErr.message);
            
            // Retry once with a completion request
            retryAttempted = true;
            const retryResult = await chat.sendMessage("The previous response was incomplete. Please provide the complete JSON response with both score and feedback fields.");
            const retryResponse = retryResult.response;
            text = retryResponse.text();
            
            console.log("Retry Gemini Response:", text);
            
            try {
                parsedResult = cleanAndParse(text);
            } catch (retryErr: any) {
                console.error("Retry also failed to parse Gemini response as JSON:", text);
                return json({ 
                    error: 'Failed to parse grading result', 
                    details: retryErr.message,
                    rawResponse: text,
                    retryAttempted: true
                }, { status: 500 });
            }
        }

        return json(parsedResult);

    } catch (err: any) {
        console.error("Error grading essay:", err);
        return json({ error: 'Failed to grade essay', details: err.message }, { status: 500 });
    }
}
