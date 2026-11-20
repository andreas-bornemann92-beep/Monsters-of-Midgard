#!/usr/bin/env node
/**
 * Monsters of Midgard – Heldenhaus V25 Treppenfix (aus V23-Quelldatei).
 *
 * Usage: node tools/apply-v25-stairs.mjs input-v23.html output-v25.html
 * The script fails without changing the input when the expected V23 code is missing.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { strict as assert } from 'node:assert';
import { Script } from 'node:vm';

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath || inputPath === outputPath) {
  console.error('Usage: node tools/apply-v25-stairs.mjs input-v23.html output-v25.html');
  process.exit(2);
}
const input = readFileSync(inputPath, 'utf8');
const opening = 'function drawGroundStairForeground(layer) {';
const closing = '\nfunction advanceStairs(dt) {';
const start = input.indexOf(opening);
const end = input.indexOf(closing, start);
assert(start >= 0 && end > start, 'V23 Treppengeländer-Funktion nicht auffindbar');
assert(input.indexOf(opening, start + 1) === -1, 'Mehrdeutige Treppengeländer-Funktion');
const previous = input.slice(start, end);
assert(previous.includes('[[923,944],[953,936]'), 'Erwartete V23-Geländermaske fehlt, kein Patch ausgeführt');
const replacement = `function drawGroundStairForeground(layer) {
 // V25: Nur vordere Holzbauteile über die Figur zeichnen.
 // Die frühere breite Pfostenmaske verdeckte den gesamten Charakter.
 if (floorIndex !== 1 || layer !== 'steps' ||
     !stairTransition?.onSteps || !ground.naturalWidth) return;
 const rails = [
   // Schmaler diagonaler Handlauf.
   [[941,965],[1190,756],[1209,751],[1209,764],[955,980],[944,980]],
   // Kappe des unteren Pfostens.
   [[926,945],[956,941],[964,950],[964,965],[925,971]],
   // Schmaler Pfostenkörper, nicht mehr die breite alte Fläche.
   [[933,971],[951,971],[954,1098],[936,1105]],
   // Oberer Pfosten: nur gezeichnete Holzfläche.
   [[1195,745],[1223,742],[1231,752],[1228,783],[1209,790],[1193,779]]
 ];
 ctx.save();
 ctx.beginPath();
 for(const points of rails) {
   ctx.moveTo(...points[0]);
   for(const point of points.slice(1)) ctx.lineTo(...point);
   ctx.closePath();
 }
 ctx.clip();
 ctx.drawImage(ground,0,0);
 ctx.restore();
}
`;
let result = input.slice(0, start) + replacement + input.slice(end);

/* The player walks on the foreground side of the staircase banister.
   Do not redraw banister pixels over an animated character while on steps.
   Normal collision still prevents entering the railing off the transition. */
const pathStart = "const stairFoot = [944,1091];";
const pathTreads = "const treads = [[976,1075],[1015,1043],[1050,1013],[1092,978],[1132,938]];";
assert(result.includes(pathStart) && result.includes(pathTreads),
 'V23 step coordinates differ, refusing geometry change');
// The diagonal footpath is lowered on the picture by 18-25 pixels.
result = result.replace(pathStart, "const stairFoot = [944,1110];")
  .replace(pathTreads, "const treads = [[976,1095],[1015,1066],[1050,1037],[1092,1001],[1132,961]];");
// Align the older floor definition's cached treads to the actual route.
const oldFloorTreads = 'treadTurns: [[944,1091],[976,1075],[1015,1043],[1050,1013],[1092,978],[1132,938]]';
assert(result.includes(oldFloorTreads), 'V23 floor treads changed');
result = result.replace(oldFloorTreads,
 'treadTurns: [[944,1110],[976,1095],[1015,1066],[1050,1037],[1092,1001],[1132,961]]');
// The rendered rail stays in the room background, but is never overlaid above the hero.
const foregroundCall='drawGroundStairForeground(groundStairLayer(y, onSteps));';
assert(result.includes(foregroundCall), 'V23 foreground draw call changed');
result = result.replace(foregroundCall,
 'if(!stairTransition?.onSteps) drawGroundStairForeground(groundStairLayer(y, onSteps));');

result = result.replace('Oberwelt-Demo V23', 'Oberwelt-Demo V25 – Treppengeländer');
assert(result !== input);
assert(result.includes('function advanceStairs(dt) {'));
assert(result.includes("const heroHouseFootprintsV21"));
assert(result.includes('stairTransition?.onSteps'));
assert(result.includes('[[976,1095],[1015,1066]'));
assert(result.includes('if(!stairTransition?.onSteps) drawGroundStairForeground'));
assert(!result.includes('const stairFoot = [944,1091]'));
assert(!result.includes('[[923,944],[953,936]'));
// Separate embedded scripts, without accidentally interpreting CSS/image data URLs.
for (const [i, match] of [...result.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].entries()) {
  new Script(match[1], {filename: 'embedded-' + i + '.js'});
}
writeFileSync(outputPath, result, 'utf8');
console.log('V25 Treppengeländer-Fix angewendet; Skript-Syntax geprüft. iPhone-Praxistest offen.');
