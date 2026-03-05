<script lang="ts">
  import { fade, scale } from 'svelte/transition';

  let { isOpen, onClose, title, children } = $props();
</script>

{#if isOpen}
  <!-- Backdrop -->
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div 
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 dark:bg-black/80 backdrop-blur-sm dark:backdrop-blur-md p-4 transition-all duration-300"
    transition:fade={{ duration: 200 }}
    onclick={onClose}
    role="button"
    tabindex="0"
    onkeydown={(e) => e.key === 'Escape' && onClose()}
  >
    <!-- Modal Content -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div 
      class="w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-gray-200 dark:bg-zinc-900 dark:ring-zinc-800 transition-colors duration-300"
      transition:scale={{ duration: 200, start: 0.95 }}
      onclick={(e) => e.stopPropagation()}
      role="document"
    >
      <!-- Header -->
      <div class="border-b border-gray-100 bg-gray-50/50 dark:border-zinc-800 dark:bg-zinc-950 px-6 py-4 flex items-center justify-between transition-colors duration-300">
        <h3 class="text-lg font-semibold text-gray-900 dark:font-bold dark:tracking-tight dark:text-white flex items-center gap-2 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="hidden dark:block h-5 w-5 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"/><polyline points="14 2 14 8 20 8"/><path d="M2 15h10"/><path d="m9 18 3-3-3-3"/></svg>
            {title}
        </h3>
        <button 
          onclick={onClose}
          class="rounded-full p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-white transition-colors"
          aria-label="Close modal"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Body -->
      <div class="px-6 py-5 max-h-[70vh] overflow-y-auto text-gray-600 leading-relaxed dark:text-zinc-300 dark:font-serif dark:text-[15px] transition-colors duration-300">
        {@render children()}
      </div>
      
      <!-- Footer -->
      <div class="border-t border-gray-100 bg-gray-50 dark:border-zinc-800 dark:bg-zinc-950 px-6 py-3 flex justify-end transition-colors duration-300">
        <button 
          onclick={onClose}
          class="px-5 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:text-zinc-900 dark:bg-amber-500 dark:border-transparent dark:hover:bg-amber-400 dark:focus:ring-amber-500 dark:focus:ring-offset-zinc-900 transition-colors dark:shadow-lg dark:shadow-amber-500/20"
        >
          Close
        </button>
      </div>
    </div>
  </div>
{/if}
