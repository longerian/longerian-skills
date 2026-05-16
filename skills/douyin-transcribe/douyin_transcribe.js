#!/usr/bin/env node
/**
 * Douyin Video Transcription with Markdown Report
 * Usage: node douyin_transcribe.js
 *   - Interactive: paste URLs when prompted
 *   - Batch: node douyin_transcribe.js --batch url1,url2,url3
 *   - Single: node douyin_transcribe.js "https://www.douyin.com/..."
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const readline = require('readline');

// Configuration
const OUTPUT_DIR = path.join(
    process.env.HOME || process.env.USERPROFILE,
    '.longerian/data/douyin'
);
const PYTHON_BIN = '/c/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe';

// Colors for terminal output
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    blue: '\x1b[34m',
    yellow: '\x1b[33m',
    gray: '\x1b[90m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

async function promptUrl() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    return new Promise((resolve) => {
        rl.question('\n请输入抖音视频链接 (多个链接用空格分隔): ', (url) => {
            rl.close();
            // Split by spaces and filter empty strings
            const urls = url.trim().split(/\\s+/).filter(u => u.length > 0);
            resolve(urls);
        });
    });
}

async function getDouyinVideoUrl(url) {
    log('\n[步骤 1/5] 正在获取视频 URL...', 'blue');

    const browser = await chromium.launch({
        headless: false,
        timeout: 60000
    });
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });
    const page = await context.newPage();

    let mediaUrl = null;
    let videoInfo = {};

    // Capture video info from page
    page.on('response', async (response) => {
        const requestUrl = response.url();
        if (requestUrl.includes('douyinvod.com') &&
            (requestUrl.includes('media-video') || requestUrl.includes('media-audio'))) {
            if (!mediaUrl) {
                mediaUrl = requestUrl;
                log(`  ✓ 捕获到视频 URL`, 'green');
            }
        }
    });

    try {
        log(`  正在访问: ${url.substring(0, 50)}...`, 'gray');
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

        // Extract video info from page
        try {
            videoInfo = await page.evaluate(() => {
                const title = document.querySelector('h1, [class*="title"], [class*="desc"]')?.textContent?.trim() || '';
                const author = document.querySelector('[class*="author"], [class*="user"]')?.textContent?.trim() || '';
                return { title, author };
            });
        } catch (e) {
            // If extraction fails, use defaults
        }

        await page.waitForTimeout(15000); // Wait for video to load
    } catch (e) {
        log(`  ⚠ 访问页面出错: ${e.message}`, 'yellow');
    }

    await browser.close();

    return { mediaUrl, videoInfo };
}

async function downloadVideo(url, outputDir) {
    log('\n[步骤 2/5] 正在下载视频...', 'blue');

    const timestamp = Date.now();
    const filename = `douyin_${timestamp}.mp4`;
    const filepath = path.join(outputDir, filename);

    const curlCmd = `curl -L -o "${filepath}" "${url}"`;

    try {
        execSync(curlCmd, { stdio: 'pipe', encoding: 'utf-8' });

        const stats = fs.statSync(filepath);
        const sizeMB = (stats.size / 1024 / 1024).toFixed(2);
        log(`  ✓ 下载完成: ${sizeMB} MB`, 'green');

        return { filepath, sizeMB };
    } catch (e) {
        throw new Error(`下载失败: ${e.message}`);
    }
}

async function transcribeVideo(videoPath, outputDir, videoInfo) {
    log('\n[步骤 3/5] 正在使用 Whisper 转录 (GPU 加速)...', 'blue');

    const timestamp = Date.now();
    const outputName = `douyin_${timestamp}`;

    // Python transcription script with Markdown generation
    const pythonScript = `
import os, sys, time, whisper, re
from datetime import datetime
from collections import Counter

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

video_path = r"${videoPath.replace(/\\/g, '\\\\')}"
output_dir = r"${outputDir.replace(/\\/g, '\\\\')}"
output_name = "${outputName}"

# Video info
video_title = r"${videoInfo.title || '抖音视频'}"
video_author = r"${videoInfo.author || '未知作者'}"

print("Loading model...")
model = whisper.load_model('large-v3-turbo')

print("Transcribing...")
start = time.time()
result = model.transcribe(video_path, language='zh', verbose=False)
transcribe_time = time.time() - start

duration = result['segments'][-1]['end']

# Save plain text
transcript_path = os.path.join(output_dir, f'{output_name}-transcript.txt')
with open(transcript_path, 'w', encoding='utf-8') as f:
    f.write(result['text'])

# Save segments with timestamps
segments_path = os.path.join(output_dir, f'{output_name}-segments.txt')
with open(segments_path, 'w', encoding='utf-8') as f:
    for seg in result['segments']:
        f.write(f"[{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}\\n")

# ========== 增强标点规则 ==========
def enhance_punctuation(text):
    """应用增强的标点符号规则"""

    # 连词和转折词后加逗号
    conjunctions = ['那么', '但是', '所以', '因为', '还有', '另外', '而且', '不过',
                   '此外', '同时', '首先', '其次', '最后', '总之', '然后', '接着']
    for word in conjunctions:
        text = re.sub(f'({word})([，。！？、]?)', r'\\1，', text)

    # 序数词后加冒号
    ordinal_patterns = [
        r'(第一是?|第二是?|第三是?|第四是?|第五是?)',
        r'(首先|其次|再[次其]|最后)',
        r'(一|二|三|四|五)(个?是?方面?)?'
    ]
    for pattern in ordinal_patterns:
        text = re.sub(f'({pattern})([，。！？、]?)', r'\\1：', text)

    # 疑问句结尾
    text = re.sub(r'(吗呢吧)([，。]?)', r'\\1？', text)
    text = re.sub(r'(怎么|什么|为什么|哪|谁)([，。]?)', r'\\1？', text)

    # 感叹句
    text = re.sub(r'(真的|确实|实在|太)([，。]?)', r'\\1！', text)

    # 名字和称呼优化
    name_replacements = {
        '老黄': '老黄（黄仁勋）',
        '老川': '老川（川普）',
        '库克': '库克（苹果CEO）',
        '老马': '老马（马斯克）',
        '雷总': '雷总（雷军）',
    }
    for old, new in name_replacements.items():
        text = text.replace(old, new)

    # 数字和时间表达
    text = re.sub(r'(\\d+)(个)([天月周年])', r'\\1\\2\\3', text)
    text = re.sub(r'(\\d+)(点|分|秒)', r'\\1\\2', text)

    # 段落分隔（根据话题标记）
    topic_markers = ['那么', '所以', '但是', '另外', '还有', '此外']
    for marker in topic_markers[:3]:  # 只对前三个进行换行处理
        text = text.replace(marker，'\\n\\n' + marker)

    return text

# ========== 关键词提取 ==========
def extract_keywords(text, top_n=15):
    """提取关键词和关键短语"""

    # 常用停用词
    stopwords = set(['的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
                    '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
                    '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '能',
                    '这个', '那个', '什么', '怎么', '如果', '可以', '但是', '因为',
                    '所以', '然后', '还是', '或者', '而且', '不过', '的话', '吗'])

    # 分词（简单按字符和常见词边界）
    words = []

    # 提取2-4字的词
    for i in range(len(text)):
        for length in [4, 3, 2]:
            if i + length <= len(text):
                word = text[i:i+length]
                # 检查是否是有效词（包含中文且不在停用词中）
                if re.match(r'^[\\u4e00-\\u9fa5]+$', word) and word not in stopwords:
                    words.append(word)

    # 统计词频
    word_freq = Counter(words)

    # 过滤掉只出现一次的词
    filtered = {k: v for k, v in word_freq.items() if v > 1}

    # 获取高频词
    top_words = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return [w[0] for w in top_words]

def extract_key_phrases(text):
    """提取关键短语（4-8字的行业术语和表达）"""
    phrases = []

    # 常见模式
    patterns = [
        r'[A-Z]{2,}',  # 英文缩写 (GPU, CPU, CPO等)
        r'[\\u4e00-\\u9fa5]{2,4}(模块|技术|产品|公司|概念|板块|指数|股票)',  # 行业术语
        r'[\\u4e00-\\u9fa5]{2,4}(增长|下跌|上涨|回调|突破|调整)',  # 趋势描述
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        phrases.extend(matches)

    # 去重并返回
    return list(set(phrases))[:10]

# ========== 生成 Markdown 报告 ==========
md_path = os.path.join(output_dir, f'{output_name}-报告.md')
with open(md_path, 'w', encoding='utf-8') as f:
    # Header
    f.write(f"# {video_title}\\n\\n")
    f.write(f"**作者**: {video_author}\\n")
    f.write(f"**转录时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\\n")
    f.write(f"**视频时长**: {duration:.1f}秒 ({duration/60:.1f}分钟)\\n")
    f.write(f"**转录耗时**: {transcribe_time:.1f}秒\\n")
    f.write(f"**处理速度**: {duration/transcribe_time:.1f}x 实时\\n\\n")

    f.write("---\\n\\n")

    # 关键词提取
    f.write("## 📌 关键词\\n\\n")
    keywords = extract_keywords(result['text'])
    key_phrases = extract_key_phrases(result['text'])

    if keywords:
        f.write("**高频词**: " + "、".join(keywords[:10]) + "\\n\\n")
    if key_phrases:
        f.write("**关键短语**: " + "、".join(key_phrases[:10]) + "\\n\\n")

    f.write("---\\n\\n")

    # Full transcript with enhanced punctuation
    f.write("## 完整转录\\n\\n")
    text = enhance_punctuation(result['text'])
    f.write(text + "\\n\\n")

    # Segments with timestamps
    f.write("---\\n\\n## 分段转录 (带时间戳)\\n\\n")
    for i, seg in enumerate(result['segments'], 1):
        timestamp = f"{int(seg['start']//60)}:{int(seg['start']%60):02d}"
        f.write(f"### [{timestamp}] {seg['text']}\\n\\n")

print(f"\\n转录完成:")
print(f"  文本: {transcript_path}")
print(f"  分段: {segments_path}")
print(f"  报告: {md_path}")
print(f"\\n视频时长: {duration:.1f}秒")
print(f"转录耗时: {transcribe_time:.1f}秒")
print(f"处理速度: {duration/transcribe_time:.1f}x")
`;

    const scriptPath = path.join(OUTPUT_DIR, 'temp_transcribe.py');
    fs.writeFileSync(scriptPath, pythonScript);

    try {
        const output = execSync(`"${PYTHON_BIN}" "${scriptPath}"`, {
            encoding: 'utf-8',
            stdio: 'pipe',
            timeout: 300000
        });

        log(`  ✓ 转录完成`, 'green');
        console.log(output);

        return {
            transcriptPath: path.join(OUTPUT_DIR, `${outputName}-transcript.txt`),
            segmentsPath: path.join(OUTPUT_DIR, `${outputName}-segments.txt`),
            mdPath: path.join(OUTPUT_DIR, `${outputName}-报告.md`)
        };
    } catch (e) {
        log(`  ✗ 转录失败: ${e.message}`, 'yellow');
        throw e;
    } finally {
        try {
            fs.unlinkSync(scriptPath);
        } catch (e) {}
    }
}

async function copyToClipboard(text) {
    try {
        // Windows clipboard
        execSync(`echo "${text.replace(/"/g, '\\"')}" | clip`, { stdio: 'ignore' });
        return true;
    } catch (e) {
        return false;
    }
}

async function processVideo(url, index, total) {
    if (total > 1) {
        log(`\n${'='.repeat(50)}`, 'blue');
        log(`  处理视频 ${index}/${total}`, 'blue');
        log('='.repeat(50), 'blue');
    }

    // Step 1: Get video URL
    const { mediaUrl, videoInfo } = await getDouyinVideoUrl(url);

    if (!mediaUrl) {
        log('✗ 无法获取视频 URL', 'yellow');
        log('提示: 请确保网络连接正常，或稍后重试', 'gray');
        return null;
    }

    // Step 2: Download video
    const { filepath, sizeMB } = await downloadVideo(mediaUrl, OUTPUT_DIR);

    // Step 3: Transcribe
    const { mdPath } = await transcribeVideo(filepath, OUTPUT_DIR, videoInfo);

    return { mdPath, videoInfo, filepath };
}

async function main() {
    console.clear();
    log('='.repeat(50), 'blue');
    log('  抖音视频转录工具 (Whisper GPU 加速)', 'blue');
    log('  支持: 单个链接 / 批量处理', 'blue');
    log('='.repeat(50), 'blue');

    fs.mkdirSync(OUTPUT_DIR, { recursive: true });

    // Parse command line arguments
    const args = process.argv.slice(2);
    let urls = [];

    if (args.length > 0) {
        // Command line mode
        if (args[0] === '--batch' && args[1]) {
            // Batch mode: node douyin_transcribe.js --batch url1,url2,url3
            urls = args[1].split(',').map(u => u.trim()).filter(u => u.length > 0);
        } else if (args[0].includes('douyin.com')) {
            // Single URL mode: node douyin_transcribe.js "url"
            urls = [args[0]];
        } else {
            log('⚠ 无效的参数格式', 'yellow');
            log('  单个链接: node douyin_transcribe.js "https://..."', 'gray');
            log('  批量处理: node douyin_transcribe.js --batch url1,url2,url3', 'gray');
            process.exit(1);
        }
    } else {
        // Interactive mode
        urls = await promptUrl();
    }

    if (urls.length === 0) {
        log('未输入链接，退出', 'yellow');
        process.exit(0);
    }

    // Validate URLs
    for (const url of urls) {
        if (!url.includes('douyin.com')) {
            log('⚠ 请输入有效的抖音链接', 'yellow');
            process.exit(1);
        }
    }

    const total = urls.length;
    const results = [];

    try {
        for (let i = 0; i < total; i++) {
            const result = await processVideo(urls[i], i + 1, total);
            if (result) {
                results.push(result);
            }
        }

        // Summary
        log('\n' + '='.repeat(50), 'green');
        log(`✓ 批量处理完成! (${results.length}/${total})`, 'green');
        log('='.repeat(50), 'green');
        log('\n输出文件:', 'blue');
        for (const r of results) {
            log(`  📄 ${r.videoInfo.title || '视频'}`, 'gray');
            log(`     ${r.mdPath}`, 'gray');
        }
        log(`\n📁 输出目录: ${OUTPUT_DIR}`);

        // Ask if open last report
        if (results.length > 0) {
            log('\n是否打开最后一个报告? (Y/n)', 'yellow');

            const rl = readline.createInterface({
                input: process.stdin,
                output: process.stdout
            });

            rl.question('', async (answer) => {
                rl.close();

                if (answer.toLowerCase() !== 'n') {
                    try {
                        const lastResult = results[results.length - 1];
                        execSync(`start "" "${lastResult.mdPath}"`);
                        log('  ✓ 已打开报告', 'green');
                    } catch (e) {
                        log(`  请手动打开报告`, 'gray');
                    }
                }

                log('\n' + '='.repeat(50) + '\n', 'green');
            });
        }

    } catch (e) {
        log(`\n✗ 错误: ${e.message}`, 'yellow');
        process.exit(1);
    }
}

// Handle errors
process.on('uncaughtException', (e) => {
    log(`\n✗ 未捕获的错误: ${e.message}`, 'yellow');
    process.exit(1);
});

main();
