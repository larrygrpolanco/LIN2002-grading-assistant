<script>
    import "../app.css";
</script>

<div class="min-h-screen bg-gray-50 text-gray-900 font-sans selection:bg-blue-100 selection:text-blue-900">
    <div class="max-w-5xl mx-auto px-4 py-8">
        <header class="mb-8 flex items-center justify-between">
            <div>
                 <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">Grading Assistant</h1>
                 <p class="text-gray-500 mt-1">Benevolent Mentor Persona</p>
            </div>
            <div class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded border border-blue-200">
                LIN2002
            </div>
        </header>

        <main>
            <slot />
        </main>

        <footer class="mt-12 text-center text-gray-400 text-sm">
            <p>&copy; {new Date().getFullYear()} Grading Assistant</p>
        </footer>
    </div>
</div>
