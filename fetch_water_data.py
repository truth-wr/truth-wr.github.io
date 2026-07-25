"""
武汉水系数据采集脚本
使用天地图API查询武汉市河流、湖泊数据
"""
import urllib.request, urllib.parse, json, time

TK = "74fd204fef79a62c371ff28f9581eb2c"
BASE = "https://api.tianditu.gov.cn"

# 武汉范围
WUHAN_BOUND = "113.7,29.9,115.2,31.3"

def tianditu_search(keyword, start=0, count=100):
    """天地图搜索API"""
    post = json.dumps({
        "keyWord": keyword,
        "mapBound": WUHAN_BOUND,
        "level": 10,
        "queryType": 1,
        "start": start,
        "count": count
    })
    url = f"{BASE}/search?postStr={urllib.parse.quote(post)}&type=query&tk={TK}"
    req = urllib.request.Request(url, headers={"User-Agent": "WaterMap/1.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def tianditu_geocode(address):
    """天地图地理编码 - 获取某点的行政区划"""
    post = json.dumps({"keyWord": address})
    url = f"{BASE}/geocoder?postStr={urllib.parse.quote(post)}&type=geocode&tk={TK}"
    req = urllib.request.Request(url, headers={"User-Agent": "WaterMap/1.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except:
        return None

# ====== 搜索湖泊 ======
print("=" * 60)
print("搜索武汉湖泊数据...")
print("=" * 60)

lake_names = [
    "东湖", "汤逊湖", "梁子湖", "南湖", "沙湖", "墨水湖", "月湖",
    "金银湖", "后官湖", "严西湖", "严东湖", "紫阳湖", "莲花湖",
    "沉湖", "涨渡湖", "武湖", "木兰湖", "菱角湖", "北湖", "南太子湖",
    "三角湖", "龙阳湖", "野芷湖", "黄家湖", "青菱湖", "野湖",
    "斧头湖", "鲁湖", "梁子后湖", "陶家大湖", "七湖", "安仁湖",
    "柴泊湖", "朱山湖", "小奓湖", "西湖", "北湖", "后湖"
]

all_lakes = []
for name in lake_names:
    print(f"  查询: {name}...", end=" ")
    time.sleep(0.3)  # 限速
    result = tianditu_search(name, count=5)
    if result and result.get("status") == "0" and result.get("prompt") == "ok":
        pois = result.get("pois", [])
        # 筛选在武汉范围内的结果
        wuhan_pois = []
        for p in pois:
            lon = float(p.get("lon", 0))
            lat = float(p.get("lat", 0))
            if 113.6 < lon < 115.3 and 29.8 < lat < 31.4:
                wuhan_pois.append(p)

        if wuhan_pois:
            p = wuhan_pois[0]
            all_lakes.append({
                "name": p.get("name", name),
                "lon": float(p.get("lon", 0)),
                "lat": float(p.get("lat", 0)),
                "address": p.get("address", ""),
                "phone": p.get("phone", ""),
                "area": p.get("area", ""),
                "type": p.get("type", ""),
                "admin": p.get("admin", "")
            })
            print(f"OK (lon={p['lon']}, lat={p['lat']})")
        else:
            print("不在武汉范围")
    else:
        status = result.get("status") if result else "None"
        print(f"未找到 (status={status})")

print(f"\n湖泊共找到: {len(all_lakes)} 个")

# ====== 搜索河流 ======
print("\n" + "=" * 60)
print("搜索武汉河流数据...")
print("=" * 60)

river_names = [
    "长江武汉段", "汉江武汉段", "府河", "滠水", "倒水", "举水",
    "金水河", "巡司河", "东荆河", "通顺河", "沙河"
]

all_rivers = []
for name in river_names:
    print(f"  查询: {name}...", end=" ")
    time.sleep(0.3)
    result = tianditu_search(name, count=5)
    if result and result.get("status") == "0":
        pois = result.get("pois", [])
        wuhan_pois = []
        for p in pois:
            lon = float(p.get("lon", 0))
            lat = float(p.get("lat", 0))
            if 113.6 < lon < 115.3 and 29.8 < lat < 31.4:
                wuhan_pois.append(p)

        if wuhan_pois:
            p = wuhan_pois[0]
            all_rivers.append({
                "name": p.get("name", name),
                "lon": float(p.get("lon", 0)),
                "lat": float(p.get("lat", 0)),
                "address": p.get("address", ""),
                "type": p.get("type", "")
            })
            print(f"OK (lon={p['lon']}, lat={p['lat']})")
        else:
            print("不在武汉范围")
    else:
        print("未找到")

print(f"\n河流共找到: {len(all_rivers)} 个")

# ====== 搜索水库 ======
print("\n" + "=" * 60)
print("搜索武汉水库数据...")
print("=" * 60)

reservoir_names = [
    "夏家寺水库", "梅店水库", "道观河水库", "院基寺水库", "泥河水库"
]

all_reservoirs = []
for name in reservoir_names:
    print(f"  查询: {name}...", end=" ")
    time.sleep(0.3)
    result = tianditu_search(name, count=3)
    if result and result.get("status") == "0":
        pois = result.get("pois", [])
        if pois:
            p = pois[0]
            lon = float(p.get("lon", 0))
            lat = float(p.get("lat", 0))
            if 113.6 < lon < 115.3 and 29.8 < lat < 31.4:
                all_reservoirs.append({
                    "name": p.get("name", name),
                    "lon": lon, "lat": lat,
                    "address": p.get("address", ""),
                    "type": "水库"
                })
                print(f"OK (lon={p['lon']}, lat={p['lat']})")
            else:
                print("不在武汉范围")
        else:
            print("未找到")
    else:
        print("未找到")

print(f"\n水库共找到: {len(all_reservoirs)} 个")

# ====== 汇总保存 ======
output = {
    "source": "天地图API (Tianditu)",
    "region": "武汉市",
    "bounds": WUHAN_BOUND,
    "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    "lakes": all_lakes,
    "rivers": all_rivers,
    "reservoirs": all_reservoirs,
    "summary": {
        "total_lakes": len(all_lakes),
        "total_rivers": len(all_rivers),
        "total_reservoirs": len(all_reservoirs)
    }
}

outpath = r"c:\Users\Sakuar\Desktop\vscode测试\武汉四时花信空间分布可交互网页地图\武汉美食地图\wuhan_water_tianditu.json"
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n{'=' * 60}")
print(f"数据已保存: wuhan_water_tianditu.json")
print(f"湖泊 {len(all_lakes)} | 河流 {len(all_rivers)} | 水库 {len(all_reservoirs)}")
print(f"总计 {len(all_lakes)+len(all_rivers)+len(all_reservoirs)} 条水系记录")
print(f"{'=' * 60}")

# 打印完整列表
print("\n--- 湖泊列表 ---")
for l in all_lakes:
    print(f"  {l['name']:8s}  lng={l['lon']:.4f}  lat={l['lat']:.4f}  addr={l.get('address','')[:30]}")
print("\n--- 河流列表 ---")
for r in all_rivers:
    print(f"  {r['name']:8s}  lng={r['lon']:.4f}  lat={r['lat']:.4f}")
print("\n--- 水库列表 ---")
for r in all_reservoirs:
    print(f"  {r['name']:8s}  lng={r['lon']:.4f}  lat={r['lat']:.4f}")
