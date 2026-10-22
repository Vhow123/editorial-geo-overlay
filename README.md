# editorial-geo-overlay

把旅行摄影做成独立杂志 / 旅行小志风格的地理视觉作品。

原片不重新生成，只在天空、海面等负空间叠一层真实路网地图，红点标拍摄点，地名和坐标只用实查结果，配罗盘和比例尺。只输出主图，不输出地图图层文件。

## 这是什么

- 输入：一张旅行摄影原图，最好是带 EXIF 的手机原文件。
- 输出：一张同尺寸、同画幅的成品图，地图只出现在负空间，不遮挡摄影主体。
- 地图默认是真实路网，不是示意等高线、不是装饰性线条。
- 地名、坐标、海拔和朝向只用实查结果，没查到的不写、不猜。

## 版式

默认版式来自西安参考图的要素：

- 左上角大号衬线城市名，字母间留空，下面是两位的经纬度。
- 左侧有罗盘，标 N、E、S、W，下面有 0、1、2、4 km 比例尺，比例尺按地图实际宽度算，不照抄别的图。
- 地图是真实街道网，细线、低饱和米白，边缘约 70 px 内渐隐，没有方形地图卡片和边框。
- 拍摄点是一个带白圈的红点，旁边是实查的地名；附近地点最多再标一到两个，且按各自坐标投影落点，不随手放在顺眼的位置。
- 只加约 3% 的轻微纸张颗粒，不改变原片色彩和光影。

## 在 Muse 里使用

不用记命令，技能已经装好时，直接发图加一句话就行：

> 做成杂志风地理图，地图放天空，红点标拍摄点

如果照片本身没有 GPS，就顺手告诉地点；如果不想在图上印坐标，也可以直接说不要印坐标。

## 工作流程

1. 先读原片 EXIF，取经纬度、海拔、朝向和拍摄时间；用户留空地点不等于照片没有 GPS。
2. 用 OpenStreetMap Nominatim 反查行政层级和附近地点，层级缺失的不补，村名不同的条目不合并。
3. 用 OpenStreetMap Overpass 分两档取真实路网，先取主干道，再取次干道，502 或超时要重试，不要回退到凭空画的等高线。
4. 按经纬度把道路和地点投影到地图区域，北朝上，比例尺按地图宽度实算。
5. 先看图再交付：检查这是不是真实路网、标题罗盘比例尺是否可读、标签有没有被路网压住、地图有没有盖住主体。

## 手动跑脚本

```bash
python3 scripts/make_editorial_geo.py \
  --src photo.jpg \
  --osm-major osm_major.json \
  --osm-minor osm_minor.json \
  --config references/example-config.json \
  --out finished.jpg
```

`references/example-config.json` 只是格式示例，里面的坐标和地名都是占位，跑之前必须换成实查值。

Overpass 查询示例（以拍摄点为中心，先定好经纬度范围再查）：

```text
way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"](south,west,north,east); out geom;
way["highway"~"^(unclassified|residential|road|living_street)$"](south,west,north,east); out geom;
```

## 目录结构

```text
SKILL.md                          技能完整流程
skill.yaml                        技能元数据
scripts/make_editorial_geo.py     合成脚本，只输出成品图
references/example-config.json    配置格式示例，全部是占位值
README.md                         本文件
```

## 要求

- Python 3，Pillow；边缘渐隐用 NumPy，没有 NumPy 时会跳过渐隐并提示。
- DejaVu Serif / DejaVu Sans 字体，用于标题、罗盘和标签。
- 能访问 OpenStreetMap Nominatim 和 Overpass。

## 诚实规则

- 没查到的地名、山名、路名、风电场名不写。
- 郊区或山边的路网本来就稀，这是真实结果，不用人手加密。
- 等高线只有用户明确要求、并接受“示意、非实测”标注时才用，默认不用。
- 地图图层、Overpass 原始 JSON 和合成脚本是工作文件，不作为成品交付；用户明确要图层时再另给，并说明白底上白线看起来会很淡。

## 数据来源

- 拍摄点、海拔和朝向：照片 EXIF。
- 行政层级和附近地点：OpenStreetMap Nominatim。
- 道路几何：OpenStreetMap Overpass。
- 地图数据 © OpenStreetMap contributors。
