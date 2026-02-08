<script lang="ts">
	import modules from '$lib/data/modules.json';
	import { DEFAULT_SYSTEM_PROMPT } from '$lib/data/prompts';
	import type { GradeResponse } from '$lib/types';
	import { fade, slide } from 'svelte/transition';

	import Modal from '$lib/components/Modal.svelte';
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
		<div class="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
			<div class="flex flex-col gap-4">
				<div class="w-full">
					<label for="module" class="mb-2 block text-sm font-medium text-gray-700">Select Module</label>
					<select
						id="module"
						bind:value={selectedModuleId}
						class="w-full rounded-lg border border-gray-300 p-2 shadow-sm focus:border-blue-500 focus:ring-blue-500"
						onchange={() => {
							result = null;
						}}
					>
						{#each modules as module}
							<option value={module.id}>Module {module.id}: {module.movie}</option>
						{/each}
					</select>
				</div>
				
				<div class="flex gap-2">
					<button
						onclick={() => openModal('question')}
						class="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100 hover:text-blue-800 transition-colors"
					>
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						Essay Question
					</button>
					<button
						onclick={() => openModal('details')}
						class="flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100 hover:text-indigo-800 transition-colors"
					>
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
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
		<div class="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
			<label for="essay" class="mb-2 block text-sm font-medium text-gray-700">Student Essay</label>
			<textarea
				id="essay"
				bind:value={essayText}
				rows="15"
				placeholder="Paste the student's essay here..."
				class="w-full resize-y rounded-lg border border-gray-300 p-3 font-mono text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500"
			></textarea>

			<div class="mt-4 flex justify-end">
				<button
					onclick={handleGrade}
					disabled={isLoading || !essayText.trim()}
					class="flex items-center rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-2.5 font-medium text-white shadow-md transition-all hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
				>
					{#if isLoading}
						<svg class="mr-2 -ml-1 h-4 w-4 animate-spin text-white" fill="none" viewBox="0 0 24 24">
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							></circle>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							></path>
						</svg>
						Grading...
					{:else}
						✨ Grade Essay
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
				class="sticky top-6 rounded-xl border border-indigo-100 bg-white p-6 shadow-lg"
				transition:fade
			>
				<div class="mb-4 flex items-center justify-between">
					<h2 class="text-lg font-bold text-gray-900">Grading Result</h2>
					<span class="rounded-lg bg-green-100 px-3 py-1 text-xl font-bold text-green-800">
						{result.score}/100
					</span>
				</div>

				<div
					class="prose prose-sm max-w-none rounded-lg border border-gray-200 bg-gray-50 p-4 text-gray-700 whitespace-pre-wrap"
				>
					{result.feedback}
				</div>

				<div class="mt-6 flex gap-3">
					<button
						onclick={() => navigator.clipboard.writeText(result?.feedback || '')}
						class="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
					>
						Copy Feedback
					</button>
				</div>
			</div>
		{:else if !error && !isLoading}
			<div class="flex h-64 flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 bg-gray-50 p-6 text-center text-gray-400">
				<div class="mb-4 rounded-full bg-gray-100 p-4">
					<svg class="h-8 w-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
				</div>
				<p class="font-medium">Waiting for essay</p>
				<p class="mt-1 text-xs">Enter a student's essay and click grade to see results</p>
			</div>
		{/if}

		{#if isLoading}
			<div class="flex h-64 flex-col items-center justify-center rounded-xl border border-blue-100 bg-blue-50 p-6 text-center text-blue-600">
				<svg class="mb-4 h-8 w-8 animate-spin" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
				</svg>
				<p class="font-medium animate-pulse">Analyzing Essay...</p>
			</div>
		{/if}

		{#if error}
			<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700" transition:fade>
				<strong>Error:</strong>
				{error}
			</div>
		{/if}
	</div>
</div>
