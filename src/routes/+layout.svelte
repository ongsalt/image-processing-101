<script lang="ts">
  let { children } = $props();
</script>

{@render children()}

<svelte:head>
  <title>webgpu - </title>
</svelte:head>

<style>
  :global(body) {
    margin: 0;
  }
  :global(html) {
    margin: 0;
  }
</style>
