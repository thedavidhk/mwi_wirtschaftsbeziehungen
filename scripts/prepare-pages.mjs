/**
 * Assemble a self-contained static site for GitHub Pages (no node_modules).
 * Run after: npm run build
 */
import { cpSync, existsSync, mkdirSync, rmSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const site = join(root, 'site');

const required = [
	'index.html',
	'slides.md',
	'assets/css/custom.css',
	'vendor/reveal.js/dist/reveal.js',
];

for (const rel of required) {
	if (!existsSync(join(root, rel))) {
		console.error(`Missing ${rel}. Run: npm run build`);
		process.exit(1);
	}
}

rmSync(site, { recursive: true, force: true });
mkdirSync(site, { recursive: true });

for (const name of ['index.html', 'slides.md', 'images', 'assets', 'vendor']) {
	cpSync(join(root, name), join(site, name), { recursive: true });
}

console.log('site/ ready for GitHub Pages');
