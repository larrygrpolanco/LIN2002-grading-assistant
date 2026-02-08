
const rawResponsePartial = `{
  "score": 94,
  "feedback": "Hi {{STUDENT_NAME}},\\n\\nYou presented a sophisticated conclusion: that life cannot be \\"optimized through control,\\" whether that be strict sobriety or calculated intoxication. This captures the film's existential nuance perfectly.\\n\\nHowever, please proofread your work more carefully before submitting. You had a few phrasing errors, such as`;

const rawResponseFuller = `{
  "score": 94,
  "feedback": "Hi {{STUDENT_NAME}},\\n\\nYou presented a sophisticated conclusion: that life cannot be \\"optimized through control,\\" whether that be strict sobriety or calculated intoxication. This captures the film's existential nuance perfectly.\\n\\nHowever,"
}`;

function extractJson(text) {
    let jsonString = text.trim();
    console.log("Input length:", jsonString.length);

    // improved JSON extraction: find the *first* complete JSON object
    const firstBrace = jsonString.indexOf('{');
    if (firstBrace !== -1) {
        let braceCount = 0;
        let inString = false;
        let escape = false;
        let endIndex = -1;

        for (let i = firstBrace; i < jsonString.length; i++) {
            const char = jsonString[i];
            
            if (escape) {
                escape = false;
                continue;
            }
            
            if (char === '\\\\') {
                escape = true;
                continue;
            }

            if (char === '"') {
                inString = !inString;
                continue;
            }

            if (!inString) {
                if (char === '{') {
                    braceCount++;
                } else if (char === '}') {
                    braceCount--;
                    if (braceCount === 0) {
                        endIndex = i;
                        break;
                    }
                }
            }
        }

        if (endIndex !== -1) {
            console.log("Found complete JSON ends at:", endIndex);
            jsonString = jsonString.substring(firstBrace, endIndex + 1);
        } else {
             console.log("Did not find complete JSON structure.");
             // Fallback: if structure seems broken, try simple last brace heuristic
             const lastBrace = jsonString.lastIndexOf('}');
             if (lastBrace !== -1) {
                console.log("Fallback to last brace at:", lastBrace);
                jsonString = jsonString.substring(firstBrace, lastBrace + 1);
             } else {
                 console.log("No last brace found.");
             }
        }
    }
    
    return jsonString;
}

console.log("--- TEST PARTIAL ---");
const partial = extractJson(rawResponsePartial);
console.log("Extracted Parsial:", partial);
try {
    JSON.parse(partial);
    console.log("Success parse partial");
} catch (e) {
    console.log("Failed parse partial:", e.message);
}

console.log("\\n--- TEST FULL ---");
const full = extractJson(rawResponseFuller);
console.log("Extracted Full:", full);
try {
    JSON.parse(full);
    console.log("Success parse full");
} catch (e) {
    console.log("Failed parse full:", e.message);
}
