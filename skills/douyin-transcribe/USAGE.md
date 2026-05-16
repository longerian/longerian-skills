# 抖音视频转录工具

使用 Whisper GPU 加速转录抖音视频，自动生成 Markdown 报告。

## 使用方法

### 方式一：交互式（推荐）

```bash
cd D:\Dev\learn-longerian-skills\.agents\skills\douyin-transcribe
node douyin_transcribe.js
```

然后：
1. 粘贴抖音视频链接（支持多个链接，空格分隔）
2. 等待下载和转录
3. 自动打开 Markdown 报告

### 方式二：单个链接

```bash
node douyin_transcribe.js "https://www.douyin.com/jingxuan?modal_id=7637131372982149285"
```

### 方式三：批量处理

```bash
node douyin_transcribe.js --batch "url1,url2,url3"
```

## 输出文件

保存在 `C:\Users\Administrator\.longerian\data\douyin\`：

- `douyin_{时间戳}-report.md` - Markdown 格式报告
- `douyin_{时间戳}-transcript.txt` - 纯文本
- `douyin_{时间戳}.mp4` - 下载的视频

## 报告格式

```markdown
# {视频标题}

**作者**: {作者}
**转录时间**: 2026-05-16 20:15
**视频时长**: 140.6秒 (2.3分钟)
**转录耗时**: 7.4秒
**处理速度**: 19.0x 实时

---

## 📌 关键词

**高频词**: 英伟达、H200、松绑、阿里、腾讯、关税
**关键短语**: GPU加速、光模块、AI芯片、供应链

---

## 完整转录

{带有增强标点的转录文本}

---

## 分段转录 (带时间戳)

### [0:15] 第一段内容

### [0:30] 第二段内容
...
```

## 性能

- **GPU**: RTX 4070 SUPER
- **速度**: ~19x 实时 (2.3分钟视频 → 7秒)
- **模型**: Whisper large-v3-turbo

## 示例

测试转录结果：
- 视频: CPO光模块分析
- 时长: 2.3分钟
- 转录: 7.4秒
- 报告: `douyin_1778933514-report.md`
