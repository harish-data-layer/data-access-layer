import os, re, time, argparse, urllib.parse, asyncio
from datetime import datetime
import httpx
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from config_db import SessionLocal, SapData, ServiceList

# Settings you can easily change
CHUNK_SIZE = 1000      # DB records per row
MAX_PAGES = 20         # SAP pages to fetch at once (20 * 1000 = 20k rows max)
PAGE_SIZE = 1000       # SAP page limit

# SAP connection from .env
SAP_URL  = f"{os.getenv('SAP_PROTOCOL','https')}://{os.getenv('SAP_HOST')}:{os.getenv('SAP_PORT')}/sap/opu/odata/sap"
SAP_AUTH = (os.getenv("SAP_USER"), os.getenv("SAP_PASSWORD"))
SAP_HDR  = {"Accept": "application/json", "sap-client": os.getenv("SAP_CLIENT", "100")}


def get_latest_date(records, col):
    """Finds the newest date in a list of SAP records."""
    if not col: return None
    dates = []
    for r in records:
        v = str(r.get(col, ""))
        m = re.search(r'/Date\((\d+).*\)/', v)
        if m: dates.append(datetime.fromtimestamp(int(m.group(1))/1000))
        elif 'T' in v:
            try: dates.append(datetime.fromisoformat(v.replace('Z','+00:00')))
            except: pass
    return max(dates) if dates else None


def build_filter(s, since, to_date):
    """Builds the URL filter for picking dates."""
    if not s.delta_column: return ""
    parts = []
    if since:   parts.append(f"{s.delta_column} ge datetime'{since.strftime('%Y-%m-%dT%H:%M:%S')}'")
    if to_date: parts.append(f"{s.delta_column} le datetime'{to_date.strftime('%Y-%m-%dT%H:%M:%S')}'")
    return f"&$filter={urllib.parse.quote(' and '.join(parts))}" if parts else ""


async def fetch_service(http, s, since, to_date, limit):
    """Hits SAP to grab the data (either a quick limit or all pages)."""
    t0 = time.time()

    # 1. Quick mode (used if you pass --limit)
    if limit:
        url = f"{SAP_URL}{s.endpoint}?$format=json&$top={limit}{build_filter(s, since, to_date)}"
        try:
            r = await http.get(url)
            if r.status_code == 403: return None
            data = r.json().get("d",{}).get("results",[])
        except: return None
        return {"svc":s, "data":data, "since":since, "took":round(time.time()-t0, 2)} if data else None

    # 2. Full mode (pulls all data by hitting many pages at once)
    urls = [f"{SAP_URL}{s.endpoint}?$format=json&$top={PAGE_SIZE}&$skip={i*PAGE_SIZE}{build_filter(s, since, to_date)}" for i in range(MAX_PAGES)]
    try:
        responses = await asyncio.gather(*[http.get(u) for u in urls], return_exceptions=True)
    except: return None

    data = []
    for r in responses:
        if isinstance(r, Exception) or r.status_code != 200: break
        batch = r.json().get("d",{}).get("results",[])
        if not batch: break
        data.extend(batch)
        if len(batch) < PAGE_SIZE: break  # Reached the last page

    return {"svc":s, "data":data, "since":since, "took":round(time.time()-t0, 2)} if data else None


def fetch_and_store(from_date=None, to_date=None, limit=None):
    """Main job: gets services, fetches data, and saves to database."""
    t0 = time.time()
    print(f"\n--- SAP Fetch | {datetime.now().strftime('%d-%b %H:%M')} ---\n")

    db = SessionLocal()
    services = db.query(ServiceList).filter_by(is_active=True).all()
    if not services: print("No services found"); return

    # Check when we last pulled each service
    info = []
    for s in services:
        prev = db.query(SapData.last_data_timestamp).filter_by(service_name=s.service_name).first()
        info.append((s, from_date or (prev[0] if prev else None)))

    # Run the fetch in parallel for maximum speed
    async def go():
        limits = httpx.Limits(max_connections=100)
        async with httpx.AsyncClient(auth=SAP_AUTH, headers=SAP_HDR, verify=False, timeout=30, limits=limits) as http:
            return await asyncio.gather(*[fetch_service(http, s, since, to_date, limit) for s, since in info])

    results = asyncio.run(go())

    # Save to database in 1000-record chunks
    for res in results:
        if not res: continue
        s, data, since, took = res["svc"], res["data"], res["since"], res["took"]
        delta = since and s.delta_column
        
        # If it's a full refresh, wipe old data first
        if not delta:
            db.query(SapData).filter_by(service_name=s.service_name).delete()
            db.commit()

        # Insert chunks
        for i in range(0, len(data), CHUNK_SIZE):
            chunk = data[i:i + CHUNK_SIZE]
            newest = get_latest_date(chunk, s.delta_column)
            
            db.execute(insert(SapData).values(
                service_name=s.service_name, endpoint=s.endpoint,
                record_count=len(chunk), payload=chunk,
                last_data_timestamp=newest or func.now(), time_taken_seconds=took,
                freshpull=len(chunk)
            ))
            
        db.commit()
        print(f"  {s.service_name} - {len(data)} rows [{took}s]")

    print(f"\n--- done in {round(time.time()-t0, 2)}s ---\n")
    db.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--from",  dest="from_date", type=str)
    p.add_argument("--to",    dest="to_date",   type=str)
    p.add_argument("--limit", type=int)
    a = p.parse_args()
    
    fetch_and_store(
        from_date = datetime.fromisoformat(a.from_date) if a.from_date else None,
        to_date   = datetime.fromisoformat(a.to_date)   if a.to_date   else None,
        limit     = a.limit
    )
