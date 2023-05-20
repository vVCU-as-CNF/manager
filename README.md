# Manager

Uses FastAPI

To run locally for development:
```bash
uvicorn main:app --reload
```

## Endpoints
Base URL: http://localhost:8000/
### OSM Manager
TODO

### Grafana Data
/grafana/vim_accounts
- lists all vim accounts and the dts of each

/grafana/dt/{dt_id}
- provides info about a specific dt