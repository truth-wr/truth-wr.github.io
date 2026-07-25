"""
解析天地图水系 GeoJSON → 生成地图 JS 数据文件
筛选主要湖泊(面积>0.5km²)和主要河流，避免地图过于密集
"""
import json, os, math

DIR = r"c:\Users\Sakuar\Desktop\vscode测试\武汉四时花信空间分布可交互网页地图\武汉美食地图"

# 加载数据
with open(os.path.join(DIR, "wuhan_lakes_tianditu.json"), "r", encoding="utf-8") as f:
    lake_data = json.load(f)
with open(os.path.join(DIR, "wuhan_rivers_tianditu.json"), "r", encoding="utf-8") as f:
    river_data = json.load(f)

# ===== 处理湖泊 =====
def calc_area(coords, geom_type):
    """粗略计算面状要素面积 (km²)"""
    try:
        if geom_type == "Polygon":
            ring = coords[0]
        elif geom_type == "MultiPolygon":
            ring = coords[0][0]  # 取第一个多边形
        else:
            return 0
        lats = [p[1] for p in ring]
        lngs = [p[0] for p in ring]
        dlat = max(lats) - min(lats)
        dlng = max(lngs) - min(lngs)
        mid_lat = (max(lats) + min(lats)) / 2
        km_per_deg_lat = 111.32
        km_per_deg_lng = 111.32 * math.cos(mid_lat * math.pi / 180)
        return dlat * km_per_deg_lat * dlng * km_per_deg_lng
    except:
        return 0

lakes_processed = []
for f in lake_data.get("features", []):
    geom = f.get("geometry", {})
    gtype = geom.get("type", "Polygon")
    coords = geom.get("coordinates", [])
    area = calc_area(coords, gtype)
    props = f.get("properties", {})
    name = props.get("NAME", "") or props.get("name", "")

    # 只保留面积 > 1 km2 的湖泊
    if area < 1:
        continue

    # 计算中心点
    if gtype == "Polygon":
        ring = coords[0]
    elif gtype == "MultiPolygon":
        ring = coords[0][0]
    else:
        continue
    lats = [p[1] for p in ring]
    lngs = [p[0] for p in ring]
    center_lat = sum(lats) / len(lats)
    center_lng = sum(lngs) / len(lngs)

    lakes_processed.append({
        "name": name or "(未命名)",
        "area_km2": round(area, 2),
        "center": [round(center_lng, 5), round(center_lat, 5)],
        "ring": ring[::max(1, len(ring)//20)],  # 最多20个点
        "type": "large" if area > 10 else ("medium" if area > 1 else "small")
    })

# 按面积降序
lakes_processed.sort(key=lambda x: x["area_km2"], reverse=True)

print(f"湖泊: {len(lakes_processed)} 个 (已过滤微小水体)")
for l in lakes_processed[:25]:
    print(f"  {l['name']:12s} {l['area_km2']:8.1f} km2 [{l['type']}]")

# ===== 处理河流 =====
def calc_length(coords, geom_type):
    """粗略计算线状要素长度 (km)，只取主要线段"""
    try:
        if geom_type == "LineString":
            pts = coords
        elif geom_type == "MultiLineString":
            # 取最长的线段
            pts = max(coords, key=len)
        else:
            return 0
        total = 0
        for i in range(len(pts) - 1):
            dlat = pts[i+1][1] - pts[i][1]
            dlng = pts[i+1][0] - pts[i][0]
            mid_lat = (pts[i+1][1] + pts[i][1]) / 2
            km_lat = dlat * 111.32
            km_lng = dlng * 111.32 * math.cos(mid_lat * math.pi / 180)
            total += math.sqrt(km_lat**2 + km_lng**2)
        return total
    except:
        return 0

rivers_processed = []
for f in river_data.get("features", []):
    geom = f.get("geometry", {})
    gtype = geom.get("type", "LineString")
    coords = geom.get("coordinates", [])
    length = calc_length(coords, gtype)
    props = f.get("properties", {})
    name = props.get("NAME", "") or props.get("name", "")

    # 只保留长度 > 15km 的主要河流, 且要有名称
    if length < 15 or not name:
        continue

    # 简化坐标（每隔N个点取一个）
    step = max(1, len(coords) // 100) if gtype == "LineString" else 1
    if gtype == "LineString":
        simplified = coords[::step]
    else:
        main_line = max(coords, key=len)
        step2 = max(1, len(main_line) // 100)
        simplified = main_line[::step2]

    rivers_processed.append({
        "name": name or "(未命名)",
        "length_km": round(length, 2),
        "path": simplified,
        "type": "major" if length > 30 else ("medium" if length > 10 else "minor")
    })

rivers_processed.sort(key=lambda x: x["length_km"], reverse=True)

print(f"\n河流: {len(rivers_processed)} 条 (已过滤短小沟渠)")
for r in rivers_processed[:20]:
    print(f"  {r['name']:12s} {r['length_km']:8.1f} km [{r['type']}]")

# ===== 输出可直接嵌入的 JS =====
js_output = "// 武汉水系真实数据 (来源: 天地图 WFS, 已筛选主要水体)\n"
js_output += "var WATER_LAKES = " + json.dumps(lakes_processed, ensure_ascii=False, indent=2) + ";\n"
js_output += "var WATER_RIVERS = " + json.dumps(rivers_processed, ensure_ascii=False, indent=2) + ";\n"

outpath = os.path.join(DIR, "wuhan_water_data.js")
with open(outpath, "w", encoding="utf-8") as f:
    f.write(js_output)

print(f"\n已生成: wuhan_water_data.js")
print(f"湖泊 {len(lakes_processed)} | 河流 {len(rivers_processed)}")
tsize = os.path.getsize(outpath)
print(f"文件大小: {tsize} bytes ({tsize//1024} KB)")
