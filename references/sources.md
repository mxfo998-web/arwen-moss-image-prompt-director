# 来源与维护

版本：1.1.0；资料核查日期：2026-10-22。此次更新按用户要求增加语言选择：默认普通场景中文，复杂场景提供等义中英双版，明确指定语言优先；上游编译器和模型事实未改动。

## 上游与接口

- 官方仓库：https://github.com/OpenMOSS/MOSS-Image
- 官方提示词 Skill：https://github.com/OpenMOSS/MOSS-Image/tree/main/skills/moss-image-prompt-enhancer
- 中文用户指南：https://github.com/OpenMOSS/MOSS-Image/blob/main/USERGUIDE_ZH.md
- Base：https://huggingface.co/OpenMOSS-Team/MOSS-Image-Base
- SFT：https://huggingface.co/OpenMOSS-Team/MOSS-Image-SFT
- 技术报告：https://arxiv.org/html/2610.23374v1
- ComfyUI 适配：https://github.com/OpenMOSS/MOSS-Image/blob/main/comfyui/README.md
- Comfy-Org 权重：https://huggingface.co/Comfy-Org/MOSS-Image
- Comfy-Org 模板：https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_moss_image_t2i.json

本包以官方接口和模式分流为基础，重新组织中文工作流程、视觉知识和反馈规则。未复制社区限制改编的规则文本。

## 固定的上游文件

scripts/compile_prompt.py 来自 OpenMOSS/MOSS-Image，保持原样：

- revision：52b87fca23acedc399d062d593bec388aee9926a
- 上游路径：skills/moss-image-prompt-enhancer/scripts/compile_prompt.py
- SHA-256：1d75780cf9f22f9ebed1a33d8100158f8d73ebfe59a5d435c1cc8c8e1374a8a3

LICENSE 是该仓库 Apache-2.0 许可证原文，NOTICE 记录归属。完整机器记录见 upstream.json。scripts/validate_prompt.py 和 tests 是本包新增内容。

更新时先检查上游 schema/编译器，再运行回归校验；不要将新版文件与旧版字段约定混用。只在用户授权维护 Skill 时修改安装文件。

## 视觉知识参考

- ARRI 灯光手册及布光案例：https://www.arri.com/en/learn/lighting/lighting-handbook
- ASC《沙丘2》摄影制作访谈：https://theasc.com/article/expanding-view-dune-part-two/
- 景别、角度、焦点、构图和灯光分类：https://www.studiobinder.com/camera-shots/
- W3C 中文排版需求：https://www.w3.org/TR/clreq/ （当前为持续修订草案，作为排版参考，不声称是 MOSS 支持规范）

视觉知识是基于通用摄影/设计原则写成的选择指南，不是相应来源对 MOSS 的实测结论。本包不包含这些来源的图片、长篇正文或字体。

## 社区线索

- https://github.com/Moeblack/moss-image-prompt-skill
- https://github.com/slmonker/ComfyUI-MOSS-PromptEnhancer
- https://github.com/0Printemps0/ComfyUI-MOSSLayout
- https://github.com/MaxKruse/ComfyUI-PromptEnhancer
- https://github.com/tw2ni9-arisu/dsh-moss-image-prompt-enhancer

本地尚无出图复测记录。未来新增记录应保留来源、适用条件、失败例和日期，而不是复制整份社区 Skill 或宣布新通用规律。
