export interface GradeRequest {
    moduleId: number;
    studentName: string;
    essayText: string;
    systemPrompt?: string; // Allow overriding system prompt
}

export interface GradeResponse {
    score: number;
    feedback: string;
    error?: string;
}
