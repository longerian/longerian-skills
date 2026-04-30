#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');

const SKILLS_DIR = path.join(os.homedir(), '.claude', 'skills');
const SOURCE_DIR = path.join(__dirname, '..', 'skills');

const skills = ['podcast-transcribe-whisper', 'podcast-transcribe-mimo'];

console.log('Installing longerian-skills...\n');

if (!fs.existsSync(SKILLS_DIR)) {
  fs.mkdirSync(SKILLS_DIR, { recursive: true });
}

for (const skill of skills) {
  const src = path.join(SOURCE_DIR, skill);
  const dest = path.join(SKILLS_DIR, skill);

  if (fs.existsSync(dest)) {
    fs.rmSync(dest, { recursive: true });
  }

  fs.cpSync(src, dest, { recursive: true });
  console.log(`  Installed: ${skill}`);
}

console.log('\nDone! Skills installed to ~/.claude/skills/');
console.log('\nUsage:');
console.log('  /podcast-transcribe-whisper <podcast-url>');
console.log('  /podcast-transcribe-mimo <podcast-url>  (requires MIMO_API_KEY env)');
