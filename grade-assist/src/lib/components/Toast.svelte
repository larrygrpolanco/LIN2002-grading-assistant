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
	class="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-lg bg-gray-900 px-4 py-3 text-white shadow-xl"
>
	<div class="flex h-6 w-6 items-center justify-center rounded-full bg-green-500/20">
		<svg
			class="h-4 w-4 text-green-400"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
			stroke-width="2.5"
		>
			<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
		</svg>
	</div>
	<span class="text-sm font-medium">{message}</span>
</div>
