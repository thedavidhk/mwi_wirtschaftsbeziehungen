/**
 * Copy a minimal reveal.js subset from node_modules into assets/reveal/
 * (under assets/ so it ships with the rest of the static site).
 * for static serving (no node_modules in deployment).
 */
import { cpSync, mkdirSync, rmSync, existsSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const root = join( dirname( fileURLToPath( import.meta.url ) ), '..' );
const srcRoot = join( root, 'node_modules', 'reveal.js' );
const destRoot = join( root, 'assets', 'reveal' );

if( !existsSync( srcRoot ) ) {
	console.error( 'reveal.js not found. Run: npm install' );
	process.exit( 1 );
}

const copies = [
	[ 'dist/reset.css', 'dist/reset.css' ],
	[ 'dist/reveal.css', 'dist/reveal.css' ],
	[ 'dist/reveal.js', 'dist/reveal.js' ],
	[ 'dist/theme/night.css', 'dist/theme/night.css' ],
	[ 'dist/theme/fonts', 'dist/theme/fonts' ],
	[ 'plugin/notes/notes.js', 'plugin/notes/notes.js' ],
	[ 'plugin/markdown/markdown.js', 'plugin/markdown/markdown.js' ],
	[ 'plugin/highlight/highlight.js', 'plugin/highlight/highlight.js' ],
	[ 'plugin/highlight/monokai.css', 'plugin/highlight/monokai.css' ],
	[ 'plugin/math/math.js', 'plugin/math/math.js' ],
	[ 'plugin/math/katex.js', 'plugin/math/katex.js' ],
];

rmSync( destRoot, { recursive: true, force: true } );
mkdirSync( destRoot, { recursive: true } );

for( const [ from, to ] of copies ) {
	const src = join( srcRoot, from );
	const dest = join( destRoot, to );
	if( !existsSync( src ) ) {
		console.error( `Missing in reveal.js package: ${from}` );
		process.exit( 1 );
	}
	mkdirSync( dirname( dest ), { recursive: true } );
	cpSync( src, dest, { recursive: true } );
	console.log( `copied ${to}` );
}

console.log( 'assets/reveal ready' );
