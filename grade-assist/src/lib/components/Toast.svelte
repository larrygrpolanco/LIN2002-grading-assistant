<script lang="ts">
	import { fade, fly } from 'svelte/transition';

	let { message, duration = 3000, onClose } = $props();

	$effect(() => {
		const timer = setTimeout(() => {
			onClose();
		}, duration);
		return () => clearTimeout(timer);
	});
</script>

<div
	in:fly={{ y: 20, duration: 300 }}
	out:fade
	role="alert"
	class="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-lg bg-gray-900 px-4 py-3 text-white shadow-xl dark:border dark:border-zinc-700/50 dark:bg-zinc-900/95 dark:px-5 dark:py-4 dark:text-zinc-200 dark:shadow-2xl dark:backdrop-blur-md transition-all duration-300"
>
	<div class="flex h-6 w-6 items-center justify-center rounded-full bg-green-500/20 dark:bg-amber-500/20 transition-colors duration-300">
		<svg
			class="h-4 w-4 text-green-400 dark:text-amber-500 transition-colors duration-300"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
			stroke-width="2.5"
		>
			<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
		</svg>
	</div>
	<span class="text-sm font-medium dark:tracking-wide transition-all">{message}</span>
</div>
