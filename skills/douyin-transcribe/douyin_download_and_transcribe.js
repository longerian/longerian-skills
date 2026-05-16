#!/usr/bin/env node
/**
 * Douyin Video Downloader and Transcriber
 * Usage: node douyin_download_and_transcribe.js <douyin_url>
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const DOUYIN_URL = process.argv[2];
if (!DOUYIN_URL) {
    console.log('Usage: node douyin_download_and_transcribe.js <douyin_url>');
    process.exit(1);
}

// Configuration
const OUTPUT_DIR = path.join(
    process.env.HOME || process.env.USERPROFILE,
    '.longerian/data/douyin'
);
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

const PYTHON_BIN = '/c/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe';

async function main() {
    console.log('=' .repeat(50));
    console.log('Douyin Video Transcription');
    console.log('=' .repeat(50));
    console.log(`URL: ${DOUYIN_URL}`);
    console.log(`Output: ${OUTPUT_DIR}`);
    console.log('');

    // Step 1: Get video URL
    console.log('[Step 1/3] Fetching video URL from Douyin...');
    const videoUrl = await getDouyinVideoUrl(DOUIN_URL);

    if (!videoUrl) {
        console.error('Failed to get video URL');
        process.exit(1);
    }

    console.log(`Found video URL: ${videoUrl.substring(0, 60)}...`);

    // Step 2: Download video
    console.log('\n[Step 2/3] Downloading video...');
    const videoPath = await downloadVideo(videoUrl, OUTPUT_DIR);
    console.log(`Downloaded to: ${videoPath}`);

    // Step 3: Transcribe
    console.log('\n[Step 3/3] Transcribing with Whisper (GPU)...');
    const transcriptPath = await transcribeVideo(videoPath, OUTPUT_DIR);

    console.log('\n' + '='.repeat(50));
    console.log('Done!');
    console.log(`Transcript: ${transcriptPath}`);
    console.log('='.repeat(50));
}

async function getDouyinVideoUrl(url) {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    });
    const page = await context.newPage();

    let mediaUrl = null;

    page.on('response', async (response) => {
        const requestUrl = response.url();
        if (requestUrl.includes('douyinvod.com') &&
            (requestUrl.includes('media-video') || requestUrl.includes('media-audio'))) {
            if (!mediaUrl) {
                mediaUrl = requestUrl;
                console.log(`  Captured: ${requestUrl.substring(0, 60)}...`);
            }
        }
    });

    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.waitForTimeout(15000); // Wait for video to load
    } catch (e) {
        console.error(`  Error navigating: ${e.message}`);
    }

    await browser.close();
    return mediaUrl;
}

async function downloadVideo(url, outputDir) {
    const timestamp = Date.now();
    const filename = `douyin_${timestamp}.mp4`;
    const filepath = path.join(outputDir, filename);

    // Use curl to download
    const curlCmd = `curl -L -o "${filepath}" "${url}"`;
    try {
        execSync(curlCmd, { stdio: 'inherit' });
    } catch (e) {
        throw new Error(`Download failed: ${e.message}`);
    }

    // Verify file exists
    if (!fs.existsSync(filepath)) {
        throw new Error(`File not created: ${filepath}`);
    }

    const stats = fs.statSync(filepath);
    console.log(`  Size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);

    return filepath;
}

async function transcribeVideo(videoPath, outputDir) {
    const timestamp = Date.now();
    const outputName = `douyin_${timestamp}`;

    const pythonScript = `
import os, sys, time, whisper
sys.stdout.reconfigure(encoding='utf-8')

video_path = "${videoPath.replace(/\\/g, '\\\\')}"
output_dir = "${outputDir.replace(/\\/g, '\\\\')}"
output_name = "${outputName}"

model = whisper.load_model('large-v3-turbo')
result = model.transcribe(video_path, language='zh', verbose=False)

# Save transcript
transcript_path = os.path.join(output_dir, f'{output_name}-transcript.txt')
with open(transcript_path, 'w', encoding='utf-8') as f:
    f.write(result['text'])

# Save segments
segments_path = os.path.join(output_dir, f'{output_name}-segments.txt')
with open(segments_path, 'w', encoding='utf-8') as f:
    for seg in result['segments']:
        f.write(f"[{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}\\n")

print(f'Saved: {transcript_path}')
print(f'Saved: {segments_path}')
`;

    const scriptPath = path.join(OUTPUT_DIR, 'temp_transcribe.py');
    fs.writeFileSync(scriptPath, pythonScript);

    try {
        const output = execSync(`"${PYTHON_BIN}" "${scriptPath}"`, {
            encoding: 'utf-8',
            stdio: 'inherit'
        });
        return path.join(OUTPUT_DIR, `${outputName}-transcript.txt`);
    } finally {
        fs.unlinkSync(scriptPath);
    }
}

main().catch(console.error);
