<script lang="ts">
  import { fade, scale } from 'svelte/transition';

  let { isOpen, onClose, title, children } = $props();
</script>

{#if isOpen}
  <!-- Backdrop -->
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div 
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
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
      class="w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-gray-200"
      transition:scale={{ duration: 200, start: 0.95 }}
      onclick={(e) => e.stopPropagation()}
      role="document"
    >
      <!-- Header -->
      <div class="border-b border-gray-100 bg-gray-50/50 px-6 py-4 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900">{title}</h3>
        <button 
          onclick={onClose}
          class="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
          aria-label="Close modal"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Body -->
      <div class="px-6 py-4 max-h-[70vh] overflow-y-auto text-gray-600 leading-relaxed">
        {@render children()}
      </div>
      
      <!-- Footer (Optional, mostly for close button if needed, but header logic is often enough) -->
      <div class="border-t border-gray-100 bg-gray-50 px-6 py-3 flex justify-end">
        <button 
          onclick={onClose}
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Close
        </button>
      </div>
    </div>
  </div>
{/if}
