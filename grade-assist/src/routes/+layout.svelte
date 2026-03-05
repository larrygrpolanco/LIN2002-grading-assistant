<script lang="ts">
    import "../app.css";
	import { onMount } from 'svelte';

	let isDarkMode = $state(false);

	onMount(() => {
		// Initialize the state based on the current document class
		isDarkMode = document.documentElement.classList.contains('dark');
	});

	function toggleTheme() {
		isDarkMode = !isDarkMode;
		if (isDarkMode) {
			document.documentElement.classList.add('dark');
			localStorage.theme = 'dark';
		} else {
			document.documentElement.classList.remove('dark');
			localStorage.theme = 'light';
		}
	}
</script>

<div class="min-h-screen bg-gray-50 text-gray-900 font-sans selection:bg-blue-100 selection:text-blue-900 dark:bg-zinc-950 dark:text-zinc-300 dark:selection:bg-amber-500/30 dark:selection:text-amber-200 transition-colors duration-300">
    <div class="max-w-5xl mx-auto px-4 py-8">
        <header class="mb-8 flex items-center justify-between">
            <div class="flex items-center gap-3">
                 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-8 w-8 text-blue-600 dark:text-amber-500"><path d="M20.2 6 3 11l-.9-2.4c-.3-1.1.3-2.2 1.3-2.5l13.5-4c1.1-.3 2.2.3 2.5 1.3Z"/><path d="m6.2 5.3 3.1 3.9"/><path d="m12.4 3.4 3.1 4"/><path d="M3 11h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/></svg>
                 <div>
                     <h1 class="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-amber-200 dark:to-amber-500">Grading Assistant</h1>
                     <p class="text-gray-500 dark:text-zinc-500 mt-1 uppercase tracking-wider text-xs font-semibold">Linguistics & Film</p>
                 </div>
            </div>
            
			<div class="flex gap-4">
				<div class="bg-blue-100 text-blue-800 border-blue-200 dark:bg-amber-500/10 dark:text-amber-500 text-xs font-bold tracking-wider px-3 py-1 rounded border dark:border-amber-500/20 mr-4 self-center">
					LIN2002
				</div>
				<button 
					onclick={toggleTheme} 
					class="p-2 rounded-full bg-gray-200 text-gray-600 hover:bg-gray-300 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700 transition"
					aria-label="Toggle theme"
				>
					{#if isDarkMode}
						<!-- Moon icon -->
						<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
					{:else}
						<!-- Sun icon -->
					    <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
					{/if}
				</button>
			</div>
			
        </header>

        <main>
            <slot />
        </main>

        <footer class="mt-12 text-center text-gray-400 dark:text-zinc-600 text-sm">
            <p>&copy; {new Date().getFullYear()} Grading Assistant</p>
        </footer>
    </div>
</div>
