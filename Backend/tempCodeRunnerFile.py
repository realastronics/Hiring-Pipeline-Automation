from database import supabase

@app.get("/test-db")
def test_db():
    result = supabase.table("companies").select("*").execute()
    return {"status": "connected", "data": result.data}