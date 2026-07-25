"""
从 OpenStreetMap 分批下载武汉水系真实数据
"""
import urllib.request, json, time, sys, os

OUTDIR = r"c:\Users\Sakuar\Desktop\vscode测试\武汉四时花信空间分布可交互网页地图\武汉美食地图"
HEADERS = {"Content-Type": "text/plain", "User-Agent": "WuhanWaterMap/1.0"}
BASE_URL = "https://overpass-api.de/api/interpreter"

# 武汉范围拆分为 6 个小块
BLOCKS = [
    ("NW", 30.5, 113.6, 31.4, 114.3),
    ("NC", 30.5, 114.3, 31.4, 114.8),
    ("NE", 30.5, 114.8, 31.4, 115.2),
    ("SW", 29.8, 113.6, 30.5, 114.3),
    ("SC", 29.8, 114.3, 30.5, 114.8),
    ("SE", 29.8, 114.8, 30.5, 115.2),
]

all_elements = []

for block_name, south, west, north, east in BLOCKS:
    print(f"\n[{block_name}] bbox=({south},{west},{north},{east}) ...", end=" ", flush=True)

    query = (
        f'[out:json][timeout:60];'
        f'(way["water"]({south},{west},{north},{east});'
        f'way["waterway"="river"]({south},{west},{north},{east});'
        f'relation["water"]({south},{west},{north},{east});'
        f'relation["waterway"="river"]({south},{west},{north},{east});'
        f');out geom;'
    )

    try:
        req = urllib.request.Request(BASE_URL, data=query.encode("utf-8"), headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=120)
        raw = resp.read()
        d = json.loads(raw)
        els = d.get("elements", [])
        all_elements.extend(els)
        print(f"OK: {len(els)} features ({len(raw)} bytes)")

        # 分类统计
        n_river = sum(1 for e in els if e.get("tags", {}).get("waterway") == "river")
        n_water = sum(1 for e in els if e.get("tags", {}).get("water") and not e.get("tags", {}).get("waterway"))
        print(f"       rivers={n_river}, lakes/ponds={n_water}")

    except Exception as ex:
        print(f"FAILED: {ex}")

    time.sleep(1.5)

# 去重
seen = set()
unique = []
for e in all_elements:
    eid = (e.get("type", ""), e.get("id", 0))
    if eid not in seen:
        seen.add(eid)
        unique.append(e)

print(f"\n{'='*50}")
print(f"总计: {len(all_elements)} raw → {len(unique)} unique features")

# 分类
rivers = [e for e in unique if e.get("tags", {}).get("waterway") == "river"]
lakes = [e for e in unique if e.get("tags", {}).get("water") == "lake"]
ponds = [e for e in unique if e.get("tags", {}).get("water") in ("pond", "reservoir", "basin")]
other = [e for e in unique if e not in rivers and e not in lakes and e not in ponds]

print(f"  河流(river): {len(rivers)}")
print(f"  湖泊(lake):  {len(lakes)}")
print(f"  池塘/水库:   {len(ponds)}")
print(f"  其他:        {len(other)}")

# 打印湖泊名称
print(f"\n--- 湖泊列表 ---")
for e in lakes:
    tags = e.get("tags", {})
    nm = tags.get("name", "") or tags.get("name:zh", "") or tags.get("name:en", "") or "(未命名)"
    geom = e.get("geometry", [])
    npts = len(geom) if geom else 0
    # 计算中心点
    if geom and len(geom) >= 3:
        lats = [p["lat"] for p in geom]
        lngs = [p["lon"] for p in geom]
        clat = sum(lats) / len(lats)
        clng = sum(lngs) / len(lngs)
        dlat = max(lats) - min(lats)
        dlng = max(lngs) - min(lngs)
        area_approx = dlat * dlng * 111 * 111 * 0.85  # 粗略面积 km²
        print(f"  {nm:12s}  pts={npts:4d}  center=({clng:.4f},{clat:.4f})  ~{area_approx:.1f}km²")

# 保存完整数据
outpath = os.path.join(OUTDIR, "wuhan_water_osm_full.json")
output = {
    "source": "OpenStreetMap (overpass-api.de)",
    "region": "Wuhan, China",
    "bounds": "29.8,113.6,31.4,115.2",
    "total_features": len(unique),
    "rivers": len(rivers),
    "lakes": len(lakes),
    "ponds_reservoirs": len(ponds),
    "elements": unique
}
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n已保存: wuhan_water_osm_full.json ({os.path.getsize(outpath)} bytes)")
print("数据来源: OpenStreetMap 真实地理数据")
