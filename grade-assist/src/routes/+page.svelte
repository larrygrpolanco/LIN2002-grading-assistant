<script lang="ts">
	import modules from '$lib/data/modules.json';
	import { DEFAULT_SYSTEM_PROMPT } from '$lib/data/prompts';
	import type { GradeResponse } from '$lib/types';
	import { fade, slide } from 'svelte/transition';

	import Modal from '$lib/components/Modal.svelte';
	import Toast from '$lib/components/Toast.svelte';
	import { onMount } from 'svelte';

	let selectedModuleId = $state(1); // Default to 1
	let essayText = $state('');
	let isLoading = $state(false);
	let result = $state<GradeResponse | null>(null);
	let error = $state<string | null>(null);

	// Modal State
	let isModalOpen = $state(false);
	let modalContent = $state('');
	let modalTitle = $state('');

	// Toast State
	let showToast = $state(false);

	// Derived values
	let selectedModule = $derived(modules.find((m) => m.id === selectedModuleId));

	onMount(() => {
		const storedModuleId = localStorage.getItem('selectedModuleId');
		if (storedModuleId) {
			const parsed = parseInt(storedModuleId);
			if (!isNaN(parsed) && modules.find((m) => m.id === parsed)) {
				selectedModuleId = parsed;
			}
		}
	});

	$effect(() => {
		if (selectedModuleId) {
			localStorage.setItem('selectedModuleId', selectedModuleId.toString());
		}
	});

	function openModal(type: 'question' | 'details') {
		if (!selectedModule) return;
		
		if (type === 'question') {
			modalTitle = 'Essay Question';
			modalContent = selectedModule.question;
		} else {
			modalTitle = 'Movie Details';
			modalContent = selectedModule.details;
		}
		isModalOpen = true;
	}

	async function handleGrade() {
		if (!essayText.trim()) return;

		isLoading = true;
		result = null;
		error = null;

		try {
			const response = await fetch('/api/grade', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					moduleId: selectedModuleId,
					essayText,
					systemPrompt: DEFAULT_SYSTEM_PROMPT
				})
			});

			const data = await response.json();

			if (response.ok) {
				result = data;
			} else {
				error = data.error || 'Something went wrong';
				console.error('API Error:', data);
			}
		} catch (e: any) {
			error = e.message;
			console.error('Network Error:', e);
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
	<!-- Left Column: Inputs & Context -->
	<div class="space-y-6 lg:col-span-2">
		<!-- Module Selection -->
		<div class="rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 dark:shadow-xl dark:backdrop-blur-sm transition-colors duration-300">
			<div class="flex flex-col gap-4">
				<div class="w-full">
					<label for="module" class="mb-2 block text-sm font-medium text-gray-700 dark:text-zinc-400 transition-colors">Select Module</label>
					<div class="relative">
						<select
							id="module"
							bind:value={selectedModuleId}
							class="w-full appearance-none rounded-lg border border-gray-300 bg-white p-3 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-200 dark:shadow-inner dark:focus:border-amber-500 dark:focus:ring-amber-500 transition-colors duration-300"
							onchange={() => {
								result = null;
							}}
						>
							{#each modules as module}
								<option value={module.id}>Module {module.id}: {module.movie}</option>
							{/each}
						</select>
						<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 dark:text-zinc-500 transition-colors">
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
							</svg>
						</div>
					</div>
				</div>
				
				<div class="flex gap-3">
					<button
						onclick={() => openModal('question')}
						class="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-zinc-700/50 dark:bg-zinc-800/50 dark:text-zinc-300 dark:hover:bg-zinc-700 dark:hover:text-white dark:focus:ring-amber-500 dark:focus:ring-offset-zinc-900"
					>
						<svg class="h-4 w-4 text-blue-600 dark:text-amber-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						Essay Question
					</button>
					<button
						onclick={() => openModal('details')}
						class="flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 transition-colors hover:bg-indigo-100 hover:text-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:border-zinc-700/50 dark:bg-zinc-800/50 dark:text-zinc-300 dark:hover:bg-zinc-700 dark:hover:text-white dark:focus:ring-amber-500 dark:focus:ring-offset-zinc-900"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-indigo-600 dark:text-amber-500 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18"/><path d="M3 7.5h4"/><path d="M3 12h18"/><path d="M3 16.5h4"/><path d="M17 3v18"/><path d="M17 7.5h4"/><path d="M17 16.5h4"/></svg>
						Movie Details
					</button>
				</div>
			</div>
		</div>

		<Modal 
			isOpen={isModalOpen} 
			onClose={() => isModalOpen = false} 
			title={modalTitle}
		>
			<div class="whitespace-pre-wrap">{modalContent}</div>
		</Modal>

		<!-- Essay Input -->
		<div class="rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 dark:shadow-xl dark:backdrop-blur-sm relative overflow-hidden flex flex-col h-[calc(100%-12rem)] min-h-[400px] transition-colors duration-300">
			<!-- Subtle corner film strip decor - only visible in dark mode-->
			<div class="hidden dark:block absolute -right-4 -top-4 opacity-[0.03] pointer-events-none transform rotate-12">
				<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18"/><path d="M3 7.5h4"/><path d="M3 12h18"/><path d="M3 16.5h4"/><path d="M17 3v18"/><path d="M17 7.5h4"/><path d="M17 16.5h4"/></svg>
			</div>
			
			<label for="essay" class="mb-2 block text-sm font-medium text-gray-700 dark:text-zinc-400 transition-colors">Student Essay</label>
			<textarea
				id="essay"
				bind:value={essayText}
				placeholder="Paste the student's essay here..."
				class="w-full flex-grow relative z-10 resize-none rounded-lg border border-gray-300 bg-white p-4 font-mono text-sm leading-relaxed text-gray-900 shadow-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-300 dark:shadow-inner dark:placeholder:text-zinc-600 dark:focus:border-amber-500 dark:focus:ring-amber-500 transition-colors duration-300"
			></textarea>

			<div class="mt-4 flex justify-end">
				<!-- Light mode button -->
				<button
					onclick={handleGrade}
					disabled={isLoading || !essayText.trim()}
					class="dark:hidden flex items-center rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-2.5 font-medium text-white shadow-md transition-all hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
				>
					{#if isLoading}
						<svg class="mr-2 -ml-1 h-4 w-4 animate-spin text-white" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Grading...
					{:else}
						✨ Grade Essay
					{/if}
				</button>

				<!-- Dark mode button (Cinematic) -->
				<button
					onclick={handleGrade}
					disabled={isLoading || !essayText.trim()}
					class="hidden dark:flex group relative items-center overflow-hidden rounded-lg bg-amber-500 px-6 py-2.5 font-semibold text-zinc-900 shadow-lg shadow-amber-500/20 transition-all hover:bg-amber-400 hover:shadow-amber-500/40 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 focus:ring-offset-zinc-900 disabled:cursor-not-allowed disabled:opacity-50"
				>
					<div class="absolute inset-0 flex h-full w-full justify-center [transform:skew(-12deg)_translateX(-100%)] group-hover:duration-1000 group-hover:[transform:skew(-12deg)_translateX(100%)]">
						<div class="relative h-full w-8 bg-white/30"></div>
					</div>
					{#if isLoading}
						<svg class="mr-2 -ml-1 h-4 w-4 animate-spin text-zinc-900" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Action! Grading...
					{:else}
						<svg xmlns="http://www.w3.org/2000/svg" class="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>
						Grade Essay
					{/if}
				</button>
			</div>
		</div>
	</div>

	<!-- Right Column: Results -->
	<div class="space-y-6">
		<!-- Grading Results -->
		{#if result}
			<div
				class="sticky top-6 rounded-xl border border-indigo-100 bg-white p-6 shadow-lg dark:border-amber-500/20 dark:bg-zinc-900/80 dark:shadow-2xl dark:backdrop-blur-md relative overflow-hidden transition-colors duration-300"
				transition:fade
			>
				<!-- subtle spotlight effect - dark mode only -->
				<div class="hidden dark:block absolute -top-24 -right-24 h-48 w-48 rounded-full bg-amber-500/10 blur-3xl"></div>

				<div class="mb-4 flex items-center justify-between relative z-10">
					<h2 class="text-lg font-bold text-gray-900 dark:text-white dark:tracking-tight flex items-center gap-2 transition-colors">
						<svg xmlns="http://www.w3.org/2000/svg" class="hidden dark:block h-5 w-5 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15l-3.09 1.636.59-3.455-2.51-2.455 3.47-.504L12 7l1.54 3.223 3.47.504-2.51 2.455.59 3.455z"/><path d="M22 12c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2s10 4.477 10 10z"/></svg>
						<span class="dark:hidden">Grading Result</span>
						<span class="hidden dark:inline">Director's Cut</span>
					</h2>
					<span class="rounded-lg bg-green-100 px-3 py-1 text-xl font-bold text-green-800 dark:border dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-2xl dark:font-black dark:text-amber-500 dark:shadow-inner transition-colors">
						{result.score}<span class="hidden dark:inline text-sm font-medium text-amber-500/60 transition-colors">/100</span><span class="dark:hidden">/100</span>
					</span>
				</div>

				<div
					class="prose prose-sm max-w-none rounded-lg border border-gray-200 bg-gray-50 p-4 text-gray-700 whitespace-pre-wrap dark:prose-invert dark:border-zinc-700/50 dark:bg-zinc-950/50 dark:p-5 dark:text-zinc-300 dark:leading-relaxed relative z-10 transition-colors duration-300"
				>
					{result.feedback}
				</div>

				<div class="mt-6 flex gap-3 relative z-10">
					<button
						onclick={async () => {
							if (result?.feedback) {
								await navigator.clipboard.writeText(result.feedback);
								showToast = true;
							}
						}}
						class="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-zinc-700 dark:bg-zinc-800 dark:py-2.5 dark:text-zinc-200 dark:hover:bg-zinc-700 dark:hover:text-white dark:focus:outline-none dark:focus:ring-2 dark:focus:ring-amber-500 dark:focus:ring-offset-2 dark:focus:ring-offset-zinc-900 flex justify-center items-center gap-2"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="hidden dark:block h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
						<span class="dark:hidden">Copy Feedback</span>
						<span class="hidden dark:inline">Copy Script</span>
					</button>
				</div>
			</div>
		{:else if !error && !isLoading}
			<div class="flex h-64 flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 bg-gray-50 p-6 text-center text-gray-400 dark:border-zinc-800 dark:bg-zinc-900/30 dark:text-zinc-500 dark:backdrop-blur-sm transition-colors duration-300">
				<div class="mb-4 rounded-full bg-gray-100 p-4 dark:bg-zinc-800/50 transition-colors">
					<!-- Light Icon -->
					<svg class="h-8 w-8 text-gray-300 dark:hidden" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
					<!-- Dark Icon -->
					<svg xmlns="http://www.w3.org/2000/svg" class="hidden dark:block h-8 w-8 text-zinc-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m22 8-6 4 6 4V8Z"/><rect width="14" height="12" x="2" y="6" rx="2" ry="2"/></svg>
				</div>
				<p class="font-medium dark:text-zinc-400 transition-colors">
					<span class="dark:hidden">Waiting for essay</span>
					<span class="hidden dark:inline">Awaiting the script</span>
				</p>
				<p class="mt-1 text-xs dark:text-sm dark:text-zinc-600 transition-colors">
					<span class="dark:hidden">Enter a student's essay and click grade to see results</span>
					<span class="hidden dark:inline">Enter an essay and hit action</span>
				</p>
			</div>
		{/if}

		{#if isLoading}
			<!-- Light Mode Loader -->
			<div class="flex dark:hidden h-64 flex-col items-center justify-center rounded-xl border border-blue-100 bg-blue-50 p-6 text-center text-blue-600 transition-colors">
				<svg class="mb-4 h-8 w-8 animate-spin" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
				</svg>
				<p class="font-medium animate-pulse">Analyzing Essay...</p>
			</div>
			
			<!-- Dark Mode Loader -->
			<div class="hidden dark:flex h-64 flex-col items-center justify-center rounded-xl border border-amber-500/20 bg-amber-500/5 p-6 text-center text-amber-500 backdrop-blur-sm transition-colors">
				<div class="relative mb-4 flex h-12 w-12 items-center justify-center">
					<svg xmlns="http://www.w3.org/2000/svg" class="absolute h-full w-full animate-spin opacity-20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="2"/><line x1="12" y1="2" x2="12" y2="10"/><line x1="12" y1="14" x2="12" y2="22"/><line x1="2" y1="12" x2="10" y2="12"/><line x1="14" y1="12" x2="22" y2="12"/><line x1="4.93" y1="4.93" x2="10.59" y2="10.59"/><line x1="13.41" y1="13.41" x2="19.07" y2="19.07"/><line x1="4.93" y1="19.07" x2="10.59" y2="13.41"/><line x1="13.41" y1="10.59" x2="19.07" y2="4.93"/></svg>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 animate-pulse text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
				</div>
				<p class="font-medium animate-pulse tracking-wide">Reviewing dailies...</p>
			</div>
		{/if}

		{#if error}
			<!-- Light Mode Error -->
			<div class="dark:hidden rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 transition-colors" transition:fade>
				<strong>Error:</strong>
				{error}
			</div>
			
			<!-- Dark Mode Error -->
			<div class="hidden dark:block rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-400 backdrop-blur-sm transition-colors" transition:fade>
				<div class="flex items-center gap-2 mb-1">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
					<strong class="font-semibold text-red-300">Technical Difficulties</strong>
				</div>
				<p class="text-sm pl-7">{error}</p>
			</div>
		{/if}
	</div>
</div>

{#if showToast}
	<Toast 
		message="Feedback copied to clipboard!" 
		onClose={() => showToast = false} 
	/>
{/if}
