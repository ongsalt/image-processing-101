<script lang="ts">
  let { children } = $props();
</script>

{@render children()}

<style>
  :global(body) {
    margin: 0;
  }
  :global(html) {
    margin: 0;
  }
</style>
