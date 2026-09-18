import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import svelte from '@astrojs/svelte';
import tailwindcss from '@tailwindcss/vite';
// https://astro.build/config
export default defineConfig({
  // Canonical, og:url and twitter:image are absolute URLs built from `site`.
  // Without it, a static build emits http://localhost:4321 into every page's
  // metadata, so shared links and social previews point at the visitor's own
  // machine. Falls back to localhost only for local development.
  site: process.env.PUBLIC_SITE_URL || 'http://localhost:4321',

  integrations: [react(), svelte()],

  vite: {
    plugins: [tailwindcss()]
  }
});