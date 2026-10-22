# MOSS Layout：海报、影视静帧与多格

海报与影视画面使用同一公开 schema；题材变化不增加字段。

## 草稿字段

~~~json
{
  "width": 1024,
  "height": 1536,
  "bbox_coord_space": "abs",
  "bbox_format": "xyxy",
  "summary": {
    "canvas": "single",
    "caption": "完整的全局画面描述"
  },
  "items": [
    {
      "label": "text",
      "caption": "文字的外观、字重、颜色、位置关系",
      "text": "准确文字\n准确换行",
      "bbox": [96, 96, 928, 320]
    }
  ]
}
~~~

这段只说明草稿结构，不是直接粘贴的最终提示词。

- 顶层字段固定为 width、height、bbox_coord_space、bbox_format、summary、items。
- width/height：正整数、16 的倍数，与生成尺寸一致。
- 草稿框为左上原点实际像素 [x_min,y_min,x_max,y_max]；x 向右、y 向下，不用百分比或 0–1000 归一化。
- summary 必须有非空 caption；可选 meta、canvas、palette。canvas 枚举为 single、multi_panel、collage。
- items 为非空平坦数组；label 枚举为 object、character、text。每项必须有非空 caption、有效 bbox；text 项必须有非空 text。
- items 可选 tags、palette 字符串数组。画师/媒介/颜色等信息只在有用时填写，不为凑字段而加。
- 不添加 id、children、parent、elements、shots、camera_angle、font_size 等自定义字段。意图写在对应 caption 中。

## 分工

| 信息 | 放置位置 |
| --- | --- |
| 全局场景、媒介、电影色调、光线、统一景别/机位 | summary.caption |
| 某个人物的动作、朝向、表情、衣着、局部光影 | 该 character 的 caption |
| 物体外观、材质、朝向、接触与反射 | 该 object 的 caption |
| 文案、标点、大小写与换行 | text 项的 text |
| 字体类别、字重、颜色、层级、对齐与承载表面 | 同一 text 项的 caption |
| 位置与大致占幅 | bbox |

同一组杯碟等紧密组合可为一个可见单元；需要独立摆放的标题、人物、物体分开。分组以控制需求为准，不机械地给每个细节建框。

## 构图与文字检查

- bbox 是位置约束，不表示要画边框。只有用户要求时才描述面板、边框、贴纸或字幕底板。
- 框、语言方位和人物朝向应一致；保留自然遮挡、交叠和出入画空间，不将所有重叠判错。
- 短标题、长段落需要不同的框。明确行序和换行；文字过密先重新分配区域或调整画布，不擅自删改用户文案。
- 可粗估每行字数和高度，但模型不保证精确字体度量。几何通过不代表文字能读或字体会准确还原。
- 提供准确文字而非“标题放这里”等占位。说明性注释不写进图片描述。
- 修改现有布局时保留未改元素；调整框之后同步检查阴影、遮挡、视线和阅读顺序。

## 编译与验证

调用随包 scripts/compile_prompt.py，输出一物理行 JSON。它会：

1. 检查草稿字段、尺寸、数字与边界。
2. 对左/上边缘取 floor、右/下取 ceil，然后减去画布中心。
3. 将坐标重排为 [y_min,x_min,y_max,x_max]。
4. 移除顶层 width/height，将标记改为 abs_centralized / yxyx，保留文字。

保持编译器不变，归属与版本见 sources.md。不要凭记忆手算最终坐标。用户提供 compiled JSON 时，先验证并还原为草稿：

~~~text
python "<Skill目录>/scripts/validate_prompt.py" existing.prompt.txt --kind compiled --width 1024 --height 1536 --draft-output recovered.draft.json
~~~

还原转换由脚本完成。再修改 recovered.draft.json 并重新编译。缺少原画布时不能可靠恢复，应先确认尺寸。

需要核对用户文案时，将“要出现的文字”保存为 JSON 字符串数组，执行：

~~~text
python "<Skill目录>/scripts/validate_prompt.py" poster.draft.json --kind draft --expect-text copy.json
python "<Skill目录>/scripts/validate_prompt.py" poster.prompt.txt --kind compiled --width 1024 --height 1536 --expect-text copy.json
~~~

对 Layout 检查文字项的原文与重复次数，不把其他 caption 内引用算成独立文字项。

## 影视与多格

- 单镜影视静帧可没有任何 text 项；不自动画字幕、镜号、摄影说明或黑边。
- 用户要多张独立镜头时，分别生成文件/提示词，共享人物、服装、道具、场景与光色约定。
- 用户要一张多格图时用 multi_panel，并在 summary.caption 明确行列、阅读顺序、分隔和全局风格。
- 多格的所有 bbox 仍是整个画布坐标，没有父子坐标或局部坐标。
- 每格不同的景别/机位放进该格相关 items 的 caption，summary 只写全板共同规则。背景/角色/道具分别落在该格范围内；同一角色出现多次时分别建立项，明确同一身份与所在格。
- 未要求画面注释时，镜头参数和台词说明留在提示词外。需要气泡时作为 text 项，明确说话人、气泡位置和指向关系。
